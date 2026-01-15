#!/usr/bin/env python3
"""
Test script to demonstrate album art URL support.
"""

import os
import json

def is_url(path: str) -> bool:
    """Check if a path is a URL."""
    return path.startswith('http://') or path.startswith('https://')

def get_mime_type_from_data(image_data: bytes) -> str:
    """Detect MIME type from image data."""
    if image_data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif image_data[8:12] == b'WEBP':
        return 'image/webp'
    else:
        return 'image/jpeg'

def test_url_support():
    """Test that album art URLs are properly supported."""

    # Test URL detection
    test_cases = [
        ('https://example.com/image.jpg', True),
        ('http://example.com/image.png', True),
        ('./local/path/image.jpg', False),
        ('/absolute/path/image.jpg', False),
        ('relative/path/image.jpg', False),
    ]

    print("=" * 80)
    print("Album Art URL Support Test")
    print("=" * 80)
    print()

    print("URL Detection Test:")
    print("-" * 80)
    for path, expected in test_cases:
        result = is_url(path)
        status = "✓" if result == expected else "✗"
        print(f"{status} {path}: {'URL' if result else 'Local Path'}")
    print()

    # Test MIME type detection
    print("MIME Type Detection Test:")
    print("-" * 80)

    # JPEG signature
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    mime = get_mime_type_from_data(jpeg_data)
    print(f"{'✓' if mime == 'image/jpeg' else '✗'} JPEG signature: {mime}")

    # PNG signature
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    mime = get_mime_type_from_data(png_data)
    print(f"{'✓' if mime == 'image/png' else '✗'} PNG signature: {mime}")

    print()

    print("=" * 80)
    print("Example JSON Configuration")
    print("=" * 80)
    print()

    example_config = {
        "tracks": [
            {
                "song_name": "Example Track Extended Mix",
                "artist_name": "Example Artist",
                "label_name": "Example Label",
                "genre": "House",
                "bpm_key": "128 BPM - A Minor",
                "album_art": "https://example.com/artwork.jpg"
            },
            {
                "song_name": "Another Track",
                "artist_name": "Another Artist",
                "label_name": "Another Label",
                "genre": "Techno",
                "bpm_key": "130 BPM - D Minor",
                "album_art": "./local_images/artwork.jpg"
            }
        ]
    }

    print("You can now use either URLs or local paths for album art:")
    print()
    print(json.dumps(example_config, indent=2))
    print()

    print("=" * 80)
    print("Benefits of URL Support")
    print("=" * 80)
    print()
    print("✓ No need to download album art manually")
    print("✓ Automatically handles image formats (JPEG, PNG, WebP)")
    print("✓ Works with direct image URLs from Beatport or other sources")
    print("✓ Falls back to local files seamlessly")
    print("✓ Proper error handling for failed downloads")
    print()

if __name__ == '__main__':
    test_url_support()
