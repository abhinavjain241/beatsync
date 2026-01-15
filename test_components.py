#!/usr/bin/env python3
"""
Test individual components of the Beatport downloader.
Useful for debugging and development.
"""

import sys


def test_scraper():
    """Test the scraper module."""
    print("Testing Beatport Scraper")
    print("=" * 60)

    try:
        from scraper import BeatportScraper

        scraper = BeatportScraper()
        print("✓ BeatportScraper initialized")

        # Test search string creation
        test_track = {
            'artist': 'Test Artist',
            'track': 'Test Track',
            'remix': 'Test Remix'
        }
        search_string = scraper.create_search_string(test_track)
        print(f"✓ Search string: {search_string}")

        print()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_downloader():
    """Test the downloader module."""
    print("Testing Audio Downloader")
    print("=" * 60)

    try:
        from downloader import AudioDownloader

        downloader = AudioDownloader(output_dir='test_downloads')
        print("✓ AudioDownloader initialized")

        # Test filename creation
        test_track = {
            'artist': 'Test Artist',
            'track': 'Test Track'
        }
        filename = downloader.create_filename(test_track)
        print(f"✓ Filename: {filename}")

        # Test sanitization
        bad_filename = 'Artist/Track:Name*Test?.mp3'
        sanitized = downloader.sanitize_filename(bad_filename)
        print(f"✓ Sanitized: {sanitized}")

        print()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_imports():
    """Test that all modules can be imported."""
    print("Testing Module Imports")
    print("=" * 60)

    modules = [
        'scraper',
        'downloader',
        'beatport_downloader'
    ]

    all_ok = True
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            all_ok = False

    print()
    return all_ok


def main():
    """Run all tests."""
    print()
    print("=" * 60)
    print("Component Tests")
    print("=" * 60)
    print()

    results = []

    # Test imports
    results.append(('Imports', test_imports()))

    # Test scraper
    results.append(('Scraper', test_scraper()))

    # Test downloader
    results.append(('Downloader', test_downloader()))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
        all_passed &= passed

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
