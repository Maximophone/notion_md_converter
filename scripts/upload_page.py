#!/usr/bin/env python3
"""
Upload a file to Notion as a new page.

This script can take one of three input types and create a page under the specified parent:
- Markdown file
- Payload JSON (clean Notion create payload)
- API JSON (raw Notion API page or blocks; will be cleaned first)

Usage:
    python upload_page.py <input_file> <parent_url_or_id> [--type markdown|payload|api] [--parent-type page|database] [--title "Custom Title"]
"""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output for help text on Windows consoles
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion_markdown_converter.utils import extract_page_id
from notion_markdown_converter.api import create_page_from_markdown, create_page_from_payload
from notion_markdown_converter.converters import markdown_to_payload, api_to_payload


def main():
    parser = argparse.ArgumentParser(
        description="Upload a file to Notion as a new page (markdown, payload JSON, or API JSON)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python upload_page.py document.md "https://notion.so/parent-page-url"
    python upload_page.py page_payload.json "https://notion.so/parent-db-url" --type payload --parent-type database
    python upload_page.py page_api.json "https://notion.so/parent-page-url" --type api --title "My Custom Title"
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Path to the input file (Markdown, payload JSON, or API JSON)"
    )
    
    parser.add_argument(
        "parent_page_url", 
        help="URL or ID of the parent Notion page or database"
    )
    
    parser.add_argument(
        "--title", "-t",
        help="Custom title for the page. If not provided, extracts from first # heading in markdown"
    )
    
    parser.add_argument(
        "--type", "-T",
        choices=["markdown", "payload", "api"],
        help="Type of input file. If omitted, inferred from extension (.md → markdown, .json → payload)"
    )
    
    parser.add_argument(
        "--parent-type", "-p",
        choices=["page", "database"],
        default="page",
        help="Type of parent container (default: page). Use 'database' to create inside a database."
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    # Extract parent page ID from URL
    parent_id = extract_page_id(args.parent_page_url)
    if not parent_id:
        print("Error: Could not extract page ID from parent URL")
        sys.exit(1)

    # Infer input type if not provided
    inferred_type = None
    if args.type:
        inferred_type = args.type
    else:
        ext = input_path.suffix.lower()
        if ext == ".md":
            inferred_type = "markdown"
        elif ext == ".json":
            inferred_type = "payload"  # default assumption for .json
        else:
            print("Error: Unable to infer input type from extension. Please provide --type.")
            sys.exit(1)

    print(f"Uploading '{args.input_file}' to Notion as {inferred_type}...")

    try:
        if inferred_type == "markdown":
            # For database parent, build payload ourselves to set database_id
            content = input_path.read_text(encoding='utf-8')
            if args.parent_type == "database":
                payload = markdown_to_payload(content)
                payload["parent"] = {"database_id": parent_id}
                if args.title:
                    payload["properties"] = {
                        "title": {
                            "title": [{"text": {"content": args.title}}]
                        }
                    }
                response = create_page_from_payload(payload)
            else:
                response = create_page_from_markdown(
                    markdown_content=content,
                    parent_id=parent_id,
                    title=args.title
                )

        elif inferred_type == "payload":
            import json
            payload = json.loads(input_path.read_text(encoding='utf-8'))
            # Ensure parent is set correctly
            if args.parent_type == "database":
                payload["parent"] = {"database_id": parent_id}
            else:
                payload["parent"] = {"page_id": parent_id}
            # Optional title override
            if args.title:
                payload["properties"] = {
                    "title": {
                        "title": [{"text": {"content": args.title}}]
                    }
                }
            response = create_page_from_payload(payload)

        elif inferred_type == "api":
            import json
            api_data = json.loads(input_path.read_text(encoding='utf-8'))
            payload = api_to_payload(api_data)
            # Set parent and optional title
            if args.parent_type == "database":
                payload["parent"] = {"database_id": parent_id}
            else:
                payload["parent"] = {"page_id": parent_id}
            if args.title:
                payload.setdefault("properties", {})
                payload["properties"]["title"] = {
                    "title": [{"text": {"content": args.title}}]
                }
            response = create_page_from_payload(payload)

        else:
            print(f"Error: Unsupported type '{inferred_type}'")
            sys.exit(1)

        print("Successfully created Notion page!")
        print(f"Page URL: {response['url']}")
        print(f"Page ID: {response['id']}")

    except Exception as e:
        print(f"Error creating page: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()