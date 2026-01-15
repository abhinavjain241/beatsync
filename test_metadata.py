#!/usr/bin/env python3
"""
Test script to verify metadata writing works correctly.
Usage: python test_metadata.py <path_to_mp3_file>
"""

import sys
import os
from metadata_writer import MetadataWriter

def test_metadata_writing(mp3_file_path):
    """Test metadata writing on a sample MP3 file."""

    if not os.path.exists(mp3_file_path):
        print(f"Error: File not found: {mp3_file_path}")
        return False

    print(f"Testing metadata writing on: {mp3_file_path}")
    print("-" * 60)

    # Sample metadata (you can customize this)
    test_metadata = {
        'song_name': 'Test Track Extended Mix',
        'artist_name': 'Test Artist',
        'label_name': 'Test Label',
        'genre': 'Melodic House & Techno',
        'bpm_key': '128 BPM - G Minor',
        'album_art': './melotech_t100_files/817e25bd-c35c-42db-bd35-53905b9aebfa(1).jpg'
    }

    print("Metadata to write:")
    for key, value in test_metadata.items():
        if key != 'album_art':
            print(f"  {key}: {value}")
        else:
            art_exists = "✓ exists" if os.path.exists(value) else "✗ not found"
            print(f"  {key}: {value} ({art_exists})")

    print("\nWriting metadata...")
    writer = MetadataWriter()
    success = writer.write_metadata(mp3_file_path, test_metadata)

    if success:
        print("\n✓ Metadata written successfully!")
        print("\nTo verify, check the file in:")
        print("  - macOS Music/iTunes")
        print("  - macOS Finder (Get Info)")
        print("  - Or run: python -c \"from mutagen.mp3 import MP3; print(MP3('{}').tags)\"".format(mp3_file_path))
    else:
        print("\n✗ Failed to write metadata")

    print("-" * 60)
    return success


def read_existing_metadata(mp3_file_path):
    """Read and display existing metadata from MP3 file."""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3

    if not os.path.exists(mp3_file_path):
        print(f"Error: File not found: {mp3_file_path}")
        return

    print(f"\nReading existing metadata from: {mp3_file_path}")
    print("-" * 60)

    try:
        audio = MP3(mp3_file_path, ID3=ID3)

        if audio.tags is None:
            print("No ID3 tags found in file")
            return

        print("Existing tags:")
        for key, value in audio.tags.items():
            print(f"  {key}: {value}")

        print("\nCommon tags:")
        print(f"  Title (TIT2): {audio.tags.get('TIT2', 'Not set')}")
        print(f"  Artist (TPE1): {audio.tags.get('TPE1', 'Not set')}")
        print(f"  Album (TALB): {audio.tags.get('TALB', 'Not set')}")
        print(f"  Genre (TCON): {audio.tags.get('TCON', 'Not set')}")
        print(f"  BPM (TBPM): {audio.tags.get('TBPM', 'Not set')}")
        print(f"  Key (TKEY): {audio.tags.get('TKEY', 'Not set')}")

        has_apic = 'APIC:' in str(audio.tags) or any('APIC' in str(k) for k in audio.tags.keys())
        print(f"  Album Art (APIC): {'Present' if has_apic else 'Not set'}")

    except Exception as e:
        print(f"Error reading metadata: {e}")
        import traceback
        traceback.print_exc()

    print("-" * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_metadata.py <path_to_mp3_file> [--read-only]")
        print("\nOptions:")
        print("  <path_to_mp3_file>  Path to MP3 file to test")
        print("  --read-only         Only read existing metadata without writing")
        sys.exit(1)

    mp3_path = sys.argv[1]
    read_only = '--read-only' in sys.argv

    if read_only:
        read_existing_metadata(mp3_path)
    else:
        # First read existing metadata
        read_existing_metadata(mp3_path)

        # Then test writing
        input("\nPress Enter to write test metadata...")
        test_metadata_writing(mp3_path)

        # Read again to verify
        read_existing_metadata(mp3_path)
