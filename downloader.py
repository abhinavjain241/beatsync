"""
Audio downloader module using yt-dlp.
Handles searching and downloading audio from SoundCloud.
"""

import os
import subprocess
from typing import Dict, Optional


class AudioDownloader:
    """Downloads audio tracks using yt-dlp."""

    def __init__(self, output_dir: str = 'downloads'):
        self.output_dir = output_dir
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

    def download_track(self, search_query: str, output_filename: str) -> bool:
        """
        Download a track from SoundCloud using yt-dlp.

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

        # Construct yt-dlp command
        # Use scsearch1: to search SoundCloud and get top result
        search_url = f"scsearch1:{search_query}"

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
            search_url
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
