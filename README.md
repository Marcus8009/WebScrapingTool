# Decent Web Scraper

A robust web scraper built with Selenium and undetected-chromedriver that handles transcript buttons and extracts content from web pages.

## Features

- Scrapes content from web pages using undetected-chromedriver
- Handles "Show Transcript" buttons automatically
- Manages popups and cookie notices
- Extracts both transcript content and paragraph text
- Separates content into short (<500 words) and long (≥500 words) categories
- Implements smart delays to avoid rate limiting
- Saves content with detailed metadata

## Setup

1. Install Python dependencies:
```bash
pip install requirements.txt
```

2. Ensure Google Chrome is installed on your system
3. Configure your URLs in `urls.py`

## URL Configuration

Create a `urls.py` file based on the template `templateurls.py`. Avoid grouping your website like in `badtemplateurls.py`. Structure your URLs as follows:

```python
urls = [
    {
        "url": "https://example.com/page1",
        "source": "Source Name 1"
    },
    {
        "url": "https://example.com/page2",
        "source": "Source Name 2"
    }
]
```

## Developer Notes

1. URL Management:
   - Add your target URLs in `urls.py`
   - Use `templateurls.py` as a template for proper formatting
   - URLs should be structured as a list of dictionaries with `url` and `source` keys

2. Rate Limiting Prevention:
   - Organize URLs from different domains sequentially
   - Avoid clustering multiple URLs from the same domain together (See badtemplateurls.py)
   - The scraper implements random delays between requests (4-9 seconds)

3. File Naming Convention:
   - Output files are named after the URL
   - `https://` and `http://` are removed
   - Forward slashes `/` are converted to `#` for easy URL reconstruction
   - Example: `example.com#page1.txt`

## Output Structure

The scraper creates two directories:
- `scraped_transcripts_short/`: For content with <500 words
- `scraped_transcripts_long/`: For content with ≥500 words

Note: Due to website rate limiters and blocking, some transcripts may be incorrectly categorized in `scraped_transcripts_short/`. To address this:
1. Review failed scrapes in `scraped_transcripts_short/`
2. Edit `urls.py` to include only the failed URLs and retry
3. Create an `OkayShort/` folder inside `scraped_transcripts_short/` for legitimate short transcripts
4. Move verified short transcripts to the `OkayShort/` folder

Under normal circumstances, the majority of transcripts should appear in `scraped_transcripts_long/`. Manual verification is recommended to ensure proper categorization.

Each output file contains:
- URL and source information
- Total word count
- Transcript content (if found)
- Page paragraph content
- Individual word counts for transcript and paragraph sections

## Usage

Run the scraper:
```bash
python app.py
```

The script will process all URLs and provide progress updates and a summary of successful/failed scrapes.
