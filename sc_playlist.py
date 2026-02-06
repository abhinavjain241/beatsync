#!/usr/bin/env python3
"""
Sync a SoundCloud playlist - downloads new tracks, skips existing.

Usage:
    python sc_playlist.py <playlist_url> [-o output_dir]

Examples:
    python sc_playlist.py "https://soundcloud.com/user/sets/my-playlist"
    python sc_playlist.py "https://soundcloud.com/user/likes" -o ~/Music/sc-likes
"""

import argparse
from downloader import AudioDownloader


def main():
    parser = argparse.ArgumentParser(
        description='Sync a SoundCloud playlist (download new, skip existing)'
    )
    parser.add_argument('url', help='SoundCloud playlist or likes URL')
    parser.add_argument('--output-dir', '-o', default='downloads', help='Output directory')

    args = parser.parse_args()

    print("=" * 50)
    print("SoundCloud Playlist Sync")
    print("=" * 50)
    print(f"Output: {args.output_dir}")
    print()

    downloader = AudioDownloader(output_dir=args.output_dir)
    stats = downloader.sync_soundcloud_playlist(args.url)

    print()
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Total tracks:  {stats['total']}")
    print(f"Downloaded:    {stats['downloaded']}")
    print(f"Skipped:       {stats['skipped']}")
    print(f"Failed:        {stats['failed']}")

    exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
