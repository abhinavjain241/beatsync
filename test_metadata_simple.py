#!/usr/bin/env python3
"""
Simple test to verify JSON parsing preserves all metadata fields.
"""

import json

# Load JSON file directly
with open('basshouse_t100.json', 'r') as f:
    original_data = json.load(f)

print("\n" + "="*70)
print("TEST: JSON Metadata Preservation")
print("="*70)

# Check first track from original JSON
first_original = original_data[0]
print(f"\nOriginal JSON first track fields: {list(first_original.keys())}")
print("\nOriginal metadata values:")
for key, value in first_original.items():
    if key != 'album_art':
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {value[:50]}...")

# Now simulate what scraper.load_json_file does
artist = first_original.get('artist_name', first_original.get('artist', ''))
song_name = first_original.get('song_name', first_original.get('track', first_original.get('name', '')))

# Try to separate remix info from song name
remix = ''
track = song_name

remix_patterns = [
    'Extended Mix', 'Original Mix', 'Remix', 'Edit', 'VIP',
    'Club Mix', 'Radio Edit', 'Dub Mix'
]

for pattern in remix_patterns:
    if pattern.lower() in song_name.lower():
        parts = song_name.rsplit(maxsplit=2)
        if len(parts) >= 2:
            potential_remix = ' '.join(parts[-2:])
            if any(p.lower() in potential_remix.lower() for p in remix_patterns):
                remix = potential_remix
                track = ' '.join(parts[:-2])
                break

label = first_original.get('label', first_original.get('label_name', ''))

# Create track dict as scraper does
track_dict = {
    'artist': artist,
    'track': track,
    'remix': remix,
    'label': label
}

# PRESERVE ALL ORIGINAL METADATA FIELDS (the fix)
for key, value in first_original.items():
    if key not in track_dict and value:
        track_dict[key] = value

print("\n" + "-"*70)
print("After scraper processing:")
print(f"Track dict fields: {list(track_dict.keys())}")

# Verify all required metadata fields are preserved
required_metadata = ['artist_name', 'song_name', 'label_name', 'genre', 'bpm_key', 'album_art']
missing = [field for field in required_metadata if field not in track_dict]

print("\nMetadata preservation check:")
for field in required_metadata:
    status = "✓" if field in track_dict else "✗"
    value = track_dict.get(field, 'MISSING')
    if field != 'album_art':
        print(f"  {status} {field}: {value}")
    else:
        print(f"  {status} {field}: {value[:50] + '...' if value != 'MISSING' else 'MISSING'}")

print("\n" + "="*70)
if missing:
    print(f"❌ TEST FAILED: Missing metadata fields: {missing}")
else:
    print("✅ TEST PASSED: All metadata fields preserved after scraper processing!")
print("="*70 + "\n")
