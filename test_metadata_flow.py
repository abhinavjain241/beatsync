#!/usr/bin/env python3
"""
Test script to verify metadata is properly preserved from JSON to metadata writer.
"""

from scraper import BeatportScraper

# Load a sample JSON file
scraper = BeatportScraper()
tracks = scraper.load_json_file('basshouse_t100.json')

if tracks:
    print("\n" + "="*70)
    print("TEST: Metadata Flow from JSON to Track Dictionary")
    print("="*70)

    # Check first track
    first_track = tracks[0]
    print(f"\nFirst track dictionary keys: {list(first_track.keys())}")
    print("\nExpected metadata fields:")
    print(f"  ✓ artist_name: {'artist_name' in first_track} - {first_track.get('artist_name', 'MISSING')}")
    print(f"  ✓ song_name: {'song_name' in first_track} - {first_track.get('song_name', 'MISSING')}")
    print(f"  ✓ label_name: {'label_name' in first_track} - {first_track.get('label_name', 'MISSING')}")
    print(f"  ✓ genre: {'genre' in first_track} - {first_track.get('genre', 'MISSING')}")
    print(f"  ✓ bpm_key: {'bpm_key' in first_track} - {first_track.get('bpm_key', 'MISSING')}")
    print(f"  ✓ album_art: {'album_art' in first_track} - {first_track.get('album_art', 'MISSING')[:50] + '...' if first_track.get('album_art') else 'MISSING'}")

    print("\nSearch-related fields:")
    print(f"  ✓ artist: {first_track.get('artist', 'MISSING')}")
    print(f"  ✓ track: {first_track.get('track', 'MISSING')}")
    print(f"  ✓ remix: {first_track.get('remix', 'MISSING')}")
    print(f"  ✓ label: {first_track.get('label', 'MISSING')}")

    # Verify all required fields are present
    required_fields = ['artist_name', 'song_name', 'label_name', 'genre', 'bpm_key', 'album_art']
    missing_fields = [field for field in required_fields if field not in first_track]

    print("\n" + "="*70)
    if missing_fields:
        print(f"❌ TEST FAILED: Missing fields: {missing_fields}")
    else:
        print("✅ TEST PASSED: All metadata fields preserved!")
    print("="*70 + "\n")
else:
    print("❌ Failed to load tracks from JSON")
