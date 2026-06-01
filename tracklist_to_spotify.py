#!/usr/bin/env python3
"""
Turn a pasted DJ-set tracklist into a Spotify playlist.

Usage:
    python3 tracklist_to_spotify.py --file tracklist.txt --name "My Set"
    cat tracklist.txt | python3 tracklist_to_spotify.py --stdin --name "My Set"

Prints structured progress lines that server.js can parse:
    [STAGE] Parsing tracklist
    [TRACK_START] {"index": 1, "total": 30, "query": "..."}
    [TRACK_RESULT] {"index": 1, "status": "matched|low_confidence|missing", ...}
    [PLAYLIST_CREATED] {"id": "...", "url": "...", "name": "..."}
    [SUMMARY] {"matched": N, "missing": N, "low_confidence": N}
"""

from __future__ import annotations

import argparse
import json
import sys

from spotify_client import SpotifyClient
from tracklist_parser import format_search_query, parse_tracklist

# A score below this means we picked something but we're not confident
LOW_CONFIDENCE_THRESHOLD = 0.45
# A score below this means we drop the result entirely
MIN_ACCEPT_SCORE = 0.20


def _emit(tag: str, payload: dict) -> None:
    print(f"[{tag}] {json.dumps(payload, ensure_ascii=False)}", flush=True)


def read_input(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read()
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return f.read()
    raise SystemExit("Provide --file <path> or --stdin")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tracklist → Spotify playlist")
    parser.add_argument("--file", help="Path to a text file with the tracklist")
    parser.add_argument("--stdin", action="store_true", help="Read tracklist from stdin")
    parser.add_argument("--name", required=True, help="Name for the new Spotify playlist")
    parser.add_argument("--description", default="Created by beatsync", help="Playlist description")
    parser.add_argument("--public", action="store_true", help="Make the playlist public (default: private)")
    args = parser.parse_args()

    print("[STAGE] Parsing tracklist", flush=True)
    text = read_input(args)
    tracks = parse_tracklist(text)
    if not tracks:
        print("[ERROR] No tracks found in the tracklist input", flush=True)
        return 1
    print(f"Parsed {len(tracks)} tracks", flush=True)

    print("[STAGE] Authenticating with Spotify", flush=True)
    client = SpotifyClient()
    # Touch user_id to trigger OAuth dance up-front (browser opens on first run)
    _ = client.user_id

    print("[STAGE] Searching Spotify", flush=True)
    matched_uris: list[str] = []
    missing: list[dict] = []
    low_confidence: list[dict] = []

    for i, track in enumerate(tracks, start=1):
        query = format_search_query(track)
        _emit("TRACK_START", {"index": i, "total": len(tracks), "query": query})

        results = client.search_track(track["artist"], track["title"], limit=5)
        if not results or results[0].score < MIN_ACCEPT_SCORE:
            missing.append(track)
            _emit(
                "TRACK_RESULT",
                {
                    "index": i,
                    "status": "missing",
                    "query": query,
                    "best_score": results[0].score if results else 0.0,
                },
            )
            continue

        best = results[0]
        matched_uris.append(best.uri)
        status = "low_confidence" if (best.score < LOW_CONFIDENCE_THRESHOLD or track["low_confidence"]) else "matched"
        if status == "low_confidence":
            low_confidence.append(track)
        _emit(
            "TRACK_RESULT",
            {
                "index": i,
                "status": status,
                "query": query,
                "matched_name": best.name,
                "matched_artists": best.artists,
                "score": round(best.score, 3),
                "uri": best.uri,
            },
        )

    print("[STAGE] Creating playlist", flush=True)
    playlist = client.create_playlist(args.name, args.description, public=args.public)
    _emit(
        "PLAYLIST_CREATED",
        {
            "id": playlist["id"],
            "url": playlist["external_urls"]["spotify"],
            "name": playlist["name"],
        },
    )

    if matched_uris:
        print(f"[STAGE] Adding {len(matched_uris)} tracks", flush=True)
        client.add_tracks(playlist["id"], matched_uris)

    _emit(
        "SUMMARY",
        {
            "total": len(tracks),
            "matched": len(matched_uris) - len(low_confidence),
            "low_confidence": len(low_confidence),
            "missing": len(missing),
            "playlist_url": playlist["external_urls"]["spotify"],
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
