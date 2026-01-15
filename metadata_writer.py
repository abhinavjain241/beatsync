"""
MP3 Metadata Writer Module

Handles writing ID3 tags and embedding album art into MP3 files.
"""

import os
import re
from typing import Dict, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TBPM, TKEY, APIC, error


class MetadataWriter:
    """Writes metadata to MP3 files."""

    def __init__(self):
        """Initialize metadata writer."""
        pass

    def parse_bpm_key(self, bpm_key_str: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse BPM and key from the bpm_key field.

        Args:
            bpm_key_str: String like "128 BPM - G Minor"

        Returns:
            Tuple of (bpm, key) where each can be None if not found
        """
        bpm = None
        key = None

        if not bpm_key_str:
            return bpm, key

        # Extract BPM (e.g., "128 BPM")
        bpm_match = re.search(r'(\d+)\s*BPM', bpm_key_str, re.IGNORECASE)
        if bpm_match:
            bpm = bpm_match.group(1)

        # Extract key (e.g., "G Minor", "F Major", "Ab Minor")
        key_match = re.search(r'-\s*([A-G][b#]?\s*(?:Major|Minor))', bpm_key_str, re.IGNORECASE)
        if key_match:
            key = key_match.group(1).strip()

        return bpm, key

    def write_metadata(self, mp3_file_path: str, metadata: Dict[str, str]) -> bool:
        """
        Write metadata to an MP3 file.

        Args:
            mp3_file_path: Path to the MP3 file
            metadata: Dictionary containing metadata fields:
                - song_name: Track title
                - artist_name: Artist name
                - label_name: Record label (used as album)
                - genre: Music genre
                - bpm_key: BPM and key info
                - album_art: Path to album art image

        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(mp3_file_path):
            print(f"  ⚠ Metadata: MP3 file not found: {mp3_file_path}")
            return False

        try:
            # Load or create ID3 tags
            try:
                audio = MP3(mp3_file_path, ID3=ID3)
                audio.add_tags()
            except error:
                # Tags already exist
                audio = MP3(mp3_file_path, ID3=ID3)

            # Write title
            if metadata.get('song_name'):
                audio.tags.add(TIT2(encoding=3, text=metadata['song_name']))

            # Write artist
            if metadata.get('artist_name'):
                audio.tags.add(TPE1(encoding=3, text=metadata['artist_name']))

            # Write album (using label name)
            if metadata.get('label_name'):
                audio.tags.add(TALB(encoding=3, text=metadata['label_name']))

            # Write genre
            if metadata.get('genre'):
                audio.tags.add(TCON(encoding=3, text=metadata['genre']))

            # Parse and write BPM and key
            if metadata.get('bpm_key'):
                bpm, key = self.parse_bpm_key(metadata['bpm_key'])

                if bpm:
                    audio.tags.add(TBPM(encoding=3, text=bpm))

                if key:
                    audio.tags.add(TKEY(encoding=3, text=key))

            # Embed album art
            if metadata.get('album_art'):
                album_art_path = metadata['album_art']

                # Handle relative paths
                if not os.path.isabs(album_art_path):
                    # Get the directory of the JSON file (or current directory)
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    album_art_path = os.path.join(base_dir, album_art_path)

                if os.path.exists(album_art_path):
                    with open(album_art_path, 'rb') as img_file:
                        image_data = img_file.read()

                    # Determine MIME type from file extension
                    ext = os.path.splitext(album_art_path)[1].lower()
                    mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'

                    # Add album art (type 3 = front cover)
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime=mime_type,
                            type=3,
                            desc='Cover',
                            data=image_data
                        )
                    )

            # Save tags
            audio.save()
            return True

        except Exception as e:
            print(f"  ⚠ Metadata write error: {e}")
            return False

    def apply_metadata_to_track(self, mp3_file_path: str, track_metadata: Dict[str, str]) -> bool:
        """
        Apply metadata to a downloaded track.

        Args:
            mp3_file_path: Path to the MP3 file
            track_metadata: Metadata from JSON file

        Returns:
            True if successful, False otherwise
        """
        success = self.write_metadata(mp3_file_path, track_metadata)

        if success:
            metadata_summary = []
            if track_metadata.get('artist_name'):
                metadata_summary.append(f"Artist: {track_metadata['artist_name']}")
            if track_metadata.get('label_name'):
                metadata_summary.append(f"Label: {track_metadata['label_name']}")
            if track_metadata.get('bpm_key'):
                metadata_summary.append(f"{track_metadata['bpm_key']}")

            summary_str = " | ".join(metadata_summary) if metadata_summary else "metadata"
            print(f"  ✓ Added {summary_str}")

        return success
