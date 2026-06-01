#!/usr/bin/env python3
"""
Download every track in a Spotify playlist via SoundCloud / YouTube.

Usage:
    python3 spotify_to_download.py <playlist_url> [--output-dir DIR] [--source auto|soundcloud|youtube]

Streams the same [TRACK_START] / [TRACK_RESULT] / [DOWNLOAD_FOLDER] / [DOWNLOADED_TRACKS]
protocol that server.js already parses, so it slots into the existing progress UI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from downloader import AudioDownloader
from spotify_client import SpotifyClient


def _emit(tag: str, payload) -> None:
    print(f"[{tag}] {json.dumps(payload, ensure_ascii=False)}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Spotify playlist → MP3 downloads")
    parser.add_argument("playlist_url", help="Spotify playlist URL, URI, or ID")
    parser.add_argument("--output-dir", default="downloads", help="Where to save the MP3s")
    parser.add_argument(
        "--source",
        default="auto",
        choices=["auto", "soundcloud", "youtube"],
        help="Search source(s) (default: auto = both, pick longer)",
    )
    parser.add_argument("--base-music-dir", help="If set, output to <base>/<playlist_name>/")
    args = parser.parse_args()

    print("[STAGE] Authenticating with Spotify", flush=True)
    client = SpotifyClient()
    _ = client.user_id  # forces OAuth on first run

    print("[STAGE] Fetching playlist", flush=True)
    meta = client.get_playlist_meta(args.playlist_url)
    tracks = client.get_playlist_tracks(args.playlist_url)
    if not tracks:
        print("[ERROR] Playlist is empty or unreadable", flush=True)
        return 1

    print(f"Found {len(tracks)} tracks in playlist '{meta['name']}'", flush=True)

    output_dir = args.output_dir
    if args.base_music_dir:
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in meta["name"]).strip()
        output_dir = os.path.join(args.base_music_dir, safe_name or meta["id"])

    downloader = AudioDownloader(output_dir=output_dir, source=args.source)
    print(f"[DOWNLOAD_FOLDER] {downloader.output_dir}", flush=True)

    downloaded: list[str] = []
    failed: list[dict] = []
    skipped: list[str] = []

    for i, track in enumerate(tracks, start=1):
        query = f"{track['artist']} - {track['title']}"
        print(f"[{i}/{len(tracks)}] Processing: {query}", flush=True)
        _emit("TRACK_START", {"index": i, "total": len(tracks), "query": query})

        try:
            success, filename, already = downloader.download_track(query, requested_track_info=track)
        except Exception as e:
            failed.append({"query": query, "error": str(e)})
            _emit("TRACK_RESULT", {"index": i, "status": "failed", "query": query, "error": str(e)})
            continue

        if success and already:
            skipped.append(filename or query)
            _emit("TRACK_RESULT", {"index": i, "status": "skipped", "query": query, "filename": filename})
        elif success:
            downloaded.append(filename or query)
            _emit("TRACK_RESULT", {"index": i, "status": "downloaded", "query": query, "filename": filename})
        else:
            failed.append({"query": query, "error": "not found"})
            _emit("TRACK_RESULT", {"index": i, "status": "failed", "query": query, "error": "not found"})

    _emit("DOWNLOADED_TRACKS", downloaded)
    _emit("FAILED_TRACKS", failed)
    _emit("SKIPPED_TRACKS", skipped)
    _emit(
        "SUMMARY",
        {
            "total": len(tracks),
            "downloaded": len(downloaded),
            "skipped": len(skipped),
            "failed": len(failed),
            "folder": downloader.output_dir,
        },
    )
    return 0 if not failed else 2


if __name__ == "__main__":
    sys.exit(main())
