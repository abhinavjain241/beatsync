"""
MP3 Metadata Writer Module

Handles writing ID3 tags and embedding album art into MP3 files.
Optimized for Rekordbox compatibility.
Supports both local file paths and URLs for album art.
"""

import os
import re
import ssl
from typing import Dict, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TPE2, TALB, TCON, TBPM, TKEY, TYER, COMM, APIC, error


class MetadataWriter:
    """Writes metadata to MP3 files."""

    def __init__(self):
        """Initialize metadata writer."""
        pass

    def _is_url(self, path: str) -> bool:
        """
        Check if a path is a URL.

        Args:
            path: Path or URL string

        Returns:
            True if the path is a URL, False otherwise
        """
        return path.startswith('http://') or path.startswith('https://')

    def _download_image_from_url(self, url: str) -> Optional[bytes]:
        """
        Download image data from a URL.

        Args:
            url: URL of the image

        Returns:
            Image data as bytes, or None if download fails
        """
        try:
            # Create request with a user agent to avoid blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            request = Request(url, headers=headers)

            # Create SSL context that doesn't verify certificates (for album art downloads only)
            # This fixes SSL certificate verification errors with some image hosting services
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urlopen(request, timeout=30, context=ssl_context) as response:
                if response.status == 200:
                    image_data = response.read()
                    return image_data
                else:
                    print(f"  ⚠ Album art download failed: HTTP {response.status}")
                    return None
        except HTTPError as e:
            print(f"  ⚠ Album art HTTP error: {e.code} - {e.reason}")
            return None
        except URLError as e:
            print(f"  ⚠ Album art URL error: {e.reason}")
            return None
        except Exception as e:
            print(f"  ⚠ Album art download error: {e}")
            return None

    def _get_mime_type_from_data(self, image_data: bytes) -> str:
        """
        Detect MIME type from image data by checking file signature.

        Args:
            image_data: Image data bytes

        Returns:
            MIME type string
        """
        # Check for JPEG signature
        if image_data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        # Check for PNG signature
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        # Check for WebP signature
        elif image_data[8:12] == b'WEBP':
            return 'image/webp'
        # Default to JPEG
        else:
            return 'image/jpeg'

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
        Write metadata to an MP3 file with full Rekordbox compatibility.

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
        print(f"  [Metadata] Starting metadata write for: {os.path.basename(mp3_file_path)}")

        if not os.path.exists(mp3_file_path):
            print(f"  ⚠ [Metadata] MP3 file not found: {mp3_file_path}")
            return False

        # Log what metadata we're trying to write
        print(f"  [Metadata] Writing - Artist: {metadata.get('artist_name', 'N/A')}")
        print(f"  [Metadata] Writing - Title: {metadata.get('song_name', 'N/A')}")
        print(f"  [Metadata] Writing - Album: {metadata.get('label_name', 'N/A')}")
        print(f"  [Metadata] Writing - Genre: {metadata.get('genre', 'N/A')}")
        print(f"  [Metadata] Writing - BPM/Key: {metadata.get('bpm_key', 'N/A')}")
        print(f"  [Metadata] Writing - Album Art: {'Yes' if metadata.get('album_art') else 'No'}")

        try:
            # Load the MP3 file
            print(f"  [Metadata] Loading MP3 file...")
            audio = MP3(mp3_file_path, ID3=ID3)

            # Try to add tags if they don't exist
            try:
                audio.add_tags()
                print(f"  [Metadata] Created new ID3 tags")
            except error:
                print(f"  [Metadata] ID3 tags already exist")
                pass

            # Ensure tags exist
            if audio.tags is None:
                print(f"  ⚠ [Metadata] Could not create ID3 tags")
                return False

            print(f"  [Metadata] Clearing existing tags...")
            # Clear all existing tags for clean state
            audio.tags.clear()

            print(f"  [Metadata] Adding ID3 tags...")

            # Title (TIT2) - Required by Rekordbox
            if metadata.get('song_name'):
                audio.tags.add(TIT2(encoding=3, text=metadata['song_name']))
                print(f"  [Metadata] ✓ Added title")

            # Artist (TPE1) - Required by Rekordbox
            if metadata.get('artist_name'):
                audio.tags.add(TPE1(encoding=3, text=metadata['artist_name']))
                # Also set album artist (TPE2) for better compatibility
                audio.tags.add(TPE2(encoding=3, text=metadata['artist_name']))
                print(f"  [Metadata] ✓ Added artist")

            # Album (TALB) - Use label name
            if metadata.get('label_name'):
                audio.tags.add(TALB(encoding=3, text=metadata['label_name']))
                print(f"  [Metadata] ✓ Added album (label)")

            # Genre (TCON) - Important for Rekordbox organization
            if metadata.get('genre'):
                audio.tags.add(TCON(encoding=3, text=metadata['genre']))
                print(f"  [Metadata] ✓ Added genre")

            # Parse and write BPM and key
            if metadata.get('bpm_key'):
                bpm, key = self.parse_bpm_key(metadata['bpm_key'])

                # BPM (TBPM) - Critical for Rekordbox DJ features
                if bpm:
                    audio.tags.add(TBPM(encoding=3, text=bpm))
                    print(f"  [Metadata] ✓ Added BPM: {bpm}")

                # Key (TKEY) - Critical for harmonic mixing in Rekordbox
                if key:
                    audio.tags.add(TKEY(encoding=3, text=key))
                    print(f"  [Metadata] ✓ Added key: {key}")

            # Add current year if not present
            from datetime import datetime
            current_year = str(datetime.now().year)
            audio.tags.add(TYER(encoding=3, text=current_year))
            print(f"  [Metadata] ✓ Added year")

            # Add comment with source info for tracking
            comment_text = f"Downloaded from Beatport - {metadata.get('label_name', 'Unknown Label')}"
            audio.tags.add(COMM(encoding=3, lang='eng', desc='', text=comment_text))
            print(f"  [Metadata] ✓ Added comment")

            # Embed album art - CRITICAL for Rekordbox
            if metadata.get('album_art'):
                print(f"  [Metadata] Processing album art...")
                album_art_source = metadata['album_art']
                image_data = None
                mime_type = None

                # Check if album art is a URL or local file
                if self._is_url(album_art_source):
                    # Download image from URL
                    print(f"  [Metadata] Album art is URL: {album_art_source[:50]}...")
                    print(f"  [Metadata] Downloading album art from URL...")
                    image_data = self._download_image_from_url(album_art_source)
                    if image_data:
                        # Detect MIME type from image data
                        mime_type = self._get_mime_type_from_data(image_data)
                        print(f"  [Metadata] ✓ Downloaded album art ({len(image_data)} bytes, {mime_type})")
                    else:
                        print(f"  ⚠ [Metadata] Failed to download album art from URL")
                else:
                    # Load image from local file
                    print(f"  [Metadata] Album art is local file: {album_art_source}")
                    if os.path.exists(album_art_source):
                        try:
                            with open(album_art_source, 'rb') as img_file:
                                image_data = img_file.read()

                            # Determine MIME type from file extension
                            ext = os.path.splitext(album_art_source)[1].lower()
                            mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                            print(f"  [Metadata] ✓ Loaded album art from: {os.path.basename(album_art_source)} ({len(image_data)} bytes, {mime_type})")
                        except Exception as e:
                            print(f"  ⚠ [Metadata] Album art file error: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"  ⚠ [Metadata] Album art not found at: {album_art_source}")

                # Embed the album art if we have the data
                if image_data and mime_type:
                    print(f"  [Metadata] Embedding album art into MP3...")
                    try:
                        # Add album art with Rekordbox-compatible settings
                        # encoding=0 for binary data (not text)
                        # type=3 is front cover (standard for album art)
                        audio.tags.add(APIC(
                            encoding=0,
                            mime=mime_type,
                            type=3,
                            desc='Cover',
                            data=image_data
                        ))
                        print(f"  [Metadata] ✓ Album art embedded successfully")
                    except Exception as e:
                        print(f"  ⚠ [Metadata] Album art embedding error: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"  ⚠ [Metadata] No album art data to embed")
            else:
                print(f"  [Metadata] No album art specified in metadata")

            # Save with ID3v2.3 for maximum Rekordbox compatibility
            # v2.3 is better supported by Rekordbox than v2.4
            print(f"  [Metadata] Saving ID3 tags to file...")
            audio.save(v2_version=3)
            print(f"  [Metadata] ✓ Successfully saved all metadata to MP3")

            # Verify tags were written
            print(f"  [Metadata] Verifying tags were written...")
            verify_audio = MP3(mp3_file_path, ID3=ID3)
            if verify_audio.tags:
                tag_count = len(verify_audio.tags.keys())
                print(f"  [Metadata] ✓ Verified: {tag_count} tags found in file")
                return True
            else:
                print(f"  ⚠ [Metadata] Verification failed: No tags found in file")
                return False

        except Exception as e:
            print(f"  ⚠ [Metadata] CRITICAL ERROR during metadata write: {e}")
            import traceback
            print(f"  [Metadata] Full traceback:")
            traceback.print_exc()
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
        print(f"\n{'='*70}")
        print(f"  APPLYING METADATA TO: {os.path.basename(mp3_file_path)}")
        print(f"{'='*70}")

        success = self.write_metadata(mp3_file_path, track_metadata)

        print(f"{'='*70}")
        if success:
            metadata_summary = []
            if track_metadata.get('bpm_key'):
                metadata_summary.append(f"{track_metadata['bpm_key']}")
            if track_metadata.get('genre'):
                metadata_summary.append(f"Genre: {track_metadata['genre']}")
            if track_metadata.get('label_name'):
                metadata_summary.append(f"Label: {track_metadata['label_name']}")

            summary_str = " | ".join(metadata_summary) if metadata_summary else "Complete metadata"
            print(f"  ✓✓✓ METADATA WRITE SUCCESSFUL: {summary_str}")
        else:
            print(f"  ✗✗✗ METADATA WRITE FAILED")

        print(f"{'='*70}\n")
        return success
