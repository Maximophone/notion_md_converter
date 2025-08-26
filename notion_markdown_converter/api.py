"""
Minimalistic Notion API wrapper that abstracts away common operations.

This module provides simple functions for fetching and creating pages while
handling the intricacies of the Notion API (pagination, 100-block limit, etc.).
"""

import os
import json
from typing import Dict, List, Any, Optional
from notion_client import Client, APIResponseError
from dotenv import load_dotenv

from .converters import api_to_payload, payload_to_markdown

load_dotenv()

def create_notion_client(token: Optional[str] = None) -> Client:
    """
    Create a Notion client with the provided token or from environment.
    
    Args:
        token: Notion API token. If None, uses NOTION_TOKEN environment variable.
        
    Returns:
        Configured Notion client
        
    Raises:
        ValueError: If no token is provided and NOTION_TOKEN is not set
    """
    if token is None:
        token = os.getenv("NOTION_TOKEN")
    
    if not token:
        raise ValueError(
            "Notion token is required. Provide it as argument or set NOTION_TOKEN environment variable."
        )
    
    return Client(auth=token)


def fetch_page_blocks(page_id: str, client: Optional[Client] = None) -> List[Dict[str, Any]]:
    """
    Fetch all blocks from a Notion page, handling pagination automatically.
    
    Args:
        page_id: The Notion page ID 
        client: Optional Notion client. If None, creates one from environment.
        
    Returns:
        List of all blocks in the page (raw API response format)
    """
    if client is None:
        client = create_notion_client()
    
    def _fetch_children(block_id: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Fetch children with optional cursor."""
        kwargs = {"block_id": block_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        return client.blocks.children.list(**kwargs)
    
    def _fetch_children_recursive(parent_id: str) -> List[Dict[str, Any]]:
        """Fetch direct children for a parent and recursively populate each child's children."""
        collected: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        while True:
            response = _fetch_children(parent_id, cursor)
            page_blocks = response.get("results", [])
            for block in page_blocks:
                if block.get("has_children", False):
                    # Recursively fetch only this block's direct children
                    block["children"] = _fetch_children_recursive(block["id"])
                collected.append(block)
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        return collected

    return _fetch_children_recursive(page_id)


def fetch_page_full(page_id: str, client: Optional[Client] = None) -> Dict[str, Any]:
    """
    Fetch a complete Notion page including properties and all blocks.
    
    Args:
        page_id: The Notion page ID
        client: Optional Notion client. If None, creates one from environment.
        
    Returns:
        Complete page data with properties and children blocks
    """
    if client is None:
        client = create_notion_client()
    
    # Fetch page properties
    page = client.pages.retrieve(page_id)
    
    # Fetch all blocks
    blocks = fetch_page_blocks(page_id, client)
    
    # Combine into full page structure
    page["children"] = blocks
    return page


def create_page_from_payload(payload: Dict[str, Any], client: Optional[Client] = None) -> Dict[str, Any]:
    """
    Create a new Notion page from a payload, handling the 100-block limit automatically.
    
    Args:
        payload: Clean payload data (from api_to_payload or markdown_to_payload)
        client: Optional Notion client. If None, creates one from environment.
        
    Returns:
        The created page response from Notion API
        
    Raises:
        APIResponseError: If page creation fails
    """
    if client is None:
        client = create_notion_client()
    
    # Extract children and prepare for chunked upload
    original_children = payload.pop("children", [])
    
    def _remove_underscore_keys(obj):
        """Recursively remove all keys starting with underscore."""
        if isinstance(obj, dict):
            cleaned = {k: _remove_underscore_keys(v) for k, v in obj.items() if not k.startswith("_")}
            return cleaned
        elif isinstance(obj, list):
            return [_remove_underscore_keys(item) for item in obj]
        else:
            return obj

    # Clean underscore keys
    original_children = _remove_underscore_keys(original_children)

    def _split_block_and_children(block):
        """Split block into block data and children."""
        children = []
        if isinstance(block, dict):
            # Special handling for structures whose children must remain nested in type payload
            # - column_list/column: children are handled separately by API
            # - table: Notion expects table.rows to be provided under table.children at creation
            if block.get("type") in ("column_list", "column", "table"):
                return block, []
                
            # Extract top-level children
            if isinstance(block.get("children"), list):
                children = block.get("children", [])
                try:
                    del block["children"]
                except Exception:
                    pass
            
            # Also handle nested children under type key
            block_type = block.get("type")
            if (block_type and 
                block_type not in ("column_list", "column", "table") and 
                isinstance(block.get(block_type), dict) and 
                isinstance(block[block_type].get("children"), list)):
                children = children or block[block_type].get("children", [])
                try:
                    del block[block_type]["children"]
                except Exception:
                    pass
        return block, children

    def _prepare_blocks_for_creation(blocks):
        """Prepare blocks by separating children."""
        flat_blocks = []
        pending_children = []
        for b in blocks:
            b_no_children, b_children = _split_block_and_children(b)
            flat_blocks.append(b_no_children)
            pending_children.append(b_children)
        return flat_blocks, pending_children

    def _append_children_recursive(parent_block_id, children_blocks):
        """Recursively append children to a parent block."""
        if not children_blocks:
            return
            
        flat_children, pending_nested = _prepare_blocks_for_creation(children_blocks)
        
        # Append in chunks of 100
        for i in range(0, len(flat_children), 100):
            chunk = flat_children[i:i+100]
            nested_chunk = pending_nested[i:i+100]
            
            try:
                result = client.blocks.children.append(block_id=parent_block_id, children=chunk)
                created = result.get("results", [])
                
                # Recurse for each created block
                for created_block, nested_children in zip(created, nested_chunk):
                    if nested_children:
                        _append_children_recursive(created_block["id"], nested_children)
                        
            except APIResponseError as e:
                print(f"Error appending children to block {parent_block_id}: {e}")
                raise

    # Prepare top-level blocks
    top_level_blocks, pending_top_level_children = _prepare_blocks_for_creation(original_children)

    # Create page with first 100 blocks
    payload["children"] = top_level_blocks[:100]

    try:
        response = client.pages.create(**payload)
        new_page_id = response["id"]

        # Append remaining top-level blocks
        if len(top_level_blocks) > 100:
            for i in range(100, len(top_level_blocks), 100):
                chunk = top_level_blocks[i:i+100]
                client.blocks.children.append(block_id=new_page_id, children=chunk)

        # Fetch created top-level blocks and append their children
        created_top_level = []
        start_cursor = None
        while True:
            list_kwargs = {"block_id": new_page_id, "page_size": 100}
            if start_cursor:
                list_kwargs["start_cursor"] = start_cursor
            children_page = client.blocks.children.list(**list_kwargs)
            created_top_level.extend(children_page.get("results", []))
            if not children_page.get("has_more"):
                break
            start_cursor = children_page.get("next_cursor")

        # Append nested children
        for created_block, pending_children in zip(created_top_level, pending_top_level_children):
            if pending_children:
                _append_children_recursive(created_block["id"], pending_children)

        return response
        
    except APIResponseError as e:
        print(f"Error creating Notion page: {e}")
        if hasattr(e, "body") and e.body:
            print(json.dumps(e.body, indent=2))
        raise


# Convenience functions combining conversion and API operations

def fetch_page_as_payload(page_id: str, client: Optional[Client] = None) -> Dict[str, Any]:
    """
    Fetch a Notion page and convert it to clean payload format.
    
    Args:
        page_id: The Notion page ID
        client: Optional Notion client
        
    Returns:
        Clean payload data suitable for page creation
    """
    api_response = fetch_page_full(page_id, client)
    return api_to_payload(api_response)

def fetch_page_as_markdown(page_id: str, client: Optional[Client] = None) -> str:
    """
    Fetch a Notion page and convert it to Markdown format.
    
    Args:
        page_id: The Notion page ID
        client: Optional Notion client
        
    Returns:
        Markdown content of the page
    """
    payload = fetch_page_as_payload(page_id, client)
    return payload_to_markdown(payload)

def create_page_from_markdown(markdown_content: str, parent_id: str, 
                             title: Optional[str] = None,
                             parent_type: str = "onPage",
                             client: Optional[Client] = None) -> Dict[str, Any]:
    """
    Create a Notion page from Markdown content.
    
    Args:
        markdown_content: The Markdown content
        parent_id: Parent page or database ID
        title: Optional page title. If None, extracts from first # heading
        parent_type: Where to create the page. Accepts "onPage"/"page" or
            "inDatabase"/"database". Defaults to "onPage".
        client: Optional Notion client
        
    Returns:
        The created page response from Notion API
    """
    from .converters import markdown_to_payload
    
    payload = markdown_to_payload(markdown_content)
    
    # Normalize and set parent
    normalized_parent_type = None
    if parent_type in ("onPage", "page"):
        normalized_parent_type = "page"
    elif parent_type in ("inDatabase", "database"):
        normalized_parent_type = "database"
    else:
        raise ValueError("parent_type must be one of 'onPage', 'page', 'inDatabase', or 'database'")

    if normalized_parent_type == "database":
        payload["parent"] = {"database_id": parent_id}
    else:
        payload["parent"] = {"page_id": parent_id}
    
    # Set title if provided
    if title:
        payload["properties"] = {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        }
    
    return create_page_from_payload(payload, client)