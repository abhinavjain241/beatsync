"""
Beatport playlist scraper module.
Handles scraping track information from Beatport URLs.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class BeatportScraper:
    """Scrapes track information from Beatport playlists."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from Beatport URL.

        Args:
            url: Beatport playlist URL

        Returns:
            HTML content as string, or None if request fails
        """
        try:
            print(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def load_local_html(self, file_path: str) -> Optional[str]:
        """
        Load HTML content from a local file.

        Args:
            file_path: Path to local HTML file

        Returns:
            HTML content as string, or None if file cannot be read
        """
        try:
            print(f"Reading local file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading local file: {e}")
            return None

    def parse_tracks(self, html: str) -> List[Dict[str, str]]:
        """
        Parse track information from Beatport HTML.

        Args:
            html: HTML content

        Returns:
            List of track dictionaries with 'artist', 'track', and 'remix' keys
        """
        soup = BeautifulSoup(html, 'lxml')
        tracks = []

        # Try multiple selectors as Beatport's structure may vary
        # Method 1: bucket-item (older Beatport structure)
        track_elements = soup.find_all('li', class_='bucket-item')
        print(f"Method 1 (bucket-item): Found {len(track_elements)} elements")

        if not track_elements:
            # Method 2: track class
            track_elements = soup.find_all('div', class_='track')
            print(f"Method 2 (div.track): Found {len(track_elements)} elements")

        if not track_elements:
            # Method 3: table rows
            track_elements = soup.find_all('tr', class_='track-row')
            print(f"Method 3 (track-row): Found {len(track_elements)} elements")

        if not track_elements:
            # Method 4: li with track class
            track_elements = soup.find_all('li', class_='track')
            print(f"Method 4 (li.track): Found {len(track_elements)} elements")

        if not track_elements:
            # Method 5: Look for data-track attributes (modern Beatport)
            track_elements = soup.find_all(['div', 'li', 'tr'], attrs={'data-track': True})
            print(f"Method 5 (data-track): Found {len(track_elements)} elements")

        if not track_elements:
            # Method 6: Look for playable-track class
            track_elements = soup.find_all(['div', 'li'], class_='playable-track')
            print(f"Method 6 (playable-track): Found {len(track_elements)} elements")

        print(f"Total track elements to process: {len(track_elements)}")

        for element in track_elements:
            track_info = self._extract_track_info(element)
            if track_info:
                tracks.append(track_info)

        return tracks

    def _extract_track_info(self, element) -> Optional[Dict[str, str]]:
        """
        Extract track information from a single element.

        Args:
            element: BeautifulSoup element containing track info

        Returns:
            Dictionary with track info or None if extraction fails
        """
        try:
            # Try to find artist - multiple approaches
            artist = ''

            # Method 1: buk-track-artists (older Beatport)
            artist_elem = element.find('p', class_='buk-track-artists')
            if not artist_elem:
                # Method 2: Various artist classes
                artist_elem = element.find('a', class_='artist')
            if not artist_elem:
                artist_elem = element.find('span', class_='artist')
            if not artist_elem:
                # Method 3: Modern structure - look for artist link/span in track container
                artist_elem = element.select_one('.track-artists a, .track-artist a, [class*="artist"] a')
            if not artist_elem:
                # Method 4: Look for data-artist attribute
                artist_elem = element.find(attrs={'data-artist': True})
                if artist_elem:
                    artist = artist_elem.get('data-artist', '')
            if artist_elem and not artist:
                artist = artist_elem.get_text(strip=True)

            # Try to find track name - multiple approaches
            track = ''

            # Method 1: buk-track-primary-title (older Beatport)
            track_elem = element.find('p', class_='buk-track-primary-title')
            if not track_elem:
                # Method 2: buk-track-title
                track_elem = element.find('a', class_='buk-track-title')
            if not track_elem:
                # Method 3: track-title class
                track_elem = element.find('a', class_='track-title')
            if not track_elem:
                track_elem = element.find('span', class_='track-title')
            if not track_elem:
                # Method 4: Modern structure - look for title in various containers
                track_elem = element.select_one('.track-title, .track-name, [class*="title"] a, [class*="name"] a')
            if not track_elem:
                # Method 5: Look for data-title or data-track-title attribute
                track_elem = element.find(attrs={'data-title': True})
                if not track_elem:
                    track_elem = element.find(attrs={'data-track-title': True})
                if track_elem:
                    track = track_elem.get('data-title', '') or track_elem.get('data-track-title', '')
            if track_elem and not track:
                track = track_elem.get_text(strip=True)

            # Try to find remix name
            remix = ''
            remix_elem = element.find('p', class_='buk-track-remixed')
            if not remix_elem:
                remix_elem = element.find('span', class_='buk-track-remixed')
            if not remix_elem:
                remix_elem = element.find('span', class_='remix')
            if not remix_elem:
                remix_elem = element.select_one('.track-remix, [class*="remix"]')
            if remix_elem:
                remix = remix_elem.get_text(strip=True)

            # Clean up artist and track
            artist = artist.replace('\n', ' ').strip()
            track = track.replace('\n', ' ').strip()
            remix = remix.replace('\n', ' ').strip()

            # Only return if we have at least artist and track
            if artist and track:
                return {
                    'artist': artist,
                    'track': track,
                    'remix': remix
                }

            return None

        except Exception as e:
            print(f"Error extracting track info: {e}")
            return None

    def create_search_string(self, track_info: Dict[str, str]) -> str:
        """
        Create a search string from track information.

        Args:
            track_info: Dictionary with 'artist', 'track', and 'remix' keys

        Returns:
            Formatted search string
        """
        parts = [track_info['artist'], track_info['track']]
        if track_info.get('remix'):
            parts.append(track_info['remix'])
        return ' '.join(parts)
