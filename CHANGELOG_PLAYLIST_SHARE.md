# Changelog: Playlist Share URL Support

## Summary

Added support for Beatport playlist share URLs (e.g., `https://www.beatport.com/playlists/share/6421928`) which use a different HTML structure than regular charts and playlists.

## Changes Made

### 1. Updated User-Agent Header (`scraper.py`)

**Before:**
```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

**After:**
```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
```

### 2. Added Tracklist Table Parsing (`scraper.py`)

**New Method:** `_extract_track_info_from_table(row)`

This method handles the playlist share URL format which uses:
- `<table class="tracklist">` container
- `<tbody>` with `<tr>` rows for each track
- First `<td>`: Track title
- Second `<td>`: Artist/Label
- Automatic remix detection from title (e.g., "Track Name (Remix)")

**Implementation Details:**
- Checks for `table.tracklist` first (Method 0)
- Iterates through `tbody > tr` elements
- Extracts track title from first `<td>`
- Extracts artist from second `<td>`
- Automatically detects and separates remix information
- Cleans up newlines and extra whitespace

### 3. Updated Parsing Priority (`scraper.py`)

The `parse_tracks()` method now checks for tracklist tables **first** before trying other methods:

```python
# Method 0: tracklist table (playlist share pages) - NEW
# Method 1: bucket-item (older Beatport structure)
# Method 2: track class
# Method 3: table rows
# Method 4: li with track class
# Method 5: data-track attributes
# Method 6: playable-track class
```

### 4. Enhanced Debug Script (`debug_beatport.py`)

Added checks for:
- `table.tracklist` element
- `table.tracklist tbody tr` rows
- Shows structure of table rows when found

### 5. Created Test Script

**New File:** `test_playlist_url.py`

Specifically tests the playlist share URL format:
- Tests `https://www.beatport.com/playlists/share/6421928`
- Shows debug info if parsing fails
- Displays first 10 tracks if successful

### 6. Updated Documentation

**README.md:**
- Added mention of playlist share URL support
- Listed supported URL formats

**DEBUGGING.md:**
- Added section on supported URL formats
- Explained different HTML structures
- Updated testing examples

## How It Works

### URL Detection Flow

1. **Fetch HTML** with updated User-Agent header
2. **Check for tracklist table** (`<table class="tracklist">`)
3. **If found:**
   - Find `<tbody>` element
   - Loop through all `<tr>` rows
   - Extract from each row:
     - Title from first `<td>`
     - Artist from second `<td>`
     - Detect remix in title (parentheses)
4. **If not found:** Fall back to original methods

### Remix Detection

Automatically detects remix information in track titles:

```python
# Input: "Track Name (Artist Remix)"
# Output:
# - track: "Track Name"
# - remix: "Artist Remix"
```

Regex pattern: `\(([^)]+(?:Remix|Mix|Edit|Version))\)`

## Testing

### Test Playlist Share URL

```bash
python test_playlist_url.py
```

Expected output:
```
✓ Fetched HTML successfully
✓ Found X tracks
1. Artist - Track Name
2. Artist - Track Name (Remix)
...
```

### Debug Playlist Share URL

```bash
python debug_beatport.py "https://www.beatport.com/playlists/share/6421928"
```

Should show:
```
table.tracklist              →   1 found
table.tracklist tbody tr     →  XX found
```

## Supported URL Formats

### Before
- `https://www.beatport.com/chart/...`

### After
- `https://www.beatport.com/chart/...` (still supported)
- `https://www.beatport.com/playlists/share/[id]` (NEW)

## Backward Compatibility

All changes are **backward compatible**. The scraper will:
1. Try the new tracklist table method first
2. Fall back to all existing methods if not found
3. Work with both old and new URL formats

## Files Modified

1. `scraper.py` - Added table parsing method
2. `debug_beatport.py` - Added table detection
3. `test_playlist_url.py` - NEW test script
4. `README.md` - Updated features
5. `DEBUGGING.md` - Added URL format docs

## Build Status

```bash
npm run build
```

✓ Build successful - All files compatible

## Known Limitations

1. **Requires at least 2 `<td>` elements** per row (title + artist)
2. **Remix detection** only works for patterns in parentheses
3. **Label information** (if in same `<td>` as artist) not separated

## Future Enhancements

- Separate label from artist if both in same `<td>`
- Support additional table column formats
- Handle multi-row track entries
- Support BPM/key extraction from additional columns
