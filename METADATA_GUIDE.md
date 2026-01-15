# MP3 Metadata Writing Guide

## Overview

The Beatport Downloader now automatically embeds ID3v2.4 metadata tags into downloaded MP3 files when using JSON input files with metadata fields.

## Key Improvements for macOS Compatibility

### 1. Proper Tag Overwriting
- Uses `delall()` before setting tags to ensure clean metadata
- Uses direct tag assignment (`audio.tags['TIT2'] = ...`) instead of `add()`
- Prevents duplicate or conflicting tags

### 2. ID3v2.4 Format
- Saves with `v2_version=4` for maximum macOS compatibility
- Fully supported by macOS Music, iTunes, and Finder
- UTF-8 encoding (encoding=3) for international characters

### 3. Album Art Handling
- Removes existing album art before embedding new art
- Supports JPEG and PNG formats
- Properly sets MIME type based on file extension
- Embeds as front cover (type=3)

## JSON Format with Metadata

```json
[
  {
    "artist_name": "Vintage Culture, Gabss",
    "song_name": "Lost Original Mix",
    "label_name": "AFFAIRS",
    "genre": "Melodic House & Techno",
    "bpm_key": "128 BPM - G Minor",
    "album_art": "./melotech_t100_files/image.jpg"
  }
]
```

### Required Fields
- `artist_name`: Artist name(s)
- `song_name`: Track title

### Optional Metadata Fields
- `label_name`: Record label (saved as Album tag)
- `genre`: Music genre
- `bpm_key`: BPM and musical key (e.g., "128 BPM - G Minor")
- `album_art`: Path to album artwork image (relative or absolute)

## Tag Mapping

| JSON Field | ID3 Tag | Frame ID | Description |
|------------|---------|----------|-------------|
| `song_name` | Title | TIT2 | Track title |
| `artist_name` | Artist | TPE1 | Artist name |
| `label_name` | Album | TALB | Album/label name |
| `genre` | Genre | TCON | Music genre |
| `bpm_key` (BPM part) | BPM | TBPM | Beats per minute |
| `bpm_key` (Key part) | Key | TKEY | Musical key |
| `album_art` | Album Art | APIC | Embedded image |

## Testing Metadata

### Using the Test Script

```bash
# Install dependencies
pip install -r requirements.txt

# Read existing metadata from a file
python test_metadata.py your_track.mp3 --read-only

# Write test metadata to a file
python test_metadata.py your_track.mp3
```

### Verifying in macOS

1. **Finder**: Right-click file → Get Info → More Info tab
2. **Music App**: Add file to library, check in song details
3. **Terminal**:
   ```bash
   python -c "from mutagen.mp3 import MP3; print(MP3('your_track.mp3').tags)"
   ```

## Troubleshooting

### Album Art Not Showing
- Verify image file exists at the specified path
- Check image format (JPEG or PNG supported)
- Ensure image file is not corrupted
- Try absolute path instead of relative path

### Artist/Title Not Showing
- Verify JSON fields are spelled correctly
- Check for UTF-8 encoding issues in JSON file
- Run test script to verify tags are being written

### Tags Not Visible in Music App
- Remove and re-add the file to Music library
- Check file permissions (should be readable)
- Verify ID3 version with: `ffprobe -hide_banner file.mp3`

## Code Changes

### metadata_writer.py
- Changed from `audio.tags.add()` to direct assignment
- Added `delall()` calls before setting tags
- Added ID3v2.4 format specification
- Improved error handling and logging
- Better album art path resolution

### beatport_downloader.py
- Stores track metadata map for lookup
- Applies metadata after successful downloads
- Skips metadata for already-existing files
- Reports metadata statistics in summary

## Performance

- Metadata writing adds ~0.1-0.5 seconds per track
- Album art embedding depends on image size
- No impact if metadata fields are not provided
- Failures are handled gracefully without stopping downloads
