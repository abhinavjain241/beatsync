# Quick Start Guide

Get started with the Beatport Playlist Downloader in 3 simple steps.

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for web interface)
npm install
```

Also install ffmpeg (required for audio conversion):

**macOS:**
```bash
brew install ffmpeg node
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg nodejs npm
```

**Windows:**
Download ffmpeg from https://ffmpeg.org/download.html and Node.js from https://nodejs.org/

## Step 2: Verify Installation

Run the dependency checker to make sure everything is installed:

```bash
python check_dependencies.py
```

You should see checkmarks for all dependencies.

## Step 3: Test the Scraper (Important!)

Before using the web interface, test if the scraper works with your URL:

```bash
python test_scraper.py "https://www.beatport.com/chart/your-playlist-url"
```

**Expected output:**
- ✓ Fetched HTML successfully
- ✓ Found X tracks
- List of first 5 tracks

**If it fails:**
```bash
# Run the debug script to see why
python debug_beatport.py "your-url"
```

Common issue: Beatport may have changed their HTML structure. See [DEBUGGING.md](DEBUGGING.md) for solutions.

## Step 4: Run the Downloader

### Option A: Web Interface (Recommended)

```bash
# Build the frontend
npm run build

# Start the server
npm start
```

Then open `http://localhost:3000` in your browser and paste your Beatport URL!

### Option B: Command Line

```bash
# Non-interactive (for automation)
python beatport_downloader_web.py "https://www.beatport.com/chart/..."

# Interactive mode (with prompts)
python beatport_downloader.py "https://www.beatport.com/chart/..."
```

### Option C: Interactive with Local HTML File

If direct URL fetching fails:

```bash
python beatport_downloader.py
```

When prompted, provide a local HTML file saved from your browser.

## That's It!

Your tracks will be downloaded to the `downloads/` folder as MP3 files.

## Troubleshooting

### "Process exited with code 1" or "No tracks found"

This is the most common issue. The scraper couldn't extract tracks from the Beatport page.

**Quick fix:**
```bash
# See what's wrong
python debug_beatport.py "your-url"
```

**Common causes:**
1. Beatport changed their HTML structure (happens frequently)
2. Page loads content via JavaScript
3. Anti-scraping measures

**Solutions:**
- Save the Beatport page as HTML from your browser (Ctrl+S / Cmd+S)
- Use the interactive mode: `python beatport_downloader.py`
- See [DEBUGGING.md](DEBUGGING.md) for detailed fixes

### Getting 403 Errors?

If the script can't access Beatport directly:

1. Open the playlist in your browser
2. Save the page as HTML (Ctrl+S or Cmd+S)
3. Run the interactive script: `python beatport_downloader.py`
4. Provide the path to the HTML file when prompted

### Web Interface Not Loading?

```bash
# Make sure frontend is built
npm run build

# Verify files are present
npm run verify

# Check server logs for errors
```

### Still Having Issues?

Check [DEBUGGING.md](DEBUGGING.md) for detailed troubleshooting or the full [README.md](README.md) for more options.

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
