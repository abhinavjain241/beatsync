# Authentication Guide for Beatport Playlists

## The Problem

URLs like `https://www.beatport.com/library/playlists/XXXXXX` are **private playlists** that require you to be logged into your Beatport account. The scraper cannot access these without authentication.

## Solutions

### Option 1: Use Public Playlists (Recommended)

Instead of private library playlists, use **public Beatport charts or playlists**:

- Top 100: `https://www.beatport.com/charts/top-100`
- Genre charts: `https://www.beatport.com/genre/techno/6/charts`
- DJ charts: `https://www.beatport.com/dj/[dj-name]/[id]/charts`

These public pages don't require authentication.

### Option 2: Manual HTML Download

If you need to scrape your private playlists:

1. **Log into Beatport** in your browser
2. **Navigate to your playlist**
3. **Save the page**: Right-click → "Save Page As" → Save as "playlist.html"
4. **Run the scraper with the local file**:

```bash
python beatport_downloader.py
# When prompted for URL, press Enter to skip
# Then provide the path: playlist.html
```

### Option 3: Browser Cookie Authentication (Advanced)

You can manually add your Beatport session cookies to Selenium. This requires:

1. Log into Beatport in your browser
2. Copy your session cookies (use browser dev tools)
3. Add them to the Selenium driver before navigating to the page

Example code modification in `scraper.py`:

```python
def fetch_html(self, url: str, cookies: dict = None):
    # ... existing setup code ...

    self.driver.get("https://www.beatport.com")

    # Add cookies if provided
    if cookies:
        for name, value in cookies.items():
            self.driver.add_cookie({'name': name, 'value': value})

    # Now navigate to the actual URL
    self.driver.get(url)
    # ... rest of the code ...
```

## Debugging Tips

When the scraper runs, it saves the fetched HTML to `debug.html`. You can:

1. **Open debug.html** in a browser to see what the scraper sees
2. **Run the inspector** to analyze the HTML structure:
   ```bash
   python inspect_html.py
   ```

This will show you:
- Whether authentication is required
- What CSS selectors are present
- Potential track container elements

## Recommended Workflow

For the best experience:

1. **Test with public playlists first** to ensure the scraper works
2. **For private playlists**, use the manual HTML download method
3. Only attempt cookie authentication if you're comfortable with the technical complexity
