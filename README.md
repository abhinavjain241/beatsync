# Beatport Playlist Downloader

A modern web application that downloads music from Beatport playlists by scraping track information and downloading audio from SoundCloud or YouTube. Features both a web UI and command-line interface.

## Features

- Modern web interface for easy downloads
- **NEW: Album art URL support - Use direct image URLs or local paths in JSON files**
- **NEW: Enhanced track matching - Intelligently parses artists, track names, and mix types (Extended Mix, Remix, etc.)**
- **NEW: Advanced source selection - Compares top 5 results from each platform for best match**
- **NEW: Smart relevance scoring - Balances track name accuracy with duration (10% threshold)**
- **NEW: Automatic MP3 metadata tagging - Embeds artist, title, label, genre, BPM, key, and album art**
- **NEW: Rekordbox-optimized metadata - ID3v2.3 tags with proper encoding for DJ software**
- **NEW: Smart track matching - Validates search results to ensure correct tracks (50% minimum match)**
- **NEW: Uses actual track metadata from SoundCloud/YouTube for accurate filenames**
- **NEW: Intelligent duplicate detection - Recognizes similar filenames (80% similarity threshold)**
- **NEW: AUTO mode - Searches BOTH SoundCloud AND YouTube, downloads the longer version**
- **NEW: JSON file input for fastest and most reliable track loading**
- **NEW: YouTube download support alongside SoundCloud**
- **NEW: Automatic filtering of DJ sets (max 15 minutes per track)**
- Scrapes Beatport playlist URLs to extract track information
- Intelligent duration comparison to get extended mixes
- Downloads as high-quality MP3 files with embedded metadata
- Real-time progress tracking with match score percentages
- Fallback to local HTML file if URL scraping fails
- Skip already downloaded tracks
- Detailed download summary
- Command-line interface for automation

## Requirements

- Python 3.7 or higher
- ffmpeg (required by yt-dlp for audio conversion)

## Installation

### 1. Install System Dependencies

**macOS:**
```bash
brew install ffmpeg node
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg nodejs npm python3-pip
```

**Windows:**
- Download ffmpeg from https://ffmpeg.org/download.html
- Download Node.js from https://nodejs.org/

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies

```bash
npm install
cd frontend && npm install && cd ..
```

## Usage

### Web Interface (Recommended)

1. Install dependencies (see Installation section)
2. Start the application:

```bash
npm run dev
```

3. Open your browser and go to `http://localhost:5173`
4. Enter your Beatport playlist URL and click "Download Playlist"
5. Watch the progress in real-time

For production build and server:

```bash
npm run build
npm run start
```

Then open `http://localhost:3000`

### Command Line

#### Using JSON File (Recommended)

The fastest and most reliable method is to use a JSON file with track data:

```bash
# AUTO mode (default) - Searches both SoundCloud and YouTube, downloads longer version
# Downloads to /Users/srinidhi/Music/{json_filename}/
python beatport_downloader.py --json-file tracks.json

# Example: basshouse_t100.json downloads to /Users/srinidhi/Music/basshouse_t100/
python beatport_downloader.py --json-file basshouse_t100.json

# SoundCloud only
python beatport_downloader.py --json-file tracks.json --source soundcloud

# YouTube only
python beatport_downloader.py --json-file tracks.json --source youtube

# Custom output directory (override default location)
python beatport_downloader.py --json-file tracks.json --output-dir /custom/path
```

**JSON Format (Basic):**
```json
[
  {
    "artist_name": "Artist Name",
    "song_name": "Track Name Extended Mix"
  },
  {
    "artist_name": "Another Artist",
    "song_name": "Another Track Original Mix"
  }
]
```

**JSON Format (With Metadata):**
```json
[
  {
    "artist_name": "Vintage Culture, Gabss",
    "song_name": "Lost Original Mix",
    "label_name": "AFFAIRS",
    "genre": "Melodic House & Techno",
    "bpm_key": "128 BPM - G Minor",
    "album_art": "./album_art_folder/track_image.jpg"
  }
]
```

When additional fields are provided, they will be automatically embedded as ID3 tags in the downloaded MP3 files.

#### Using Beatport URL

```bash
# AUTO mode (default) - Searches both sources
python beatport_downloader.py --url "https://www.beatport.com/chart/..."

# Specific source
python beatport_downloader.py --url "https://www.beatport.com/chart/..." --source youtube
```

#### Using Local HTML File

```bash
# AUTO mode (default) - Searches both sources
python beatport_downloader.py --local-html playlist.html

# Specific source
python beatport_downloader.py --local-html playlist.html --source soundcloud
```

#### Interactive Mode

```bash
python beatport_downloader.py
```

Select from multiple input options when prompted.

#### Additional Options

```bash
# Specify custom output directory
python beatport_downloader.py --json-file tracks.json --output-dir "my_music"

# Force a specific source
python beatport_downloader.py --json-file tracks.json --source youtube

# Combine options
python beatport_downloader.py --json-file tracks.json --source soundcloud --output-dir "my_music"

# Show help
python beatport_downloader.py --help
```

## How It Works

1. **Input**: Accepts JSON file (recommended), Beatport URL, or local HTML file
2. **Parsing**: Extracts Artist, Track Name, and Remix information from input
3. **Search**: In AUTO mode (default), searches BOTH SoundCloud AND YouTube simultaneously
4. **Validate**: Verifies search results match the requested track (50% minimum match score)
5. **Compare**: Gets duration information from both sources without downloading
6. **Filter**: Automatically filters out tracks longer than 15 minutes (likely DJ sets)
7. **Select**: Chooses the longer version (usually the extended mix) with match score display
8. **Check Duplicates**: Intelligently detects if track already exists (80% similarity)
9. **Download**: Downloads the selected audio and converts it to MP3 format
10. **Tag**: Embeds metadata (artist, title, label, genre, BPM, key, album art) if provided in JSON
11. **Save**: Saves files using the actual track title from SoundCloud/YouTube metadata

### Download Modes

- **AUTO** (default): Searches both SoundCloud and YouTube, downloads the longer version
  - Best for getting extended mixes and longest versions
  - Automatically compares durations and selects the better source
  - Example: `python beatport_downloader.py --json-file tracks.json`

- **SoundCloud**: Searches SoundCloud only
  - Good for DJ mixes, remixes, and electronic music
  - Example: `python beatport_downloader.py --json-file tracks.json --source soundcloud`

- **YouTube**: Searches YouTube only
  - Alternative source with broader music catalog
  - Example: `python beatport_downloader.py --json-file tracks.json --source youtube`

### Why Use JSON Files?

- **Fastest**: No need to wait for page loading or scrolling
- **Most Reliable**: No issues with authentication or dynamic content
- **Portable**: Easy to share, backup, and reuse
- **Flexible**: Works with any source (Beatport, Spotify, manual lists, etc.)

## Output

### When Using JSON Files

Files are automatically organized by playlist:
- **Location**: `/Users/srinidhi/Music/{json_filename}/`
- **Example**: `basshouse_t100.json` → `/Users/srinidhi/Music/basshouse_t100/`
- **Naming**: Uses actual track title from SoundCloud/YouTube (e.g., `Artist - Track Name (Extended Mix).mp3`)
- **Metadata**: If JSON includes metadata fields (label_name, genre, bpm_key, album_art), they are embedded as ID3 tags

### When Using URLs or HTML Files

Downloaded files are saved in the `downloads` folder (or specified output directory):
- **Location**: `./downloads/` (or custom via `--output-dir`)
- **Naming**: Uses actual track title from SoundCloud/YouTube (e.g., `Artist - Track Name (Official Audio).mp3`)
- **Metadata**: No metadata is embedded (requires JSON format with metadata fields)

## MP3 Metadata Support

When using JSON files with metadata fields, the downloader automatically embeds ID3v2.4 tags (fully compatible with macOS):

- **Title** (TIT2): From `song_name` field
- **Artist** (TPE1): From `artist_name` field
- **Album** (TALB): From `label_name` field (record label)
- **Genre** (TCON): From `genre` field
- **BPM** (TBPM): Extracted from `bpm_key` field (e.g., "128 BPM - G Minor" → 128)
- **Key** (TKEY): Extracted from `bpm_key` field (e.g., "128 BPM - G Minor" → "G Minor")
- **Album Art** (APIC): Embedded from image file specified in `album_art` field

The metadata writer:
- Uses ID3v2.4 format for maximum compatibility with macOS Music/iTunes
- Properly overwrites existing tags to ensure clean metadata
- Handles UTF-8 encoding for international characters
- Continues downloading if metadata writing fails

### Testing and Verifying Metadata

#### Test Metadata Writing System

Test that the metadata writing system works correctly:

```bash
python3 test_metadata_write.py
```

This creates a test MP3 and writes metadata to verify everything works.

#### Check Metadata in Existing Files

Check what metadata is in a downloaded MP3 file:

```bash
python3 check_mp3_metadata.py path/to/your/track.mp3
```

This shows all tags, album art status, and whether the file is properly tagged for Rekordbox.

#### Troubleshooting Metadata Issues

If metadata isn't showing in your files or Rekordbox:

1. **Run the test script first:**
   ```bash
   python3 test_metadata_write.py
   ```

2. **Check a downloaded file:**
   ```bash
   python3 check_mp3_metadata.py downloads/track.mp3
   ```

3. **Review the detailed logs** when downloading - look for:
   - `[Metadata] Starting metadata write`
   - `✓✓✓ METADATA WRITE SUCCESSFUL`
   - Any `⚠` warning messages

4. **See the troubleshooting guide:**
   ```bash
   cat METADATA_TROUBLESHOOTING.md
   ```

The new logging system provides detailed output showing exactly what metadata is being written and any errors that occur.

## Example

### Using JSON File with AUTO Mode

```bash
$ python beatport_downloader.py --json-file basshouse_t100.json

============================================================
Beatport Playlist Downloader
============================================================
Download mode: AUTO (searches both SoundCloud & YouTube, downloads longer version)
Output directory: /Users/srinidhi/Music/basshouse_t100

Reading JSON file: basshouse_t100.json
Found 100 tracks in JSON file
✓ Successfully parsed 100 tracks

Tracks to download:
------------------------------------------------------------
1. Artist Name - Track Name (Remix)
2. Another Artist - Another Track
...

Proceed with download? (y/n): y

Starting downloads...
============================================================

[1/20] Processing: Artist Name - Track Name
  Searching both SoundCloud and YouTube...
  SoundCloud: Artist Name - Track Name (Extended Mix) (6:45) [match: 95%]
  YouTube: Artist Name - Track Name (Radio Edit) (3:30) [match: 90%]
  ✓ Selected SoundCloud (longer version)
  Downloading: Artist Name - Track Name (Extended Mix).mp3
  ✓ Downloaded: Artist Name - Track Name (Extended Mix).mp3
  ✓ Added Artist: Artist Name | Label: AFFAIRS | 128 BPM - G Minor

[2/20] Processing: Another Artist - Another Track
  Searching both SoundCloud and YouTube...
  ⚠ SoundCloud result doesn't match query: Different Artist - Different Song
  YouTube only: Another Artist - Another Track (Extended Mix) (7:20) [match: 88%]
  Downloading: Another Artist - Another Track (Extended Mix).mp3
  ✓ Downloaded: Another Artist - Another Track (Extended Mix).mp3
  ✓ Added Artist: Another Artist | Label: Record Label | 130 BPM - F Minor

[3/20] Processing: Previously Downloaded - Track Name
  Searching both SoundCloud and YouTube...
  SoundCloud: Previously Downloaded - Track Name (Official Audio) (5:15) [match: 92%]
  YouTube: Previously Downloaded - Track Name (4:50) [match: 88%]
  ✓ Selected SoundCloud (longer version)
  ✓ Already exists: Previously Downloaded - Track Name (Official Audio).mp3

[4/20] Processing: DJ Name - Live Set
  Searching both SoundCloud and YouTube...
  SoundCloud: DJ Name - Full Live Set (125:30) - TOO LONG, skipping
  YouTube: DJ Name - Live Set Recording (90:45) - TOO LONG, skipping
  ✗ No valid tracks found

...

============================================================
Download Summary
============================================================
Total tracks:      20
Downloaded:        18
Already existed:   0
Failed:            2
Metadata added:    18

Success rate: 90.0%

Files saved to: /Users/srinidhi/Music/basshouse_t100/
============================================================
```

## Authentication & Private Playlists

**Important:** URLs like `https://www.beatport.com/library/playlists/XXXXXX` are private and require authentication.

For detailed solutions, see [AUTHENTICATION.md](AUTHENTICATION.md)

**Quick solutions:**
- Use public Beatport charts instead (Top 100, genre charts)
- Save the playlist page as HTML after logging in
- Use the debug helper: `python inspect_html.py` to analyze issues

## Troubleshooting

### No Tracks Found / Private Playlists

If the scraper can't find tracks, the playlist might require authentication:
1. Check `debug.html` (generated automatically) to see what was loaded
2. Run `python inspect_html.py` to analyze the HTML structure
3. See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed solutions

### 403 Forbidden Error

If you get a 403 error when accessing Beatport:
1. Save the playlist page as HTML from your browser
2. Use the local HTML file option when prompted

### yt-dlp Not Found

Install yt-dlp:
```bash
pip install yt-dlp
```

### ffmpeg Not Found

Install ffmpeg using the instructions in the Installation section.

### No Tracks Found

- Verify the URL points to a valid Beatport playlist
- Try using the local HTML file option
- Check that the page contains track information

## Project Structure

```
.
├── server.js                    # Node.js Express backend
├── beatport_downloader.py       # Python orchestration script
├── scraper.py                   # Beatport scraping logic (Selenium + BeautifulSoup)
├── downloader.py                # yt-dlp download logic
├── inspect_html.py              # Debug helper for analyzing HTML
├── requirements.txt             # Python dependencies
├── package.json                 # Node.js dependencies
├── AUTHENTICATION.md            # Guide for private playlists
├── frontend/                    # React web interface
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── components/
│   │       ├── DownloadForm.jsx
│   │       ├── ProgressDisplay.jsx
│   │       └── SummaryDisplay.jsx
│   └── package.json
└── downloads/                   # Output directory (created automatically)
```

## Troubleshooting

### Web UI Issues

**Port already in use:**
```bash
# Change the port
PORT=3001 npm run start
```

**Cannot connect to frontend/backend:**
- Make sure both services are running: `npm run dev`
- Check that `http://localhost:5173` (dev) or `http://localhost:3000` (production) is accessible
- Check browser console for errors (F12)

**Downloads not starting:**
- Verify Python and dependencies are installed
- Check server logs for errors
- Ensure the Beatport URL is valid

### Command Line Issues

**403 Forbidden Error:**
If you get a 403 error when accessing Beatport:
1. Save the playlist page as HTML from your browser
2. Use the local HTML file option when prompted

**yt-dlp Not Found:**
Install yt-dlp:
```bash
pip install yt-dlp
```

**ffmpeg Not Found:**
Install ffmpeg using the instructions in the Installation section.

**No Tracks Found:**
- Verify the URL points to a valid Beatport playlist
- Try using the local HTML file option
- Check that the page contains track information

## License

MIT
