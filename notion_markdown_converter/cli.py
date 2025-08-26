import argparse
import json
import sys
from pathlib import Path

from .utils import extract_page_id
from .api import (
    fetch_page_full,
    fetch_page_as_payload,
    create_page_from_markdown,
    create_page_from_payload,
)
from .converters import (
    payload_to_markdown,
    api_to_payload,
)


def fetch_page_main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a Notion page and save it in various formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  notion-fetch \"https://notion.so/page-url\" --format api --output page.json\n"
            "  notion-fetch \"https://notion.so/page-url\" --format payload --output clean_page.json\n"
            "  notion-fetch \"https://notion.so/page-url\" --format markdown --output page.md\n"
        ),
    )

    parser.add_argument("page_url", help="URL of the Notion page to fetch")
    parser.add_argument(
        "--format",
        "-f",
        choices=["api", "payload", "markdown"],
        default="payload",
        help="Output format (default: payload)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output filename. If not provided, generates based on page ID and format",
    )

    args = parser.parse_args()

    page_id = extract_page_id(args.page_url)
    if not page_id:
        print("Error: Could not extract page ID from URL")
        sys.exit(1)

    print(f"Fetching page {page_id}...")

    try:
        if args.format == "api":
            data = fetch_page_full(page_id)
            extension = ".json"
            content = json.dumps(data, indent=2, ensure_ascii=False)
        elif args.format == "payload":
            data = fetch_page_as_payload(page_id)
            extension = ".json"
            content = json.dumps(data, indent=2, ensure_ascii=False)
        else:  # markdown
            payload = fetch_page_as_payload(page_id)
            content = payload_to_markdown(payload)
            extension = ".md"

        output_file = args.output or f"{page_id}_{args.format}{extension}"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def upload_page_main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a file to Notion as a new page (markdown, payload JSON, or API JSON)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  notion-upload document.md \"https://notion.so/parent-page-url\"\n"
            "  notion-upload page_payload.json \"https://notion.so/parent-db-url\" --type payload --parent-type database\n"
            "  notion-upload document.md \"https://notion.so/parent-db-url\" --type markdown --parent-type database --title \"My Title\"\n"
            "  notion-upload page_api.json \"https://notion.so/parent-page-url\" --type api --title \"My Title\"\n"
        ),
    )

    parser.add_argument("input_file", help="Path to the input file (Markdown, payload JSON, or API JSON)")
    parser.add_argument("parent_page_url", help="URL or ID of the parent Notion page or database")
    parser.add_argument("--title", "-t", help="Custom title for the page")
    parser.add_argument(
        "--type",
        "-T",
        choices=["markdown", "payload", "api"],
        help="Type of input file. If omitted, inferred from extension (.md → markdown, .json → payload)",
    )
    parser.add_argument(
        "--parent-type",
        "-p",
        choices=["page", "database"],
        default="page",
        help="Type of parent container (default: page).",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)

    parent_id = extract_page_id(args.parent_page_url)
    if not parent_id:
        print("Error: Could not extract page ID from parent URL")
        sys.exit(1)

    inferred_type = args.type
    if not inferred_type:
        ext = input_path.suffix.lower()
        if ext == ".md":
            inferred_type = "markdown"
        elif ext == ".json":
            inferred_type = "payload"
        else:
            print("Error: Unable to infer input type from extension. Please provide --type.")
            sys.exit(1)

    print(f"Uploading '{args.input_file}' to Notion as {inferred_type}...")

    try:
        if inferred_type == "markdown":
            content = input_path.read_text(encoding="utf-8")
            response = create_page_from_markdown(
                markdown_content=content,
                parent_id=parent_id,
                title=args.title,
                parent_type=("database" if args.parent_type == "database" else "page"),
            )
        elif inferred_type == "payload":
            payload_data = json.loads(input_path.read_text(encoding="utf-8"))
            if args.parent_type == "database":
                payload_data["parent"] = {"database_id": parent_id}
            else:
                payload_data["parent"] = {"page_id": parent_id}
            if args.title:
                payload_data["properties"] = {
                    "title": {"title": [{"text": {"content": args.title}}]}
                }
            response = create_page_from_payload(payload_data)
        else:  # api
            api_data = json.loads(input_path.read_text(encoding="utf-8"))
            payload = api_to_payload(api_data)
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

        print("Successfully created Notion page!")
        print(f"Page URL: {response['url']}")
        print(f"Page ID: {response['id']}")
    except Exception as e:
        print(f"Error creating page: {e}")
        sys.exit(1)


