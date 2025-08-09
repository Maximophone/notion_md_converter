import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def clean_block(block):
    """
    Removes fields from a block object that are not allowed when creating new content.
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
        # Recursively clean nested blocks if any (e.g., in a toggle block)
        if "children" in block[block_type]:
            block[block_type]["children"] = [clean_block(child) for child in block[block_type]["children"]]

    return block

def main():
    """
    Transforms the fetched Notion page JSON into a format suitable for creating a new page.
    """
    input_filename = "page_content.json"
    output_filename = "upload_payload.json"
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")

    if not parent_page_id:
        print("Error: Please set NOTION_PARENT_PAGE_ID in your .env file.")
        print("This should be the ID of the page where you want to create the new page.")
        return

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

        # Save the transformed payload to a new JSON file
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(upload_payload, f, ensure_ascii=False, indent=4)

        print(f"Successfully transformed JSON. Payload saved to {output_filename}")
        print("You can now use this file to create a new page with the Notion API.")

    except FileNotFoundError:
        print(f"Error: The file {input_filename} was not found.")
        print("Please run `fetch_page.py` first to generate it.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_filename}.")

if __name__ == "__main__":
    main()