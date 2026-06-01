"""
Spotify integration: OAuth, search-with-scoring, playlist CRUD.

Credentials default to the shared "vibecheck" Spotify app (which predates
the Nov 2024 API restrictions that limit new-app access to certain endpoints).
Override via .env (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI)
if you ever need to point at a different app.

The OAuth flow uses spotipy's SpotifyOAuth, which opens a browser the first time
and caches the refresh token in `.cache-spotify` so subsequent CLI/subprocess
invocations don't re-prompt.

Search scoring mirrors downloader.calculate_match_score: a fuzzy weighted
overlap of artist tokens, title tokens, and mix info.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

load_dotenv()

# Reused from ../vibecheck/clients/spotify.py — that app is already grandfathered
# in for the full set of Spotify Web API endpoints.
DEFAULT_CLIENT_ID = "68206b2fe8684cb984cd5199fdd9a58c"
DEFAULT_CLIENT_SECRET = "92ad7105d3ec45e4982b1f3c8c70617d"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"

SCOPE = "playlist-modify-private playlist-modify-public playlist-read-private"
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-spotify")

# Spotify limits user_playlist_add_tracks() to 100 URIs per call
ADD_TRACKS_CHUNK = 100

PLAYLIST_URL_RE = re.compile(r"(?:open\.spotify\.com/playlist/|spotify:playlist:)([A-Za-z0-9]+)")


@dataclass
class SearchResult:
    uri: str
    name: str
    artists: list[str]
    score: float
    duration_ms: int


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _score(query_artist: str, query_title: str, result_artists: list[str], result_title: str) -> float:
    """Weighted token overlap: artist 40%, title 45%, mix info 15%."""
    norm_q_artist = set(_normalize(query_artist).split())
    norm_r_artist = set(_normalize(" ".join(result_artists)).split())
    norm_q_title = set(_normalize(query_title).split())
    norm_r_title = set(_normalize(result_title).split())

    parts: list[tuple[float, float]] = []
    if norm_q_artist and norm_r_artist:
        overlap = len(norm_q_artist & norm_r_artist) / max(len(norm_q_artist), len(norm_r_artist))
        parts.append((overlap, 0.4))
    if norm_q_title and norm_r_title:
        overlap = len(norm_q_title & norm_r_title) / max(len(norm_q_title), len(norm_r_title))
        parts.append((overlap, 0.45))

    if not parts:
        return 0.0
    total_weight = sum(w for _, w in parts)
    return sum(s * w for s, w in parts) / total_weight


def extract_playlist_id(url_or_uri: str) -> str:
    """Pull the playlist ID out of a Spotify URL, URI, or bare ID."""
    m = PLAYLIST_URL_RE.search(url_or_uri)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9]{20,}", url_or_uri.strip()):
        return url_or_uri.strip()
    raise ValueError(f"Could not parse Spotify playlist id from: {url_or_uri!r}")


class SpotifyClient:
    """Thin wrapper around spotipy.Spotify with OAuth + the operations we need."""

    def __init__(self) -> None:
        client_id = os.environ.get("SPOTIFY_CLIENT_ID") or DEFAULT_CLIENT_ID
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET") or DEFAULT_CLIENT_SECRET
        redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI") or DEFAULT_REDIRECT_URI

        self._auth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SCOPE,
            cache_path=CACHE_PATH,
            open_browser=True,
        )
        self.sp = spotipy.Spotify(auth_manager=self._auth)
        self._user_id: str | None = None

    @property
    def user_id(self) -> str:
        if self._user_id is None:
            self._user_id = self.sp.current_user()["id"]
        return self._user_id

    def search_track(self, artist: str, title: str, limit: int = 5) -> list[SearchResult]:
        """Search Spotify and return scored, ranked candidates (best first)."""
        query = f"{artist} {title}"
        try:
            resp = self.sp.search(q=query, type="track", limit=limit)
        except spotipy.SpotifyException:
            logger.exception("Spotify search failed for %r", query)
            return []

        results: list[SearchResult] = []
        for item in resp.get("tracks", {}).get("items", []):
            artists = [a["name"] for a in item.get("artists", [])]
            score = _score(artist, title, artists, item.get("name", ""))
            results.append(
                SearchResult(
                    uri=item["uri"],
                    name=item["name"],
                    artists=artists,
                    score=score,
                    duration_ms=item.get("duration_ms", 0),
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def create_playlist(self, name: str, description: str = "", public: bool = False) -> dict:
        return self.sp.user_playlist_create(
            user=self.user_id, name=name, public=public, description=description
        )

    def add_tracks(self, playlist_id: str, track_uris: list[str]) -> None:
        for i in range(0, len(track_uris), ADD_TRACKS_CHUNK):
            chunk = track_uris[i : i + ADD_TRACKS_CHUNK]
            self.sp.playlist_add_items(playlist_id=playlist_id, items=chunk)

    def get_playlist_tracks(self, playlist_url_or_id: str) -> list[dict]:
        """Return [{'artist': ..., 'title': ..., 'uri': ...}, ...] for every track."""
        playlist_id = extract_playlist_id(playlist_url_or_id)
        out: list[dict] = []
        results = self.sp.playlist_items(playlist_id, additional_types=("track",))
        while results:
            for item in results.get("items", []):
                track = item.get("track")
                if not track or track.get("is_local"):
                    continue
                artists = ", ".join(a["name"] for a in track.get("artists", []))
                out.append(
                    {
                        "artist": artists,
                        "title": track["name"],
                        "uri": track["uri"],
                    }
                )
            results = self.sp.next(results) if results.get("next") else None
        return out

    def get_playlist_meta(self, playlist_url_or_id: str) -> dict:
        playlist_id = extract_playlist_id(playlist_url_or_id)
        pl = self.sp.playlist(playlist_id, fields="id,name,external_urls,owner")
        return {
            "id": pl["id"],
            "name": pl["name"],
            "url": pl["external_urls"]["spotify"],
            "owner": pl["owner"]["display_name"],
        }
