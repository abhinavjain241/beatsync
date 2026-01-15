#!/usr/bin/env python3
"""
Test script to demonstrate the improved track matching algorithm.
"""

from downloader import AudioDownloader

def test_matching():
    """Test the improved matching algorithm with various track name patterns."""
    downloader = AudioDownloader()

    test_cases = [
        {
            'query': 'Westend, SIDEPIECE - Take Your Places Extended Mix',
            'candidates': [
                'Westend & SIDEPIECE - Take Your Places (Extended Mix)',
                'Take Your Places - Westend SIDEPIECE Extended Mix',
                'Westend feat SIDEPIECE - Take Your Places Extended',
                'DJ Mix - Take Your Places (Some Other Remix)',
            ]
        },
        {
            'query': 'Sean Paul, Odd Mob - Get Busy Odd Mob Extended Club Mix',
            'candidates': [
                'Sean Paul - Get Busy (Odd Mob Extended Club Mix)',
                'Sean Paul & Odd Mob - Get Busy Extended Club Mix',
                'Get Busy - Odd Mob Extended Club Mix feat Sean Paul',
                'Sean Paul - Get Busy (Different Remix)',
            ]
        },
        {
            'query': 'Chris Lake, Skrillex, ANITA B QUEEN - LA NOCHE Extended Mix',
            'candidates': [
                'Chris Lake, Skrillex & ANITA B QUEEN - LA NOCHE (Extended Mix)',
                'LA NOCHE Extended Mix - Chris Lake feat Skrillex',
                'Chris Lake - LA NOCHE (Radio Edit)',
                'LA NOCHE - Skrillex x Chris Lake Extended',
            ]
        }
    ]

    print("=" * 80)
    print("Testing Improved Track Matching Algorithm")
    print("=" * 80)
    print()

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['query']}")
        print("-" * 80)

        scores = []
        for candidate in test['candidates']:
            score = downloader.calculate_match_score(test['query'], candidate)
            scores.append((candidate, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        for candidate, score in scores:
            match_indicator = "✓✓✓" if score >= 0.8 else "✓✓" if score >= 0.6 else "✓" if score >= 0.4 else "✗"
            print(f"  {match_indicator} {score:.0%} - {candidate}")

        print()

    print("=" * 80)
    print("Component Extraction Test")
    print("=" * 80)
    print()

    extraction_tests = [
        'Westend, SIDEPIECE - Take Your Places Extended Mix',
        'Sean Paul - Get Busy (Odd Mob Extended Club Mix)',
        'Chris Lake x Skrillex feat ANITA B QUEEN - LA NOCHE (Extended Mix)',
        'Anti Up - I Cannot Extended Mix',
    ]

    for track in extraction_tests:
        components = downloader.extract_track_components(track)
        print(f"Track: {track}")
        print(f"  Artists: {', '.join(components['artists'])}")
        print(f"  Track Name: {components['track_name']}")
        print(f"  Mix Info: {', '.join(components['mix_info']) if components['mix_info'] else 'None'}")
        print()

if __name__ == '__main__':
    test_matching()
