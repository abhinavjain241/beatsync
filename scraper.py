"""
Beatport playlist scraper module.
Handles scraping track information from Beatport URLs.
"""

import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class BeatportScraper:
    """Scrapes track information from Beatport playlists."""

    def __init__(self):
        self.driver = None

    def _setup_driver(self):
        """Set up headless Chrome WebDriver with webdriver_manager."""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def fetch_html(self, url: str, save_debug_html: bool = True) -> Optional[str]:
        """
        Fetch HTML content from Beatport URL using Selenium.

        Args:
            url: Beatport playlist URL
            save_debug_html: Save HTML to debug.html for inspection

        Returns:
            HTML content as string, or None if request fails
        """
        try:
            print(f"Fetching URL with Selenium: {url}")
            self._setup_driver()

            self.driver.get(url)

            # Wait for the page to load
            print("Waiting for page to load...")
            time.sleep(3)

            # Scroll down to trigger lazy loading of tracks
            print("Scrolling to load all tracks...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for i in range(10):  # Scroll up to 10 times
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                # Check if we've loaded more content
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # No more content loaded
                    break
                last_height = new_height
                print(f"  Scroll {i+1}: Page height = {new_height}")

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

            # Wait for __NEXT_DATA__ to be populated with track data
            print("Waiting for track data to load...")
            max_wait = 30
            for attempt in range(max_wait):
                html = self.driver.page_source

                # Check if track data is present in JSON
                import re
                import json
                pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
                match = re.search(pattern, html, re.DOTALL)

                if match:
                    try:
                        data = json.loads(match.group(1))
                        # Check if queries contain track data
                        queries = data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])

                        for query in queries:
                            state_data = query.get('state', {}).get('data', {})
                            if isinstance(state_data, dict):
                                track_list = state_data.get('results') or state_data.get('tracks') or []
                                if isinstance(track_list, list) and len(track_list) > 0:
                                    print(f"✓ Track data loaded! Found {len(track_list)} tracks")
                                    break

                        if track_list and len(track_list) > 0:
                            break

                    except json.JSONDecodeError:
                        pass

                print(f"  Waiting for tracks... ({attempt + 1}/{max_wait})")
                time.sleep(1)

            html = self.driver.page_source

            if save_debug_html:
                try:
                    with open('debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("Saved page HTML to debug.html for inspection")
                except Exception as e:
                    print(f"Could not save debug HTML: {e}")

            return html
        except Exception as e:
            print(f"Error fetching URL with Selenium: {e}")
            return None

    def __del__(self):
        """Clean up WebDriver on deletion."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

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
            List of track dictionaries with 'artist', 'track', 'remix', and 'label' keys
        """
        import json
        import re

        tracks = []

        # First, try to extract from __NEXT_DATA__ JSON (modern Beatport)
        pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)

        if match:
            try:
                data = json.loads(match.group(1))
                tracks = self._extract_from_json(data)
                if tracks:
                    print(f"Successfully extracted {len(tracks)} tracks from JSON data")
                    return tracks
            except json.JSONDecodeError:
                print("Found __NEXT_DATA__ but couldn't parse JSON")

        # Fallback to HTML parsing
        soup = BeautifulSoup(html, 'lxml')
        track_elements = []

        selectors = [
            ('div', lambda x: x and 'bucket-item' in x and 'track' in x),
            ('li', 'bucket-item'),
            ('div', 'track'),
            ('tr', 'track-row'),
            ('div', 'playqueue-track'),
            ('li', lambda x: x and 'track' in x if x else False)
        ]

        for tag, class_filter in selectors:
            track_elements = soup.find_all(tag, class_=class_filter)
            if track_elements:
                print(f"Found {len(track_elements)} track elements using <{tag}> with class filter")
                break

        if not track_elements:
            print("No track elements found with standard selectors.")
            print("Checking for common class patterns...")
            all_divs = soup.find_all('div', class_=True)
            track_like = [d for d in all_divs if any(word in ' '.join(d.get('class', [])).lower() for word in ['track', 'song', 'item'])]
            if track_like:
                print(f"Found {len(track_like)} potential track elements")
                track_elements = track_like[:50]

        print(f"Attempting to parse {len(track_elements)} elements")

        for element in track_elements:
            track_info = self._extract_track_info(element)
            if track_info:
                tracks.append(track_info)

        return tracks

    def _extract_from_json(self, data: dict) -> List[Dict[str, str]]:
        """
        Extract tracks from Beatport's __NEXT_DATA__ JSON structure.

        Args:
            data: Parsed JSON data from __NEXT_DATA__

        Returns:
            List of track dictionaries
        """
        tracks = []

        try:
            # Navigate through the JSON structure
            page_props = data.get('props', {}).get('pageProps', {})
            dehydrated = page_props.get('dehydratedState', {})
            queries = dehydrated.get('queries', [])

            # Look through all queries for track data
            for query in queries:
                state_data = query.get('state', {}).get('data', {})

                # Check if this query contains tracks
                if isinstance(state_data, dict):
                    # Check for 'results' or 'tracks' key
                    track_list = state_data.get('results') or state_data.get('tracks') or []

                    if isinstance(track_list, list) and len(track_list) > 0:
                        # Check if first item looks like a track
                        first_item = track_list[0]
                        if isinstance(first_item, dict) and 'name' in first_item:
                            for track_data in track_list:
                                track_info = self._parse_json_track(track_data)
                                if track_info:
                                    tracks.append(track_info)

                            if tracks:
                                return tracks

        except Exception as e:
            print(f"Error extracting from JSON: {e}")

        return tracks

    def _parse_json_track(self, track_data: dict) -> Optional[Dict[str, str]]:
        """
        Parse a single track from JSON data.

        Args:
            track_data: Dictionary containing track information

        Returns:
            Dictionary with track info or None if parsing fails
        """
        try:
            # Extract track name
            track = track_data.get('name', '')

            # Extract artists
            artists_list = track_data.get('artists', [])
            if isinstance(artists_list, list):
                artist_names = [a.get('name', '') for a in artists_list if isinstance(a, dict)]
                artist = ', '.join(artist_names)
            else:
                artist = ''

            # Extract remix info
            remix = track_data.get('mix_name', '')

            # Extract label
            label_data = track_data.get('label') or track_data.get('release', {}).get('label', {})
            if isinstance(label_data, dict):
                label = label_data.get('name', '')
            else:
                label = ''

            if artist and track:
                return {
                    'artist': artist,
                    'track': track,
                    'remix': remix,
                    'label': label
                }

        except Exception as e:
            print(f"Error parsing track: {e}")

        return None

    def _extract_track_info(self, element) -> Optional[Dict[str, str]]:
        """
        Extract track information from a single element.

        Args:
            element: BeautifulSoup element containing track info

        Returns:
            Dictionary with track info or None if extraction fails
        """
        try:
            artist = ''
            artist_selectors = [
                ('span', 'track-artists'),
                ('p', 'buk-track-artists'),
                ('a', 'artist'),
                ('span', 'artist'),
                ('div', lambda x: x and 'artist' in x if x else False),
                ('span', lambda x: x and 'artist' in x if x else False)
            ]

            for tag, class_filter in artist_selectors:
                artist_elem = element.find(tag, class_=class_filter)
                if artist_elem:
                    artist = artist_elem.get_text(strip=True)
                    break

            track = ''
            track_selectors = [
                ('span', 'track-title'),
                ('p', 'buk-track-primary-title'),
                ('a', 'track-title'),
                ('a', 'buk-track-title'),
                ('div', lambda x: x and 'title' in x if x else False),
                ('span', lambda x: x and 'title' in x if x else False)
            ]

            for tag, class_filter in track_selectors:
                track_elem = element.find(tag, class_=class_filter)
                if track_elem:
                    track = track_elem.get_text(strip=True)
                    break

            remix = ''
            remix_elem = element.find('p', class_='buk-track-remixed')
            if not remix_elem:
                remix_elem = element.find('span', class_='buk-track-remixed')
            if not remix_elem:
                remix_elem = element.find('span', class_='remix')
            if remix_elem:
                remix = remix_elem.get_text(strip=True)

            label = ''
            label_elem = element.find('span', class_='track-labels')
            if not label_elem:
                label_elem = element.find('p', class_='buk-track-labels')
            if not label_elem:
                label_elem = element.find('a', class_='label')
            if label_elem:
                label = label_elem.get_text(strip=True)

            if artist and track:
                return {
                    'artist': artist,
                    'track': track,
                    'remix': remix,
                    'label': label
                }

            return None

        except Exception as e:
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
