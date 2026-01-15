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

            try:
                print("Waiting for track list to load...")
                wait = WebDriverWait(self.driver, 15)

                selectors_to_try = [
                    'div.bucket-item',
                    'li.bucket-item',
                    'div.track',
                    'div[class*="track"]',
                    'tr.track-row',
                    'div.playqueue-track',
                    'li[class*="track"]'
                ]

                for selector in selectors_to_try:
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"Track list loaded using selector: {selector}")
                        break
                    except:
                        continue

            except Exception as e:
                print(f"Warning: Timeout waiting for tracks with all selectors")
                print("The page might require authentication or use different selectors.")

            print("Waiting additional time for dynamic content...")
            time.sleep(3)

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
        soup = BeautifulSoup(html, 'lxml')
        tracks = []

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
