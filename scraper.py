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

    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from Beatport URL using Selenium.

        Args:
            url: Beatport playlist URL

        Returns:
            HTML content as string, or None if request fails
        """
        try:
            print(f"Fetching URL with Selenium: {url}")
            self._setup_driver()

            self.driver.get(url)

            try:
                print("Waiting for track list to load...")
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.bucket-item, li.bucket-item, div.track')))
                print("Track list loaded!")
            except Exception as e:
                print(f"Warning: Timeout waiting for tracks, proceeding anyway: {e}")
                time.sleep(5)

            time.sleep(2)

            html = self.driver.page_source
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

        track_elements = soup.find_all('div', class_=lambda x: x and 'bucket-item' in x and 'track' in x)

        if not track_elements:
            track_elements = soup.find_all('li', class_='bucket-item')

        if not track_elements:
            track_elements = soup.find_all('div', class_='track')

        if not track_elements:
            track_elements = soup.find_all('tr', class_='track-row')

        print(f"Found {len(track_elements)} track elements")

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
            artist_elem = element.find('span', class_='track-artists')
            if not artist_elem:
                artist_elem = element.find('p', class_='buk-track-artists')
            if not artist_elem:
                artist_elem = element.find('a', class_='artist')
            if not artist_elem:
                artist_elem = element.find('span', class_='artist')
            if artist_elem:
                artist = artist_elem.get_text(strip=True)

            track = ''
            track_elem = element.find('span', class_='track-title')
            if not track_elem:
                track_elem = element.find('p', class_='buk-track-primary-title')
            if not track_elem:
                track_elem = element.find('a', class_='track-title')
            if not track_elem:
                track_elem = element.find('a', class_='buk-track-title')
            if track_elem:
                track = track_elem.get_text(strip=True)

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
