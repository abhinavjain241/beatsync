"""
Extract and analyze track data from Beatport HTML file.
"""
import json
import re

with open('basshouse_t100.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for __NEXT_DATA__ JSON
pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
match = re.search(pattern, html, re.DOTALL)

if match:
    json_str = match.group(1)
    try:
        data = json.loads(json_str)

        # Pretty print structure
        print("Found __NEXT_DATA__ JSON!")
        print("\nTop-level keys:", list(data.keys()))

        # Navigate to find tracks
        if 'props' in data:
            print("\nprops keys:", list(data['props'].keys()))
            if 'pageProps' in data['props']:
                print("pageProps keys:", list(data['props']['pageProps'].keys()))

                # Look for playlist or tracks data
                page_props = data['props']['pageProps']
                for key in page_props:
                    if 'track' in key.lower() or 'playlist' in key.lower():
                        print(f"\nFound key: {key}")
                        print(f"Type: {type(page_props[key])}")
                        if isinstance(page_props[key], dict):
                            print(f"Sub-keys: {list(page_props[key].keys())}")
                        elif isinstance(page_props[key], list) and len(page_props[key]) > 0:
                            print(f"List with {len(page_props[key])} items")
                            print(f"First item keys: {list(page_props[key][0].keys()) if isinstance(page_props[key][0], dict) else 'Not a dict'}")

                # Try to find the tracks array
                if 'dehydratedState' in page_props:
                    print("\n=== Dehydrated State Found ===")
                    dehydrated = page_props['dehydratedState']
                    if 'queries' in dehydrated:
                        print(f"Found {len(dehydrated['queries'])} queries")
                        for i, query in enumerate(dehydrated['queries'][:3]):
                            print(f"\nQuery {i}:")
                            if 'state' in query and 'data' in query['state']:
                                state_data = query['state']['data']
                                print(f"  Data keys: {list(state_data.keys()) if isinstance(state_data, dict) else type(state_data)}")
                                if isinstance(state_data, dict) and 'results' in state_data:
                                    results = state_data['results']
                                    print(f"  Results type: {type(results)}")
                                    if isinstance(results, list):
                                        print(f"  Number of results: {len(results)}")
                                        if len(results) > 0:
                                            print(f"  First result keys: {list(results[0].keys())}")
                                            print(f"\n  SAMPLE TRACK DATA:")
                                            print(json.dumps(results[0], indent=2)[:1000])

                # Save full JSON to file for inspection
                with open('beatport_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                print("\n\nSaved full JSON to beatport_data.json")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
else:
    print("No __NEXT_DATA__ found")
