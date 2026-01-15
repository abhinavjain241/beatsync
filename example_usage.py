#!/usr/bin/env python3
"""
Example usage of the Beatport Playlist Downloader.

This demonstrates how to use the downloader programmatically.
"""

from beatport_downloader import BeatportPlaylistDownloader


def example_1_with_url():
    """Example: Download from a Beatport URL."""
    print("Example 1: Download from URL")
    print("-" * 40)

    # Replace with your actual Beatport playlist URL
    url = "https://www.beatport.com/chart/your-playlist-url"

    downloader = BeatportPlaylistDownloader(output_dir='downloads')
    downloader.run(url)


def example_2_interactive():
    """Example: Interactive mode (prompt for URL)."""
    print("Example 2: Interactive Mode")
    print("-" * 40)

    downloader = BeatportPlaylistDownloader(output_dir='downloads')
    downloader.run()  # Will prompt for URL


def example_3_custom_output():
    """Example: Use custom output directory."""
    print("Example 3: Custom Output Directory")
    print("-" * 40)

    # Download to a custom directory
    downloader = BeatportPlaylistDownloader(output_dir='my_music')
    downloader.run()


if __name__ == '__main__':
    # Uncomment the example you want to run:

    # example_1_with_url()
    # example_2_interactive()
    # example_3_custom_output()

    print("Uncomment one of the examples in example_usage.py to run it.")
