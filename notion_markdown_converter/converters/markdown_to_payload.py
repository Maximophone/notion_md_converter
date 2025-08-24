import re
import json
from typing import List, Dict, Any, Optional, Tuple
import uuid


class NotionMarkdownToPayloadConverter:
    """Converts Markdown text to Notion payload JSON format."""
    
    def __init__(self):
        self.current_line_index = 0
        self.lines: List[str] = []
        
    def convert_markdown(self, markdown_text: str) -> Dict[str, Any]:
        """
        Convert Markdown text to Notion payload JSON format.
        
        Args:
            markdown_text: The Markdown text to convert
            
        Returns:
            A dictionary representing the Notion page structure
        """
        self.lines = markdown_text.split('\n')
        self.current_line_index = 0
        
        # Initialize the page structure
        page_data = {
            "parent": {
                "page_id": str(uuid.uuid4()).replace('-', '')
            },
            "properties": {},
            "children": []
        }
        
        # Check if first line is a title (# Title)
        if self.lines and self.lines[0].startswith('# '):
            title_text = self.lines[0][2:].strip()
            page_data["properties"]["title"] = {
                "title": [
                    {
                        "text": {
                            "content": title_text
                        }
                    }
                ]
            }
            self.current_line_index = 1
            # Skip empty line after title if present
            if self.current_line_index < len(self.lines) and not self.lines[self.current_line_index].strip():
                self.current_line_index += 1
        
        # Parse the rest of the content
        blocks = self._parse_blocks()
        page_data["children"] = blocks
        
        return page_data
    
    def _parse_blocks(self, parent_indent: int = 0) -> List[Dict[str, Any]]:
        """Parse markdown lines into Notion blocks."""
        blocks = []
        
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index]
            indent = self._get_indent_level(line)
            
            # If we're parsing nested content and hit something at parent level or less, return
            if parent_indent > 0 and indent < parent_indent:
                break
            
            # Skip if we're at a deeper indent than expected (will be handled by parent)
            if indent > parent_indent:
                self.current_line_index += 1
                continue
            
            block = self._parse_block(line.strip(), indent)
            if block:
                blocks.append(block)
                
            self.current_line_index += 1
        
        return blocks
    
    def _parse_block(self, line: str, indent: int) -> Optional[Dict[str, Any]]:
        """Parse a single line into a Notion block."""
        if not line:
            return None
        
        # Check for different block types
        # Headings
        if line.startswith('### '):
            return self._create_heading_block(line[4:], 3)
        elif line.startswith('## '):
            return self._create_heading_block(line[3:], 2)
        elif line.startswith('# '):
            return self._create_heading_block(line[2:], 1)
        
        # Horizontal rule
        elif line in ['---', '***', '___']:
            return self._create_divider_block()
        
        # Quote
        elif line.startswith('> '):
            return self._create_quote_block(line[2:])
        
        # Code block
        elif line.startswith('```'):
            return self._parse_code_block(line)
        
        # Lists
        elif re.match(r'^-\s+\[[ x]\]\s+', line):
            # Todo item
            checked = '[x]' in line
            text = re.sub(r'^-\s+\[[ x]\]\s+', '', line)
            return self._create_todo_block(text, checked, indent)
        elif line.startswith('- '):
            # Bulleted list
            return self._create_bulleted_list_block(line[2:], indent)
        elif re.match(r'^\d+\.\s+', line):
            # Numbered list
            text = re.sub(r'^\d+\.\s+', '', line)
            return self._create_numbered_list_block(text, indent)
        
        # Table
        elif '|' in line and self._is_table_row(line):
            return self._parse_table()
        
        # Default to paragraph
        else:
            return self._create_paragraph_block(line)
    
    def _is_table_row(self, line: str) -> bool:
        """Check if a line is part of a table."""
        # Simple check for pipe characters
        # More sophisticated check would look ahead for separator row
        if not '|' in line:
            return False
        
        # Look ahead to see if next line is a separator
        if self.current_line_index + 1 < len(self.lines):
            next_line = self.lines[self.current_line_index + 1].strip()
            # Check if next line looks like a table separator
            if re.match(r'^[|\s:\-]+$', next_line) and '|' in next_line:
                return True
        
        # Look back to see if we're in middle of table
        if self.current_line_index > 0:
            prev_line = self.lines[self.current_line_index - 1].strip()
            if '|' in prev_line:
                return True
        
        return False
    
    def _parse_table(self) -> Optional[Dict[str, Any]]:
        """Parse a markdown table into a Notion table block."""
        table_rows = []
        has_header = False
        
        # Parse table rows
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index].strip()
            
            if not line or not '|' in line:
                self.current_line_index -= 1  # Back up one line
                break
            
            # Check if this is a separator row
            if re.match(r'^[|\s:\-]+$', line):
                has_header = True
                self.current_line_index += 1
                continue
            
            # Parse table row
            cells = [cell.strip() for cell in line.split('|')]
            # Remove empty first and last elements if they exist
            if cells and not cells[0]:
                cells = cells[1:]
            if cells and not cells[-1]:
                cells = cells[:-1]
            
            # Convert cells to rich text
            cell_blocks = []
            for cell in cells:
                cell_blocks.append(self._parse_inline_formatting(cell))
            
            table_row = {
                "object": "block",
                "type": "table_row",
                "table_row": {
                    "cells": cell_blocks
                }
            }
            table_rows.append(table_row)
            self.current_line_index += 1
        
        if not table_rows:
            return None
        
        # Create table block
        table_block = {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": len(table_rows[0]["table_row"]["cells"]) if table_rows else 0,
                "has_column_header": has_header,
                "has_row_header": False,
                "children": table_rows
            }
        }
        
        return table_block
    
    def _parse_code_block(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a code block."""
        language = ''
        if len(line) > 3:
            language = line[3:].strip()
        
        code_lines = []
        self.current_line_index += 1
        
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index]
            if line.strip().startswith('```'):
                break
            code_lines.append(line)
            self.current_line_index += 1
        
        code_text = '\n'.join(code_lines)
        
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": code_text
                        }
                    }
                ],
                "language": language if language else "plain text"
            }
        }
    
    def _create_heading_block(self, text: str, level: int) -> Dict[str, Any]:
        """Create a heading block."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._parse_inline_formatting(text),
                "is_toggleable": False,
                "color": "default"
            }
        }
    
    def _create_paragraph_block(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._parse_inline_formatting(text),
                "color": "default"
            }
        }
    
    def _create_quote_block(self, text: str) -> Dict[str, Any]:
        """Create a quote block."""
        # Handle multi-line quotes
        quote_lines = [text]
        
        # Look ahead for continuation quote lines
        temp_index = self.current_line_index + 1
        while temp_index < len(self.lines):
            next_line = self.lines[temp_index].strip()
            if next_line.startswith('> '):
                quote_lines.append(next_line[2:])
                self.current_line_index = temp_index
                temp_index += 1
            else:
                break
        
        full_text = '\n'.join(quote_lines)
        
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": self._parse_inline_formatting(full_text),
                "color": "default"
            }
        }
    
    def _create_divider_block(self) -> Dict[str, Any]:
        """Create a divider block."""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    def _create_bulleted_list_block(self, text: str, indent: int) -> Dict[str, Any]:
        """Create a bulleted list item block."""
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._parse_inline_formatting(text),
                "color": "default"
            }
        }
        
        # Check for nested items
        children = self._parse_nested_list_items(indent)
        if children:
            block["bulleted_list_item"]["children"] = children
        
        return block
    
    def _create_numbered_list_block(self, text: str, indent: int) -> Dict[str, Any]:
        """Create a numbered list item block."""
        block = {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._parse_inline_formatting(text),
                "color": "default"
            }
        }
        
        # Check for nested items
        children = self._parse_nested_list_items(indent)
        if children:
            block["numbered_list_item"]["children"] = children
        
        return block
    
    def _create_todo_block(self, text: str, checked: bool, indent: int) -> Dict[str, Any]:
        """Create a to-do list item block."""
        block = {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": self._parse_inline_formatting(text),
                "checked": checked,
                "color": "default"
            }
        }
        
        # Check for nested items
        children = self._parse_nested_list_items(indent)
        if children:
            block["to_do"]["children"] = children
        
        return block
    
    def _parse_nested_list_items(self, parent_indent: int) -> List[Dict[str, Any]]:
        """Parse nested list items."""
        children = []
        
        # Look ahead for nested items
        temp_index = self.current_line_index + 1
        while temp_index < len(self.lines):
            line = self.lines[temp_index]
            indent = self._get_indent_level(line)
            
            # If indentation is greater, it's a child
            if indent > parent_indent:
                self.current_line_index = temp_index
                child_block = self._parse_block(line.strip(), indent)
                if child_block:
                    children.append(child_block)
                temp_index = self.current_line_index + 1
            else:
                # No longer a child, stop looking
                break
        
        return children
    
    def _get_indent_level(self, line: str) -> int:
        """Calculate the indentation level of a line."""
        # Count leading spaces (2 spaces = 1 indent level for bullets, 3 for numbers)
        spaces = len(line) - len(line.lstrip())
        
        # Check if it's a numbered list (use 3-space indents)
        if re.match(r'^\s*\d+\.\s+', line):
            return spaces // 3
        else:
            return spaces // 2
    
    def _parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """Parse inline Markdown formatting into Notion rich text."""
        if not text:
            return []
        
        rich_text = []
        
        # Regular expressions for different formatting patterns
        # Order matters: more specific patterns first
        patterns = [
            (r'\[([^\]]+)\]\(([^)]+)\)', 'link'),  # Links
            (r'`([^`]+)`', 'code'),  # Inline code
            (r'\*\*\*([^*]+)\*\*\*', 'bold_italic'),  # Bold and italic
            (r'\*\*([^*]+)\*\*', 'bold'),  # Bold
            (r'\*([^*]+)\*', 'italic'),  # Italic
            (r'~~([^~]+)~~', 'strikethrough'),  # Strikethrough
            (r'<u>([^<]+)</u>', 'underline'),  # Underline (HTML)
        ]
        
        remaining_text = text
        position = 0
        
        while remaining_text:
            earliest_match = None
            earliest_pattern_type = None
            earliest_start = len(remaining_text)
            
            # Find the earliest matching pattern
            for pattern, pattern_type in patterns:
                match = re.search(pattern, remaining_text)
                if match and match.start() < earliest_start:
                    earliest_match = match
                    earliest_pattern_type = pattern_type
                    earliest_start = match.start()
            
            if earliest_match:
                # Add any text before the match
                if earliest_match.start() > 0:
                    rich_text.append(self._create_plain_text(remaining_text[:earliest_match.start()]))
                
                # Add the formatted text
                if earliest_pattern_type == 'link':
                    link_text = earliest_match.group(1)
                    link_url = earliest_match.group(2)
                    rich_text.append(self._create_link_text(link_text, link_url))
                else:
                    formatted_text = earliest_match.group(1)
                    rich_text.append(self._create_formatted_text(formatted_text, earliest_pattern_type))
                
                # Continue with remaining text
                remaining_text = remaining_text[earliest_match.end():]
            else:
                # No more patterns found, add remaining as plain text
                rich_text.append(self._create_plain_text(remaining_text))
                break
        
        return rich_text
    
    def _create_plain_text(self, content: str) -> Dict[str, Any]:
        """Create a plain text rich text object."""
        return {
            "type": "text",
            "text": {
                "content": content
            },
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        }
    
    def _create_formatted_text(self, content: str, format_type: str) -> Dict[str, Any]:
        """Create a formatted rich text object."""
        annotations = {
            "bold": format_type in ['bold', 'bold_italic'],
            "italic": format_type in ['italic', 'bold_italic'],
            "strikethrough": format_type == 'strikethrough',
            "underline": format_type == 'underline',
            "code": format_type == 'code',
            "color": "default"
        }
        
        return {
            "type": "text",
            "text": {
                "content": content
            },
            "annotations": annotations
        }
    
    def _create_link_text(self, content: str, url: str) -> Dict[str, Any]:
        """Create a link rich text object."""
        return {
            "type": "text",
            "text": {
                "content": content,
                "link": {
                    "url": url
                }
            },
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            }
        }


def markdown_to_payload(markdown_text: str) -> Dict[str, Any]:
    """
    Convert Markdown text to Notion payload format.
    
    Args:
        markdown_text: The Markdown text to convert
        
    Returns:
        The converted Notion payload structure
    """
    converter = NotionMarkdownToPayloadConverter()
    return converter.convert_markdown(markdown_text)


def markdown_to_payload_file(markdown_file_path: str, payload_file_path: str) -> None:
    """
    Convert a Markdown file to a Notion payload JSON file.
    
    Args:
        markdown_file_path: Path to the input Markdown file
        payload_file_path: Path to the output payload JSON file
    """
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    payload_data = markdown_to_payload(markdown_content)
    
    with open(payload_file_path, 'w', encoding='utf-8') as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)


# Legacy function names for backward compatibility
def markdown_to_json(markdown_file_path: str) -> Dict[str, Any]:
    """Legacy function. Use markdown_to_payload_file instead."""
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    converter = NotionMarkdownToPayloadConverter()
    return converter.convert_markdown(markdown_content)


def markdown_to_json_file(markdown_file_path: str, json_file_path: str) -> None:
    """Legacy function. Use markdown_to_payload_file instead."""
    markdown_to_payload_file(markdown_file_path, json_file_path)