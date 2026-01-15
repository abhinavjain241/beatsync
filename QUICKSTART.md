# Quick Start Guide

Get started with the Beatport Playlist Downloader in 3 simple steps.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Also install ffmpeg (required for audio conversion):

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH

## Step 2: Verify Installation

Run the dependency checker to make sure everything is installed:

```bash
python check_dependencies.py
```

You should see checkmarks for all dependencies.

## Step 3: Run the Downloader

### Option A: Command Line

```bash
python beatport_downloader.py "https://www.beatport.com/chart/your-playlist-url"
```

### Option B: Interactive Mode

```bash
python beatport_downloader.py
```

Then paste your Beatport playlist URL when prompted.

## That's It!

Your tracks will be downloaded to the `downloads/` folder as MP3 files.

## Troubleshooting

### Getting 403 Errors?

If the script can't access Beatport directly:

1. Open the playlist in your browser
2. Save the page as HTML (Ctrl+S or Cmd+S)
3. Run the script and provide the path to the HTML file when prompted

### Still Having Issues?

Check the full README.md for detailed troubleshooting steps.

## Example Output

```
============================================================
Beatport Playlist Downloader
============================================================

Fetching URL: https://www.beatport.com/chart/...
Found 20 tracks

Tracks to download:
------------------------------------------------------------
1. Artist Name - Track Title (Remix)
2. Another Artist - Another Track
...

Proceed with download? (y/n): y

Starting downloads...
============================================================

[1/20] Processing: Artist Name - Track Title
  Downloading: Artist Name - Track Title.mp3
  ✓ Downloaded: Artist Name - Track Title.mp3

...

============================================================
Download Summary
============================================================
Total tracks:      20
Downloaded:        18
Already existed:   0
Failed:            2

Success rate: 90.0%

Files saved to: downloads/
============================================================
```
