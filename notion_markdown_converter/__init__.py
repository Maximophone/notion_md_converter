"""
Notion Markdown Converter Library

A bidirectional converter between Notion API JSON format and Markdown.
Supports all major Notion block types and Markdown features.
"""

from .json_to_markdown import (
    NotionToMarkdownConverter,
    json_to_markdown,
    json_to_markdown_file
)

from .markdown_to_json import (
    MarkdownToNotionConverter,
    markdown_to_json,
    markdown_to_json_file
)

from .utils import extract_page_id

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = [
    "NotionToMarkdownConverter",
    "MarkdownToNotionConverter",
    "json_to_markdown",
    "json_to_markdown_file",
    "markdown_to_json",
    "markdown_to_json_file",
    "extract_page_id"
]