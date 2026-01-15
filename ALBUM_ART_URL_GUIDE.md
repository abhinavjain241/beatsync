# Album Art URL Support Guide

## Overview

The metadata writer now supports both local file paths and URLs for album art. This makes it easier to work with album art directly from online sources without needing to download and manage image files locally.

## Usage

### Using URLs

You can now specify album art as a URL in your JSON files:

```json
{
  "song_name": "Take Your Places Extended Mix",
  "artist_name": "Westend, SIDEPIECE",
  "label_name": "LIP SERVICE",
  "genre": "Bass House",
  "bpm_key": "130 BPM - D Major",
  "album_art": "https://example.com/album-art/artwork.jpg"
}
```

### Using Local Paths

Local paths continue to work as before:

```json
{
  "song_name": "Take Your Places Extended Mix",
  "artist_name": "Westend, SIDEPIECE",
  "label_name": "LIP SERVICE",
  "genre": "Bass House",
  "bpm_key": "130 BPM - D Major",
  "album_art": "./basshouse_t100_files/artwork.jpg"
}
```

## Features

### Automatic Detection

The system automatically detects whether you've provided a URL or a local file path:

- **URLs**: Start with `http://` or `https://`
- **Local paths**: Everything else (relative or absolute paths)

### Supported Image Formats

The system automatically detects and handles:
- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **WebP** (.webp)

Format detection is done by analyzing the image data signature, not just the file extension, ensuring accurate MIME type tagging for Rekordbox.

### Smart Error Handling

The download system includes:
- **User-Agent headers** to avoid blocks from image servers
- **30-second timeout** prevents hanging on slow connections
- **Graceful fallback** with clear error messages
- **Network error recovery** with detailed error reporting

## Benefits

### For Users
- ✓ No need to manually download and organize album art files
- ✓ Simplified JSON file creation
- ✓ Reduced storage requirements
- ✓ Direct integration with online image sources

### For Developers
- ✓ Automatic format detection
- ✓ Built-in error handling
- ✓ Rekordbox-compatible MIME types
- ✓ No external dependencies (uses Python's built-in urllib)

## How It Works

### URL Detection Flow

1. **Check if URL**: System checks if the path starts with `http://` or `https://`
2. **Download Image**: If URL, downloads image with proper headers
3. **Detect Format**: Analyzes image signature to determine format (JPEG/PNG/WebP)
4. **Embed in MP3**: Embeds image data with correct MIME type
5. **Save Metadata**: Saves all metadata to MP3 file

### Local Path Flow

1. **Check Existence**: Verifies file exists at the specified path
2. **Read File**: Loads image data from disk
3. **Detect Format**: Uses file extension to determine format
4. **Embed in MP3**: Embeds image data with correct MIME type
5. **Save Metadata**: Saves all metadata to MP3 file

## Example Workflow

### Before (Local Files Only)

```bash
# Step 1: Download album art manually
wget https://example.com/art1.jpg -O ./images/art1.jpg
wget https://example.com/art2.jpg -O ./images/art2.jpg

# Step 2: Create JSON with local paths
{
  "album_art": "./images/art1.jpg"
}

# Step 3: Run downloader
python beatport_downloader.py --json-file tracks.json
```

### After (With URL Support)

```bash
# Step 1: Create JSON with URLs directly
{
  "album_art": "https://example.com/art1.jpg"
}

# Step 2: Run downloader (album art downloaded automatically)
python beatport_downloader.py --json-file tracks.json
```

## Technical Details

### MIME Type Detection

The system detects image formats by checking file signatures:

```python
# JPEG: Starts with FF D8 FF
if image_data.startswith(b'\xff\xd8\xff'):
    return 'image/jpeg'

# PNG: Starts with 89 50 4E 47 0D 0A 1A 0A
elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
    return 'image/png'

# WebP: Contains "WEBP" at offset 8
elif image_data[8:12] == b'WEBP':
    return 'image/webp'
```

This ensures accurate MIME type tagging regardless of file extension or URL parameters.

### HTTP Headers

Downloads include proper User-Agent headers to avoid blocks:

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
```

### Error Messages

Clear error messages help debug issues:
- `⚠ Album art HTTP error: 404 - Not Found`
- `⚠ Album art URL error: Connection timeout`
- `⚠ Album art not found: /path/to/image.jpg`
- `✓ Downloaded album art (45123 bytes, image/jpeg)`

## Testing

Run the test script to verify URL support:

```bash
python3 test_album_art_url.py
```

Expected output:
```
✓ https://example.com/image.jpg: URL
✓ http://example.com/image.png: URL
✓ ./local/path/image.jpg: Local Path
✓ JPEG signature: image/jpeg
✓ PNG signature: image/png
```

## Rekordbox Compatibility

Album art downloaded from URLs is fully compatible with Rekordbox:
- Proper ID3v2.3 tags
- Correct MIME type (image/jpeg, image/png)
- Standard cover art type (type 3 = front cover)
- Binary encoding for image data

## Troubleshooting

### URL Not Downloading

**Problem**: Album art URL fails to download

**Solutions**:
- Check that URL is accessible in a web browser
- Verify URL starts with `http://` or `https://`
- Check for firewall or network restrictions
- Try a different image host if the server blocks automated requests

### Image Not Showing in Rekordbox

**Problem**: MP3 has metadata but no album art in Rekordbox

**Solutions**:
- Verify image URL is a direct link to image (not HTML page)
- Check that image format is JPEG or PNG (WebP may have limited support)
- Try re-importing the track in Rekordbox
- Check Rekordbox preferences for artwork display settings

### Mixed Local and URL Paths

**Problem**: Some tracks use URLs, others use local paths

**Solution**: This is fully supported! The system handles both automatically:

```json
[
  {
    "album_art": "https://example.com/art1.jpg"
  },
  {
    "album_art": "./local/art2.jpg"
  }
]
```

## Best Practices

### URL Format
- Use direct image URLs (ending in .jpg, .png, etc.)
- Avoid URLs with query parameters when possible
- Ensure URLs are publicly accessible

### Performance
- URLs add download time (typically 1-3 seconds per image)
- For large playlists, consider local files for faster processing
- Download failures won't stop the overall process

### Reliability
- Keep local backups of album art for critical tracks
- Test URLs before adding to large JSON files
- Use stable image hosts (CDNs preferred)

## Migration Guide

### From Local Files to URLs

If you have existing JSON files with local paths and want to use URLs:

1. Upload your album art to a stable image host
2. Update JSON file with new URLs
3. Remove old local image files (optional)

### From URLs to Local Files

If you want to switch from URLs to local files:

1. Download images from URLs
2. Save to a local directory
3. Update JSON file with local paths
4. Verify paths are correct relative to JSON file location

## Summary

Album art URL support provides:
- **Flexibility**: Use URLs or local paths interchangeably
- **Convenience**: No manual image management
- **Compatibility**: Full Rekordbox support
- **Reliability**: Proper error handling and fallbacks

This feature streamlines the workflow while maintaining full compatibility with Rekordbox and other DJ software.
