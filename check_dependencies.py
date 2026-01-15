#!/usr/bin/env python3
"""
Check if all required dependencies are installed.
Run this before using the Beatport downloader.
"""

import sys
import subprocess


def check_python_module(module_name, package_name=None):
    """Check if a Python module is installed."""
    if package_name is None:
        package_name = module_name

    try:
        __import__(module_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False


def check_command(command_name):
    """Check if a command-line tool is installed."""
    try:
        result = subprocess.run(
            [command_name, '--version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ {command_name} is installed")
            return True
        else:
            print(f"✗ {command_name} is NOT installed")
            return False
    except FileNotFoundError:
        print(f"✗ {command_name} is NOT installed")
        return False
    except Exception:
        print(f"? {command_name} check failed")
        return False


def main():
    """Check all dependencies."""
    print("=" * 60)
    print("Checking Beatport Downloader Dependencies")
    print("=" * 60)
    print()

    all_ok = True

    print("Python Modules:")
    print("-" * 60)
    all_ok &= check_python_module('requests')
    all_ok &= check_python_module('bs4', 'beautifulsoup4')
    all_ok &= check_python_module('yt_dlp', 'yt-dlp')
    all_ok &= check_python_module('lxml')

    print()
    print("Command-line Tools:")
    print("-" * 60)
    all_ok &= check_command('yt-dlp')
    all_ok &= check_command('ffmpeg')

    print()
    print("=" * 60)
    if all_ok:
        print("✓ All dependencies are installed!")
        print()
        print("You're ready to use the Beatport downloader.")
        print("Run: python beatport_downloader.py")
    else:
        print("✗ Some dependencies are missing.")
        print()
        print("To install Python dependencies, run:")
        print("  pip install -r requirements.txt")
        print()
        print("To install ffmpeg:")
        print("  macOS:    brew install ffmpeg")
        print("  Ubuntu:   sudo apt install ffmpeg")
        print("  Windows:  Download from https://ffmpeg.org/download.html")
    print("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
