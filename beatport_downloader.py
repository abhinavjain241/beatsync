#!/usr/bin/env python3
"""
Beatport Playlist Downloader

Downloads music from Beatport playlists by:
1. Scraping track information from Beatport
2. Searching for tracks on SoundCloud
3. Downloading audio as MP3 files

Usage:
    python beatport_downloader.py <beatport_url>
    python beatport_downloader.py  # Interactive mode
"""

import sys
import os
from typing import List, Dict
from scraper import BeatportScraper
from downloader import AudioDownloader


class BeatportPlaylistDownloader:
    """Main orchestrator for the Beatport playlist download process."""

    def __init__(self, output_dir: str = 'downloads'):
        self.scraper = BeatportScraper()
        self.downloader = AudioDownloader(output_dir)
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }

    def run(self, url: str = None):
        """
        Run the complete download process.

        Args:
            url: Beatport playlist URL (optional, will prompt if not provided)
        """
        print("=" * 60)
        print("Beatport Playlist Downloader")
        print("=" * 60)
        print()

        # Get URL if not provided
        if not url:
            url = input("Enter Beatport playlist URL: ").strip()

        if not url:
            print("Error: No URL provided")
            return

        # Fetch HTML content
        html = self.scraper.fetch_html(url)

        # If fetching fails, offer local file option
        if not html:
            print()
            print("Failed to fetch URL. You can provide a local HTML file instead.")
            file_path = input("Enter path to local HTML file (or press Enter to exit): ").strip()

            if not file_path:
                print("Exiting...")
                return

            html = self.scraper.load_local_html(file_path)

            if not html:
                print("Failed to load HTML content. Exiting...")
                return

        # Parse tracks
        print()
        print("Parsing track information...")
        tracks = self.scraper.parse_tracks(html)

        if not tracks:
            print("No tracks found. Please check the URL or HTML content.")
            print()
            print("Tips:")
            print("- Make sure the URL points to a valid Beatport playlist")
            print("- Try saving the page as HTML and using the local file option")
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
            print(f"{i}. {search_string}")

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
    # Check if URL provided as argument
    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]

    # Create and run downloader
    downloader = BeatportPlaylistDownloader()
    downloader.run(url)


if __name__ == '__main__':
    main()
