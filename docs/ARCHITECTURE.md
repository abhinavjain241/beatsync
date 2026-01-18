# Architecture Overview

This document describes the architecture of the Beatport Playlist Downloader.

## Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                  beatport_downloader.py                     │
│                  (Main Orchestrator)                        │
│                                                             │
│  • Coordinates the entire download process                 │
│  • Manages user interaction                                │
│  • Tracks download statistics                              │
└──────────────┬──────────────────────┬──────────────────────┘
               │                      │
               │                      │
      ┌────────▼──────────┐  ┌────────▼──────────┐
      │   scraper.py      │  │  downloader.py    │
      │                   │  │                   │
      │ • Fetch HTML      │  │ • Search tracks   │
      │ • Parse tracks    │  │ • Download audio  │
      │ • Extract metadata│  │ • Convert to MP3  │
      └───────────────────┘  └───────────────────┘
               │                      │
               │                      │
      ┌────────▼──────────┐  ┌────────▼──────────┐
      │   Beatport        │  │   yt-dlp +        │
      │   (Website)       │  │   SoundCloud      │
      └───────────────────┘  └───────────────────┘
```

## Data Flow

```
1. User Input
   ↓
2. Fetch Beatport Playlist
   ↓
3. Parse HTML → Extract Track Info
   ↓
4. For Each Track:
   ├─ Create search query
   ├─ Search on SoundCloud via yt-dlp
   ├─ Download audio
   └─ Convert to MP3
   ↓
5. Save to downloads/ folder
   ↓
6. Display Summary
```

## Module Responsibilities

### beatport_downloader.py (Main Orchestrator)

**Responsibilities:**
- User interaction and input handling
- Coordinating scraper and downloader
- Progress tracking and statistics
- Summary reporting

**Key Classes:**
- `BeatportPlaylistDownloader`: Main orchestrator class

### scraper.py (Beatport Scraper)

**Responsibilities:**
- HTTP requests to Beatport
- HTML parsing with BeautifulSoup
- Track metadata extraction
- Search query generation
- Local HTML file fallback

**Key Classes:**
- `BeatportScraper`: Handles all scraping operations

**Key Methods:**
- `fetch_html()`: Get HTML from URL
- `load_local_html()`: Load from file
- `parse_tracks()`: Extract track info
- `create_search_string()`: Format search query

### downloader.py (Audio Downloader)

**Responsibilities:**
- Audio search via yt-dlp
- Download management
- File naming and sanitization
- Format conversion (MP3)
- Duplicate detection

**Key Classes:**
- `AudioDownloader`: Handles all download operations

**Key Methods:**
- `download_track()`: Search and download
- `create_filename()`: Generate filename
- `sanitize_filename()`: Clean invalid chars

## External Dependencies

### Python Libraries

- **requests**: HTTP client for fetching Beatport pages
- **beautifulsoup4**: HTML parsing and data extraction
- **lxml**: XML/HTML parser (faster than default)
- **yt-dlp**: YouTube/SoundCloud downloader

### System Tools

- **ffmpeg**: Audio format conversion (MP3)

## Error Handling

### HTTP Errors (403 Forbidden)
- Fallback to local HTML file
- User-friendly error messages
- Guidance for manual page saving

### Download Failures
- Individual track failures don't stop process
- Failed tracks are tracked in statistics
- Clear error messages for each failure

### Missing Dependencies
- Graceful error messages
- Installation instructions
- Dependency checker utility

## File Organization

Following single responsibility principle:

- **One file = One responsibility**
- **Clear module boundaries**
- **No circular dependencies**
- **Easy to test independently**

## Testing Strategy

### Manual Testing
- `test_components.py`: Test individual modules
- `example_usage.py`: Example usage patterns
- `check_dependencies.py`: Verify installation

### Test Coverage
- Module imports
- Basic functionality
- Filename sanitization
- Error handling

## Configuration

### Customizable Parameters

- **Output directory**: Where to save MP3 files
- **Audio quality**: yt-dlp quality setting (default: 0 = best)
- **Search source**: SoundCloud (via scsearch1:)

### Hardcoded Settings

- User-Agent string (to avoid bot detection)
- Timeout values (30s for HTTP, 5m for downloads)
- Audio format (MP3)

## Future Enhancements

Potential improvements:
- Parallel downloads
- Progress bars
- GUI interface
- Multiple source support (YouTube, etc.)
- Playlist management
- Download queue
- Retry mechanism
- Audio quality selection

## Security Considerations

- No API keys or credentials stored
- Uses public SoundCloud search
- Respects robots.txt indirectly via yt-dlp
- User-Agent string for legitimate access
- No copyright circumvention

## Performance

### Bottlenecks
- Network speed (downloading audio)
- SoundCloud search rate limits
- Sequential processing

### Optimizations
- Skip existing files
- Efficient HTML parsing
- Minimal memory footprint
- Stream-based downloads

## Deployment

### Requirements
- Python 3.7+
- Internet connection
- ~100MB disk space per album

### Installation Time
- 2-5 minutes (dependencies + ffmpeg)

### First Run
- Creates downloads/ directory automatically
- No configuration needed
