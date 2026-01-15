# Setup Guide - Beatport Downloader Web UI

Complete setup instructions for running the Beatport Downloader with the web interface.

## Prerequisites

Before starting, ensure you have:
- **Node.js** 16+ (download from https://nodejs.org/)
- **Python** 3.7+
- **ffmpeg** installed
- **yt-dlp** Python package

## Quick Start (5 minutes)

### 1. Clone/Extract the Project

```bash
cd beatport-downloader
```

### 2. Install Dependencies

```bash
# Install Node.js dependencies for backend
npm install

# Install Node.js dependencies for frontend
cd frontend
npm install
cd ..

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Start the Application

**Development Mode** (recommended for development):
```bash
npm run dev
```

This starts:
- Frontend dev server on `http://localhost:5173`
- Backend server on `http://localhost:3000`

The frontend will automatically proxy API requests to the backend.

**Production Mode**:
```bash
npm run build
npm run start
```

Then open `http://localhost:3000`

## System-Specific Installation

### macOS

```bash
# Install ffmpeg and Node.js via Homebrew
brew install ffmpeg node

# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install
cd frontend && npm install && cd ..
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg nodejs npm python3-pip

# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install
cd frontend && npm install && cd ..
```

### Windows

1. **Install ffmpeg:**
   - Download from https://ffmpeg.org/download.html
   - Extract and add to System PATH

2. **Install Node.js:**
   - Download from https://nodejs.org/
   - Install using the installer

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies:**
   ```bash
   npm install
   cd frontend && npm install && cd ..
   ```

## Verify Installation

Run the dependency checker:

```bash
python check_dependencies.py
```

All items should have checkmarks. If any are missing, install them using the instructions above.

## Running the Application

### Development

```bash
npm run dev
```

Then open `http://localhost:5173` in your browser.

### Production

```bash
npm run build
npm run start
```

Then open `http://localhost:3000` in your browser.

### Command Line Only (no web UI)

```bash
python beatport_downloader.py <beatport_url>
```

## Project Structure

```
beatport-downloader/
├── server.js                  # Express backend server
├── beatport_downloader.py     # Python downloader orchestrator
├── scraper.py                 # Beatport HTML scraper
├── downloader.py              # Audio download handler
├── requirements.txt           # Python packages
├── package.json               # Node.js backend packages
├── frontend/                  # React web interface
│   ├── vite.config.js
│   ├── index.html
│   ├── package.json           # Frontend packages (React, Vite)
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       └── components/
│           ├── DownloadForm.jsx
│           ├── ProgressDisplay.jsx
│           └── SummaryDisplay.jsx
└── downloads/                 # Downloaded MP3 files
```

## Configuration

### Backend (Node.js)

Environment variables in `.env`:

```env
PORT=3000
NODE_ENV=development
```

### Frontend (React)

The frontend automatically connects to the backend API at:
- Development: `http://localhost:3000` (proxied via Vite)
- Production: Same domain (Express serves frontend)

## Troubleshooting

### Port Already in Use

If port 3000 or 5173 is already in use:

```bash
# Use a different port
PORT=3001 npm run start
```

### Module Not Found Errors

If you get "module not found" errors:

```bash
# Clear and reinstall dependencies
rm -rf node_modules frontend/node_modules
npm install
cd frontend && npm install && cd ..
```

### Python Module Errors

If Python dependencies fail:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### ffmpeg Not Found

Install ffmpeg for your system:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

### Connection Refused Errors

Make sure both servers are running:

```bash
# In one terminal
npm run dev

# This should start both:
# - Frontend on http://localhost:5173
# - Backend on http://localhost:3000
```

## Development

### Frontend Development

The frontend uses:
- **React** 18 for UI components
- **Vite** for fast development and building
- **CSS Modules** for styling

To modify the UI, edit files in `frontend/src/`.

### Backend Development

The backend uses:
- **Express** for HTTP server
- **Python subprocess** for running the downloader
- **Streaming responses** for real-time progress

To modify the API, edit `server.js`.

## Building for Production

```bash
# Build the frontend
npm run build

# Start the production server
npm run start
```

The production build will serve both frontend and backend from `http://localhost:3000`.

## Support

For issues:
1. Check the main [README.md](README.md) troubleshooting section
2. Verify all dependencies are installed: `python check_dependencies.py`
3. Check browser console (F12) for frontend errors
4. Check terminal output for backend errors

## Next Steps

- Open the web interface and start downloading
- Enjoy your music!
