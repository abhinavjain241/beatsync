#!/usr/bin/env python3
"""
Check metadata in an MP3 file.
Usage: python3 check_mp3_metadata.py <path_to_mp3>
"""

import sys
import os

def check_metadata(mp3_path):
    """Check and display all metadata in an MP3 file."""
    if not os.path.exists(mp3_path):
        print(f"Error: File not found: {mp3_path}")
        return False

    try:
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3
    except ImportError:
        print("Error: mutagen library not installed")
        print("Install with: pip install mutagen")
        return False

    print("=" * 80)
    print(f"MP3 METADATA CHECK: {os.path.basename(mp3_path)}")
    print("=" * 80)
    print(f"File path: {mp3_path}")
    print(f"File size: {os.path.getsize(mp3_path):,} bytes")
    print()

    try:
        audio = MP3(mp3_path, ID3=ID3)

        if audio.tags is None:
            print("✗ NO TAGS FOUND IN FILE")
            print()
            print("This MP3 file has no ID3 tags.")
            print("Metadata writing may have failed or never occurred.")
            return False

        tag_count = len(audio.tags.keys())
        print(f"✓ TAGS FOUND: {tag_count} tags present")
        print()

        # Display all tags
        print("-" * 80)
        print("ALL TAGS:")
        print("-" * 80)
        for tag in sorted(audio.tags.keys()):
            tag_value = str(audio.tags[tag])
            # Truncate long values
            if len(tag_value) > 100:
                tag_value = tag_value[:100] + "..."
            print(f"  {tag}: {tag_value}")
        print()

        # Check important tags for music
        print("-" * 80)
        print("IMPORTANT MUSIC TAGS:")
        print("-" * 80)

        important_tags = [
            ('TIT2', 'Title'),
            ('TPE1', 'Artist'),
            ('TPE2', 'Album Artist'),
            ('TALB', 'Album'),
            ('TCON', 'Genre'),
            ('TBPM', 'BPM'),
            ('TKEY', 'Key'),
            ('TYER', 'Year'),
            ('COMM', 'Comment'),
        ]

        all_present = True
        for tag_id, tag_name in important_tags:
            if tag_id in audio.tags:
                value = str(audio.tags[tag_id])
                print(f"  ✓ {tag_name} ({tag_id}): {value}")
            else:
                print(f"  ✗ {tag_name} ({tag_id}): NOT FOUND")
                all_present = False

        print()

        # Check for album art
        print("-" * 80)
        print("ALBUM ART:")
        print("-" * 80)

        has_album_art = False
        album_art_info = []

        for tag in audio.tags.keys():
            if tag.startswith('APIC'):
                has_album_art = True
                apic = audio.tags[tag]
                album_art_info.append({
                    'type': apic.type,
                    'mime': apic.mime,
                    'size': len(apic.data),
                    'desc': apic.desc
                })

        if has_album_art:
            print(f"  ✓ ALBUM ART FOUND: {len(album_art_info)} image(s)")
            for i, info in enumerate(album_art_info, 1):
                print(f"\n  Image {i}:")
                print(f"    Type: {info['type']} (3=front cover)")
                print(f"    MIME: {info['mime']}")
                print(f"    Size: {info['size']:,} bytes")
                print(f"    Description: {info['desc']}")
        else:
            print("  ✗ NO ALBUM ART FOUND")

        print()
        print("-" * 80)
        print("AUDIO PROPERTIES:")
        print("-" * 80)
        print(f"  Duration: {int(audio.info.length)} seconds ({int(audio.info.length/60)}:{int(audio.info.length%60):02d})")
        print(f"  Bitrate: {audio.info.bitrate:,} bps ({int(audio.info.bitrate/1000)} kbps)")
        print(f"  Sample Rate: {audio.info.sample_rate:,} Hz")
        print(f"  Channels: {audio.info.channels}")
        print()

        # Summary
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        if all_present and has_album_art:
            print("✓✓✓ COMPLETE METADATA")
            print("This file has all important tags and album art.")
            print("Should work perfectly in Rekordbox and other DJ software.")
        elif all_present:
            print("✓✓ GOOD METADATA (no album art)")
            print("This file has all important tags but no album art.")
            print("Will work in Rekordbox but won't show artwork.")
        elif has_album_art:
            print("✓ PARTIAL METADATA (has album art)")
            print("This file has album art but missing some important tags.")
            print("May not work optimally in DJ software.")
        else:
            print("⚠ INCOMPLETE METADATA")
            print("This file is missing important tags and album art.")
            print("Metadata writing may have partially failed.")

        print("=" * 80)
        return True

    except Exception as e:
        print(f"✗ ERROR reading file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 check_mp3_metadata.py <path_to_mp3_file>")
        print()
        print("Example:")
        print("  python3 check_mp3_metadata.py downloads/track.mp3")
        sys.exit(1)

    mp3_path = sys.argv[1]
    success = check_metadata(mp3_path)
    sys.exit(0 if success else 1)
