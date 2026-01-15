# Beatport Playlist Downloader

A modern web application that downloads music from Beatport playlists by scraping track information and downloading audio from SoundCloud. Features both a web UI and command-line interface.

## Features

- Modern web interface for easy downloads
- Supports multiple Beatport URL formats:
  - Public playlists and charts
  - Playlist share URLs (e.g., `/playlists/share/...`)
  - Multiple HTML structure types
- Searches and downloads audio from SoundCloud using yt-dlp
- Downloads as high-quality MP3 files
- Real-time progress tracking and updates
- Fallback to local HTML file if URL scraping fails
- Skip already downloaded tracks
- Detailed download summary
- Command-line interface for automation
- Built-in debugging tools

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

```bash
python beatport_downloader.py <beatport_playlist_url>
```

### Interactive Mode

```bash
python beatport_downloader.py
```

Then enter the Beatport playlist URL when prompted.

### Local HTML File

If the URL scraping fails (403 error), you can save the Beatport playlist page as HTML and provide the local file path:

1. Open the Beatport playlist in your browser
2. Save the page as HTML (Ctrl+S or Cmd+S)
3. Run the script and provide the path to the saved HTML file when prompted

## How It Works

1. **Scraping**: Fetches the Beatport playlist page and extracts Artist, Track Name, and Remix Name for each track
2. **Search**: Creates a search query and uses yt-dlp to find the top result on SoundCloud
3. **Download**: Downloads the audio and converts it to MP3 format
4. **Save**: Saves files as `Artist - Track.mp3` in the `downloads` folder

## Output

Downloaded tracks are saved to the `downloads/` directory with the naming format:
```
Artist - Track.mp3
```

## Example

```bash
$ python beatport_downloader.py "https://www.beatport.com/chart/..."

============================================================
Beatport Playlist Downloader
============================================================

Fetching URL: https://www.beatport.com/chart/...
Found 20 track elements
Parsing track information...
Found 20 tracks

Tracks to download:
------------------------------------------------------------
1. Artist Name - Track Name (Remix)
2. Another Artist - Another Track
...

Proceed with download? (y/n): y

Starting downloads...
============================================================

[1/20] Processing: Artist Name - Track Name
  Downloading: Artist Name - Track Name.mp3
  ✓ Downloaded: Artist Name - Track Name.mp3

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

## Troubleshooting

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
├── scraper.py                   # Beatport scraping logic
├── downloader.py                # yt-dlp download logic
├── requirements.txt             # Python dependencies
├── package.json                 # Node.js dependencies
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

## Deployment

### Verifying Installation

Run the verification script to check if all required files are present:

```bash
npm run verify
```

This will check for:
- Python scripts (beatport_downloader.py, scraper.py, downloader.py)
- Node.js server (server.js)
- Frontend build files
- Configuration files

### Build Before Deployment

Make sure to build the frontend before deploying:

```bash
npm install
npm run build
npm run verify
npm run start
```

The server will automatically:
- Create the `downloads` directory if it doesn't exist
- Serve the frontend from `frontend/dist`
- Display helpful error messages if files are missing

## Troubleshooting

### Deployment Errors

**"No such file or directory" error:**
- Run `npm run verify` to check which files are missing
- Make sure you've run `npm run build` before deploying
- Ensure Python scripts are not in .gitignore
- Check that `frontend/dist` folder exists with index.html

**Frontend not loading:**
- Verify the build completed: `ls frontend/dist/`
- Rebuild if needed: `npm run build`
- Check server logs for path errors
- Server will show a helpful message if dist is missing

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
- Verify Python and dependencies are installed: `python check_dependencies.py`
- Check server logs for errors
- Ensure the Beatport URL is valid
- Make sure Python 3 is in your PATH
- Run `npm run verify` to check all files are present

**"Process exited with code 1" / No tracks found:**
This is the most common issue and means the scraper couldn't extract tracks from the Beatport page.

**Quick Fix:**
```bash
# Run the debug script to see what's wrong
python debug_beatport.py "your-beatport-url"
```

**Common causes:**
1. Beatport changed their HTML structure (they do this frequently)
2. The page loads content via JavaScript (not visible in raw HTML)
3. Anti-scraping measures are blocking the request

**Solutions:**
- See [DEBUGGING.md](DEBUGGING.md) for detailed troubleshooting
- Save the Beatport page as HTML from your browser and use the local file option
- Test directly: `python beatport_downloader_web.py "your-url"`

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
