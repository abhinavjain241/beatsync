"""
Parse pasted DJ-set tracklists into structured track entries.

Handles, in a single paste:
- Numbered lines:        "1. Artist - Title (Mix)"
- Timestamped lines:     "4:50 Artist - Title"   /   "1:23:50 Artist - Title"
- Slash-joined pairs:    "Track A (...) / Artist B - Track B (Acappella)"  →  two entries
- "ID - ID" / pure "ID"  →  skipped (unknown)
- "(unreleased)"         →  skipped (won't be on Spotify)
- "(ID Remix)"           →  kept but flagged low confidence
- Headers / blurbs       →  ignored (anything that doesn't match a track shape)

Each parsed track is returned as a dict:
    {
        "artist":     str,
        "title":      str,
        "raw":        str,         # the original line (or split half)
        "timestamp":  str | None,  # "4:50" or "1:23:50" when present
        "low_confidence": bool,    # True for ID-Remix entries
    }
"""

from __future__ import annotations

import re

# A line is "numbered" if it starts with "<digits>." or "<digits>)"
NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")

# A line is "timestamped" if it starts with "M:SS" or "H:MM:SS"
TIMESTAMP_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$")

# Split an entry into artist and title on " - " (with surrounding spaces)
SPLIT_RE = re.compile(r"\s+[-–—]\s+")

ID_TOKENS = {"id", "id - id"}


def _looks_like_id_only(text: str) -> bool:
    return text.strip().lower() in ID_TOKENS


def _split_slash_pair(body: str) -> list[str]:
    """Split "A - B / C - D" into ["A - B", "C - D"] when both halves look like tracks."""
    if " / " not in body:
        return [body]
    halves = [h.strip() for h in body.split(" / ")]
    if all(SPLIT_RE.search(h) for h in halves):
        return halves
    return [body]


def _parse_entry(body: str, timestamp: str | None) -> list[dict]:
    """Parse the artist/title body of one line. May yield multiple entries on slash-splits."""
    out: list[dict] = []
    for piece in _split_slash_pair(body):
        raw = piece.strip()
        if not raw:
            continue
        if _looks_like_id_only(raw):
            continue
        if "(unreleased)" in raw.lower():
            continue

        parts = SPLIT_RE.split(raw, maxsplit=1)
        if len(parts) != 2:
            continue
        artist, title = parts[0].strip(), parts[1].strip()
        if not artist or not title or _looks_like_id_only(artist) or _looks_like_id_only(title):
            continue

        low_conf = "id remix" in title.lower() or "id mix" in title.lower()
        out.append(
            {
                "artist": artist,
                "title": title,
                "raw": raw,
                "timestamp": timestamp,
                "low_confidence": low_conf,
            }
        )
    return out


def parse_tracklist(text: str) -> list[dict]:
    """Parse a pasted tracklist blob into a list of track entries.

    Lines that don't match either the numbered or timestamped shape are ignored,
    so headers like "Tracklist 🩶" and prose like "or this:" pass through silently.
    """
    tracks: list[dict] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Strip stray "or this:" / "Tracklist:" prefixes before the timestamp
        cleaned = re.sub(r"^(or this:|tracklist[:\s]*)", "", line, flags=re.IGNORECASE).strip()

        m = NUMBERED_RE.match(cleaned)
        if m:
            tracks.extend(_parse_entry(m.group(1), timestamp=None))
            continue

        m = TIMESTAMP_RE.match(cleaned)
        if m:
            tracks.extend(_parse_entry(m.group(2), timestamp=m.group(1)))
            continue

    return tracks


def format_search_query(track: dict) -> str:
    """Build a Spotify search query string from a parsed track."""
    return f"{track['artist']} {track['title']}"


if __name__ == "__main__":
    import json
    import sys

    blob = sys.stdin.read()
    parsed = parse_tracklist(blob)
    json.dump(parsed, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    print(f"\nParsed {len(parsed)} tracks.", file=sys.stderr)
