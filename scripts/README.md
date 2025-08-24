# Scripts

This directory contains utility scripts for working with Notion pages and Markdown conversion.

## Available Scripts

### `fetch_page.py`
Fetch a Notion page and save it in various formats.

```bash
# Fetch as clean payload (default)
python scripts/fetch_page.py "https://notion.so/your-page-url"

# Fetch as raw API response
python scripts/fetch_page.py "https://notion.so/your-page-url" --format api --output raw_page.json

# Fetch as Markdown
python scripts/fetch_page.py "https://notion.so/your-page-url" --format markdown --output page.md
```

**Formats:**
- `api`: Raw JSON response from Notion API (includes IDs, timestamps, etc.)
- `payload`: Clean JSON suitable for page creation (default)
- `markdown`: Converted to Markdown format

### `upload_markdown.py`
Upload a Markdown file to Notion as a new page.

```bash
# Upload with title extracted from first # heading
python scripts/upload_markdown.py document.md "https://notion.so/parent-page-url"

# Upload with custom title
python scripts/upload_markdown.py document.md "https://notion.so/parent-page-url" --title "My Custom Title"
```

## Setup

Make sure you have:
1. Set the `NOTION_TOKEN` environment variable with your Notion integration token
2. Shared the relevant pages with your integration
3. Installed the required dependencies (`pip install -r requirements.txt`)

## Examples

```bash
# Complete workflow: fetch, modify, and re-upload
python scripts/fetch_page.py "https://notion.so/source-page" --format markdown --output temp.md
# ... edit temp.md ...
python scripts/upload_markdown.py temp.md "https://notion.so/target-parent-page"
```