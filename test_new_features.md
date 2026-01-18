# Testing New URL and File Upload Features

## Overview
The application now supports two input methods:
1. **URL Input**: Enter a Beatport playlist URL, which is processed using `url_to_json.py` to extract track data
2. **HTML File Upload**: Upload a saved Beatport playlist HTML file for local processing

## What Changed

### Frontend Changes
- **DownloadForm.jsx**: Added toggle between URL and HTML file input modes
- **DownloadForm.css**: Added styles for input type selector and file input
- **App.jsx**: Updated to handle both URL and file upload requests

### Backend Changes
- **server.js**:
  - Added `multer` middleware for file uploads
  - When URL is provided, first calls `url_to_json.py` to generate JSON
  - Then uses the generated JSON file with `beatport_downloader.py --json-file`
  - When HTML file is uploaded, saves it temporarily and uses `beatport_downloader.py --local-html`
  - Cleans up temporary files after processing

## Testing Instructions

### Test 1: URL Input
1. Start the server: `npm start`
2. Open browser to `http://localhost:3000`
3. Ensure "URL" toggle is selected (default)
4. Enter a Beatport playlist URL (e.g., `https://www.beatport.com/chart/...`)
5. Click "Download Playlist"
6. Expected behavior:
   - Shows "Extracting playlist from URL..."
   - Calls `url_to_json.py` to extract track data
   - Shows "Playlist extracted successfully. Starting downloads..."
   - Proceeds with track downloads using the extracted JSON

### Test 2: HTML File Upload
1. Save a Beatport playlist page as HTML (Right-click → Save As)
2. In the app, click the "HTML File" toggle
3. Click "Choose File" and select the saved HTML file
4. Click "Download Playlist"
5. Expected behavior:
   - Shows "Processing file..."
   - Uploads file to server
   - Server processes HTML with `beatport_downloader.py --local-html`
   - Shows track download progress

### Test 3: Error Handling
1. Try submitting without input (button should be disabled)
2. Try invalid URL (should show warning)
3. Try uploading non-HTML file (should be restricted by file picker)

## Architecture Flow

### URL Input Flow
```
User enters URL
    ↓
Frontend sends POST to /api/download with { url: "..." }
    ↓
Backend receives URL
    ↓
Backend calls: python3 url_to_json.py <url> -o <temp_json>
    ↓
url_to_json.py uses Selenium to fetch and parse playlist
    ↓
Generates JSON file with track data
    ↓
Backend calls: python3 beatport_downloader.py --json-file <temp_json>
    ↓
Downloads tracks using JSON data
    ↓
Backend cleans up temp JSON file
```

### HTML File Flow
```
User uploads HTML file
    ↓
Frontend sends POST to /api/download with FormData containing file
    ↓
Backend receives file via multer middleware
    ↓
File saved to temp directory
    ↓
Backend calls: python3 beatport_downloader.py --local-html <temp_html>
    ↓
Downloads tracks from HTML
    ↓
Backend cleans up temp HTML file
```

## Dependencies Added
- **multer** (v2.0.0-rc.4): Handles multipart/form-data file uploads

## Files Modified
1. `/frontend/src/components/DownloadForm.jsx` - Added URL/File toggle UI
2. `/frontend/src/components/DownloadForm.css` - Added styles
3. `/frontend/src/App.jsx` - Updated download handler
4. `/server.js` - Complete rewrite of `/api/download` endpoint
5. `/package.json` - Added multer dependency

## Verification Checklist
- [x] Frontend builds without errors
- [x] Server.js syntax is valid
- [x] Multer dependency installed
- [x] URL input UI implemented
- [x] File upload UI implemented
- [x] Backend handles URL processing
- [x] Backend handles file uploads
- [x] Temporary files are cleaned up
- [x] Error handling implemented

## Next Steps for Manual Testing
1. Install Selenium if not already installed: `pip install selenium`
2. Test with a real Beatport playlist URL
3. Test with a saved HTML file
4. Verify tracks are downloaded correctly
5. Check that temporary files are removed from temp directory
