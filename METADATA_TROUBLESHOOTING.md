# Metadata Writing Troubleshooting Guide

## Overview

This guide helps diagnose and fix metadata writing issues. If you're not seeing metadata (artist, title, album art, BPM, key) in your downloaded MP3 files, follow these steps.

## Quick Diagnosis

### Step 1: Run the Metadata Test

Run the standalone metadata test to verify the metadata writing system works:

```bash
python3 test_metadata_write.py
```

This will:
1. Create a test MP3 file
2. Write metadata to it
3. Verify the metadata was written
4. Show all tags in the file

**Expected Output:**
```
✓ Test MP3 created successfully
✓ Metadata write reported success
✓ Tags found in file: 8 tags
✓✓✓ TEST PASSED - Metadata writing works correctly
```

**If this fails:** There's a problem with your Python environment or dependencies
**If this succeeds:** The issue is with how metadata is being passed during downloads

### Step 2: Check Downloaded Files

If you've already downloaded tracks, check the logs carefully. Look for these indicators:

**Good Signs (metadata should be present):**
```
[Metadata] Starting metadata write for: track.mp3
[Metadata] ✓ Added title
[Metadata] ✓ Added artist
[Metadata] ✓ Album art embedded successfully
[Metadata] ✓ Successfully saved all metadata to MP3
✓✓✓ METADATA WRITE SUCCESSFUL
```

**Bad Signs (metadata was not written):**
```
⚠ No metadata found for track in JSON
⚠ MP3 file not found
⚠ [Metadata] CRITICAL ERROR
✗✗✗ METADATA WRITE FAILED
```

## Common Issues and Solutions

### Issue 1: No Metadata in JSON File

**Symptom:** Log shows "No metadata found for track in JSON"

**Cause:** Your JSON file doesn't contain the metadata fields

**Solution:** Ensure your JSON file has this structure:

```json
[
  {
    "song_name": "Track Name Extended Mix",
    "artist_name": "Artist Name",
    "label_name": "Label Name",
    "genre": "House",
    "bpm_key": "128 BPM - A Minor",
    "album_art": "./path/to/artwork.jpg"
  }
]
```

**Required fields for metadata:**
- `song_name` (becomes Title tag)
- `artist_name` (becomes Artist tag)
- `label_name` (becomes Album tag)
- `genre` (becomes Genre tag)
- `bpm_key` (split into BPM and Key tags)
- `album_art` (optional, embedded as cover art)

### Issue 2: Album Art Not Found

**Symptom:** Log shows "Album art not found at: /path/to/file.jpg"

**Cause:** Album art path is incorrect or file doesn't exist

**Solution:**
1. Check if using relative paths - they're resolved from JSON file location
2. Verify file exists at the path
3. Try using absolute paths or URLs instead

**Example with URL:**
```json
{
  "album_art": "https://example.com/artwork.jpg"
}
```

**Example with absolute path:**
```json
{
  "album_art": "/Users/username/Music/artwork.jpg"
}
```

**Example with relative path:**
```json
{
  "album_art": "./images/artwork.jpg"
}
```
(Resolves relative to JSON file location)

### Issue 3: Metadata Skipped for Already Downloaded Tracks

**Symptom:** Track was already in downloads folder, metadata not applied

**Cause:** System skips metadata writing for existing files to avoid overwriting

**Solution:**
1. Delete the existing MP3 file
2. Re-run the download
3. Metadata will be written to the new file

### Issue 4: Permission Issues

**Symptom:** "Permission denied" errors in logs

**Cause:** Can't write to the MP3 file or output directory

**Solution:**
1. Check folder permissions
2. Try a different output directory
3. On macOS, may need to grant Terminal/Python access to folders

### Issue 5: Missing Dependencies

**Symptom:** "ModuleNotFoundError: No module named 'mutagen'"

**Cause:** Mutagen library not installed

**Solution:**
```bash
pip install mutagen
```

Or reinstall all requirements:
```bash
pip install -r requirements.txt
```

## Manual Metadata Verification

### macOS - Finder

1. Right-click the MP3 file
2. Select "Get Info" (⌘ + I)
3. Check the "More Info" section
4. Should see: Title, Artist, Album, Genre, BPM, etc.

### macOS - Preview

1. Open MP3 in Preview
2. Go to Tools → Show Inspector (⌘ + I)
3. Click the "More Info" tab
4. Should see all metadata

### Using Python (Most Reliable)

```python
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

audio = MP3('path/to/file.mp3', ID3=ID3)
if audio.tags:
    print("Tags found:")
    for tag in audio.tags.keys():
        print(f"  {tag}: {audio.tags[tag]}")

    # Check for album art
    if 'APIC:Cover' in audio.tags:
        print("Album art: Present")
    else:
        print("Album art: Not found")
else:
    print("No tags found in file")
```

### Using Command Line

```bash
# Install exiftool if not already installed
# macOS: brew install exiftool

exiftool file.mp3
```

## Detailed Logging

The system now provides detailed logging for metadata operations. When you run a download, look for these log sections:

### 1. Metadata Application Start
```
======================================================================
  APPLYING METADATA TO: track_name.mp3
======================================================================
```

### 2. Metadata Loading
```
[Metadata] Starting metadata write for: track_name.mp3
[Metadata] Writing - Artist: Artist Name
[Metadata] Writing - Title: Track Name
[Metadata] Writing - Album: Label Name
[Metadata] Writing - Genre: House
[Metadata] Writing - BPM/Key: 128 BPM - A Minor
[Metadata] Writing - Album Art: Yes
```

### 3. Tag Writing
```
[Metadata] Loading MP3 file...
[Metadata] Created new ID3 tags
[Metadata] Clearing existing tags...
[Metadata] Adding ID3 tags...
[Metadata] ✓ Added title
[Metadata] ✓ Added artist
[Metadata] ✓ Added album (label)
[Metadata] ✓ Added genre
[Metadata] ✓ Added BPM: 128
[Metadata] ✓ Added key: A Minor
[Metadata] ✓ Added year
[Metadata] ✓ Added comment
```

### 4. Album Art Processing
```
[Metadata] Processing album art...
[Metadata] Album art is local file: /path/to/file.jpg
[Metadata] ✓ Loaded album art from: file.jpg (45123 bytes, image/jpeg)
[Metadata] Embedding album art into MP3...
[Metadata] ✓ Album art embedded successfully
```

### 5. Save and Verification
```
[Metadata] Saving ID3 tags to file...
[Metadata] ✓ Successfully saved all metadata to MP3
[Metadata] Verifying tags were written...
[Metadata] ✓ Verified: 8 tags found in file
```

### 6. Final Status
```
======================================================================
  ✓✓✓ METADATA WRITE SUCCESSFUL: 128 BPM - A Minor | Genre: House
======================================================================
```

## Troubleshooting Specific Error Messages

### "MP3 file not found"

**Full message:** `⚠ [Metadata] MP3 file not found: /path/to/file.mp3`

**Cause:** The MP3 wasn't downloaded successfully or path is wrong

**Check:**
1. Look earlier in the logs for download status
2. Verify file exists at the path
3. Check for download errors

### "Could not create ID3 tags"

**Full message:** `⚠ [Metadata] Could not create ID3 tags`

**Cause:** File may be corrupted or not a valid MP3

**Solution:**
1. Delete the file
2. Re-download the track
3. Verify ffmpeg is working: `ffmpeg -version`

### "Album art file error"

**Full message:** `⚠ [Metadata] Album art file error: [error details]`

**Cause:** Problem reading the album art file

**Check:**
1. File exists and is readable
2. File is a valid image (JPEG, PNG)
3. No special characters in filename
4. Correct path (relative to JSON file)

### "Verification failed: No tags found in file"

**Full message:** `⚠ [Metadata] Verification failed: No tags found in file`

**Cause:** Tags were not saved to the file

**This is a serious issue. Try:**
1. Update mutagen: `pip install --upgrade mutagen`
2. Check Python version: `python3 --version` (need 3.7+)
3. Run the test script: `python3 test_metadata_write.py`
4. Check file permissions

## Rekordbox-Specific Issues

### Metadata Shows in macOS but Not in Rekordbox

**Possible causes:**
1. Rekordbox hasn't rescanned the file
2. Cache issue in Rekordbox
3. ID3 version compatibility

**Solutions:**
1. **Reimport the track:**
   - Remove track from Rekordbox collection
   - Delete from database (don't delete file)
   - Re-import the track

2. **Force Rekordbox to update:**
   - Right-click track in Rekordbox
   - Select "Reload Tag"
   - Wait for analysis to complete

3. **Clear Rekordbox cache:**
   - Close Rekordbox
   - Delete: `~/Library/Pioneer/rekordbox/` (backup first!)
   - Reopen Rekordbox
   - Re-import tracks

### Album Art Shows in macOS but Not in Rekordbox

**Possible causes:**
1. Image format not supported
2. Image too large
3. Rekordbox cache issue

**Solutions:**
1. **Check image:**
   - Should be JPEG or PNG
   - Recommended: 500x500 to 1400x1400 pixels
   - Max: 3000x3000 pixels

2. **Force Rekordbox to reanalyze:**
   - Right-click track
   - Select "Analyze"
   - Select "Reload Tag"

## Getting Help

If none of these solutions work:

1. **Run the test script:**
   ```bash
   python3 test_metadata_write.py
   ```
   Share the complete output

2. **Try a manual test:**
   - Download one track
   - Save complete console output
   - Check the MP3 file with:
     ```bash
     exiftool downloaded_track.mp3
     ```

3. **Provide information:**
   - Operating system and version
   - Python version (`python3 --version`)
   - Mutagen version (`pip show mutagen`)
   - Sample JSON file structure
   - Complete error logs

## Advanced: Fixing Existing Files

If you've already downloaded files without metadata, you can fix them:

### Option 1: Re-download

1. Delete the MP3 files
2. Run the downloader again
3. Metadata will be added during download

### Option 2: Write Metadata Manually

Create a Python script:

```python
from metadata_writer import MetadataWriter

writer = MetadataWriter()

metadata = {
    'song_name': 'Track Name Extended Mix',
    'artist_name': 'Artist Name',
    'label_name': 'Label Name',
    'genre': 'House',
    'bpm_key': '128 BPM - A Minor',
    'album_art': '/path/to/artwork.jpg'
}

success = writer.apply_metadata_to_track(
    '/path/to/your/track.mp3',
    metadata
)

if success:
    print("Metadata added successfully!")
else:
    print("Failed to add metadata")
```

## Summary Checklist

Before reporting an issue, verify:

- [ ] Test script passes (`python3 test_metadata_write.py`)
- [ ] JSON file has all required fields
- [ ] Album art path is correct (or using URL)
- [ ] Download logs show metadata writing attempt
- [ ] File exists at the expected location
- [ ] Can read metadata in macOS "Get Info"
- [ ] Tried reimporting in Rekordbox
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Python version is 3.7 or higher
- [ ] ffmpeg is installed and working

Most metadata issues are caused by:
1. Missing or malformed JSON metadata
2. Incorrect album art paths
3. Rekordbox cache issues

The detailed logging added to the system will help identify the exact cause of any metadata writing failures.
