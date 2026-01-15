"""
HTML structure analyzer to help identify the correct selectors for Beatport tracks.
"""

from bs4 import BeautifulSoup
import sys
from collections import Counter

def analyze_html_structure(html_file):
    """Analyze HTML structure to identify track elements."""

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')

    print("=" * 80)
    print("HTML STRUCTURE ANALYSIS")
    print("=" * 80)

    # Analyze all class names
    all_classes = []
    for elem in soup.find_all(class_=True):
        classes = elem.get('class', [])
        all_classes.extend(classes)

    class_counts = Counter(all_classes)

    print("\n📊 Most common class names (top 30):")
    print("-" * 80)
    for class_name, count in class_counts.most_common(30):
        print(f"  {class_name:50} → {count:4} occurrences")

    # Look for track-related classes
    print("\n🎵 Track-related classes:")
    print("-" * 80)
    track_related = [c for c in class_counts if any(word in c.lower() for word in ['track', 'song', 'item', 'row', 'card', 'list'])]
    for class_name in sorted(track_related)[:20]:
        count = class_counts[class_name]
        print(f"  {class_name:50} → {count:4} occurrences")

    # Analyze data attributes
    print("\n📦 Elements with data attributes:")
    print("-" * 80)
    data_attrs = set()
    for elem in soup.find_all(True):
        for attr in elem.attrs:
            if attr.startswith('data-'):
                data_attrs.add(attr)

    for attr in sorted(data_attrs)[:20]:
        elements = soup.find_all(attrs={attr: True})
        print(f"  {attr:50} → {len(elements):4} elements")

    # Look for potential track containers
    print("\n🎯 Potential track container elements:")
    print("-" * 80)

    # Check for li elements
    li_elements = soup.find_all('li')
    if li_elements:
        print(f"\n  Found {len(li_elements)} <li> elements")
        if len(li_elements) > 0:
            first_li = li_elements[0]
            print(f"  First <li> classes: {first_li.get('class', [])}")
            print(f"  First <li> attributes: {list(first_li.attrs.keys())}")

    # Check for divs with track-like classes
    track_divs = soup.find_all('div', class_=lambda x: x and any(word in str(x).lower() for word in ['track', 'item', 'card']))
    if track_divs:
        print(f"\n  Found {len(track_divs)} <div> elements with track-like classes")
        if len(track_divs) > 0:
            first_div = track_divs[0]
            print(f"  First div classes: {first_div.get('class', [])}")

    # Check for table rows
    tr_elements = soup.find_all('tr')
    if tr_elements:
        print(f"\n  Found {len(tr_elements)} <tr> elements")

    # Sample of first potential track element
    print("\n📝 Sample of first potential track element:")
    print("-" * 80)

    potential_track = None
    if track_divs:
        potential_track = track_divs[0]
    elif li_elements:
        potential_track = li_elements[0]
    elif tr_elements:
        potential_track = tr_elements[0]

    if potential_track:
        # Pretty print the element
        print(potential_track.prettify()[:2000])

        # Look for text content
        print("\n📄 Text content in element:")
        texts = [t.strip() for t in potential_track.stripped_strings]
        for i, text in enumerate(texts[:10]):
            print(f"  [{i}] {text}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_html.py <html_file>")
        sys.exit(1)

    analyze_html_structure(sys.argv[1])
