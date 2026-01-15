"""
Audio downloader module using yt-dlp.
Handles searching and downloading audio from SoundCloud and YouTube.
Automatically selects the longer version when searching both sources.
"""

import os
import subprocess
import json
from typing import Dict, Optional, Tuple


class AudioDownloader:
    """Downloads audio tracks using yt-dlp."""

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
        return filename

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

    def search_both_sources(self, search_query: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Search both SoundCloud and YouTube for a track.

        Args:
            search_query: Search string for the track

        Returns:
            Tuple of (soundcloud_info, youtube_info), each can be None if not found
        """
        print(f"  Searching both SoundCloud and YouTube...")

        sc_url = f"scsearch1:{search_query}"
        yt_url = f"ytsearch1:{search_query}"

        sc_info = self.get_track_info(sc_url)
        yt_info = self.get_track_info(yt_url)

        return sc_info, yt_info

    def select_best_source(self, sc_info: Optional[Dict], yt_info: Optional[Dict]) -> Optional[Dict]:
        """
        Select the best source based on duration (longer is better).

        Args:
            sc_info: SoundCloud track info
            yt_info: YouTube track info

        Returns:
            Selected track info or None if both failed
        """
        if not sc_info and not yt_info:
            return None

        if not sc_info:
            print(f"  YouTube only: {yt_info['title']} ({self._format_duration(yt_info['duration'])})")
            return yt_info

        if not yt_info:
            print(f"  SoundCloud only: {sc_info['title']} ({self._format_duration(sc_info['duration'])})")
            return sc_info

        sc_duration = sc_info['duration']
        yt_duration = yt_info['duration']

        print(f"  SoundCloud: {sc_info['title']} ({self._format_duration(sc_duration)})")
        print(f"  YouTube: {yt_info['title']} ({self._format_duration(yt_duration)})")

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

    def download_track(self, search_query: str, output_filename: str) -> bool:
        """
        Download a track from SoundCloud, YouTube, or automatically select the longer version.

        Args:
            search_query: Search string for the track
            output_filename: Output filename for the downloaded track

        Returns:
            True if download successful, False otherwise
        """
        output_path = os.path.join(self.output_dir, output_filename)

        # Skip if file already exists
        if os.path.exists(output_path):
            print(f"  ✓ Already exists: {output_filename}")
            return True

        # Determine which source(s) to search
        if self.source == 'auto':
            # Search both sources and select the longer one
            sc_info, yt_info = self.search_both_sources(search_query)
            selected = self.select_best_source(sc_info, yt_info)

            if not selected:
                print(f"  ✗ Not found on either SoundCloud or YouTube")
                return False

            # Use the URL directly instead of search
            download_url = selected['url']
        else:
            # Single source search
            if self.source == 'soundcloud':
                download_url = f"scsearch1:{search_query}"
                print(f"  Searching SoundCloud: {search_query}")
            else:  # youtube
                download_url = f"ytsearch1:{search_query}"
                print(f"  Searching YouTube: {search_query}")

        # Output template without extension (yt-dlp will add .mp3)
        output_template = os.path.join(
            self.output_dir,
            output_filename.replace('.mp3', '')
        )

        command = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '--output', output_template + '.%(ext)s',
            '--no-playlist',
            '--quiet',
            '--no-warnings',
            download_url
        ]

        try:
            print(f"  Downloading: {output_filename}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                # Check if file was created
                if os.path.exists(output_path):
                    print(f"  ✓ Downloaded: {output_filename}")
                    return True
                else:
                    print(f"  ✗ File not found after download: {output_filename}")
                    return False
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"  ✗ Download failed: {error_msg}")
                return False

        except subprocess.TimeoutExpired:
            print(f"  ✗ Download timeout: {output_filename}")
            return False
        except FileNotFoundError:
            print("  ✗ Error: yt-dlp not found. Please install it:")
            print("     pip install yt-dlp")
            return False
        except Exception as e:
            print(f"  ✗ Download error: {e}")
            return False

    def get_existing_files(self) -> set:
        """
        Get set of existing filenames in download directory.

        Returns:
            Set of filenames
        """
        if not os.path.exists(self.output_dir):
            return set()
        return set(os.listdir(self.output_dir))
