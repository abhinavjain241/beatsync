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
        self.source = source
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }

    def run(self, url: Optional[str] = None, json_file: Optional[str] = None,
            local_html: Optional[str] = None, base_music_dir: Optional[str] = None):
        """
        Run the complete download process.

        Args:
            url: Beatport playlist URL (optional)
            json_file: Path to JSON file with track data (optional)
            local_html: Path to local HTML file (optional)
            base_music_dir: Base directory for music downloads (optional)
        """
        # If using JSON file and base_music_dir is provided, create folder from JSON filename
        if json_file and base_music_dir:
            json_filename = os.path.basename(json_file)
            folder_name = os.path.splitext(json_filename)[0]
            new_output_dir = os.path.join(base_music_dir, folder_name)

            # Update the downloader's output directory
            self.downloader.output_dir = new_output_dir
            self.downloader._ensure_output_dir()

        print("=" * 60)
        print("Beatport Playlist Downloader")
        print("=" * 60)
        if self.source == 'auto':
            print("Download mode: AUTO (searches both SoundCloud & YouTube, downloads longer version)")
        else:
            print(f"Download source: {self.source.upper()}")
        print(f"Output directory: {self.downloader.output_dir}")
        print()

        tracks = []

        # Priority 1: JSON file (fastest and most reliable)
        if json_file:
            print(f"Loading tracks from JSON file: {json_file}")
            tracks = self.scraper.load_json_file(json_file)

        # Priority 2: Local HTML file
        elif local_html:
            print(f"Loading tracks from local HTML: {local_html}")
            html = self.scraper.load_local_html(local_html)
            if html:
                print("Parsing track information...")
                tracks = self.scraper.parse_tracks(html)
            else:
                print("Failed to load HTML content.")
                return

        # Priority 3: URL scraping
        elif url:
            print(f"Fetching tracks from URL: {url}")
            html = self.scraper.fetch_html(url)

            if not html:
                print("Failed to fetch URL. Exiting...")
                return

            print("Parsing track information...")
            tracks = self.scraper.parse_tracks(html)

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
                    tracks = self.scraper.load_json_file(json_file)
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
            print()
            print("No tracks found. Please check your input.")
            print()
            print("Tips:")
            print("- For JSON files: Ensure the format is correct (see example)")
            print("- For URLs: Make sure the URL points to a valid Beatport playlist")
            print("- For HTML: Save the page after tracks have loaded")
            return

        self.stats['total'] = len(tracks)
        print(f"Found {len(tracks)} tracks")
        print()

        # Display tracks
        self._display_tracks(tracks)

        # Confirm before downloading
        print()
        response = input("Proceed with download? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Download cancelled.")
            return

        # Download tracks
        print()
        print("Starting downloads...")
        print("=" * 60)
        self._download_tracks(tracks)

        # Display summary
        self._display_summary()

    def _display_tracks(self, tracks: List[Dict[str, str]]):
        """Display list of tracks that will be downloaded."""
        print("Tracks to download:")
        print("-" * 60)
        for i, track in enumerate(tracks, 1):
            search_string = self.scraper.create_search_string(track)
            label_info = f" [{track['label']}]" if track.get('label') else ""
            print(f"{i}. {search_string}{label_info}")

    def _download_tracks(self, tracks: List[Dict[str, str]]):
        """Download all tracks."""
        for i, track in enumerate(tracks, 1):
            print(f"\n[{i}/{len(tracks)}] Processing: {track['artist']} - {track['track']}")

            # Create search query
            search_query = self.scraper.create_search_string(track)

            # Create output filename
            output_filename = self.downloader.create_filename(track)

            # Check if already exists
            output_path = os.path.join(self.downloader.output_dir, output_filename)
            if os.path.exists(output_path):
                print(f"  ✓ Already exists, skipping")
                self.stats['skipped'] += 1
                continue

            # Download
            success = self.downloader.download_track(search_query, output_filename)

            if success:
                self.stats['downloaded'] += 1
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
  # Downloads to /Users/srinidhi/Music/{json_filename}/
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
  - When using --json-file: Creates folder named after JSON file in /Users/srinidhi/Music/
    Example: basshouse_t100.json -> /Users/srinidhi/Music/basshouse_t100/
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

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        # User specified custom output directory
        output_dir = args.output_dir
        base_music_dir = None
    elif args.json_file:
        # Using JSON file - use temporary dir, will be updated in run()
        output_dir = 'downloads'  # temporary
        base_music_dir = '/Users/srinidhi/Music'
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
        base_music_dir=base_music_dir
    )


if __name__ == '__main__':
    main()
