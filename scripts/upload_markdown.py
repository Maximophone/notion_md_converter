#!/usr/bin/env python3
"""
Upload a Markdown file to Notion as a new page.

This script takes a Markdown file and creates a new Notion page under a specified parent.

Usage:
    python upload_markdown.py <markdown_file> <parent_page_url> [--title "Custom Title"]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion_markdown_converter.utils import extract_page_id
from notion_markdown_converter.api import create_page_from_markdown


def main():
    parser = argparse.ArgumentParser(
        description="Upload a Markdown file to Notion as a new page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python upload_markdown.py document.md "https://notion.so/parent-page-url"
    python upload_markdown.py document.md "https://notion.so/parent-page-url" --title "My Custom Title"
        """
    )
    
    parser.add_argument(
        "markdown_file",
        help="Path to the Markdown file to upload"
    )
    
    parser.add_argument(
        "parent_page_url", 
        help="URL of the parent Notion page"
    )
    
    parser.add_argument(
        "--title", "-t",
        help="Custom title for the page. If not provided, extracts from first # heading in markdown"
    )
    
    args = parser.parse_args()
    
    # Validate markdown file exists
    markdown_path = Path(args.markdown_file)
    if not markdown_path.exists():
        print(f"Error: Markdown file '{args.markdown_file}' not found")
        sys.exit(1)
    
    # Extract parent page ID from URL
    parent_id = extract_page_id(args.parent_page_url)
    if not parent_id:
        print("Error: Could not extract page ID from parent URL")
        sys.exit(1)
    
    # Read markdown content
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        sys.exit(1)
    
    print(f"Uploading '{args.markdown_file}' to Notion...")
    
    try:
        # Create the page
        response = create_page_from_markdown(
            markdown_content=markdown_content,
            parent_id=parent_id,
            title=args.title
        )
        
        print("Successfully created Notion page!")
        print(f"Page URL: {response['url']}")
        print(f"Page ID: {response['id']}")
        
    except Exception as e:
        print(f"Error creating page: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()