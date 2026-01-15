#!/usr/bin/env python3
"""
Quick test script to verify the scraper is working.
"""

import sys
from scraper import BeatportScraper


def test_scraper():
    """Test the scraper with a URL."""

    if len(sys.argv) < 2:
        print("Usage: python test_scraper.py <beatport_url>")
        sys.exit(1)

    url = sys.argv[1]

    print("Testing Beatport Scraper")
    print("=" * 60)
    print(f"URL: {url}")
    print()

    scraper = BeatportScraper()

    # Fetch HTML
    print("Step 1: Fetching HTML...")
    html = scraper.fetch_html(url)

    if not html:
        print("✗ Failed to fetch HTML")
        sys.exit(1)

    print(f"✓ Fetched {len(html)} characters")
    print()

    # Parse tracks
    print("Step 2: Parsing tracks...")
    tracks = scraper.parse_tracks(html)

    if not tracks:
        print("✗ No tracks found")
        print()
        print("This means the scraper couldn't extract track information.")
        print("Run: python debug_beatport.py <url> for detailed diagnosis")
        sys.exit(1)

    print(f"✓ Found {len(tracks)} tracks")
    print()

    # Display first few tracks
    print("First 5 tracks:")
    print("-" * 60)
    for i, track in enumerate(tracks[:5], 1):
        search_string = scraper.create_search_string(track)
        print(f"{i}. {search_string}")

    if len(tracks) > 5:
        print(f"... and {len(tracks) - 5} more")

    print()
    print("=" * 60)
    print("✓ Scraper test passed!")
    print()
    print("The scraper is working correctly.")
    print("You can now use the web interface to download these tracks.")


if __name__ == '__main__':
    test_scraper()
