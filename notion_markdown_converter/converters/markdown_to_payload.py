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
        
        # Parse YAML front matter (properties) if present and properly closed
        if self.lines and self.lines[0].strip() == '---':
            # Only treat as front matter if there is a closing '---' somewhere below
            has_closing = False
            for idx in range(1, len(self.lines)):
                if self.lines[idx].strip() == '---':
                    has_closing = True
                    break
            if has_closing:
                props, next_index = self._parse_front_matter_properties(self.lines, 0)
                if props:
                    page_data["properties"] = props
                # Continue parsing body starting right after closing '---'
                self.current_line_index = next_index
            else:
                # Not a valid front matter; treat normally so '---' can be a divider
                self.current_line_index = 0
        else:
            # Do not treat leading H1 as page title; keep it as a heading block
            self.current_line_index = 0
        
        # Title is only taken from front matter; H1 remains a heading block in the body

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
            # Represent a blank line as an empty paragraph block
            return self._create_paragraph_block("")
        
        # Check for different block types
        # Headings (including toggle headings)
        if line.startswith('### [>] '):
            block = self._create_heading_block(line[8:], 3, is_toggle=True)
            children = self._parse_nested_blocks(indent)
            if children:
                block["children"] = children
            return block
        elif line.startswith('### '):
            return self._create_heading_block(line[4:], 3)
        elif line.startswith('## [>] '):
            block = self._create_heading_block(line[7:], 2, is_toggle=True)
            children = self._parse_nested_blocks(indent)
            if children:
                block["children"] = children
            return block
        elif line.startswith('## '):
            return self._create_heading_block(line[3:], 2)
        elif line.startswith('# [>] '):
            block = self._create_heading_block(line[6:], 1, is_toggle=True)
            children = self._parse_nested_blocks(indent)
            if children:
                block["children"] = children
            return block
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
        
        # Callout block
        elif line.startswith('<aside>'):
            return self._parse_callout_block()
        
        # Link to page block
        elif line.startswith('<notion-page'):
            return self._parse_link_to_page_block(line)
        
        # Column block
        elif line.startswith('<notion-columns>'):
            return self._parse_column_list_block()
        
        # Lists
        elif re.match(r'^-\s+\[[ x]\]\s+', line):
            # Todo item
            checked = '[x]' in line
            text = re.sub(r'^-\s+\[[ x]\]\s+', '', line)
            return self._create_todo_block(text, checked, indent)
        elif re.match(r'^-\s+\[>\]\s+', line):
            # Toggle item
            text = re.sub(r'^-\s+\[>\]\s+', '', line)
            return self._create_toggle_block(text, indent)
        elif line.startswith('- '):
            # Bulleted list
            return self._create_bulleted_list_block(line[2:], indent)
        elif re.match(r'^\d+\.\s+', line) or re.match(r'^[a-zA-Z]\.\s+', line) or re.match(r'(?i:^[ivxlcdm]+)\.\s+', line):
            # Ordered list (numeric, alpha, or roman numeral markers) → treat as numbered list
            text = re.sub(r'^(?:\d+|[a-zA-Z]|(?i:[ivxlcdm]+))\.\s+', '', line)
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
    
    def _create_toggle_block(self, text: str, indent: int) -> Dict[str, Any]:
        """Create a toggle block and parse nested children at greater indent."""
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": self._parse_inline_formatting(text),
                "color": "default"
            },
            "children": []
        }
        children = self._parse_nested_list_items(indent)
        if children:
            block["children"] = children
        return block
    
    def _create_heading_block(self, text: str, level: int, is_toggle: bool = False) -> Dict[str, Any]:
        """Create a heading block."""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._parse_inline_formatting(text),
                "is_toggleable": bool(is_toggle),
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

    def _parse_nested_blocks(self, parent_indent: int) -> List[Dict[str, Any]]:
        """Parse nested blocks (generic) following a parent at a higher indent."""
        children: List[Dict[str, Any]] = []
        temp_index = self.current_line_index + 1
        while temp_index < len(self.lines):
            line = self.lines[temp_index]
            indent = self._get_indent_level(line)
            if indent > parent_indent:
                self.current_line_index = temp_index
                child_block = self._parse_block(line.strip(), indent)
                if child_block:
                    children.append(child_block)
                temp_index = self.current_line_index + 1
            else:
                break
        return children

    def _parse_front_matter_properties(self, lines: List[str], start_index: int) -> Tuple[Dict[str, Any], int]:
        """Parse YAML-like front matter into Notion properties and return (properties, next_index)."""
        i = start_index
        n = len(lines)
        properties: Dict[str, Any] = {}

        def strip_quotes(s: str) -> str:
            s = s.strip()
            if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
                return s[1:-1]
            return s

        def parse_scalar(val: str):
            v = val.strip()
            if v.lower() == 'null':
                return None
            if v.lower() == 'true':
                return True
            if v.lower() == 'false':
                return False
            # number?
            try:
                if '.' in v:
                    return float(v)
                return int(v)
            except:
                pass
            return strip_quotes(v)

        if i >= n or lines[i].strip() != '---':
            return properties, start_index
        i += 1

        # Parse until closing '---'
        while i < n:
            raw = lines[i]
            s = raw.strip()
            if s == '---':
                i += 1
                break
            if not s:
                i += 1
                continue
            # key: value or key:
            m = re.match(r'^(".*?"|[^:]+):\s*(.*)$', s)
            if not m:
                i += 1
                continue
            key_raw, rest = m.group(1), m.group(2)
            key = strip_quotes(key_raw)
            # Expect key format ntn:type:Name
            km = re.match(r'^ntn:([a-z_]+):(.+)$', key)
            if not km:
                # Skip unknown keys
                i += 1
                continue
            prop_type = km.group(1)
            prop_name = km.group(2)

            # Determine value kind
            if rest == '':
                # Could be list or map; inspect next indented lines
                # List: lines starting with '  - '
                # Map: lines starting with '  key: value'
                j = i + 1
                # Collect list
                values_list = []
                values_map: Dict[str, Any] = {}
                while j < n:
                    t = lines[j]
                    if t.startswith('  - '):
                        item_str = t[4:].strip()
                        values_list.append(parse_scalar(item_str))
                        j += 1
                        continue
                    if t.startswith('  '):
                        mm = re.match(r'^\s{2}([^:]+):\s*(.*)$', t)
                        if mm:
                            sub_key = mm.group(1).strip()
                            sub_val = parse_scalar(mm.group(2))
                            values_map[sub_key] = sub_val
                            j += 1
                            continue
                    break
                # Apply parsed structure
                if values_list:
                    self._assign_property(properties, prop_name, prop_type, values_list)
                    i = j
                    continue
                if values_map:
                    self._assign_property(properties, prop_name, prop_type, values_map)
                    i = j
                    continue
                # Empty structure
                self._assign_property(properties, prop_name, prop_type, None)
                i = j
                continue
            else:
                # Inline scalar value
                val = parse_scalar(rest)
                self._assign_property(properties, prop_name, prop_type, val)
                i += 1

        return properties, i

    def _assign_property(self, props: Dict[str, Any], name: str, ptype: str, value: Any) -> None:
        """Assign a parsed front matter value into Notion properties."""
        if ptype == 'title':
            text = '' if value is None else str(value)
            props[name] = {"title": [{"text": {"content": text}}]}
            return
        if ptype == 'rich_text':
            text = '' if value is None else str(value)
            props[name] = {"rich_text": [{"type": "text", "text": {"content": text}}]}
            return
        if ptype == 'url':
            props[name] = {"url": ('' if value is None else str(value))}
            return
        if ptype == 'multi_select':
            items = value or []
            props[name] = {"multi_select": [{"name": str(v)} for v in items]}
            return
        if ptype == 'files':
            urls = value or []
            files = []
            for u in urls:
                us = str(u)
                fname = us.split('/')[-1] if '/' in us else 'file'
                files.append({"name": fname, "type": "external", "external": {"url": us}})
            props[name] = {"files": files}
            return
        if ptype == 'date':
            d = value or {}
            props[name] = {"date": {"start": d.get('start'), "end": d.get('end'), "time_zone": d.get('time_zone')}}
            return
        if ptype == 'people':
            ids = value or []
            props[name] = {"people": [{"id": str(v)} for v in ids]}
            return
        if ptype == 'select':
            props[name] = {"select": ({"name": None if value is None else str(value)})}
            return
        if ptype == 'status':
            props[name] = {"status": ({"name": None if value is None else str(value)})}
            return
        if ptype == 'email':
            props[name] = {"email": (None if value is None else str(value))}
            return
        if ptype == 'checkbox':
            props[name] = {"checkbox": bool(value)}
            return
        if ptype == 'number':
            props[name] = {"number": value}
            return
        if ptype == 'phone_number':
            props[name] = {"phone_number": (None if value is None else str(value))}
            return
    
    def _get_indent_level(self, line: str) -> int:
        """Calculate the indentation level of a line."""
        # Count leading spaces (2 spaces = 1 indent level for bullets, 3 for numbers)
        spaces = len(line) - len(line.lstrip())
        
        # Check if it's an ordered list (digits, alpha, or roman) → 3-space indents
        if (re.match(r'^\s*\d+\.\s+', line) or
            re.match(r'^\s*[a-zA-Z]\.\s+', line) or
            re.match(r'(?i:^\s*[ivxlcdm]+\.\s+)', line)):
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
            (r'\$([^$]+)\$', 'equation'),  # Math equations
            (r'<notion-user\s+id="([^"]+)">@([^<]+)</notion-user>', 'user_mention'),  # User mentions
            (r'<notion-page\s+id="([^"]+)"></notion-page>', 'page_mention'),  # Page mentions
            (r'<notion-date>([^<]+)</notion-date>', 'date_mention'),  # Date mentions
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
                elif earliest_pattern_type == 'equation':
                    expression = earliest_match.group(1)
                    rich_text.append(self._create_equation_text(expression))
                elif earliest_pattern_type == 'user_mention':
                    user_id = earliest_match.group(1)
                    user_name = earliest_match.group(2)
                    rich_text.append(self._create_user_mention_text(user_id, user_name))
                elif earliest_pattern_type == 'page_mention':
                    page_id = earliest_match.group(1)
                    rich_text.append(self._create_page_mention_text(page_id))
                elif earliest_pattern_type == 'date_mention':
                    date_text = earliest_match.group(1)
                    rich_text.append(self._create_date_mention_text(date_text))
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
    
    def _create_equation_text(self, expression: str) -> Dict[str, Any]:
        """Create an equation rich text object."""
        return {
            "type": "equation",
            "equation": {
                "expression": expression
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
    
    def _create_user_mention_text(self, user_id: str, user_name: str) -> Dict[str, Any]:
        """Create a user mention rich text object."""
        return {
            "type": "mention",
            "mention": {
                "type": "user",
                "user": {
                    "id": user_id,
                    "_name": user_name
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
    
    def _create_page_mention_text(self, page_id: str) -> Dict[str, Any]:
        """Create a page mention rich text object."""
        return {
            "type": "mention",
            "mention": {
                "type": "page",
                "page": {
                    "id": page_id
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
    
    def _create_date_mention_text(self, date_text: str) -> Dict[str, Any]:
        """Create a date mention rich text object."""
        # Convert readable date to ISO format
        iso_date = self._parse_date_to_iso(date_text)
        
        return {
            "type": "mention",
            "mention": {
                "type": "date",
                "date": {
                    "start": iso_date,
                    "end": None,
                    "time_zone": None
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
    
    def _parse_date_to_iso(self, date_text: str) -> str:
        """Convert readable date format to ISO format."""
        try:
            from datetime import datetime
            # Try to parse common formats like "August 10, 2025"
            dt = datetime.strptime(date_text, "%B %d, %Y")
            return dt.strftime("%Y-%m-%d")
        except:
            # Fallback: return as-is if parsing fails
            return date_text
    
    def _parse_callout_block(self) -> Optional[Dict[str, Any]]:
        """Parse a callout block starting with <aside>."""
        # Current line should be <aside>
        current_line = self.lines[self.current_line_index].strip()
        if not current_line.startswith('<aside>'):
            return None
            
        # Look for the callout content
        self.current_line_index += 1
        callout_content = []
        icon = "💡"  # Default icon
        
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index].strip()
            
            if line == '</aside>':
                break
            elif not line:  # Empty line
                callout_content.append("")
            else:
                # Check if first line starts with an emoji (icon)
                if not callout_content and len(line) > 0 and ord(line[0]) > 127:  # Unicode emoji
                    # Extract icon and remaining content
                    icon = line[0]
                    content = line[1:].strip()
                    if content:
                        callout_content.append(content)
                else:
                    callout_content.append(line)
                    
            self.current_line_index += 1
        
        # Create callout block
        rich_text = []
        children = []
        
        if callout_content:
            # First line goes in rich_text, rest become paragraph children
            if callout_content[0]:
                rich_text = self._parse_inline_formatting(callout_content[0])
            
            # Additional lines become paragraph children
            for content_line in callout_content[1:]:
                if content_line:  # Skip empty lines for now
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": self._parse_inline_formatting(content_line),
                            "color": "default"
                        }
                    })
        
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": rich_text,
                "icon": {
                    "type": "emoji",
                    "emoji": icon
                },
                "color": "gray_background"
            },
            "children": children
        }
    
    def _parse_link_to_page_block(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a link to page block like <notion-page id=\"...\">."""
        # Extract page ID from the HTML-like tag
        match = re.search(r'<notion-page\s+id="([^"]+)"', line)
        if match:
            page_id = match.group(1)
            return {
                "object": "block",
                "type": "link_to_page",
                "link_to_page": {
                    "type": "page_id",
                    "page_id": page_id
                }
            }
        return None
    
    def _parse_column_list_block(self) -> Optional[Dict[str, Any]]:
        """Parse a column list block starting with <notion-columns>."""
        # Skip the opening tag
        self.current_line_index += 1
        
        columns = []
        current_column_content = []
        
        while self.current_line_index < len(self.lines):
            line = self.lines[self.current_line_index].strip()
            
            if line == '</notion-columns>':
                break
            elif line == '<notion-column>':
                current_column_content = []
            elif line == '</notion-column>':
                # Process current column content
                if current_column_content:
                    # Parse the column content as markdown
                    column_markdown = '\n'.join(current_column_content)
                    temp_converter = NotionMarkdownToPayloadConverter()
                    temp_result = temp_converter.convert_markdown(column_markdown)
                    
                    columns.append({
                        "object": "block",
                        "type": "column",
                        "column": {
                            "width_ratio": 0.5,  # Default equal width
                            "children": temp_result.get('children', [])
                        }
                    })
                current_column_content = []
            else:
                current_column_content.append(line)
                
            self.current_line_index += 1
        
        return {
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": columns
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