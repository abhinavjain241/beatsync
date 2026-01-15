# Track Selection Algorithm

## Overview

The Beatport Downloader uses a sophisticated two-stage track selection algorithm that prioritizes both relevance and audio quality (duration).

## How It Works

### Stage 1: Fetch Multiple Results

When using **AUTO mode** (searches both SoundCloud and YouTube):

1. Fetches **top 5 results** from SoundCloud
2. Fetches **top 5 results** from YouTube
3. Filters out tracks longer than 15 minutes (likely DJ sets or mixes)

### Stage 2: Relevance Scoring

For each set of results, the system:

1. **Calculates match scores** for all tracks against the original query
   - Normalizes both query and track titles (lowercase, removes special chars)
   - Computes word overlap percentage
   - Score ranges from 0.0 (no match) to 1.0 (perfect match)

2. **Selects best match** from each source
   - Must meet minimum threshold of 50% match
   - Chooses track with highest relevance score
   - Automatically filters out irrelevant results

### Stage 3: Duration-Based Selection

Between the best matches from SoundCloud and YouTube:

1. **Compares durations** of the two tracks
2. **Selects the longer version**
   - Longer versions typically have better quality
   - Extended mixes preferred over radio edits
   - Original mixes preferred over shortened versions

## Example Flow

```
Query: "Vintage Culture - Lost Extended Mix"

Stage 1: Fetch top 5 from each source
├─ SoundCloud results: 5 tracks
└─ YouTube results: 5 tracks

Stage 2: Find most relevant match
├─ SoundCloud: "Vintage Culture, Gabss - Lost (Extended Mix)" [Score: 0.89]
└─ YouTube: "Vintage Culture - Lost (Official Audio)" [Score: 0.75]

Stage 3: Select longer version
├─ SoundCloud: 6:24 duration
├─ YouTube: 3:45 duration
└─ ✓ Selected: SoundCloud (longer + more relevant)
```

## Match Score Calculation

### Algorithm

```python
# Normalize text: lowercase, remove punctuation, clean whitespace
query_words = set("vintage culture lost extended mix".split())
title_words = set("vintage culture gabss lost extended mix".split())

# Calculate overlap
common_words = query_words ∩ title_words  # {vintage, culture, lost, extended, mix}
max_length = max(len(query_words), len(title_words))

score = len(common_words) / max_length
# = 5 / 6 = 0.833 (83.3% match)
```

### Threshold

- **Minimum: 50%** - Tracks below this are rejected
- **Good match: 70%+** - Most tracks fall here
- **Excellent: 90%+** - Near-perfect title match

## Benefits

### 1. Better Accuracy
- Reduces false positives from generic search results
- Ensures you get the track you actually requested
- Filters out remixes when original is requested (and vice versa)

### 2. Quality Preference
- Automatically selects extended/original mixes over radio edits
- Prefers full-length versions
- Avoids truncated or low-quality uploads

### 3. Robustness
- Works even when titles don't match exactly
- Handles variations in artist names (featuring, collab formats)
- Tolerant of spelling differences and special characters

### 4. Transparency
- Shows match scores for both sources
- Displays why a particular source was selected
- Helps identify potential issues with queries

## Single-Source Mode

When using `--source soundcloud` or `--source youtube`:

1. Still fetches top 5 results
2. Finds most relevant match from that single source
3. No cross-source comparison needed

## Performance

- Fetching 5 results takes ~1-2 seconds longer than 1 result
- Trade-off is worthwhile for significantly better accuracy
- Parallel searches (SoundCloud + YouTube) run concurrently

## Customization

### Adjusting Match Threshold

Edit `downloader.py` line 271 and 272:

```python
# More strict (fewer false positives, might miss some tracks)
sc_info = self.find_best_match(sc_tracks, search_query, threshold=0.7)

# More lenient (catches more tracks, more false positives)
sc_info = self.find_best_match(sc_tracks, search_query, threshold=0.4)
```

### Changing Result Count

Edit line 261 and 262:

```python
# Fetch more results (slower, better accuracy)
sc_url = f"scsearch10:{search_query}"
yt_url = f"ytsearch10:{search_query}"
```

## Debugging

The downloader shows detailed information during selection:

```
Searching top 5 results from SoundCloud and YouTube...
  SoundCloud: Track Name (6:24) [match: 89%]
  YouTube: Track Name (3:45) [match: 75%]
  ✓ Selected SoundCloud (longer version)
```

This helps you understand:
- What was found on each platform
- How well each result matched your query
- Why a particular source was chosen
