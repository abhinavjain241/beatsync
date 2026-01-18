#!/usr/bin/env python3
"""
Beatport Playlist Downloader

Downloads music from Beatport playlists by:
1. Scraping track information from Beatport (URL or JSON file)
2. Searching for tracks on both SoundCloud AND YouTube (AUTO mode)
3. Comparing durations and downloading the longer version
4. Downloading audio as MP3 files

Usage:
    python beatport_downloader.py --json-file <path_to_json>
    python beatport_downloader.py --json-file <path_to_json> --source soundcloud
    python beatport_downloader.py --json-file <path_to_json> --source youtube
    python beatport_downloader.py --url <beatport_url>
    python beatport_downloader.py --local-html <path_to_html>
    python beatport_downloader.py  # Interactive mode
"""

import sys
import os
import argparse
from typing import List, Dict, Optional
from scraper import BeatportScraper
from downloader import AudioDownloader
from metadata_writer import MetadataWriter


class BeatportPlaylistDownloader:
    """Main orchestrator for the Beatport playlist download process."""

    def __init__(self, output_dir: str = 'downloads', source: str = 'auto'):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files
            source: Download source ('soundcloud', 'youtube', or 'auto' to search both)
        """
        self.scraper = BeatportScraper()
        self.downloader = AudioDownloader(output_dir, source)
        self.metadata_writer = MetadataWriter()
        self.source = source
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'metadata_added': 0,
            'metadata_failed': 0
        }
        self.track_metadata_map = {}
        self.json_file_dir = None

    def run(self, url: Optional[str] = None, json_file: Optional[str] = None,
            local_html: Optional[str] = None, base_music_dir: Optional[str] = None,
            auto_confirm: bool = False):
        """
        Run the complete download process.

        Args:
            url: Beatport playlist URL (optional)
            json_file: Path to JSON file with track data (optional)
            local_html: Path to local HTML file (optional)
            base_music_dir: Base directory for music downloads (optional)
            auto_confirm: Skip confirmation prompt (for non-interactive mode)
        """
        try:
            print("[STAGE] Initializing downloader", flush=True)

            # If using JSON file and base_music_dir is provided, create folder from JSON filename
            if json_file and base_music_dir:
                json_filename = os.path.basename(json_file)
                folder_name = os.path.splitext(json_filename)[0]
                new_output_dir = os.path.join(base_music_dir, folder_name)

                # Update the downloader's output directory
                self.downloader.output_dir = new_output_dir
                self.downloader._ensure_output_dir()
                print(f"[INFO] Output directory set to: {new_output_dir}", flush=True)

            print("=" * 60, flush=True)
            print("Beatport Playlist Downloader", flush=True)
            print("=" * 60, flush=True)
            if self.source == 'auto':
                print("Download mode: AUTO (searches both SoundCloud & YouTube, downloads longer version)", flush=True)
            else:
                print(f"Download source: {self.source.upper()}", flush=True)
            print(f"Output directory: {self.downloader.output_dir}", flush=True)
            print(flush=True)

            tracks = []

            # Priority 1: JSON file (fastest and most reliable)
            if json_file:
                print("[STAGE] Loading JSON file", flush=True)
                print(f"Loading tracks from JSON file: {json_file}", flush=True)

                if not os.path.exists(json_file):
                    print(f"[ERROR] JSON file not found: {json_file}", flush=True)
                    sys.exit(1)

                try:
                    tracks = self.scraper.load_json_file(json_file)
                    print(f"[SUCCESS] Loaded {len(tracks)} tracks from JSON", flush=True)
                    # Store JSON file directory for resolving relative album art paths
                    self.json_file_dir = os.path.dirname(os.path.abspath(json_file))
                    # Store metadata for later use
                    self._store_track_metadata(tracks)
                except Exception as e:
                    print(f"[ERROR] Failed to parse JSON file: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)

            # Priority 2: Local HTML file
            elif local_html:
                print("[STAGE] Loading HTML file", flush=True)
                print(f"Loading tracks from local HTML: {local_html}", flush=True)

                if not os.path.exists(local_html):
                    print(f"[ERROR] HTML file not found: {local_html}", flush=True)
                    sys.exit(1)

                try:
                    html = self.scraper.load_local_html(local_html)
                    if html:
                        print("[STAGE] Parsing HTML content", flush=True)
                        tracks = self.scraper.parse_tracks(html)
                        print(f"[SUCCESS] Parsed {len(tracks)} tracks from HTML", flush=True)
                    else:
                        print("[ERROR] Failed to load HTML content", flush=True)
                        sys.exit(1)
                except Exception as e:
                    print(f"[ERROR] Failed to process HTML file: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)

            # Priority 3: URL scraping
            elif url:
                print("[STAGE] Fetching URL", flush=True)
                print(f"Fetching tracks from URL: {url}", flush=True)

                try:
                    html = self.scraper.fetch_html(url)

                    if not html:
                        print("[ERROR] Failed to fetch URL - no HTML returned", flush=True)
                        sys.exit(1)

                    print("[STAGE] Parsing URL content", flush=True)
                    tracks = self.scraper.parse_tracks(html)
                    print(f"[SUCCESS] Parsed {len(tracks)} tracks from URL", flush=True)
                except Exception as e:
                    print(f"[ERROR] Failed to fetch or parse URL: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    sys.exit(1)

            # Interactive mode: prompt user for input
            else:
                print("Select input method:")
                print("1. JSON file (recommended)")
                print("2. Beatport playlist URL")
                print("3. Local HTML file")
                print()
                choice = input("Enter choice (1-3): ").strip()

                if choice == '1':
                    json_file = input("Enter path to JSON file: ").strip()
                    if json_file:
                        self.json_file_dir = os.path.dirname(os.path.abspath(json_file))
                        tracks = self.scraper.load_json_file(json_file)
                        self._store_track_metadata(tracks)
                elif choice == '2':
                    url = input("Enter Beatport playlist URL: ").strip()
                    if url:
                        html = self.scraper.fetch_html(url)
                        if html:
                            print("Parsing track information...")
                            tracks = self.scraper.parse_tracks(html)
                elif choice == '3':
                    local_html = input("Enter path to local HTML file: ").strip()
                    if local_html:
                        html = self.scraper.load_local_html(local_html)
                        if html:
                            print("Parsing track information...")
                            tracks = self.scraper.parse_tracks(html)

            if not tracks:
                print("[ERROR] No tracks found in input", flush=True)
                print()
                print("No tracks found. Please check your input.")
                print()
                print("Tips:")
                print("- For JSON files: Ensure the format is correct (see example)")
                print("- For URLs: Make sure the URL points to a valid Beatport playlist")
                print("- For HTML: Save the page after tracks have loaded")
                sys.exit(1)

            self.stats['total'] = len(tracks)
            print(f"[SUCCESS] Found {len(tracks)} tracks", flush=True)
            print(f"Found {len(tracks)} tracks", flush=True)
            print(flush=True)

            # Display tracks
            print("[STAGE] Displaying track list", flush=True)
            self._display_tracks(tracks)

            # Confirm before downloading
            print(flush=True)
            if not auto_confirm:
                response = input("Proceed with download? (y/n): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("[INFO] Download cancelled by user", flush=True)
                    sys.exit(0)
            else:
                print("[INFO] Auto-confirming download (non-interactive mode)", flush=True)

            # Download tracks
            print(flush=True)
            print("[STAGE] Starting download process", flush=True)
            print("Starting downloads...", flush=True)
            print("=" * 60, flush=True)

            try:
                self._download_tracks(tracks)
            except Exception as e:
                print(f"[ERROR] Download process failed: {e}", flush=True)
                import traceback
                traceback.print_exc()
                sys.exit(1)

            # Display summary
            print("[STAGE] Generating summary", flush=True)
            self._display_summary()
            print("[SUCCESS] Download process completed", flush=True)

        except Exception as e:
            print(f"[FATAL ERROR] Unexpected error in run(): {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def _display_tracks(self, tracks: List[Dict[str, str]]):
        """Display list of tracks that will be downloaded."""
        print("Tracks to download:")
        print("-" * 60)
        for i, track in enumerate(tracks, 1):
            search_string = self.scraper.create_search_string(track)
            label_info = f" [{track['label']}]" if track.get('label') else ""
            print(f"{i}. {search_string}{label_info}")

    def _store_track_metadata(self, tracks: List[Dict[str, str]]):
        """
        Store track metadata for later lookup.

        Args:
            tracks: List of track dictionaries
        """
        print("\n[DEBUG] Storing track metadata...")
        for i, track in enumerate(tracks, 1):
            # Create a normalized key for matching
            search_query = self.scraper.create_search_string(track)
            normalized_key = self._normalize_text(search_query)
            self.track_metadata_map[normalized_key] = track

            # Debug: Show what metadata fields are stored for first track
            if i == 1:
                print(f"[DEBUG] Sample track metadata fields stored: {list(track.keys())}")
                print(f"[DEBUG] Sample has artist_name: {'artist_name' in track}")
                print(f"[DEBUG] Sample has song_name: {'song_name' in track}")
                print(f"[DEBUG] Sample has genre: {'genre' in track}")
                print(f"[DEBUG] Sample has bpm_key: {'bpm_key' in track}")

        print(f"[DEBUG] Stored metadata for {len(tracks)} tracks\n")

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison (using same logic as downloader).

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _get_metadata_for_track(self, track: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Get metadata for a track from the stored map.

        Args:
            track: Track dictionary with 'artist' and 'track' keys

        Returns:
            Metadata dictionary or None if not found
        """
        search_query = self.scraper.create_search_string(track)
        normalized_key = self._normalize_text(search_query)
        return self.track_metadata_map.get(normalized_key)

    def _download_tracks(self, tracks: List[Dict[str, str]]):
        """Download all tracks."""
        for i, track in enumerate(tracks, 1):
            print(f"\n[{i}/{len(tracks)}] Processing: {track['artist']} - {track['track']}")

            # Create search query
            search_query = self.scraper.create_search_string(track)

            # Download (the downloader will check for existing files and use actual metadata)
            success, actual_filename, already_existed = self.downloader.download_track(search_query, track)

            if success:
                if already_existed:
                    self.stats['skipped'] += 1
                else:
                    self.stats['downloaded'] += 1

                # Apply metadata if we have it and the file exists
                if actual_filename and not already_existed:
                    metadata = self._get_metadata_for_track(track)
                    if metadata:
                        print(f"  Applying metadata to: {actual_filename}")

                        # Debug: Show what metadata we retrieved
                        print(f"  [DEBUG] Retrieved metadata fields: {list(metadata.keys())}")
                        print(f"  [DEBUG] Artist: {metadata.get('artist_name', 'N/A')}")
                        print(f"  [DEBUG] Song: {metadata.get('song_name', 'N/A')}")
                        print(f"  [DEBUG] Genre: {metadata.get('genre', 'N/A')}")
                        print(f"  [DEBUG] BPM/Key: {metadata.get('bpm_key', 'N/A')}")
                        print(f"  [DEBUG] Label: {metadata.get('label_name', 'N/A')}")

                        # Resolve album art path relative to JSON file directory (only for non-URLs)
                        if metadata.get('album_art') and self.json_file_dir:
                            album_art_path = metadata['album_art']
                            # Only resolve path if it's not a URL and not absolute
                            if not album_art_path.startswith(('http://', 'https://')) and not os.path.isabs(album_art_path):
                                resolved_path = os.path.join(self.json_file_dir, album_art_path)
                                print(f"  Resolved album art path: {album_art_path} -> {resolved_path}")
                                metadata['album_art'] = resolved_path

                        mp3_path = os.path.join(self.downloader.output_dir, actual_filename)

                        # Verify file exists before writing metadata
                        if not os.path.exists(mp3_path):
                            print(f"  ⚠ MP3 file not found: {mp3_path}")
                            self.stats['metadata_failed'] += 1
                        else:
                            print(f"  MP3 file confirmed: {mp3_path}")
                            try:
                                if self.metadata_writer.apply_metadata_to_track(mp3_path, metadata):
                                    self.stats['metadata_added'] += 1
                                else:
                                    self.stats['metadata_failed'] += 1
                            except Exception as e:
                                print(f"  ⚠ Metadata error: {e}")
                                import traceback
                                traceback.print_exc()
                                self.stats['metadata_failed'] += 1
                    else:
                        print(f"  ⚠ No metadata found for track in JSON")
            else:
                self.stats['failed'] += 1

    def _display_summary(self):
        """Display download summary statistics."""
        print()
        print("=" * 60)
        print("Download Summary")
        print("=" * 60)
        print(f"Total tracks:      {self.stats['total']}")
        print(f"Downloaded:        {self.stats['downloaded']}")
        print(f"Already existed:   {self.stats['skipped']}")
        print(f"Failed:            {self.stats['failed']}")

        # Show metadata stats if applicable
        if self.stats['metadata_added'] > 0 or self.stats['metadata_failed'] > 0:
            print(f"Metadata added:    {self.stats['metadata_added']}")
            if self.stats['metadata_failed'] > 0:
                print(f"Metadata failed:   {self.stats['metadata_failed']}")

        print()

        success_rate = 0
        if self.stats['total'] > 0:
            success_count = self.stats['downloaded'] + self.stats['skipped']
            success_rate = (success_count / self.stats['total']) * 100

        print(f"Success rate: {success_rate:.1f}%")
        print()
        print(f"Files saved to: {self.downloader.output_dir}/")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download music from Beatport playlists',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use JSON file with AUTO mode (default - searches both sources, downloads longer)
  # Downloads to ~/Music/{json_filename}/
  python beatport_downloader.py --json-file tracks.json

  # Use JSON file with SoundCloud only
  python beatport_downloader.py --json-file tracks.json --source soundcloud

  # Use JSON file with custom output directory
  python beatport_downloader.py --json-file tracks.json --output-dir /path/to/folder

  # Use Beatport URL
  python beatport_downloader.py --url https://www.beatport.com/library/playlists/12345

  # Use local HTML file with specific source
  python beatport_downloader.py --local-html playlist.html --source youtube

  # Interactive mode
  python beatport_downloader.py

Download Sources:
  - auto: (DEFAULT) Searches both SoundCloud and YouTube, downloads the longer version
  - soundcloud: Searches SoundCloud only
  - youtube: Searches YouTube only

Output Directory:
  - When using --json-file: Creates folder named after JSON file in ~/Music/
    Example: basshouse_t100.json -> ~/Music/basshouse_t100/
  - Override with --output-dir to specify custom location
  - For URLs/HTML files: Uses --output-dir value (default: downloads/)

JSON Format:
  [
    {
      "artist_name": "Artist Name",
      "song_name": "Track Name Extended Mix"
    },
    ...
  ]
        """
    )

    parser.add_argument(
        '--json-file',
        '-j',
        type=str,
        help='Path to JSON file containing track data'
    )

    parser.add_argument(
        '--url',
        '-u',
        type=str,
        help='Beatport playlist URL'
    )

    parser.add_argument(
        '--local-html',
        '-l',
        type=str,
        help='Path to local HTML file'
    )

    parser.add_argument(
        '--output-dir',
        '-o',
        type=str,
        default=None,
        help='Output directory for downloaded files (overrides default JSON-based location)'
    )

    parser.add_argument(
        '--source',
        '-s',
        type=str,
        choices=['soundcloud', 'youtube', 'auto'],
        default='auto',
        help='Download source: auto (default - searches both and downloads longer), soundcloud, or youtube'
    )

    parser.add_argument(
        '--yes',
        '-y',
        action='store_true',
        help='Auto-confirm download without prompting (for non-interactive mode)'
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        # User specified custom output directory
        output_dir = args.output_dir
        base_music_dir = None
    elif args.json_file:
        # Using JSON file - use temporary dir, will be updated in run()
        output_dir = 'downloads'  # temporary
        base_music_dir = os.path.expanduser('~/Music')
    else:
        # URL or HTML - use default downloads folder
        output_dir = 'downloads'
        base_music_dir = None

    # Create and run downloader
    downloader = BeatportPlaylistDownloader(
        output_dir=output_dir,
        source=args.source
    )
    downloader.run(
        url=args.url,
        json_file=args.json_file,
        local_html=args.local_html,
        base_music_dir=base_music_dir,
        auto_confirm=args.yes
    )


if __name__ == '__main__':
    main()
