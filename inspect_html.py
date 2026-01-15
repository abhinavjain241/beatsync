#!/usr/bin/env python3
"""
Helper script to inspect debug.html and find potential track selectors.
"""

from bs4 import BeautifulSoup
import os


def inspect_html(file_path='debug.html'):
    """Inspect HTML file to find potential track elements."""
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        print("Run the scraper first to generate debug.html")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')

    print("=" * 60)
    print("HTML INSPECTION REPORT")
    print("=" * 60)
    print()

    print("1. Checking for authentication/login indicators...")
    login_indicators = soup.find_all(['button', 'a', 'div'], string=lambda x: x and any(
        word in x.lower() for word in ['log in', 'sign in', 'login', 'signin']
    ))
    if login_indicators:
        print(f"   Found {len(login_indicators)} login-related elements")
        print("   This page might require authentication!")
    else:
        print("   No obvious login indicators found")
    print()

    print("2. Looking for track-related class names...")
    all_elements = soup.find_all(class_=True)
    track_classes = set()
    for elem in all_elements:
        classes = elem.get('class', [])
        for cls in classes:
            if any(word in cls.lower() for word in ['track', 'song', 'item', 'playlist', 'queue']):
                track_classes.add(cls)

    if track_classes:
        print(f"   Found {len(track_classes)} classes with track-related names:")
        for cls in sorted(track_classes)[:20]:
            print(f"     - {cls}")
        if len(track_classes) > 20:
            print(f"     ... and {len(track_classes) - 20} more")
    else:
        print("   No track-related classes found")
    print()

    print("3. Checking common element patterns...")
    patterns = {
        'div.bucket-item': soup.find_all('div', class_='bucket-item'),
        'li.bucket-item': soup.find_all('li', class_='bucket-item'),
        'div.track': soup.find_all('div', class_='track'),
        'tr with track': soup.find_all('tr', class_=lambda x: x and 'track' in x if x else False),
        'divs with "track" in class': soup.find_all('div', class_=lambda x: x and 'track' in x if x else False)
    }

    for pattern_name, elements in patterns.items():
        print(f"   {pattern_name}: {len(elements)} found")
    print()

    print("4. Sample of first few potential track containers:")
    track_containers = soup.find_all(['div', 'li', 'tr'], class_=lambda x: x and any(
        word in ' '.join(x).lower() for word in ['track', 'item']
    ) if x else False)

    if track_containers:
        for i, container in enumerate(track_containers[:3], 1):
            print(f"\n   Container {i}:")
            print(f"   Tag: {container.name}")
            print(f"   Classes: {container.get('class', [])}")
            text = container.get_text(strip=True)[:100]
            print(f"   Text preview: {text}...")
    else:
        print("   No potential track containers found")
    print()

    print("=" * 60)


if __name__ == '__main__':
    inspect_html()
