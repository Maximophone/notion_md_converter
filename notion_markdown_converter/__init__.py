"""
Notion Markdown Converter Library

A bidirectional converter supporting three core transformations:
1. NotionApiResponse → NotionPayload (clean API data for creation)
2. NotionPayload ⟷ MarkdownContent (bidirectional conversion)

The composed operations are idempotent and preserve content.
"""

# New converter API
from .converters import (
    NotionApiToPayloadConverter,
    api_to_payload,
    NotionPayloadToMarkdownConverter, 
    payload_to_markdown,
    NotionMarkdownToPayloadConverter,
    markdown_to_payload
)

# Legacy imports for backward compatibility
from .converters.payload_to_markdown import (
    NotionPayloadToMarkdownConverter as NotionToMarkdownConverter,
    json_to_markdown,
    json_to_markdown_file
)

from .converters.markdown_to_payload import (
    NotionMarkdownToPayloadConverter as MarkdownToNotionConverter,
    markdown_to_json,
    markdown_to_json_file
)

from .utils import extract_page_id
from .api import (
    create_notion_client,
    fetch_page_blocks,
    fetch_page_full,
    fetch_page_as_payload,
    create_page_from_payload,
    create_page_from_markdown
)

__version__ = "2.0.0"
__author__ = "Your Name"

# Core API - the three stable functions
__all__ = [
    # Core converters
    "NotionApiToPayloadConverter",
    "api_to_payload", 
    "NotionPayloadToMarkdownConverter",
    "payload_to_markdown",
    "NotionMarkdownToPayloadConverter", 
    "markdown_to_payload",
    
    # API wrapper
    "create_notion_client",
    "fetch_page_blocks", 
    "fetch_page_full",
    "fetch_page_as_payload",
    "create_page_from_payload",
    "create_page_from_markdown",
    
    # Legacy compatibility
    "NotionToMarkdownConverter",
    "MarkdownToNotionConverter", 
    "json_to_markdown",
    "json_to_markdown_file",
    "markdown_to_json",
    "markdown_to_json_file",
    
    # Utilities
    "extract_page_id"
]