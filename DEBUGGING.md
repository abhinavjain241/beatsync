# Debugging Beatport Downloader Issues

This guide helps diagnose and fix issues with the Beatport downloader.

## Common Issue: "Process exited with code 1" / No tracks found

This usually means the scraper couldn't extract track information from the Beatport page.

### Quick Diagnosis

Run the debug script to see what's happening:

```bash
python debug_beatport.py "https://www.beatport.com/chart/your-playlist-url"
```

This will show:
- Whether the page was fetched successfully
- What HTML elements were found
- Sample track structure
- Why tracks might not be extracting

### Common Causes

1. **Beatport Changed Their HTML Structure**
   - Beatport frequently updates their website
   - The selectors in `scraper.py` may need updating
   - Solution: Check the debug output and update the selectors

2. **JavaScript-Loaded Content**
   - Modern Beatport pages may load content via JavaScript
   - The raw HTML doesn't contain track data
   - Solution: Use browser dev tools to save the full rendered page

3. **Anti-Scraping Measures**
   - Beatport may be blocking automated requests
   - You may get a CAPTCHA or error page
   - Solution: Save the page manually from your browser

### Testing from Command Line

Test the downloader without the web interface:

```bash
# Web-optimized version (no prompts)
python beatport_downloader_web.py "https://www.beatport.com/chart/..."

# Interactive version
python beatport_downloader.py "https://www.beatport.com/chart/..."
```

### Using a Saved HTML File

If direct URL fetching fails:

1. **Open the Beatport playlist in your browser**
2. **Save the page:**
   - Chrome: Right-click → "Save as" → "Webpage, Complete"
   - Firefox: File → "Save Page As" → "Web Page, complete"
3. **Use the saved file:**

```bash
# Interactive version supports local files
python beatport_downloader.py
# When prompted, enter the path to your saved HTML file
```

### Checking What the Scraper Sees

Add debug output to see what the scraper is finding:

```python
# In scraper.py, add this after line 76:
print(f"HTML snippet: {html[:500]}")  # First 500 chars
```

### Common Beatport URL Formats

Make sure you're using the correct URL format:

```
✓ https://www.beatport.com/chart/top-100/...
✓ https://www.beatport.com/chart/...
✗ https://beatport.com/...  (missing www)
✗ http://www.beatport.com/...  (use https)
```

### Web Interface Debugging

When using the web interface and getting errors:

1. **Check the server console output:**
   - Look for Python error messages
   - Check what HTML elements were found
   - See if tracks were parsed

2. **Check browser console (F12):**
   - Look for network errors
   - Check the API response

3. **Test the Python script directly:**
   ```bash
   python beatport_downloader_web.py "your-url-here"
   ```

### Fixing Scraper Selectors

If Beatport changed their HTML, update `scraper.py`:

1. **Run the debug script** to see current structure
2. **Identify the new selectors** for:
   - Track containers (div, li, tr elements)
   - Artist names
   - Track titles
   - Remix info

3. **Add new selectors to `scraper.py`:**

```python
# In parse_tracks() method
if not track_elements:
    track_elements = soup.find_all('div', class_='new-track-class')
    print(f"New method: Found {len(track_elements)} elements")
```

4. **Test your changes:**

```bash
python beatport_downloader_web.py "test-url"
```

### Getting Help

If you're still stuck:

1. Run `python debug_beatport.py <url>` and save the output
2. Check if Beatport loads content dynamically (view source vs. inspect element)
3. Try saving the page as HTML and using the local file option
4. Check that all dependencies are installed: `python check_dependencies.py`

### Verification Checklist

- [ ] Python 3.7+ is installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] ffmpeg is installed
- [ ] yt-dlp is installed
- [ ] URL is valid and accessible in browser
- [ ] Network connection is working
- [ ] Not behind a proxy/firewall blocking requests

## Advanced Debugging

### Enable Verbose Logging

Add verbose output to track the flow:

```python
# In beatport_downloader_web.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Save Fetched HTML

To inspect what HTML is being fetched:

```python
# In scraper.py, after line 42:
with open('debug_output.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Saved HTML to debug_output.html")
```

### Check HTTP Response

See what Beatport is actually returning:

```python
# In scraper.py, after line 40:
print(f"Status code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Content length: {len(response.text)}")
```

## Environment Issues

### Python Not Found

```bash
# Try different Python commands
python3 beatport_downloader_web.py "url"
python beatport_downloader_web.py "url"
py beatport_downloader_web.py "url"  # Windows
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission Errors

```bash
# Make scripts executable (Unix/Mac)
chmod +x beatport_downloader_web.py
chmod +x debug_beatport.py
```
