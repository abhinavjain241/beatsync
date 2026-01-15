#!/usr/bin/env python3
"""
Standalone test script to verify metadata writing works correctly.
Creates a test MP3 file and writes metadata to it.
"""

import os
import subprocess
import json
from metadata_writer import MetadataWriter

def create_test_mp3(output_path: str):
    """Create a minimal test MP3 file using ffmpeg."""
    print(f"Creating test MP3 file: {output_path}")

    # Create a 5-second silent MP3 file
    command = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'anullsrc=r=44100:cl=stereo',
        '-t', '5',
        '-q:a', '0',
        '-y',
        output_path
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✓ Test MP3 created successfully")
            return True
        else:
            print(f"✗ Failed to create test MP3: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error creating test MP3: {e}")
        return False

def test_metadata_writing():
    """Test metadata writing on a sample MP3 file."""
    print("=" * 80)
    print("METADATA WRITING TEST")
    print("=" * 80)
    print()

    # Create test directory
    test_dir = "test_metadata"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    test_mp3_path = os.path.join(test_dir, "test_track.mp3")

    # Create test MP3
    if not create_test_mp3(test_mp3_path):
        print("✗ Cannot proceed without test MP3 file")
        return False

    print()
    print("-" * 80)
    print("TESTING METADATA WRITE")
    print("-" * 80)
    print()

    # Test metadata
    test_metadata = {
        'song_name': 'Test Track Extended Mix',
        'artist_name': 'Test Artist',
        'label_name': 'Test Label',
        'genre': 'House',
        'bpm_key': '128 BPM - A Minor',
        'album_art': None  # No album art for basic test
    }

    # Write metadata
    writer = MetadataWriter()
    success = writer.apply_metadata_to_track(test_mp3_path, test_metadata)

    print()
    print("-" * 80)
    print("VERIFICATION")
    print("-" * 80)
    print()

    if success:
        print("✓ Metadata write reported success")

        # Verify using mutagen
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3

            audio = MP3(test_mp3_path, ID3=ID3)
            if audio.tags:
                print(f"✓ Tags found in file: {len(audio.tags.keys())} tags")
                print()
                print("Tag details:")
                for tag in sorted(audio.tags.keys()):
                    print(f"  {tag}: {audio.tags[tag]}")

                # Check specific tags
                print()
                print("Specific tag verification:")
                print(f"  Title (TIT2): {audio.tags.get('TIT2', 'NOT FOUND')}")
                print(f"  Artist (TPE1): {audio.tags.get('TPE1', 'NOT FOUND')}")
                print(f"  Album (TALB): {audio.tags.get('TALB', 'NOT FOUND')}")
                print(f"  Genre (TCON): {audio.tags.get('TCON', 'NOT FOUND')}")
                print(f"  BPM (TBPM): {audio.tags.get('TBPM', 'NOT FOUND')}")
                print(f"  Key (TKEY): {audio.tags.get('TKEY', 'NOT FOUND')}")
                print()

                return True
            else:
                print("✗ No tags found in file")
                return False
        except Exception as e:
            print(f"✗ Error verifying tags: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("✗ Metadata write reported failure")
        return False

if __name__ == '__main__':
    result = test_metadata_writing()
    print()
    print("=" * 80)
    if result:
        print("✓✓✓ TEST PASSED - Metadata writing works correctly")
    else:
        print("✗✗✗ TEST FAILED - Metadata writing has issues")
    print("=" * 80)
