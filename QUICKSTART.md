# Quick Start Guide

## Using JSON Files (Recommended Method)

The fastest way to download tracks is using a JSON file.

### Step 1: Create Your JSON File

Create a file named `tracks.json` with your track list:

```json
[
  {
    "artist_name": "Westend, SIDEPIECE",
    "song_name": "Take Your Places Extended Mix"
  },
  {
    "artist_name": "bradeazy",
    "song_name": "Up Down Extended Mix"
  },
  {
    "artist_name": "Sean Paul, Odd Mob",
    "song_name": "Get Busy Odd Mob Extended Club Mix"
  }
]
```

### Step 2: Run the Downloader

```bash
python beatport_downloader.py --json-file tracks.json
```

That's it! The tracks will be downloaded to the `downloads/` folder.

## Example Output

```
============================================================
Beatport Playlist Downloader
============================================================

Reading JSON file: tracks.json
Found 3 tracks in JSON file
✓ Successfully parsed 3 tracks

Tracks to download:
------------------------------------------------------------
1. Westend, SIDEPIECE - Take Your Places Extended Mix
2. bradeazy - Up Down Extended Mix
3. Sean Paul, Odd Mob - Get Busy Odd Mob Extended Club Mix

Proceed with download? (y/n): y

Starting downloads...
============================================================

[1/3] Processing: Westend, SIDEPIECE - Take Your Places
  Downloading: Westend, SIDEPIECE - Take Your Places.mp3
  ✓ Downloaded successfully

[2/3] Processing: bradeazy - Up Down
  Downloading: bradeazy - Up Down.mp3
  ✓ Downloaded successfully

[3/3] Processing: Sean Paul, Odd Mob - Get Busy Odd Mob Extended
  Downloading: Sean Paul, Odd Mob - Get Busy Odd Mob Extended.mp3
  ✓ Downloaded successfully

============================================================
Download Summary
============================================================
Total tracks:      3
Downloaded:        3
Already existed:   0
Failed:            0

Success rate: 100.0%

Files saved to: downloads/
============================================================
```

## JSON Format Details

Each track object should have:
- `artist_name`: The artist(s) name (required)
- `song_name`: The track name, including remix info (required)
- `label`: The record label (optional)

The script automatically:
- Separates remix info from track names
- Handles multiple artists
- Creates clean filenames
- Skips already downloaded tracks

## Using the Example File

An example file `basshouse_t100.json` is included with 100 Bass House tracks:

```bash
python beatport_downloader.py --json-file basshouse_t100.json
```

## Tips

1. **Multiple Artists**: Separate with commas
   ```json
   "artist_name": "Artist 1, Artist 2, Artist 3"
   ```

2. **Remix Info**: Include in the song name
   ```json
   "song_name": "Track Name Extended Mix"
   "song_name": "Track Name Original Mix"
   "song_name": "Track Name Artist Remix"
   ```

3. **Special Characters**: Use proper JSON escaping
   ```json
   "song_name": "Track Name (feat. Someone)"
   ```

4. **Custom Output**: Specify a different folder
   ```bash
   python beatport_downloader.py --json-file tracks.json --output-dir "my_music"
   ```

## Troubleshooting

**File not found:**
```bash
# Use absolute path
python beatport_downloader.py --json-file "/full/path/to/tracks.json"
```

**Invalid JSON:**
- Check for missing commas between objects
- Ensure all quotes are properly closed
- Use a JSON validator online

**No tracks found:**
- Verify `artist_name` and `song_name` fields exist
- Check that the JSON is an array `[...]`

## Next Steps

- See [README.md](README.md) for full documentation
- See [AUTHENTICATION.md](AUTHENTICATION.md) for private playlist solutions
- Try other input methods (URL, HTML file)
