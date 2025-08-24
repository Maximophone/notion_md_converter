#!/usr/bin/env python3
"""
Fetch a Notion page and save it in various formats.

This script retrieves a page from Notion and can save it as:
- API response (raw JSON from Notion API)  
- Payload (clean JSON suitable for creation)
- Markdown content

Usage:
    python fetch_page.py <page_url> [--format api|payload|markdown] [--output filename]
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion_markdown_converter.utils import extract_page_id
from notion_markdown_converter.api import fetch_page_full, fetch_page_as_payload
from notion_markdown_converter.converters import payload_to_markdown


def main():
    parser = argparse.ArgumentParser(
        description="Fetch a Notion page and save it in various formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fetch_page.py "https://notion.so/page-url" --format api --output page.json
    python fetch_page.py "https://notion.so/page-url" --format payload --output clean_page.json
    python fetch_page.py "https://notion.so/page-url" --format markdown --output page.md
        """
    )
    
    parser.add_argument(
        "page_url",
        help="URL of the Notion page to fetch"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["api", "payload", "markdown"],
        default="payload",
        help="Output format (default: payload)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output filename. If not provided, generates based on page ID and format"
    )
    
    args = parser.parse_args()
    
    # Extract page ID from URL
    page_id = extract_page_id(args.page_url)
    if not page_id:
        print("Error: Could not extract page ID from URL")
        sys.exit(1)
    
    print(f"Fetching page {page_id}...")
    
    try:
        if args.format == "api":
            # Fetch raw API response
            data = fetch_page_full(page_id)
            extension = ".json"
            content = json.dumps(data, indent=2, ensure_ascii=False)
            
        elif args.format == "payload":
            # Fetch and convert to clean payload
            data = fetch_page_as_payload(page_id)
            extension = ".json"
            content = json.dumps(data, indent=2, ensure_ascii=False)
            
        elif args.format == "markdown":
            # Fetch, convert to payload, then to markdown
            payload = fetch_page_as_payload(page_id)
            content = payload_to_markdown(payload)
            extension = ".md"
        
        # Determine output filename
        if args.output:
            output_file = args.output
        else:
            output_file = f"{page_id}_{args.format}{extension}"
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()