#!/usr/bin/env python3
"""
Quick test for the specific Beatport playlist URL.
"""

import sys
from scraper import BeatportScraper


def test_playlist_url():
    """Test the specific playlist URL."""

    url = "https://www.beatport.com/playlists/share/6421928"

    print("Testing Beatport Playlist URL")
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
        print("Running debug analysis...")
        print()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # Check for tracklist table
        tracklist = soup.find('table', class_='tracklist')
        if tracklist:
            print(f"Found tracklist table!")
            tbody = tracklist.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                print(f"Found {len(rows)} rows in tbody")

                if rows:
                    print("\nFirst row structure:")
                    print("-" * 60)
                    first_row = rows[0]
                    tds = first_row.find_all('td')
                    print(f"Number of td elements: {len(tds)}")
                    for i, td in enumerate(tds[:3]):
                        print(f"\nTD {i}:")
                        print(td.prettify()[:500])
            else:
                print("No tbody found in tracklist table")
        else:
            print("No tracklist table found")

        sys.exit(1)

    print(f"✓ Found {len(tracks)} tracks")
    print()

    # Display first few tracks
    print("First 10 tracks:")
    print("-" * 60)
    for i, track in enumerate(tracks[:10], 1):
        search_string = scraper.create_search_string(track)
        print(f"{i}. {search_string}")

    if len(tracks) > 10:
        print(f"... and {len(tracks) - 10} more")

    print()
    print("=" * 60)
    print("✓ Test passed!")
    print()
    print("The scraper is working correctly for this URL.")


if __name__ == '__main__':
    test_playlist_url()
