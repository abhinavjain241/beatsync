#!/usr/bin/env python3
"""
Debug script to analyze Beatport page HTML structure.
Usage: python debug_beatport.py <beatport_url>
"""

import sys
import requests
from bs4 import BeautifulSoup


def debug_beatport_page(url):
    """Fetch and analyze Beatport page structure."""

    print("=" * 70)
    print("Beatport Page Structure Debugger")
    print("=" * 70)
    print()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    print(f"Fetching: {url}")
    print()

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        print(f"✓ Successfully fetched page ({len(html)} characters)")
        print()
    except Exception as e:
        print(f"✗ Error fetching page: {e}")
        return

    soup = BeautifulSoup(html, 'lxml')

    print("Analyzing page structure...")
    print("=" * 70)
    print()

    # Check for various track container types
    tracklist_table = soup.find('table', class_='tracklist')
    tracklist_rows = []
    if tracklist_table:
        tbody = tracklist_table.find('tbody')
        if tbody:
            tracklist_rows = tbody.find_all('tr')

    checks = [
        ('table.tracklist', [tracklist_table] if tracklist_table else []),
        ('table.tracklist tbody tr', tracklist_rows),
        ('li.bucket-item', soup.find_all('li', class_='bucket-item')),
        ('div.track', soup.find_all('div', class_='track')),
        ('tr.track-row', soup.find_all('tr', class_='track-row')),
        ('li.track', soup.find_all('li', class_='track')),
        ('[data-track]', soup.find_all(attrs={'data-track': True})),
        ('div.playable-track', soup.find_all('div', class_='playable-track')),
        ('li.playable-track', soup.find_all('li', class_='playable-track')),
    ]

    print("Track Container Elements:")
    print("-" * 70)
    for selector, elements in checks:
        print(f"  {selector:30} → {len(elements):3} found")
    print()

    # Check for artist elements
    print("Artist Elements:")
    print("-" * 70)
    artist_checks = [
        ('p.buk-track-artists', soup.find_all('p', class_='buk-track-artists')),
        ('a.artist', soup.find_all('a', class_='artist')),
        ('.track-artists', soup.select('.track-artists')),
        ('[data-artist]', soup.find_all(attrs={'data-artist': True})),
    ]
    for selector, elements in artist_checks:
        print(f"  {selector:30} → {len(elements):3} found")
    print()

    # Check for track title elements
    print("Track Title Elements:")
    print("-" * 70)
    title_checks = [
        ('p.buk-track-primary-title', soup.find_all('p', class_='buk-track-primary-title')),
        ('a.buk-track-title', soup.find_all('a', class_='buk-track-title')),
        ('a.track-title', soup.find_all('a', class_='track-title')),
        ('.track-name', soup.select('.track-name')),
        ('[data-title]', soup.find_all(attrs={'data-title': True})),
    ]
    for selector, elements in title_checks:
        print(f"  {selector:30} → {len(elements):3} found")
    print()

    # Show sample track structure
    print("Sample Track Element Structure:")
    print("=" * 70)

    # Try to find any track-like element
    sample = None
    sample_selector = None

    # Prioritize tracklist rows if available
    if tracklist_rows:
        sample = tracklist_rows[0]
        sample_selector = 'table.tracklist tbody tr'
        print(f"Found using: {sample_selector}")
    else:
        for selector, elements in checks:
            if elements and elements[0] is not None:
                sample = elements[0]
                sample_selector = selector
                print(f"Found using: {selector}")
                break

    if sample:
        print()
        print("HTML Structure:")
        print("-" * 70)
        print(sample.prettify()[:2000])  # First 2000 chars
        if len(sample.prettify()) > 2000:
            print("\n... (truncated)")
    else:
        print("No track elements found!")
        print()
        print("Showing page title and main container classes:")
        title = soup.find('title')
        if title:
            print(f"Page title: {title.get_text()}")
        print()
        print("Main container classes found:")
        for div in soup.find_all('div', class_=True)[:20]:
            classes = ' '.join(div.get('class', []))
            if classes:
                print(f"  - {classes}")

    print()
    print("=" * 70)
    print("Debug complete!")
    print()
    print("If no tracks were found, Beatport may have:")
    print("  1. Changed their HTML structure")
    print("  2. Implemented anti-scraping measures")
    print("  3. Loaded content via JavaScript (not visible in raw HTML)")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_beatport.py <beatport_url>")
        sys.exit(1)

    url = sys.argv[1]
    debug_beatport_page(url)
