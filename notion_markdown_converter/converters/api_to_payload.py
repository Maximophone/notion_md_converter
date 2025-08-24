"""
Converter for transforming Notion API responses (snapshots) to payload format.

This module handles the conversion from NotionApiResponse (raw API data with IDs, timestamps, etc.)
to NotionPayload (clean data suitable for page creation).
"""

import json
from typing import Dict, List, Any, Optional


class NotionApiToPayloadConverter:
    """Converts Notion API response data to clean payload format for page creation."""
    
    def __init__(self):
        pass
    
    def convert_page(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a Notion API page response to a clean payload.
        
        Args:
            api_response: Raw Notion API response data
            
        Returns:
            Clean payload suitable for page creation
        """
        # Handle both page objects and just children arrays
        if isinstance(api_response, list):
            # It's just a list of blocks
            cleaned_children = [self._clean_block(block) for block in api_response]
            cleaned_children = self._flatten_grouping_blocks(cleaned_children)
            return {
                "parent": {"page_id": "placeholder"},
                "properties": {},
                "children": cleaned_children
            }
        
        # It's a full page object
        payload = {
            "parent": {"page_id": "placeholder"},
            "properties": {},
            "children": []
        }
        
        # Extract title if present
        if 'properties' in api_response and 'title' in api_response['properties']:
            title_property = api_response['properties']['title']
            if isinstance(title_property, dict) and 'title' in title_property:
                # Clean the title rich text
                cleaned_title = self._clean_rich_text(title_property['title'])
                payload["properties"]["title"] = {"title": cleaned_title}
        
        # Process children blocks
        if 'children' in api_response:
            cleaned_children = [self._clean_block(block) for block in api_response['children']]
            payload["children"] = self._flatten_grouping_blocks(cleaned_children)
            
        return payload
    
    def _clean_rich_text(self, rich_text_array: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                    user_name = (
                        mention.get("user", {}).get("name")
                        if isinstance(mention.get("user"), dict)
                        else None
                    )
                    if user_id:
                        cleaned_mention["user"] = {"id": user_id, "_name": user_name}
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
    
    def _flatten_grouping_blocks(self, children: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    
    def _clean_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Removes fields from a block object that are not allowed when creating new content.
        This version includes a workaround for a Notion API bug with code block line breaks.
        """
        # Create a copy to avoid modifying the original
        block = block.copy()
        
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
                block["children"] = [self._clean_and_flatten_child(child) for child in block["children"]]
                block["children"] = self._flatten_grouping_blocks(block["children"])
            return block

        if block_type and block_type in block:
            # Column blocks do not accept any properties on create other than nested children
            if block_type == "column":
                if not isinstance(block.get("column"), dict):
                    block["column"] = {}
                # Move any top-level children into column.children after cleaning
                if isinstance(block.get("children"), list):
                    moved_children = [self._clean_and_flatten_child(child) for child in block["children"]]
                    moved_children = self._flatten_grouping_blocks(moved_children)
                    block["column"]["children"] = moved_children
                    try:
                        del block["children"]
                    except Exception:
                        pass
            # Column list blocks must define their columns under column_list.children for creation
            elif block_type == "column_list":
                if not isinstance(block.get("column_list"), dict):
                    block["column_list"] = {}
                # If top-level children exist, move them under column_list.children after cleaning
                if isinstance(block.get("children"), list):
                    moved_children = [self._clean_and_flatten_child(child) for child in block["children"]]
                    moved_children = self._flatten_grouping_blocks(moved_children)
                    block["column_list"]["children"] = moved_children
                    try:
                        del block["children"]
                    except Exception:
                        pass
            # Clean the rich_text array within any other block type
            if "rich_text" in block[block_type]:
                block[block_type]["rich_text"] = self._clean_rich_text(block[block_type]["rich_text"])
            # If recursive fetch stored children under the type key, hoist to top-level
            # BUT keep children nested for column_list and column, which require nested children on create
            if block_type not in ("column_list", "column") and isinstance(block[block_type], dict) and isinstance(block[block_type].get("children"), list):
                hoisted_children = [self._clean_block(child) for child in block[block_type]["children"]]
                hoisted_children = self._flatten_grouping_blocks(hoisted_children)
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
            block["children"] = [self._clean_and_flatten_child(child) for child in block["children"]]
            block["children"] = self._flatten_grouping_blocks(block["children"])

        return block
    
    def _clean_and_flatten_child(self, child: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to clean a child block and flatten grouping wrappers inside the child recursively.
        """
        cleaned = self._clean_block(child)
        if isinstance(cleaned, dict) and "children" in cleaned:
            cleaned["children"] = self._flatten_grouping_blocks(cleaned["children"])
        return cleaned


def api_to_payload(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to convert Notion API response to payload format.
    
    Args:
        api_response: Raw Notion API response data
        
    Returns:
        Clean payload suitable for page creation
    """
    converter = NotionApiToPayloadConverter()
    return converter.convert_page(api_response)


def api_to_payload_file(input_file: str, output_file: str) -> None:
    """
    Convert a Notion API response JSON file to payload format.
    
    Args:
        input_file: Path to input JSON file (API response)
        output_file: Path to output JSON file (clean payload)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        api_data = json.load(f)
    
    payload = api_to_payload(api_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)