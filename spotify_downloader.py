#!/usr/bin/env python3
"""
Spotify Playlist Downloader

Downloads all tracks from a Spotify playlist as MP3s using yt-dlp.
Fetches BPM, key, genre, and album art from the Spotify API and embeds
them as ID3 tags (Rekordbox-compatible) via MetadataWriter.

Requires env vars: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
"""

import os
import re
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from downloader import AudioDownloader
from metadata_writer import MetadataWriter

# Spotify uses 0-based pitch class (C=0 … B=11) and mode (0=minor, 1=major)
_PITCH_CLASS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_MODE_NAME = {0: 'Minor', 1: 'Major'}


def _spotify_key_to_str(key: int, mode: int) -> Optional[str]:
    if key is None or key < 0:
        return None
    return f"{_PITCH_CLASS[key % 12]} {_MODE_NAME.get(mode, '')}".strip()


def _extract_playlist_id(url_or_id: str) -> str:
    match = re.search(r'playlist[/:]([A-Za-z0-9]+)', url_or_id)
    return match.group(1) if match else url_or_id


def _safe_dirname(name: str) -> str:
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_') or 'Spotify_Playlist'


class SpotifyPlaylistDownloader:
    """Downloads every track in a Spotify playlist as a tagged MP3."""

    def __init__(self, output_dir: Optional[str] = None, source: str = 'auto'):
        self.output_dir = output_dir
        self.source = source
        self.metadata_writer = MetadataWriter()
        self.sp = self._init_spotify()

        self.stats = {'total': 0, 'downloaded': 0, 'skipped': 0, 'failed': 0}
        self.downloaded_tracks: List[Dict] = []
        self.failed_tracks: List[Dict] = []
        self.skipped_tracks: List[Dict] = []

    # ------------------------------------------------------------------
    # Spotify API helpers
    # ------------------------------------------------------------------

    def _init_spotify(self) -> spotipy.Spotify:
        # client_id = os.environ.get('SPOTIFY_CLIENT_ID')
        client_id = "68206b2fe8684cb984cd5199fdd9a58c"
        # client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')
        client_secret = "92ad7105d3ec45e4982b1f3c8c70617d"
        if not client_id or not client_secret:
            print(
                'ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET '
                'environment variables must be set.',
                file=sys.stderr,
            )
            sys.exit(1)
        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    def _fetch_playlist_tracks(self, playlist_id: str) -> Tuple[str, List[Dict]]:
        """Return (playlist_name, list_of_raw_track_objects)."""
        playlist = self.sp.playlist(playlist_id, fields='name')
        playlist_name = playlist['name']
        print(f"Playlist: {playlist_name}")

        tracks: List[Dict] = []
        offset = 0
        while True:
            result = self.sp.playlist_tracks(
                playlist_id,
                offset=offset,
                limit=100,
                fields='items(track(id,name,artists(id,name),album(name,images,release_date))),next',
            )
            for item in result.get('items', []):
                track = item.get('track')
                if track and track.get('id'):
                    tracks.append(track)
            if not result.get('next'):
                break
            offset += 100

        return playlist_name, tracks

    def _fetch_audio_features(self, tracks: List[Dict]) -> Dict[str, Dict]:
        ids = [t['id'] for t in tracks]
        features_map: Dict[str, Dict] = {}
        try:
            for i in range(0, len(ids), 100):
                batch = self.sp.audio_features(ids[i : i + 100]) or []
                for f in batch:
                    if f:
                        features_map[f['id']] = f
        except Exception as e:
            # audio-features requires Extended Quota Mode (restricted since 2024)
            print(f"Warning: could not fetch audio features (BPM/key will be skipped): {e}", file=sys.stderr)
        return features_map

    def _fetch_artist_genres(self, tracks: List[Dict]) -> Dict[str, List[str]]:
        artist_ids = list({a['id'] for t in tracks for a in t.get('artists', [])})
        genres_map: Dict[str, List[str]] = {}
        for i in range(0, len(artist_ids), 50):
            artists = self.sp.artists(artist_ids[i : i + 50]).get('artists', [])
            for artist in artists:
                if artist:
                    genres_map[artist['id']] = artist.get('genres', [])
        return genres_map

    def _build_metadata(
        self,
        track: Dict,
        features_map: Dict[str, Dict],
        genres_map: Dict[str, List[str]],
    ) -> Dict:
        """Assemble the metadata dict that MetadataWriter expects."""
        features = features_map.get(track['id'], {})

        bpm = round(features['tempo']) if features.get('tempo') else None
        key_str = (
            _spotify_key_to_str(features['key'], features['mode'])
            if features.get('key') is not None and features.get('mode') is not None
            else None
        )

        if bpm and key_str:
            bpm_key = f"{bpm} BPM - {key_str}"
        elif bpm:
            bpm_key = f"{bpm} BPM"
        else:
            bpm_key = None

        first_artist_id = track['artists'][0]['id'] if track.get('artists') else None
        genres = genres_map.get(first_artist_id, []) if first_artist_id else []

        images = track.get('album', {}).get('images', [])

        return {
            'song_name': track['name'],
            'artist_name': ', '.join(a['name'] for a in track.get('artists', [])),
            'label_name': track.get('album', {}).get('name', ''),
            'genre': genres[0] if genres else None,
            'bpm_key': bpm_key,
            'album_art': images[0]['url'] if images else None,
        }

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self, playlist_url: str, auto_confirm: bool = False):
        playlist_id = _extract_playlist_id(playlist_url)

        print('Fetching tracks from Spotify playlist...')
        playlist_name, raw_tracks = self._fetch_playlist_tracks(playlist_id)
        print(f"Found {len(raw_tracks)} tracks")

        print('Fetching audio features and artist genres...')
        features_map = self._fetch_audio_features(raw_tracks)
        genres_map = self._fetch_artist_genres(raw_tracks)

        tracks = [self._build_metadata(t, features_map, genres_map) for t in raw_tracks]
        self.stats['total'] = len(tracks)

        output_dir = self.output_dir or os.path.join(
            os.path.expanduser('~/Music'), _safe_dirname(playlist_name)
        )
        os.makedirs(output_dir, exist_ok=True)

        if not auto_confirm:
            print(f"\nAbout to download {len(tracks)} tracks to: {output_dir}")
            if input('Continue? [Y/n]: ').strip().lower() == 'n':
                print('Aborted.')
                return

        print(f"\nDownloading {len(tracks)} tracks to: {output_dir}\n")
        downloader = AudioDownloader(output_dir=output_dir, source=self.source)

        for i, track in enumerate(tracks, 1):
            artist = track['artist_name']
            title = track['song_name']
            search_query = f"{artist} - {title}"

            print(f"[TRACK_START] {i}/{len(tracks)} | {artist} | {title}", flush=True)

            success, filename, already_existed = downloader.download_track(search_query)

            if success:
                if already_existed:
                    self.stats['skipped'] += 1
                    self.skipped_tracks.append({'artist': artist, 'track': title, 'filename': filename})
                    print(f"[TRACK_RESULT] SKIPPED | {artist} | {title} | {filename}", flush=True)
                else:
                    self.stats['downloaded'] += 1
                    self.downloaded_tracks.append({'artist': artist, 'track': title, 'filename': filename})
                    print(f"[TRACK_RESULT] SUCCESS | {artist} | {title} | {filename}", flush=True)

                    if filename:
                        mp3_path = os.path.join(output_dir, filename)
                        if os.path.exists(mp3_path):
                            self.metadata_writer.apply_metadata_to_track(mp3_path, track)
            else:
                self.stats['failed'] += 1
                self.failed_tracks.append({'artist': artist, 'track': title})
                print(f"[TRACK_RESULT] FAILED | {artist} | {title} | N/A", flush=True)

        self._display_summary(output_dir)

    def _display_summary(self, output_dir: str):
        print()
        print('=' * 60)
        print('Download Summary')
        print('=' * 60)
        print(f"Total tracks:      {self.stats['total']}")
        print(f"Downloaded:        {self.stats['downloaded']}")
        print(f"Already existed:   {self.stats['skipped']}")
        print(f"Failed:            {self.stats['failed']}")
        print()
        print(f"Files saved to: {output_dir}/")
        print('=' * 60)

        print(f"[DOWNLOAD_FOLDER] {output_dir}", flush=True)
        print(f"[DOWNLOADED_TRACKS] {json.dumps(self.downloaded_tracks)}", flush=True)
        print(f"[FAILED_TRACKS] {json.dumps(self.failed_tracks)}", flush=True)
        print(f"[SKIPPED_TRACKS] {json.dumps(self.skipped_tracks)}", flush=True)


def main():
    parser = argparse.ArgumentParser(description='Download a Spotify playlist as MP3s')
    parser.add_argument('playlist_url', help='Spotify playlist URL or ID')
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory (default: ~/Music/<playlist_name>)',
    )
    parser.add_argument(
        '--source', '-s',
        choices=['soundcloud', 'youtube', 'auto'],
        default='auto',
        help='Download source (default: auto — searches both, picks longer version)',
    )
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    SpotifyPlaylistDownloader(
        output_dir=args.output_dir,
        source=args.source,
    ).run(args.playlist_url, auto_confirm=args.yes)


if __name__ == '__main__':
    main()
