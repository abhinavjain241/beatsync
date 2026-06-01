# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo does

Downloads Beatport playlists by scraping Beatport for track metadata, then searching SoundCloud + YouTube via `yt-dlp` for the actual audio, picking the best match, and writing ID3 tags + album art. Ships as both a CLI and an Express + React web app.

Also handles two Spotify-side flows:
- **Tracklist → Spotify playlist**: parse a pasted DJ-set tracklist and build a Spotify playlist by fuzzy-searching each entry.
- **Spotify playlist → downloads**: take a Spotify playlist URL, fetch its tracks, and feed them through the same SoundCloud/YouTube download pipeline.

## Common commands

```bash
# Web app — dev (frontend on :5173, backend on :3000, Vite proxies /api → :3000)
npm run dev

# Web app — production (Express serves built frontend from frontend/dist on :3000)
npm run build && npm start

# CLI — primary entry point
python3 beatport_downloader.py --json-file <path>       # fastest, most reliable
python3 beatport_downloader.py --url <beatport_url>     # uses Selenium
python3 beatport_downloader.py --local-html <path>      # saved Beatport HTML
python3 beatport_downloader.py --source soundcloud|youtube|auto   # default: auto

# Scrape a Beatport URL → JSON (no download)
python3 url_to_json.py <beatport_url> -o out.json
python3 url_to_json.py --login <url>                    # uses BEATPORT_EMAIL/PASSWORD from .env

# Sync a SoundCloud playlist (downloads new, skips existing)
python3 sc_playlist.py <playlist_url> -o <dir>

# Tracklist → Spotify playlist (file or stdin)
python3 tracklist_to_spotify.py --file set.txt --name "My Set"
cat set.txt | python3 tracklist_to_spotify.py --stdin --name "My Set" --public

# Spotify playlist → SoundCloud/YouTube downloads
python3 spotify_to_download.py "https://open.spotify.com/playlist/..." --source auto

# Verify environment
python3 check_dependencies.py
```

No automated test runner — `test_*.py` files are standalone scripts run directly (`python3 test_components.py`). `npm test` is a placeholder.

## Architecture

### Three-tier flow
1. **Frontend** (`frontend/`, React + Vite) — `DownloadForm` posts URL or HTML file to `/api/download`, then renders NDJSON streamed progress events via `ProgressDisplay` and `SummaryDisplay`.
2. **Express server** (`server.js`) — accepts URL/HTML upload, spawns Python subprocesses, parses their stdout into structured progress events, streams NDJSON back to the client. Uses `multer` for uploads to `tmpdir()`. Tracks live downloads in an in-memory `ongoingDownloads` Map keyed by timestamp.
3. **Python pipeline** — orchestrator + three single-responsibility modules. Always invoked as subprocesses by the server; never imported.

### Python module boundaries
- `beatport_downloader.py` — `BeatportPlaylistDownloader` orchestrator. Owns the `stats` dict, the `track_metadata_map` (used to feed metadata into the writer after download), and the `[STAGE]` / `[TRACK_START]` / `[TRACK_RESULT]` / `[DOWNLOAD_FOLDER]` etc. print protocol that the server parses.
- `scraper.py` — `BeatportScraper`. Selenium + headless Chrome (`webdriver_manager` auto-installs the driver). Handles URL fetch, local HTML load, JSON load, and HTML parsing via BeautifulSoup.
- `downloader.py` — `AudioDownloader`. Wraps `yt-dlp` CLI. In `auto` mode it fetches top 5 results from each of SoundCloud and YouTube, computes a relevance score per result (artists 40% / track 45% / mix 15%, see `calculate_match_score`), and if the two sources score within 10% picks the *longer* track. Filters out anything > 15 minutes (`MAX_DURATION`) to drop DJ sets. Has a separate `sync_soundcloud_playlist` path used by `sc_playlist.py`.
- `metadata_writer.py` — `MetadataWriter`. Mutagen ID3 tags (TIT2/TPE1/TALB/TCON/TBPM/TKEY/APIC) tuned for Rekordbox; supports both local file paths and URLs for album art.
- `url_to_json.py` — standalone scraper that emits the canonical JSON format consumed by `--json-file`. The server also reuses its `build_playlist_data()` via an inline Python script when converting uploaded HTML.
- `tracklist_parser.py` — pure parser for pasted DJ-set tracklists. Handles numbered (`1. ...`), timestamped (`4:50 ...`, `1:23:50 ...`), slash-joined pairs (`A - B / C - D` → two entries sharing one timestamp), and skips `ID - ID` / `(unreleased)` lines.
- `spotify_client.py` — `SpotifyClient` wraps `spotipy` with OAuth from `.env`, fuzzy-scored search (same artist 40% / title 45% weighting as `downloader.calculate_match_score`), playlist create/add, and `get_playlist_tracks(url)`. Token cache lives at `./.cache-spotify` and is reused by all CLI/server invocations.
- `tracklist_to_spotify.py` + `spotify_to_download.py` — CLI entry points for the two Spotify flows. Both emit the structured `[TAG] {json}` print protocol consumed by `server.js`.

### Critical: server ↔ Python progress protocol
Two parsers in `server.js` consume Python stdout. **Do not change these print formats without updating the parsers**:

The Beatport route (`/api/download`) does *bespoke* line parsing — it ships its events as `{type: 'stage'|'progress'|'summary'|'error'}` to the frontend:
- `[TRACK_START] {json}` / `[TRACK_RESULT] {json}` — per-track lifecycle
- `[DOWNLOAD_FOLDER] <path>` — final output dir
- `[DOWNLOADED_TRACKS] {json}` / `[FAILED_TRACKS] {json}` / `[SKIPPED_TRACKS] {json}` — summary arrays
- `[X/Y] Processing: ...` — drives the progress bar (`current`/`total`)
- `Found N tracks` — sets `total`

The Spotify routes (`/api/tracklist-to-spotify`, `/api/download-from-spotify`) use a generic `streamPython()` helper that turns any `[TAG] {json}` line into `{type: 'event', tag, payload}`. The frontend's `handleStreamMessage` in `App.jsx` translates those events into the same `progress`/`summary` shapes that `ProgressDisplay` and `SummaryDisplay` already consume. Recognized tags: `STAGE`, `TRACK_START`, `TRACK_RESULT`, `PLAYLIST_CREATED`, `DOWNLOAD_FOLDER`, `DOWNLOADED_TRACKS`, `FAILED_TRACKS`, `SKIPPED_TRACKS`, `SUMMARY`.

All Python prints use `flush=True` so the server sees them in real time.

### Output directories diverge by entry point
- Web UI / CLI default: `./downloads/`
- CLI with `--json-file` and `base_music_dir` passed: `<base_music_dir>/<json_basename>/` (server passes `~/Music`, so JSON `basshouse_t100.json` → `~/Music/basshouse_t100/`)

When fixing path bugs, check `BeatportPlaylistDownloader.run()` — it mutates `self.downloader.output_dir` based on these args.

## External dependencies & gotchas

- **Chrome + ChromeDriver** required for `--url` mode (`scraper.py` and `url_to_json.py --login`). `webdriver_manager` auto-fetches the driver; no manual install needed.
- **ffmpeg** required by `yt-dlp` for MP3 conversion. Not installed by `requirements.txt` — system package.
- **`.env`** — `BEATPORT_EMAIL` / `BEATPORT_PASSWORD` for authenticated URL scraping; `PORT` for the server. Spotify creds (`SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REDIRECT_URI`) are optional overrides — `spotify_client.py` defaults to the shared vibecheck app, which is grandfathered in past the Nov 2024 Spotify API restrictions on new apps. Don't move those defaults out of code without standing up a replacement app that has the equivalent endpoints unlocked.
- Saved Beatport HTML files generally don't contain track data (it's loaded dynamically). The server detects this case and returns a specific error directing users to use a URL or JSON file instead — keep that error path intact.

### Spotify OAuth: first-run flow
`SpotifyClient` uses `spotipy.SpotifyOAuth` with `cache_path=./.cache-spotify`. The first time any Spotify-touching script runs, spotipy opens a browser to authorize and writes the refresh token to `.cache-spotify`. After that, both CLI invocations and server subprocesses reuse the cache silently. When running via the web UI for the first time, the browser opens from the *server's* process (same machine in dev/local prod), so the user authorizes once. The cache file is gitignored (it has secrets).

Note: the default redirect URI is `http://127.0.0.1:8888/callback`. `localhost` was deprecated by Spotify in early 2025 — it now silently fails. The `127.0.0.1:8888/callback` URI **must be added to the vibecheck Spotify app's redirect-URI whitelist** in the developer dashboard alongside the existing `localhost:8000` entry. Port 8888 is just spotipy's one-shot capture server for the OAuth code; it has nothing to do with beatsync (:3000) or vibecheck (:8000).

### Beatport playlist creation: deliberately not supported
There's no usable free path to create Beatport playlists programmatically — `api.beatport.com` exists but is partner-only (LINK / DJ software / labels). The intentional substitute is the Spotify playlist flow. Don't add a Selenium-based "fake" Beatport playlist creator without an explicit request.

## Python conventions in this repo

This codebase predates the modern-typing conventions in the user's global CLAUDE.md. Existing files use `Optional[X]`, `List[X]`, `Dict[...]` and standard `print()`-for-output (the server depends on that). When adding **new** functions or modules, follow the global conventions (modern union syntax, `logging` module). When editing **existing** code, match the surrounding style to avoid churn — and never change a `print()` that the server parses.
