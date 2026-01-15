# Track Selection & Metadata Improvements

## Overview
This document describes the improvements made to track matching and metadata writing for Rekordbox compatibility.

## 1. Improved Track Name Matching Algorithm

### What Changed
The track matching algorithm now uses a more sophisticated approach that understands the structure of electronic music track names.

### Key Features

#### Component-Based Matching
Instead of simple word matching, the algorithm now:
- **Separates artists from track names** by recognizing common separators (-, /, etc.)
- **Handles multiple artists** correctly (commas, &, 'and', 'feat', 'ft', 'vs', 'x')
- **Extracts mix information** separately (Extended Mix, Original Mix, Remix, etc.)
- **Applies weighted scoring**:
  - Artist match: 40% weight
  - Track name match: 45% weight
  - Mix info match: 15% weight

#### Pattern Recognition
The algorithm recognizes common patterns in electronic music:
- Extended Mix / Original Mix / Radio Edit / Club Mix
- Remix patterns (e.g., "Artist Name Remix", "Artist Remix")
- Multiple separator styles in artist names
- Parentheses and brackets for mix information

#### Example Improvements
```
Query: "Sean Paul, Odd Mob - Get Busy Odd Mob Extended Club Mix"

Old Algorithm:
- Simple word matching would be confused by "Odd Mob" appearing twice

New Algorithm:
- Recognizes Sean Paul as primary artist
- Understands "Odd Mob" in title is the remixer
- Extracts "Extended Club Mix" as mix type
- Correctly matches: "Sean Paul - Get Busy (Odd Mob Extended Club Mix)" with 80%+ score
```

### Benefits
- More accurate track selection from search results
- Better handling of tracks where remix artist appears in both artist and title
- Reduced false positives from DJ mixes and unrelated tracks
- Higher confidence in track matching scores

## 2. Rekordbox-Compatible Metadata

### What Changed
Complete overhaul of metadata writing for maximum Rekordbox compatibility.

### Key Improvements

#### ID3 Version Change
- **Changed from ID3v2.4 to ID3v2.3**
- ID3v2.3 has better compatibility with Rekordbox and other DJ software
- Ensures metadata is readable across all platforms

#### Enhanced Metadata Fields
Now writes the following ID3 tags:
- **TIT2** (Title) - Track name
- **TPE1** (Artist) - Primary artist
- **TPE2** (Album Artist) - Same as artist for consistency
- **TALB** (Album) - Record label name
- **TCON** (Genre) - Music genre
- **TBPM** (BPM) - Beats per minute (critical for DJs)
- **TKEY** (Key) - Musical key (critical for harmonic mixing)
- **TYER** (Year) - Current year
- **COMM** (Comment) - Source information
- **APIC** (Album Art) - Embedded cover image

#### Album Art Embedding
- Uses **encoding=0** for binary data (not text)
- Sets **type=3** (front cover) for standard album art
- Supports both JPEG and PNG formats
- Properly resolves relative paths from JSON file location

#### Path Resolution
- Automatically resolves relative album art paths from JSON file directory
- Handles paths like `./basshouse_t100_files/image.jpg` correctly
- Works regardless of where the script is executed from

### Rekordbox-Specific Optimizations

1. **BPM and Key Fields**: These are critical for Rekordbox's DJ features
   - BPM enables beatmatching
   - Key enables harmonic mixing

2. **Album Art Encoding**: Uses binary encoding (0) instead of text encoding (3)
   - Ensures Rekordbox can properly display artwork
   - Works with Rekordbox's artwork management system

3. **Clean Tag Writing**: Clears all existing tags before writing
   - Prevents conflicts from previous metadata
   - Ensures consistent tag structure

4. **Complete Tag Set**: Writes all common tags even if empty
   - Rekordbox works better with complete metadata
   - Improves library organization and search

### Testing
All metadata is written using the Mutagen library with settings tested for Rekordbox compatibility:
```python
audio.save(v2_version=3)  # ID3v2.3 for maximum compatibility
```

## 3. Two-Step Track Selection Process

### Fetch Top 5 from Each Source
- Searches for top 5 results from both SoundCloud and YouTube
- Uses improved matching algorithm to select best track from each source
- Filters out tracks longer than 15 minutes (likely DJ sets)

### Intelligent Comparison
1. If relevance scores differ by more than 10%: Choose higher relevance track
2. If relevance scores are within 10%: Choose longer track
3. Always prefer quality match over duration

### Benefits
- More accurate track selection
- Better balance between relevance and duration
- Reduces chance of downloading wrong version

## Testing the Improvements

### Test Matching Algorithm
```bash
python3 test_improvements.py
```

### Test Full Download
```bash
python beatport_downloader.py --json-file basshouse_t100.json
```

## Verification in Rekordbox

After downloading, verify in Rekordbox:
1. Import MP3 files into Rekordbox
2. Check that all metadata is visible:
   - Track name, artist, album (label)
   - BPM and Key
   - Album artwork
   - Genre
3. Verify artwork displays in browser and deck views
4. Test BPM detection (should use embedded BPM)
5. Test key detection (should use embedded key)

## Technical Notes

### Dependencies
No new dependencies added. Uses existing:
- `mutagen` for ID3 tag writing
- `yt-dlp` for downloading

### Backward Compatibility
- All changes are backward compatible
- Existing JSON files work without modification
- Album art paths are resolved automatically

### Performance
- Slightly slower due to fetching 5 results instead of 1
- But much higher accuracy in track selection
- Worth the trade-off for better results
