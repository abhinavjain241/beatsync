# Beatport Playlist Downloader

Download complete Beatport playlists automatically. Simply paste a URL or upload an HTML file, and get high-quality MP3s with full metadata and album art.

## What Does This Do?

This tool downloads music from Beatport playlists:
- **Easy Input**: Paste a Beatport URL or upload a saved HTML file
- **Smart Search**: Automatically finds tracks on SoundCloud and YouTube
- **Best Quality**: Downloads the longest/best version available (extended mixes preferred)
- **Complete Metadata**: Adds artist, title, album art, genre, label, BPM, and key
- **Skip Duplicates**: Automatically skips tracks you already have
- **Real-Time Progress**: Watch download progress for each track

## Quick Start Guide (Web Interface - Recommended)

### Step 1: Install Requirements

You need to install these programs first (one-time setup):

**1. Install Python**
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

**2. Install Node.js**
- Download from [nodejs.org](https://nodejs.org/)
- Use the LTS (recommended) version

**3. Install Chrome Browser**
- Download from [google.com/chrome](https://www.google.com/chrome/)
- Needed for extracting playlists from URLs

### Step 2: Setup the Application

1. **Download this project** and extract it to a folder
2. **Open Terminal** (Mac/Linux) or **Command Prompt** (Windows)
3. **Navigate to the project folder**:
   ```bash
   cd path/to/beatport-downloader
   ```
   Replace `path/to/beatport-downloader` with the actual folder location

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

### Step 3: Start the Application

In the project folder, run:
```bash
npm start
```

You should see a message like `Server running on http://localhost:3000`

### Step 4: Use the Application

1. **Open your web browser**
2. **Go to** `http://localhost:3000`
3. **Choose your input method**:
   - **URL** (Recommended): Paste a Beatport playlist URL
   - **HTML File**: Upload a saved Beatport page
4. **Click "Download Playlist"**
5. **Wait** for the downloads to complete

Your music will be saved in the `downloads/` folder with complete metadata and album art!

## Using the Command Line (Advanced Users)

If you prefer the command line or want faster downloads:

### Using Sample JSON Files (Fastest Method)

The project includes ready-to-use JSON files with popular Beatport Top 100 playlists:

```bash
# Download Bass House Top 100
python3 beatport_downloader.py --json-file basshouse_t100.json

# Download Melodic Techno Top 100
python3 beatport_downloader.py --json-file melodictech_t100.json

# Download Tech House Top 100
python3 beatport_downloader.py --json-file techhouse_t100.json
```

### Download from URL

```bash
python3 beatport_downloader.py --url "https://www.beatport.com/chart/..."
```

### Download from HTML File

```bash
python3 beatport_downloader.py --local-html playlist.html
```

### Create Your Own JSON File

Extract a Beatport playlist to JSON format:

```bash
python3 url_to_json.py https://www.beatport.com/chart/...
```

This creates a JSON file you can use for faster, more reliable downloads.

## Where Are My Downloads?

### Web Interface
- Files are saved in the `downloads/` folder
- Example: `downloads/Artist Name - Track Title.mp3`

### Command Line with JSON Files
- Files are organized by playlist name
- Location: `~/Music/{playlist_name}/`
- Example: `~/Music/basshouse_t100/Artist Name - Track Title.mp3`

## Troubleshooting

### "Python not found" error
- Make sure Python is installed and added to PATH
- Try using `python` instead of `python3` on Windows
- Restart your terminal after installing Python

### "npm not found" error
- Install Node.js from [nodejs.org](https://nodejs.org/)
- Restart your terminal after installation

### "Selenium not installed" error
```bash
pip install selenium
```

### Port 3000 already in use
Change the port when starting:
```bash
PORT=3001 npm start
```
Then go to `http://localhost:3001` in your browser

### Tracks not downloading
- Check your internet connection
- Some tracks may not be available on SoundCloud or YouTube
- Check the console for specific error messages

### ChromeDriver issues
- Make sure Chrome browser is installed
- Selenium 4+ automatically manages ChromeDriver
- If problems persist, try updating Selenium: `pip install --upgrade selenium`

## Optional: Login to Beatport

Some playlists require a Beatport account. To use authentication:

1. Create a `.env` file in the project folder
2. Add your credentials:
   ```
   BEATPORT_EMAIL=your@email.com
   BEATPORT_PASSWORD=yourpassword
   ```
3. Use the `--login` flag:
   ```bash
   python3 url_to_json.py --login https://www.beatport.com/chart/...
   ```

## Features

- **Multiple Input Methods**: URL, HTML file, or JSON file
- **Automatic Track Search**: Finds tracks on SoundCloud and YouTube
- **Smart Version Selection**: Prefers extended mixes over radio edits
- **Complete Metadata**: Embeds artist, title, album art, genre, label, BPM, key
- **Duplicate Detection**: Skips files you already have (80% similarity)
- **Batch Processing**: Download entire playlists with one command
- **Real-Time Progress**: See progress for each track
- **Automatic Filtering**: Removes DJ sets over 15 minutes

## System Requirements

- **Python**: 3.7 or higher
- **Node.js**: 14 or higher
- **Chrome or Chromium**: Latest version
- **Internet connection**: Required for downloads
- **ffmpeg**: Automatically installed with Python dependencies

## File Organization

```
beatport-downloader/
├── downloads/              # Your downloaded music (web interface)
├── ~/Music/               # Command line downloads (organized by playlist)
├── frontend/              # Web interface files
├── docs/                  # Technical documentation
├── beatport_downloader.py # Main download script
├── url_to_json.py        # URL extraction script
├── server.js             # Web server
└── README.md             # This file
```

## Tips for Best Results

- **Extended Mixes**: The tool automatically prefers longer versions
- **Album Art**: High-resolution images are embedded in each file
- **Metadata**: ID3 tags work with iTunes, Music.app, and DJ software
- **Playlists**: Can handle 100+ tracks in one batch
- **Resume Downloads**: Already downloaded files are skipped automatically

## Need More Help?

- **Technical Documentation**: See the `docs/` folder for detailed guides
- **Authentication Issues**: Check `docs/AUTHENTICATION.md`
- **Metadata Problems**: See `docs/METADATA_TROUBLESHOOTING.md`
- **Advanced Features**: Read `docs/ARCHITECTURE.md`

## Command Line Quick Reference

```bash
# Web interface
npm start                    # Start the web app

# Using JSON files (fastest)
python3 beatport_downloader.py --json-file tracks.json

# Using URLs
python3 beatport_downloader.py --url "https://www.beatport.com/..."

# Using HTML files
python3 beatport_downloader.py --local-html playlist.html

# Extract URL to JSON
python3 url_to_json.py "https://www.beatport.com/..."

# Custom output folder
python3 beatport_downloader.py --json-file tracks.json --output-dir /path/to/folder

# SoundCloud only
python3 beatport_downloader.py --json-file tracks.json --source soundcloud

# YouTube only
python3 beatport_downloader.py --json-file tracks.json --source youtube

# Show help
python3 beatport_downloader.py --help
```

## Example Workflow

### Web Interface Workflow
1. Start the app: `npm start`
2. Open browser: `http://localhost:3000`
3. Paste Beatport URL
4. Click "Download Playlist"
5. Find your music in `downloads/` folder

### Command Line Workflow
1. Extract playlist: `python3 url_to_json.py "https://www.beatport.com/chart/..."`
2. Download tracks: `python3 beatport_downloader.py --json-file output.json`
3. Find your music in `~/Music/output/` folder

## License

This tool is for personal use only. Please respect copyright laws and artist rights.

---

**Ready to start?** Follow the Quick Start Guide above, or run `npm start` if you've already installed everything!

For detailed technical documentation, see the `docs/` folder.
