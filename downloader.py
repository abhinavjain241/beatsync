"""
Audio downloader module using yt-dlp.
Handles searching and downloading audio from SoundCloud and YouTube.
Fetches top 5 results from each source, selects the most relevant track from each,
then compares relevance scores. If scores are within 10%, chooses the longer track.
"""

import os
import subprocess
import json
import re
from typing import Dict, Optional, Tuple, List


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

    def extract_track_components(self, text: str) -> Dict[str, any]:
        """
        Extract track components (artists, track name, mix type) from a track title.

        Args:
            text: Track title or search query

        Returns:
            Dictionary with extracted components
        """
        text_lower = text.lower()

        # Common mix/remix patterns in electronic music
        mix_patterns = [
            r'\b(extended|original|radio|club|dub|instrumental|acapella|vip|bootleg)\s+(mix|edit|version|remix)\b',
            r'\b(remix|edit|rework|flip|refix|reboot|version)\b',
            r'\b[a-z]+\s+remix\b',  # e.g., "Someone Remix"
        ]

        mix_info = []
        clean_text = text

        # Extract mix information
        for pattern in mix_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                mix_info.append(match.group(0))
                # Remove from text for cleaner artist/title extraction
                clean_text = clean_text[:match.start()] + clean_text[match.end():]

        # Normalize the cleaned text
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Split by common separators
        parts = re.split(r'\s*[-–—/]\s*', clean_text)

        # Extract artists and track name
        artists = []
        track_name = ""

        if len(parts) >= 2:
            # First part is usually artist(s)
            artist_part = parts[0]
            # Split multiple artists by comma, &, 'and', 'feat', 'ft', 'vs', 'x'
            artist_separators = r'[,&]|\band\b|\bfeat\.?\b|\bft\.?\b|\bvs\.?\b|\bx\b'
            artists = [a.strip() for a in re.split(artist_separators, artist_part) if a.strip()]

            # Rest is track name
            track_name = ' '.join(parts[1:])
        else:
            track_name = clean_text

        return {
            'artists': artists,
            'track_name': track_name,
            'mix_info': mix_info,
            'normalized_artists': [self.normalize_text(a) for a in artists],
            'normalized_track': self.normalize_text(track_name),
            'normalized_mix': [self.normalize_text(m) for m in mix_info]
        }

    def calculate_match_score(self, requested_query: str, found_title: str) -> float:
        """
        Calculate how well a found track matches the requested query using a more nuanced algorithm.
        Takes into account artists, track name, and mix information separately.

        Args:
            requested_query: The search query (e.g., "Artist - Track Name Extended Mix")
            found_title: The title from SoundCloud/YouTube

        Returns:
            Match score between 0.0 and 1.0 (higher is better)
        """
        req_components = self.extract_track_components(requested_query)
        found_components = self.extract_track_components(found_title)

        # Calculate scores for different components
        scores = []
        weights = []

        # Artist matching (weight: 40%)
        if req_components['normalized_artists'] and found_components['normalized_artists']:
            req_artists = set(' '.join(req_components['normalized_artists']).split())
            found_artists = set(' '.join(found_components['normalized_artists']).split())

            if req_artists and found_artists:
                artist_score = len(req_artists.intersection(found_artists)) / max(len(req_artists), len(found_artists))
                scores.append(artist_score)
                weights.append(0.4)

        # Track name matching (weight: 45%)
        if req_components['normalized_track'] and found_components['normalized_track']:
            req_track_words = set(req_components['normalized_track'].split())
            found_track_words = set(found_components['normalized_track'].split())

            if req_track_words and found_track_words:
                track_score = len(req_track_words.intersection(found_track_words)) / max(len(req_track_words), len(found_track_words))
                scores.append(track_score)
                weights.append(0.45)

        # Mix info matching (weight: 15%) - less important but still relevant
        if req_components['normalized_mix'] or found_components['normalized_mix']:
            req_mix_words = set(' '.join(req_components['normalized_mix']).split())
            found_mix_words = set(' '.join(found_components['normalized_mix']).split())

            if req_mix_words and found_mix_words:
                mix_score = len(req_mix_words.intersection(found_mix_words)) / max(len(req_mix_words), len(found_mix_words))
                scores.append(mix_score)
                weights.append(0.15)
            elif not req_mix_words and not found_mix_words:
                # Both have no mix info - that's a match
                scores.append(1.0)
                weights.append(0.15)
            else:
                # One has mix info, the other doesn't - partial penalty
                scores.append(0.5)
                weights.append(0.15)

        # Calculate weighted average
        if scores and weights:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            return weighted_score

        # Fallback to simple word matching
        req_norm = self.normalize_text(requested_query)
        found_norm = self.normalize_text(found_title)
        req_words = set(req_norm.split())
        found_words = set(found_norm.split())

        if not req_words or not found_words:
            return 0.0

        return len(req_words.intersection(found_words)) / max(len(req_words), len(found_words))

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

    def get_multiple_track_info(self, search_url: str, count: int = 5) -> List[Dict]:
        """
        Get multiple track information without downloading.

        Args:
            search_url: yt-dlp search URL (e.g., 'scsearch5:query' or 'ytsearch5:query')
            count: Number of results to fetch

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
                timeout=60
            )

            if result.returncode == 0 and result.stdout:
                tracks = []
                # Parse each JSON line
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            info = json.loads(line)
                            tracks.append({
                                'title': info.get('title', 'Unknown'),
                                'duration': info.get('duration', 0),
                                'url': info.get('webpage_url', ''),
                                'source': 'soundcloud' if 'soundcloud' in search_url else 'youtube'
                            })
                        except json.JSONDecodeError:
                            continue
                return tracks
            return []

        except (subprocess.TimeoutExpired, Exception):
            return []

    def search_both_sources(self, search_query: str, validate_match: bool = True) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Search both SoundCloud and YouTube for a track.
        Fetches top 5 results from each and selects the most relevant.

        Args:
            search_query: Search string for the track
            validate_match: Whether to validate that results match the query

        Returns:
            Tuple of (soundcloud_info, youtube_info), each can be None if not found
        """
        print(f"  Searching both SoundCloud and YouTube (top 5 results each)...")

        sc_url = f"scsearch5:{search_query}"
        yt_url = f"ytsearch5:{search_query}"

        sc_tracks = self.get_multiple_track_info(sc_url, count=5)
        yt_tracks = self.get_multiple_track_info(yt_url, count=5)

        sc_info = None
        yt_info = None

        if sc_tracks:
            sc_info = self._select_best_track_from_list(sc_tracks, search_query, validate_match)
            if sc_info:
                print(f"  SoundCloud best: {sc_info['title']} ({self._format_duration(sc_info['duration'])}) [match: {sc_info.get('match_score', 0):.0%}]")

        if yt_tracks:
            yt_info = self._select_best_track_from_list(yt_tracks, search_query, validate_match)
            if yt_info:
                print(f"  YouTube best: {yt_info['title']} ({self._format_duration(yt_info['duration'])}) [match: {yt_info.get('match_score', 0):.0%}]")

        return sc_info, yt_info

    def _select_best_track_from_list(self, tracks: List[Dict], search_query: str, validate_match: bool = True) -> Optional[Dict]:
        """
        Select the most relevant track from a list based on match score.
        Filters out tracks longer than MAX_DURATION.

        Args:
            tracks: List of track dictionaries
            search_query: Original search query
            validate_match: Whether to validate minimum match threshold

        Returns:
            Best matching track or None
        """
        best_track = None
        best_score = 0.0

        for track in tracks:
            if track['duration'] > self.MAX_DURATION:
                continue

            match_score = self.calculate_match_score(search_query, track['title'])

            if validate_match and match_score < 0.5:
                continue

            if match_score > best_score:
                best_score = match_score
                best_track = track
                best_track['match_score'] = match_score

        return best_track

    def select_best_source(self, sc_info: Optional[Dict], yt_info: Optional[Dict], search_query: str = "") -> Optional[Dict]:
        """
        Select the best source by comparing relevance scores.
        If relevance scores are close (5-10% difference), choose the longer track.
        Otherwise, choose the track with higher relevance score.

        Args:
            sc_info: SoundCloud track info (already filtered and scored)
            yt_info: YouTube track info (already filtered and scored)
            search_query: Original search query for match scoring

        Returns:
            Selected track info or None if both failed
        """
        if not sc_info and not yt_info:
            print(f"  ✗ No valid tracks found")
            return None

        if not sc_info:
            print(f"  ✓ Selected YouTube (only available option)")
            return yt_info

        if not yt_info:
            print(f"  ✓ Selected SoundCloud (only available option)")
            return sc_info

        sc_match = sc_info.get('match_score', 0.0)
        yt_match = yt_info.get('match_score', 0.0)
        sc_duration = sc_info['duration']
        yt_duration = yt_info['duration']

        score_difference = abs(sc_match - yt_match)

        if score_difference <= 0.10:
            if sc_duration >= yt_duration:
                print(f"  ✓ Selected SoundCloud (similar relevance {sc_match:.0%} vs {yt_match:.0%}, longer: {self._format_duration(sc_duration)} vs {self._format_duration(yt_duration)})")
                return sc_info
            else:
                print(f"  ✓ Selected YouTube (similar relevance {sc_match:.0%} vs {yt_match:.0%}, longer: {self._format_duration(yt_duration)} vs {self._format_duration(sc_duration)})")
                return yt_info

        if sc_match > yt_match:
            print(f"  ✓ Selected SoundCloud (better match: {sc_match:.0%} vs {yt_match:.0%})")
            return sc_info
        else:
            print(f"  ✓ Selected YouTube (better match: {yt_match:.0%} vs {sc_match:.0%})")
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

    def get_playlist_tracks(self, playlist_url: str) -> List[Dict]:
        """
        Get all tracks from a SoundCloud playlist URL with full metadata.

        Args:
            playlist_url: SoundCloud playlist/likes URL

        Returns:
            List of track dicts: {'title': str, 'artist': str, 'url': str, 'duration': int}
        """
        # Use --dump-json without --flat-playlist to get full metadata
        command = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            playlist_url
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # Longer timeout since we're fetching full metadata
            )

            if result.returncode != 0:
                print(f"  ✗ yt-dlp error: {result.stderr.strip()}")
                return []

            tracks = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        info = json.loads(line)
                        url = info.get('webpage_url') or info.get('url', '')
                        tracks.append({
                            'title': info.get('title', 'Unknown'),
                            'artist': info.get('uploader') or info.get('artist') or info.get('channel') or 'Unknown Artist',
                            'url': url,
                            'duration': info.get('duration', 0)
                        })
                    except json.JSONDecodeError:
                        continue
            return tracks

        except Exception as e:
            print(f"  ✗ Error fetching playlist: {e}")
            return []

    def sync_soundcloud_playlist(self, playlist_url: str) -> Dict[str, int]:
        """
        Download new tracks from a SoundCloud playlist, skip existing ones.

        Args:
            playlist_url: SoundCloud playlist URL

        Returns:
            Stats dict: {'total': int, 'downloaded': int, 'skipped': int, 'failed': int}
        """
        stats = {'total': 0, 'downloaded': 0, 'skipped': 0, 'failed': 0}

        print(f"Fetching playlist from SoundCloud...")
        tracks = self.get_playlist_tracks(playlist_url)

        if not tracks:
            print("  ✗ Could not fetch playlist or playlist is empty")
            return stats

        stats['total'] = len(tracks)
        print(f"  Found {len(tracks)} tracks in playlist")
        print()

        for i, track in enumerate(tracks, 1):
            title = track['title']
            artist = track.get('artist', 'Unknown Artist')
            url = track['url']

            print(f"[{i}/{len(tracks)}] {title} - {artist}")

            # Check for valid URL
            if not url or not url.startswith('http'):
                print(f"  ✗ Invalid URL: {url}")
                stats['failed'] += 1
                continue

            # Check if already exists (check both title and full name)
            existing = self.check_existing_file(title) or self.check_existing_file(f"{title} - {artist}")
            if existing:
                print(f"  ✓ Already exists: {existing}")
                stats['skipped'] += 1
                continue

            # Check duration
            if track['duration'] and track['duration'] > self.MAX_DURATION:
                print(f"  ✗ Too long: {self._format_duration(track['duration'])} (max 15 min)")
                stats['failed'] += 1
                continue

            # Download with filename: "title - artist.mp3"
            actual_filename = self.sanitize_filename(f"{title} - {artist}") + '.mp3'
            output_path = os.path.join(self.output_dir, actual_filename)
            output_template = os.path.join(self.output_dir, actual_filename.replace('.mp3', ''))

            command = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', output_template + '.%(ext)s',
                '--no-playlist',
                url
            ]

            try:
                print(f"  Downloading from: {url}")
                result = subprocess.run(command, capture_output=True, text=True, timeout=300)

                if result.returncode == 0 and os.path.exists(output_path):
                    print(f"  ✓ Downloaded: {actual_filename}")
                    stats['downloaded'] += 1
                else:
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    print(f"  ✗ Download failed: {error_msg}")
                    stats['failed'] += 1

            except subprocess.TimeoutExpired:
                print(f"  ✗ Timeout")
                stats['failed'] += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
                stats['failed'] += 1

        return stats
