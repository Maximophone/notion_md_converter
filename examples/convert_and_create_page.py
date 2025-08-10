import os
import sys
import json
from dotenv import load_dotenv
from notion_client import Client, APIResponseError
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from notion_markdown_converter import extract_page_id

# Load environment variables from .env file
load_dotenv()

def clean_rich_text(rich_text_array):
    """
    Cleans a rich_text array to only include properties valid for creation.
    Preserves mentions (e.g., user mentions) with the minimal allowed shape.
    """
    cleaned_array = []

    def _clean_rich_text_item(item):
        item_type = item.get("type")
        annotations = item.get("annotations")

        if item_type == "text":
            cleaned_item = {
                "type": "text",
                "text": {
                    "content": item.get("text", {}).get("content", ""),
                },
            }
            # Only add link if it exists and is not None
            link_value = item.get("text", {}).get("link")
            if link_value:
                cleaned_item["text"]["link"] = link_value
            if annotations:
                cleaned_item["annotations"] = annotations
            return cleaned_item

        if item_type == "mention":
            mention = item.get("mention", {})
            mention_type = mention.get("type")
            cleaned_mention = {"type": mention_type} if mention_type else {}

            if mention_type == "user":
                user_id = (
                    mention.get("user", {}).get("id")
                    if isinstance(mention.get("user"), dict)
                    else None
                )
                if user_id:
                    cleaned_mention["user"] = {"id": user_id}
            elif mention_type == "page":
                page_id = (
                    mention.get("page", {}).get("id")
                    if isinstance(mention.get("page"), dict)
                    else None
                )
                if page_id:
                    cleaned_mention["page"] = {"id": page_id}
            elif mention_type == "database":
                database_id = (
                    mention.get("database", {}).get("id")
                    if isinstance(mention.get("database"), dict)
                    else None
                )
                if database_id:
                    cleaned_mention["database"] = {"id": database_id}
            elif mention_type == "date":
                # Date mention can be preserved as-is
                if isinstance(mention.get("date"), dict):
                    cleaned_mention["date"] = mention["date"]

            cleaned_item = {"type": "mention", "mention": cleaned_mention}
            if annotations:
                cleaned_item["annotations"] = annotations
            return cleaned_item

        if item_type == "equation":
            expr = item.get("equation", {}).get("expression", "")
            cleaned_item = {"type": "equation", "equation": {"expression": expr}}
            if annotations:
                cleaned_item["annotations"] = annotations
            return cleaned_item

        # Fallback: coerce to text if possible
        fallback_text = item.get("plain_text") or item.get("text", {}).get("content", "")
        cleaned_item = {
            "type": "text",
            "text": {"content": fallback_text or ""},
        }
        if annotations:
            cleaned_item["annotations"] = annotations
        return cleaned_item

    for item in rich_text_array or []:
        cleaned_item = _clean_rich_text_item(item)
        # Drop truly empty text nodes to avoid unexpected API errors
        if cleaned_item.get("type") == "text" and not cleaned_item.get("text", {}).get("content") and not cleaned_item.get("text", {}).get("link"):
            continue
        cleaned_array.append(cleaned_item)

    return cleaned_array


def _flatten_grouping_blocks(children):
    """
    Flattens grouping-only wrapper blocks (e.g., bulleted_list, numbered_list)
    by replacing them with their children. Notion API does not accept these wrappers
    when creating content; it expects the individual *_list_item blocks directly.
    """
    if not isinstance(children, list):
        return children
    flattened = []
    for child in children:
        block_type = child.get("type")
        if block_type in {"bulleted_list", "numbered_list"}:
            # Hoist the children of the grouping block from either top-level or under the type key
            nested = []
            if isinstance(child.get("children"), list):
                nested = child.get("children", [])
            elif isinstance(child.get(block_type), dict) and isinstance(child[block_type].get("children"), list):
                nested = child[block_type].get("children", [])
            for nested_child in nested:
                flattened.append(nested_child)
        else:
            flattened.append(child)
    return flattened


def clean_block(block):
    """
    Removes fields from a block object that are not allowed when creating new content.
    This version includes a workaround for a Notion API bug with code block line breaks.
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
    block.pop("object", None)
    block.pop("in_trash", None)

    block_type = block.get("type")

    # Workaround for Notion API bug where it strips some newlines from code blocks on fetch.
    # We rebuild the rich_text array from the plain_text content to ensure all newlines are preserved.
    if block_type == "code" and "rich_text" in block.get("code", {}):
        plain_text_content = "".join([item.get("plain_text", "") for item in block["code"]["rich_text"]])

        block["code"]["rich_text"] = [{
            "type": "text",
            "text": {"content": plain_text_content}
        }]
        # Clean any top-level children recursively if present
        if "children" in block:
            block["children"] = [_clean_and_flatten_child(child) for child in block["children"]]
            block["children"] = _flatten_grouping_blocks(block["children"])
        return block

    if block_type and block_type in block:
        # Clean the rich_text array within any other block type
        if "rich_text" in block[block_type]:
            block[block_type]["rich_text"] = clean_rich_text(block[block_type]["rich_text"])
        # If recursive fetch stored children under the type key, hoist to top-level
        if isinstance(block[block_type], dict) and isinstance(block[block_type].get("children"), list):
            hoisted_children = [clean_block(child) for child in block[block_type]["children"]]
            hoisted_children = _flatten_grouping_blocks(hoisted_children)
            # Merge with any existing top-level children
            existing_children = block.get("children", []) if isinstance(block.get("children"), list) else []
            block["children"] = existing_children + hoisted_children
            # Remove nested children under the type key to satisfy create schema
            try:
                del block[block_type]["children"]
            except Exception:
                pass

    # Keep children at the top-level per Notion API and recursively clean/flatten
    if "children" in block:
        block["children"] = [_clean_and_flatten_child(child) for child in block["children"]]
        block["children"] = _flatten_grouping_blocks(block["children"])

    return block


def _clean_and_flatten_child(child):
    """
    Helper to clean a child block and flatten grouping wrappers inside the child recursively.
    """
    cleaned = clean_block(child)
    if isinstance(cleaned, dict) and "children" in cleaned:
        cleaned["children"] = _flatten_grouping_blocks(cleaned["children"])
    return cleaned


def create_notion_page(payload, notion_client):
    """
    Creates a new page in Notion using the provided payload.
    It handles the 100 block limit by creating the page with the first 100 blocks
    and then appending the rest. Nested children are appended recursively after
    the corresponding parent blocks are created.
    """
    original_children = payload.pop("children", [])

    def _split_block_and_children(block):
        # Ensure we do not carry nested children in the initial create
        children = []
        if isinstance(block, dict):
            # Prefer top-level children
            if isinstance(block.get("children"), list):
                children = block.get("children", [])
                try:
                    del block["children"]
                except Exception:
                    pass
            # Also guard against any remaining nested children under type key
            block_type = block.get("type")
            if block_type and isinstance(block.get(block_type), dict) and isinstance(block[block_type].get("children"), list):
                # Hoist then remove
                children = children or block[block_type].get("children", [])
                try:
                    del block[block_type]["children"]
                except Exception:
                    pass
        return block, children

    def _prepare_blocks_for_creation(blocks):
        flat_blocks = []
        pending_children = []
        for b in blocks:
            b_no_children, b_children = _split_block_and_children(b)
            flat_blocks.append(b_no_children)
            pending_children.append(b_children)
        return flat_blocks, pending_children

    def _append_children_recursive(parent_block_id, children_blocks):
        if not children_blocks:
            return
        # Prepare immediate children (remove their nested children before append)
        flat_children, pending_nested = _prepare_blocks_for_creation(children_blocks)
        # Append in chunks of 100
        for i in range(0, len(flat_children), 100):
            chunk = flat_children[i:i+100]
            nested_chunk = pending_nested[i:i+100]
            try:
                result = notion_client.blocks.children.append(block_id=parent_block_id, children=chunk)
                created = result.get("results", [])
                # Recurse for each created block with its pending nested children
                for created_block, nested_children in zip(created, nested_chunk):
                    if nested_children:
                        _append_children_recursive(created_block["id"], nested_children)
            except APIResponseError as e:
                print(f"Error appending children to block {parent_block_id}: {e}")
                # Print server-provided body for diagnostics when available
                try:
                    if hasattr(e, "body") and e.body:
                        print(json.dumps(e.body, indent=2))
                except Exception:
                    pass
                raise

    # Prepare top-level blocks for the initial page create
    top_level_blocks, pending_top_level_children = _prepare_blocks_for_creation(original_children)

    # Create the page with the first chunk of top-level children
    payload["children"] = top_level_blocks[:100]

    try:
        response = notion_client.pages.create(**payload)
        print("Successfully created new Notion page!")
        print(f"Page URL: {response['url']}")
        new_page_id = response["id"]

        # If there are more top-level blocks, append them in chunks
        if len(top_level_blocks) > 100:
            for i in range(100, len(top_level_blocks), 100):
                chunk = top_level_blocks[i:i+100]
                print(f"Appending {len(chunk)} more top-level blocks...")
                notion_client.blocks.children.append(
                    block_id=new_page_id,
                    children=chunk
                )
            print("All top-level blocks appended successfully.")

        # Now recursively append nested children under each created top-level block
        # Fetch the created top-level blocks in order
        created_top_level = []
        start_cursor = None
        while True:
            list_kwargs = {"block_id": new_page_id, "page_size": 100}
            if start_cursor:
                list_kwargs["start_cursor"] = start_cursor
            children_page = notion_client.blocks.children.list(**list_kwargs)
            created_top_level.extend(children_page.get("results", []))
            if not children_page.get("has_more"):
                break
            start_cursor = children_page.get("next_cursor")

        # Sanity check on alignment
        if len(created_top_level) != len(top_level_blocks):
            print("Warning: number of created top-level blocks differs from expected. Proceeding by index order.")

        for created_block, pending_children in zip(created_top_level, pending_top_level_children):
            if pending_children:
                _append_children_recursive(created_block["id"], pending_children)

        return response
    except APIResponseError as e:
        print(f"Error creating Notion page: {e}")
        # Print server-provided body for diagnostics when available
        try:
            if hasattr(e, "body") and e.body:
                print(json.dumps(e.body, indent=2))
        except Exception:
            pass
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
        # Flatten any top-level grouping-only list wrappers
        cleaned_blocks = _flatten_grouping_blocks(cleaned_blocks)

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