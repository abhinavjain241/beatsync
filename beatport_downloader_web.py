#!/usr/bin/env python3
"""
Beatport Playlist Downloader - Web Server Version
Non-interactive version optimized for use with the web interface.
"""

import sys
import os
from typing import List, Dict
from scraper import BeatportScraper
from downloader import AudioDownloader


class BeatportPlaylistDownloaderWeb:
    """Non-interactive version for web server use."""

    def __init__(self, output_dir: str = 'downloads'):
        self.scraper = BeatportScraper()
        self.downloader = AudioDownloader(output_dir)
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }

    def run(self, url: str):
        """
        Run the complete download process without interaction.

        Args:
            url: Beatport playlist URL
        """
        if not url:
            print("Error: No URL provided")
            sys.exit(1)

        # Fetch HTML content
        print(f"Fetching URL: {url}")
        html = self.scraper.fetch_html(url)

        if not html:
            print("Error: Failed to fetch URL")
            print("Possible reasons:")
            print("- Network connection issue")
            print("- Beatport may be blocking automated requests")
            print("- Invalid URL")
            sys.exit(1)

        # Parse tracks
        print("Parsing track information...")
        tracks = self.scraper.parse_tracks(html)

        if not tracks:
            print("Error: No tracks found")
            print("Debugging information:")
            print(f"- HTML length: {len(html)} characters")
            print("- Checking for common Beatport elements...")

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # Debug: check what elements we can find
            bucket_items = soup.find_all('li', class_='bucket-item')
            track_divs = soup.find_all('div', class_='track')
            track_rows = soup.find_all('tr', class_='track-row')
            playable_tracks = soup.find_all('div', {'data-track': True})
            track_list = soup.find_all('li', class_='track')

            print(f"- Found {len(bucket_items)} elements with class 'bucket-item'")
            print(f"- Found {len(track_divs)} elements with class 'track'")
            print(f"- Found {len(track_rows)} elements with class 'track-row'")
            print(f"- Found {len(playable_tracks)} elements with data-track attribute")
            print(f"- Found {len(track_list)} li elements with class 'track'")

            # Try to find any track-like structures
            titles = soup.find_all('a', class_='buk-track-title')
            artists = soup.find_all('p', class_='buk-track-artists')
            print(f"- Found {len(titles)} track titles")
            print(f"- Found {len(artists)} track artists")

            sys.exit(1)

        self.stats['total'] = len(tracks)
        print(f"Found {len(tracks)} tracks")

        # Download tracks
        print("Starting downloads...")
        self._download_tracks(tracks)

        # Display summary
        self._display_summary()

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
            print(f"  Downloading: {output_filename}")
            success = self.downloader.download_track(search_query, output_filename)

            if success:
                print(f"  ✓ Downloaded: {output_filename}")
                self.stats['downloaded'] += 1
            else:
                print(f"  ✗ Failed to download")
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


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: URL required")
        print("Usage: python beatport_downloader_web.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    downloader = BeatportPlaylistDownloaderWeb()
    downloader.run(url)


if __name__ == '__main__':
    main()
