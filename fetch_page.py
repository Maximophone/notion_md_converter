import os
import json
from dotenv import load_dotenv
from notion_client import Client, APIResponseError
from utils import extract_page_id

# Load environment variables from .env file
load_dotenv()

def get_all_blocks(client, page_id):
    """
    Retrieve all blocks from a Notion page, handling pagination and recursion.
    """
    all_blocks = []
    start_cursor = None
    while True:
        response = client.blocks.children.list(
            block_id=page_id,
            start_cursor=start_cursor,
            page_size=100  # Max page size
        )
        results = response.get("results", [])
        for block in results:
            if block["has_children"]:
                block["children"] = get_all_blocks(client, block["id"])
        all_blocks.extend(results)
        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")
    return all_blocks

def main():
    """
    Main function to fetch Notion page content and save it to a JSON file.
    """
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        raw_page_id = config.get("source_page_url")
    except FileNotFoundError:
        print("Error: config.json not found. Please create it from config.json.example.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from config.json.")
        return

    notion_token = os.getenv("NOTION_TOKEN")

    if not notion_token:
        print("Error: Please set NOTION_TOKEN in your .env file.")
        return

    if not raw_page_id or "YOUR_SOURCE_PAGE_URL_HERE" in raw_page_id:
        print("Error: Please set 'source_page_url' in your config.json file.")
        return

    notion_page_id = extract_page_id(raw_page_id)
    print(f"Extracted Page ID: {notion_page_id}")
    print("----------------------")


    if not notion_page_id:
        print("Error: Invalid Page ID extracted from source_page_url.")
        return

    try:
        # Initialize the Notion client
        notion = Client(auth=notion_token)

        print(f"Fetching content for page: {notion_page_id}")
        
        # Retrieve all block children from the page
        page_content = get_all_blocks(notion, notion_page_id)

        # Save the content to a JSON file named after the page ID
        output_filename = f"{notion_page_id}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(page_content, f, ensure_ascii=False, indent=4)

        print(f"Successfully saved page content to {output_filename}")

    except APIResponseError as e:
        print(f"Error fetching data from Notion API: {e}")
        print("Please check the following:")
        print("1. Your NOTION_TOKEN is correct.")
        print("2. The page has been shared with your integration.")
        print("3. The 'source_page_url' in config.json is correct.")

if __name__ == "__main__":
    main()