"""
Audio downloader module using yt-dlp.
Handles searching and downloading audio from SoundCloud and YouTube.
Automatically selects the longer version when searching both sources.
"""

import os
import subprocess
import json
import re
from typing import Dict, Optional, Tuple


class AudioDownloader:
    """Downloads audio tracks using yt-dlp."""

    # Maximum duration in seconds (15 minutes) to filter out DJ sets
    MAX_DURATION = 900  # 15 minutes

    def __init__(self, output_dir: str = 'downloads', source: str = 'auto'):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files
            source: Download source ('soundcloud', 'youtube', or 'auto' to search both)
        """
        self.output_dir = output_dir
        self.source = source.lower()
        if self.source not in ['soundcloud', 'youtube', 'auto']:
            raise ValueError("Source must be 'soundcloud', 'youtube', or 'auto'")
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created directory: {self.output_dir}")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison by removing special characters and converting to lowercase.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def calculate_match_score(self, requested_query: str, found_title: str) -> float:
        """
        Calculate how well a found track matches the requested query.

        Args:
            requested_query: The search query (e.g., "Artist - Track Name Extended Mix")
            found_title: The title from SoundCloud/YouTube

        Returns:
            Match score between 0.0 and 1.0 (higher is better)
        """
        req_norm = self.normalize_text(requested_query)
        found_norm = self.normalize_text(found_title)

        req_words = set(req_norm.split())
        found_words = set(found_norm.split())

        if not req_words or not found_words:
            return 0.0

        common_words = req_words.intersection(found_words)
        score = len(common_words) / max(len(req_words), len(found_words))

        return score

    def is_valid_match(self, requested_query: str, found_title: str, threshold: float = 0.5) -> bool:
        """
        Check if a found track is a valid match for the requested query.

        Args:
            requested_query: The search query
            found_title: The title from SoundCloud/YouTube
            threshold: Minimum match score required (default 0.5 = 50%)

        Returns:
            True if the match is valid, False otherwise
        """
        score = self.calculate_match_score(requested_query, found_title)
        return score >= threshold

    def create_filename(self, track_info: Dict[str, str]) -> str:
        """
        Create output filename from track information.

        Args:
            track_info: Dictionary with 'artist' and 'track' keys

        Returns:
            Sanitized filename
        """
        filename = f"{track_info['artist']} - {track_info['track']}.mp3"
        return self.sanitize_filename(filename)

    def get_track_info(self, search_url: str) -> Optional[Dict]:
        """
        Get track information without downloading.

        Args:
            search_url: yt-dlp search URL (e.g., 'scsearch1:query' or 'ytsearch1:query')

        Returns:
            Dictionary with track info (title, duration, url) or None if failed
        """
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            search_url
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                info = json.loads(result.stdout)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'url': info.get('webpage_url', ''),
                    'source': 'soundcloud' if 'soundcloud' in search_url else 'youtube'
                }
            return None

        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return None

    def get_multiple_tracks(self, search_url: str, count: int = 5) -> list:
        """
        Get multiple track results from a search.

        Args:
            search_url: yt-dlp search URL (e.g., 'scsearch5:query' or 'ytsearch5:query')
            count: Number of results to fetch (default 5)

        Returns:
            List of dictionaries with track info
        """
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            search_url
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                tracks = []
                source = 'soundcloud' if 'soundcloud' in search_url else 'youtube'

                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            info = json.loads(line)
                            tracks.append({
                                'title': info.get('title', 'Unknown'),
                                'duration': info.get('duration', 0),
                                'url': info.get('webpage_url', ''),
                                'source': source
                            })
                        except json.JSONDecodeError:
                            continue

                return tracks
            return []

        except (subprocess.TimeoutExpired, Exception):
            return []

    def find_best_match(self, tracks: list, search_query: str, threshold: float = 0.5) -> Optional[Dict]:
        """
        Find the best matching track from a list based on relevance score.

        Args:
            tracks: List of track dictionaries
            search_query: Original search query
            threshold: Minimum match score required

        Returns:
            Best matching track or None if no good match found
        """
        if not tracks:
            return None

        best_track = None
        best_score = 0.0

        for track in tracks:
            if track['duration'] > self.MAX_DURATION:
                continue

            score = self.calculate_match_score(search_query, track['title'])

            if score >= threshold and score > best_score:
                best_score = score
                best_track = track

        if best_track:
            best_track['match_score'] = best_score

        return best_track

    def search_both_sources(self, search_query: str, validate_match: bool = True) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Search both SoundCloud and YouTube for a track.
        Gets top 5 results from each source and selects the most relevant match.

        Args:
            search_query: Search string for the track
            validate_match: Whether to validate that results match the query

        Returns:
            Tuple of (soundcloud_info, youtube_info), each can be None if not found
        """
        print(f"  Searching top 5 results from SoundCloud and YouTube...")

        sc_url = f"scsearch5:{search_query}"
        yt_url = f"ytsearch5:{search_query}"

        sc_tracks = self.get_multiple_tracks(sc_url, count=5)
        yt_tracks = self.get_multiple_tracks(yt_url, count=5)

        sc_info = None
        yt_info = None

        if validate_match:
            sc_info = self.find_best_match(sc_tracks, search_query, threshold=0.5)
            yt_info = self.find_best_match(yt_tracks, search_query, threshold=0.5)

            if not sc_info and sc_tracks:
                print(f"  ⚠ No SoundCloud results matched query well enough")

            if not yt_info and yt_tracks:
                print(f"  ⚠ No YouTube results matched query well enough")
        else:
            if sc_tracks:
                sc_info = sc_tracks[0]
                sc_info['match_score'] = 1.0
            if yt_tracks:
                yt_info = yt_tracks[0]
                yt_info['match_score'] = 1.0

        return sc_info, yt_info

    def select_best_source(self, sc_info: Optional[Dict], yt_info: Optional[Dict], search_query: str = "") -> Optional[Dict]:
        """
        Select the best source based on relevance and duration.
        First filters by relevance, then selects longer version.

        Args:
            sc_info: SoundCloud track info (already filtered for relevance)
            yt_info: YouTube track info (already filtered for relevance)
            search_query: Original search query for match scoring

        Returns:
            Selected track info or None if both failed
        """
        if not sc_info and not yt_info:
            print(f"  ✗ No valid tracks found")
            return None

        if not sc_info:
            match_score = yt_info.get('match_score', 1.0)
            print(f"  YouTube only: {yt_info['title']} ({self._format_duration(yt_info['duration'])}) [match: {match_score:.0%}]")
            return yt_info

        if not yt_info:
            match_score = sc_info.get('match_score', 1.0)
            print(f"  SoundCloud only: {sc_info['title']} ({self._format_duration(sc_info['duration'])}) [match: {match_score:.0%}]")
            return sc_info

        sc_duration = sc_info['duration']
        yt_duration = yt_info['duration']

        sc_match = sc_info.get('match_score', 1.0)
        yt_match = yt_info.get('match_score', 1.0)

        print(f"  SoundCloud: {sc_info['title']} ({self._format_duration(sc_duration)}) [match: {sc_match:.0%}]")
        print(f"  YouTube: {yt_info['title']} ({self._format_duration(yt_duration)}) [match: {yt_match:.0%}]")

        if sc_duration >= yt_duration:
            print(f"  ✓ Selected SoundCloud (longer version)")
            return sc_info
        else:
            print(f"  ✓ Selected YouTube (longer version)")
            return yt_info

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to MM:SS format."""
        if seconds <= 0:
            return "Unknown"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def check_existing_file(self, track_title: str) -> Optional[str]:
        """
        Check if a track already exists in the output directory.

        Args:
            track_title: The track title to search for

        Returns:
            Filename if exists, None otherwise
        """
        if not os.path.exists(self.output_dir):
            return None

        normalized_search = self.normalize_text(track_title)

        for filename in os.listdir(self.output_dir):
            if filename.endswith('.mp3'):
                normalized_filename = self.normalize_text(filename.replace('.mp3', ''))
                if self.calculate_match_score(normalized_search, normalized_filename) >= 0.8:
                    return filename

        return None

    def download_track(self, search_query: str, requested_track_info: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str], bool]:
        """
        Download a track from SoundCloud, YouTube, or automatically select the longer version.

        Args:
            search_query: Search string for the track
            requested_track_info: Original track info from JSON (for reference only)

        Returns:
            Tuple of (success: bool, actual_filename: str or None, was_already_downloaded: bool)
        """
        selected = None

        # Determine which source(s) to search
        if self.source == 'auto':
            # Search both sources and select the longer one
            sc_info, yt_info = self.search_both_sources(search_query)
            selected = self.select_best_source(sc_info, yt_info, search_query)

            if not selected:
                print(f"  ✗ Not found on either SoundCloud or YouTube")
                return False, None, False

        else:
            # Single source search - check duration before downloading
            if self.source == 'soundcloud':
                search_url = f"scsearch1:{search_query}"
                print(f"  Searching SoundCloud: {search_query}")
            else:  # youtube
                search_url = f"ytsearch1:{search_query}"
                print(f"  Searching YouTube: {search_query}")

            # Get track info to check duration
            track_info = self.get_track_info(search_url)
            if not track_info:
                print(f"  ✗ Track not found")
                return False, None, False

            # Validate match
            if not self.is_valid_match(search_query, track_info['title']):
                print(f"  ⚠ Result doesn't match query: {track_info['title']}")
                return False, None, False

            if track_info['duration'] > self.MAX_DURATION:
                print(f"  ✗ Track too long: {self._format_duration(track_info['duration'])} (max {self.MAX_DURATION // 60} minutes)")
                return False, None, False

            match_score = self.calculate_match_score(search_query, track_info['title'])
            print(f"  Found: {track_info['title']} ({self._format_duration(track_info['duration'])}) [match: {match_score:.0%}]")
            selected = track_info

        # Create filename from actual track metadata
        actual_filename = self.sanitize_filename(selected['title']) + '.mp3'

        # Check if track already exists
        existing_file = self.check_existing_file(selected['title'])
        if existing_file:
            print(f"  ✓ Already exists: {existing_file}")
            return True, existing_file, True

        output_path = os.path.join(self.output_dir, actual_filename)
        download_url = selected['url']

        # Output template without extension (yt-dlp will add .mp3)
        output_template = os.path.join(
            self.output_dir,
            actual_filename.replace('.mp3', '')
        )

        command = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--output', output_template + '.%(ext)s',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            download_url
        ]

        try:
            print(f"  Downloading: {actual_filename}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                if os.path.exists(output_path):
                    print(f"  ✓ Downloaded: {actual_filename}")
                    return True, actual_filename, False
                else:
                    print(f"  ✗ File not found after download")
                    return False, None, False
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"  ✗ Download failed: {error_msg}")
                return False, None, False

        except subprocess.TimeoutExpired:
            print(f"  ✗ Download timeout")
            return False, None, False
        except FileNotFoundError:
            print("  ✗ Error: yt-dlp not found. Please install it:")
            print("     pip install yt-dlp")
            return False, None, False
        except Exception as e:
            print(f"  ✗ Download error: {e}")
            return False, None, False

    def get_existing_files(self) -> set:
        """
        Get set of existing filenames in download directory.

        Returns:
            Set of filenames
        """
        if not os.path.exists(self.output_dir):
            return set()
        return set(os.listdir(self.output_dir))
