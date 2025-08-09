import os
import json
from dotenv import load_dotenv
from notion_client import Client, APIResponseError
from utils import extract_page_id
import argparse

# Load environment variables from .env file
load_dotenv()

def clean_block(block):
    """
    Removes fields from a block object that are not allowed when creating new content.
    This version correctly handles nested blocks.
    """
    # Fields to remove from the top-level of the block object
    block.pop("id", None)
    block.pop("parent", None)
    block.pop("created_time", None)
    block.pop("last_edited_time", None)
    block.pop("created_by", None)
    block.pop("last_edited_by", None)
    block.pop("has_children", None)
    block.pop("archived", None)

    # The type of the block (e.g., 'paragraph', 'heading_1') contains the content
    block_type = block.get("type")
    if block_type and block_type in block:
        # If the block type has a 'children' key, recursively clean them.
        # This is the correct way to handle nested blocks (e.g., in toggles, lists).
        if "children" in block[block_type]:
            block[block_type]["children"] = [clean_block(child) for child in block[block_type]["children"]]

    # Also, if there's a top-level 'children' key from our recursive fetch, clean it.
    if "children" in block:
        block[block.get("type")]["children"] = [clean_block(child) for child in block.pop("children")]

    return block

def create_notion_page(payload, notion_client):
    """
    Creates a new page in Notion using the provided payload.
    It handles the 100 block limit by creating the page with the first 100 blocks
    and then appending the rest.
    """
    children = payload.pop("children", [])
    
    # Create the page with the first chunk of children
    payload["children"] = children[:100]

    try:
        response = notion_client.pages.create(**payload)
        print("Successfully created new Notion page!")
        print(f"Page URL: {response['url']}")

        # If there are more blocks, append them in chunks
        if len(children) > 100:
            new_page_id = response["id"]
            for i in range(100, len(children), 100):
                chunk = children[i:i+100]
                print(f"Appending {len(chunk)} more blocks...")
                notion_client.blocks.children.append(
                    block_id=new_page_id,
                    children=chunk
                )
            print("All blocks appended successfully.")

        return response
    except APIResponseError as e:
        print(f"Error creating Notion page: {e}")
        return None

def main():
    """
    Transforms a JSON file of Notion blocks and creates a new page from it.
    """
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        source_page_url = config.get("source_page_url")
        parent_page_url = config.get("parent_page_url")
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

    if not source_page_url or "YOUR_SOURCE_PAGE_URL_HERE" in source_page_url:
        print("Error: Please set 'source_page_url' in your config.json file.")
        return
        
    if not parent_page_url or "YOUR_PARENT_PAGE_URL_HERE" in parent_page_url:
        print("Error: Please set 'parent_page_url' in your config.json file.")
        return

    source_page_id = extract_page_id(source_page_url)
    parent_page_id = extract_page_id(parent_page_url)

    if not source_page_id:
        print("Error: Invalid Page ID extracted from source_page_url.")
        return
    if not parent_page_id:
        print("Error: Invalid Page ID extracted from parent_page_url.")
        return

    input_filename = f"{source_page_id}.json"
    output_filename = f"upload_payload_{source_page_id}.json"

    # Initialize the Notion client
    notion = Client(auth=notion_token)

    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            original_blocks = json.load(f)

        # Clean each block to prepare it for upload
        cleaned_blocks = [clean_block(block) for block in original_blocks]

        # Construct the payload for creating a new page
        upload_payload = {
            "parent": {
                "page_id": parent_page_id
            },
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": "My New Page from API"
                            }
                        }
                    ]
                }
            },
            "children": cleaned_blocks
        }

        # Save the transformed payload for debugging
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(upload_payload, f, ensure_ascii=False, indent=4)
        print(f"Payload for new page saved to {output_filename}")

        # Create the new page in Notion
        create_notion_page(upload_payload, notion)

    except FileNotFoundError:
        print(f"Error: The file {input_filename} was not found.")
        print("Please run `fetch_page.py` first to generate it.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_filename}.")

if __name__ == "__main__":
    main()