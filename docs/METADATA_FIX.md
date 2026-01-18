# Metadata Flow Fix

## Problem

The metadata writing workflow was not using the metadata from the original JSON file. When processing tracks, the system was losing important metadata fields like `genre`, `bpm_key`, `label_name`, and `album_art`.

## Root Cause

In `scraper.py`, the `load_json_file()` method was only extracting a minimal set of fields for search purposes:
- `artist` (for searching)
- `track` (for searching)
- `remix` (for searching)
- `label` (for display)

All other metadata fields from the JSON (`artist_name`, `song_name`, `genre`, `bpm_key`, `album_art`) were being discarded during the parsing process.

## Solution

Modified `scraper.py` line 156-238 to preserve ALL original metadata fields from the JSON:

```python
# Create track dict with search fields
track_dict = {
    'artist': artist,
    'track': track,
    'remix': remix,
    'label': label
}

# PRESERVE ALL ORIGINAL METADATA FIELDS for later use
# This ensures we can write proper ID3 tags with all metadata
for key, value in item.items():
    if key not in track_dict and value:
        track_dict[key] = value

tracks.append(track_dict)
```

## How It Works Now

1. **JSON Loading** (`scraper.py`):
   - Reads JSON file with full metadata (artist_name, song_name, genre, bpm_key, label_name, album_art)
   - Creates search fields (artist, track, remix, label)
   - **NEW:** Preserves ALL original JSON fields in the track dictionary

2. **Metadata Storage** (`beatport_downloader.py`):
   - Stores complete track dictionaries with all metadata fields
   - Creates normalized keys for lookup

3. **Metadata Retrieval** (`beatport_downloader.py`):
   - Retrieves the full track dictionary including all metadata
   - Passes complete metadata to metadata writer

4. **Metadata Writing** (`metadata_writer.py`):
   - Receives complete metadata with all fields:
     - `artist_name` → ID3 TPE1 (Artist)
     - `song_name` → ID3 TIT2 (Title)
     - `label_name` → ID3 TALB (Album)
     - `genre` → ID3 TCON (Genre)
     - `bpm_key` → ID3 TBPM + TKEY (BPM and Key)
     - `album_art` → ID3 APIC (Album Art)

## Testing

A test script `test_metadata_simple.py` was created to verify the fix:

```bash
python3 test_metadata_simple.py
```

Expected output:
```
✅ TEST PASSED: All metadata fields preserved after scraper processing!
```

## Debug Output

Added comprehensive debug logging in `beatport_downloader.py` to track metadata flow:

- Shows what fields are stored when loading JSON
- Shows what fields are retrieved before writing metadata
- Helps diagnose any future metadata issues

## Expected Behavior

When running:
```bash
python3 beatport_downloader.py --json-file basshouse_t100.json
```

The downloaded MP3 files will now have:
- ✓ Artist name from `artist_name` field
- ✓ Track title from `song_name` field
- ✓ Album (label) from `label_name` field
- ✓ Genre from `genre` field
- ✓ BPM from `bpm_key` field (parsed)
- ✓ Key from `bpm_key` field (parsed)
- ✓ Album art from `album_art` field (local path or URL)

All metadata is properly embedded in the MP3 files using ID3v2.3 tags for maximum compatibility with DJ software like Rekordbox.
