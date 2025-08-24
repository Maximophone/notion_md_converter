import json
from typing import List, Dict, Any, Optional


class NotionPayloadToMarkdownConverter:
    """Converts Notion payload JSON (clean page data) to Markdown format."""
    
    def __init__(self):
        self.numbered_list_counters_by_indent: Dict[int, int] = {}
        self.in_numbered_list_by_indent: Dict[int, bool] = {}
        
    def convert_page(self, notion_data: Dict[str, Any]) -> str:
        """
        Convert a complete Notion page JSON to Markdown.
        
        Args:
            notion_data: The Notion payload JSON containing clean page data
            
        Returns:
            The converted Markdown string
        """
        markdown_lines = []
        
        # Handle page title if present
        # Check both old format (properties.title.title) and new format (properties.title)
        if 'properties' in notion_data:
            if 'title' in notion_data['properties']:
                title_property = notion_data['properties']['title']
                title_text = None
                
                # Handle both formats
                if isinstance(title_property, dict):
                    if 'title' in title_property and title_property['title']:
                        # Standard Notion format: properties.title.title is an array
                        if isinstance(title_property['title'], list):
                            # Check if it's already rich text format
                            if title_property['title'] and isinstance(title_property['title'][0], dict) and 'text' in title_property['title'][0]:
                                # It's our converted format, extract the text
                                title_text = title_property['title'][0]['text'].get('content', '')
                            else:
                                title_text = self._convert_rich_text(title_property['title'])
                        else:
                            title_text = self._convert_rich_text(title_property['title'])
                    elif 'text' in title_property:
                        # Direct text format from our converter
                        title_text = title_property['text']['content'] if isinstance(title_property['text'], dict) else title_property['text']
                elif isinstance(title_property, list):
                    title_text = self._convert_rich_text(title_property)
                
                if title_text:
                    markdown_lines.append(f"# {title_text}")
                    markdown_lines.append("")
        
        # Process children blocks
        if 'children' in notion_data:
            markdown_lines.extend(self._process_blocks(notion_data['children']))
            
        # Clean up any trailing empty lines
        while markdown_lines and markdown_lines[-1] == "":
            markdown_lines.pop()
            
        return "\n".join(markdown_lines)
    
    def _process_blocks(self, blocks: List[Dict[str, Any]], indent_level: int = 0) -> List[str]:
        """Process a list of blocks and convert them to Markdown lines."""
        lines = []
        prev_block_type = None
        in_column_list = False
        
        for i, block in enumerate(blocks):
            block_type = block.get('type', '')
            
            # Reset numbered list counter when we exit a numbered list at the same level
            if prev_block_type == 'numbered_list_item' and block_type != 'numbered_list_item':
                # Leaving a numbered list at this indent level
                self.numbered_list_counters_by_indent[indent_level] = 0
                self.in_numbered_list_by_indent[indent_level] = False
            elif block_type == 'numbered_list_item' and not self.in_numbered_list_by_indent.get(indent_level, False):
                # Entering a numbered list at this indent level
                self.numbered_list_counters_by_indent[indent_level] = 0
                self.in_numbered_list_by_indent[indent_level] = True
            
            # Handle special column list processing
            if block_type == 'column_list':
                in_column_list = True
                lines.extend(self._convert_block(block, indent_level))
                
                # Process column children
                column_data = block.get('column_list', {})
                columns = column_data.get('children', [])
                
                for column in columns:
                    if column.get('type') == 'column':
                        lines.append("<notion-column>")
                        column_children = column.get('column', {}).get('children', [])
                        column_lines = self._process_blocks(column_children, indent_level)
                        lines.extend(column_lines)
                        lines.append("</notion-column>")
                        
                lines.append("</notion-columns>")
                in_column_list = False
                prev_block_type = block_type
                continue
                
            # Handle callout block with special formatting
            if block_type == 'callout':
                callout_data = block.get('callout', {})
                text = self._get_block_text(block, 'callout')
                
                # Get the icon
                icon_data = callout_data.get('icon', {})
                icon = ""
                if icon_data.get('type') == 'emoji':
                    icon = icon_data.get('emoji', '')
                
                lines.append(f"<aside>")
                if text:
                    lines.append(f"{icon} {text}")
                
                # Process callout children
                children = block.get('children', [])
                if children:
                    child_lines = self._process_blocks(children, indent_level)
                    lines.extend(child_lines)
                    
                lines.append("</aside>")
                prev_block_type = block_type
                continue
            
            # Convert the block normally
            block_lines = self._convert_block(block, indent_level)

            lines.extend(block_lines)
            prev_block_type = block_type
            
        # Trim trailing empty lines within this group
        while lines and lines[-1] == "":
            lines.pop()
        return lines
    
    def _is_list_continuation(self, prev_type: Optional[str], curr_type: str) -> bool:
        """Check if current block continues a list from previous block."""
        list_types = {'bulleted_list_item', 'numbered_list_item', 'to_do'}
        return prev_type in list_types and curr_type in list_types
    
    def _convert_block(self, block: Dict[str, Any], indent_level: int = 0) -> List[str]:
        """Convert a single block to Markdown lines."""
        block_type = block.get('type', '')
        indent = "    " * indent_level
        
        # Map block types to converter methods
        converters = {
            'paragraph': self._convert_paragraph,
            'heading_1': self._convert_heading_1,
            'heading_2': self._convert_heading_2,
            'heading_3': self._convert_heading_3,
            'bulleted_list_item': self._convert_bulleted_list,
            'numbered_list_item': self._convert_numbered_list,
            'to_do': self._convert_todo,
            'quote': self._convert_quote,
            'divider': self._convert_divider,
            'code': self._convert_code,
            'table': self._convert_table,
            'toggle': self._convert_toggle,
            'callout': self._convert_callout,
            'link_to_page': self._convert_link_to_page,
            'column_list': self._convert_column_list,
        }
        
        converter = converters.get(block_type)
        if not converter:
            return []
            
        lines = converter(block, indent)
        
        # Process children if present
        # Children can be at block level or inside the block type data
        children = None
        if 'children' in block:
            children = block['children']
        elif block_type in block and 'children' in block[block_type]:
            children = block[block_type]['children']
            
        if children:
            child_lines = self._process_blocks(children, indent_level + 1)
            lines.extend(child_lines)
            
        return lines
    
    def _convert_paragraph(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a paragraph block."""
        text = self._get_block_text(block, 'paragraph')
        if text:
            return [f"{indent}{text}"]
        else:
            # Empty paragraph becomes empty line
            return [""]
    
    def _convert_heading_1(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a heading 1 block."""
        text = self._get_block_text(block, 'heading_1')
        if text:
            # Check if this is a toggle header
            heading_data = block.get('heading_1', {})
            if heading_data.get('is_toggleable', False):
                return [f"{indent}# [>] {text}"]
            else:
                return [f"{indent}# {text}"]
        return []
    
    def _convert_heading_2(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a heading 2 block."""
        text = self._get_block_text(block, 'heading_2')
        if text:
            # Check if this is a toggle header
            heading_data = block.get('heading_2', {})
            if heading_data.get('is_toggleable', False):
                return [f"{indent}## [>] {text}"]
            else:
                return [f"{indent}## {text}"]
        return []
    
    def _convert_heading_3(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a heading 3 block."""
        text = self._get_block_text(block, 'heading_3')
        if text:
            # Check if this is a toggle header
            heading_data = block.get('heading_3', {})
            if heading_data.get('is_toggleable', False):
                return [f"{indent}### [>] {text}"]
            else:
                return [f"{indent}### {text}"]
        return []
    
    def _convert_bulleted_list(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a bulleted list item."""
        text = self._get_block_text(block, 'bulleted_list_item')
        if text:
            return [f"{indent}- {text}"]
        return []
    
    def _convert_numbered_list(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a numbered list item."""
        text = self._get_block_text(block, 'numbered_list_item')
        if text:
            # Determine indent level from indent string (each level is 4 spaces)
            indent_level = len(indent) // 4

            # Increment counter for this level
            current_count = self.numbered_list_counters_by_indent.get(indent_level, 0) + 1
            self.numbered_list_counters_by_indent[indent_level] = current_count

            # Determine numbering style by level
            marker = self._format_ordered_list_marker(current_count, indent_level)

            # For nested numbered lists in Markdown, use 3 spaces per level to align
            list_indent = "   " * indent_level if indent_level > 0 else ""
            return [f"{list_indent}{marker} {text}"]
        return []

    def _format_ordered_list_marker(self, count: int, indent_level: int) -> str:
        """Return the ordered list marker (e.g., '1.', 'a.', 'i.') based on nesting level."""
        # Level 0: 1., 2., 3.
        # Level 1: a., b., c.
        # Level 2: i., ii., iii.
        # Level 3+: repeat pattern starting from numbers again
        level_type = indent_level % 3
        if level_type == 0:
            return f"{count}."
        if level_type == 1:
            # a., b., c. ... wrap after z to aa., ab., etc.
            return f"{self._to_alpha(count)}."
        # Roman numerals
        return f"{self._to_roman(count).lower()}."

    def _to_alpha(self, num: int) -> str:
        """Convert 1 -> a, 2 -> b, ... 27 -> aa, etc."""
        result = []
        n = num
        while n > 0:
            n -= 1
            result.append(chr(ord('a') + (n % 26)))
            n //= 26
        return ''.join(reversed(result))

    def _to_roman(self, num: int) -> str:
        """Convert integer to Roman numerals."""
        vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = [
            'M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'
        ]
        res = []
        n = num
        for v, s in zip(vals, syms):
            while n >= v:
                res.append(s)
                n -= v
        return ''.join(res)
    
    def _convert_todo(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a to-do list item."""
        text = self._get_block_text(block, 'to_do')
        checked = block.get('to_do', {}).get('checked', False)
        checkbox = "[x]" if checked else "[ ]"
        if text:
            return [f"{indent}- {checkbox} {text}"]
        return []
    
    def _convert_quote(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a quote block."""
        text = self._get_block_text(block, 'quote')
        if text:
            # Handle multi-line quotes
            lines = text.split('\n')
            return [f"{indent}> {line}" for line in lines]
        return []
    
    def _convert_divider(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a divider block."""
        return [f"{indent}---"]
    
    def _convert_code(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a code block."""
        code_data = block.get('code', {})
        language = code_data.get('language', '')
        rich_text = code_data.get('rich_text', [])
        
        if rich_text:
            code_text = self._convert_rich_text(rich_text)
            lines = [f"{indent}```{language}"]
            # Handle multi-line code
            for line in code_text.split('\n'):
                lines.append(f"{indent}{line}")
            lines.append(f"{indent}```")
            return lines
        return []
    
    def _convert_table(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a table block."""
        table_data = block.get('table', {})
        
        # Table rows are stored in table.children, not block.children
        rows = table_data.get('children', [])
        if not rows:
            # Try block.children as fallback
            rows = block.get('children', [])
        if not rows:
            return []
            
        lines: List[str] = []
        has_header = table_data.get('has_column_header', False)

        # Gather raw cell texts for width calculation
        row_text_matrix: List[List[str]] = []
        for row in rows:
            if row.get('type') != 'table_row':
                continue
            cells = row.get('table_row', {}).get('cells', [])
            cell_texts: List[str] = []
            for cell in cells:
                if cell:
                    cell_text = self._convert_rich_text(cell)
                    cell_texts.append(cell_text)
                else:
                    cell_texts.append("")
            row_text_matrix.append(cell_texts)

        if not row_text_matrix:
            return []

        # Compute column widths aiming to match reference formatting
        num_cols = max(len(r) for r in row_text_matrix)
        header_texts = row_text_matrix[0] if row_text_matrix else []

        # Dash counts for separator
        left_dash_count = 0
        center_dash_counts: List[int] = [0] * num_cols
        # Widths for content rendering
        col_widths: List[int] = [0] * num_cols

        if has_header:
            # First column: separator width equals (max content length + 2)
            left_max_content = 0
            for r in row_text_matrix:
                if r:
                    left_max_content = max(left_max_content, len(r[0]) if len(r) > 0 else 0)
            header_len_0 = len(header_texts[0]) if header_texts else 0
            left_max = max(left_max_content, header_len_0)
            left_dash_count = left_max + 2
            # Header cell width matches separator dash count
            col_widths[0] = left_dash_count

            # Other columns: width = header length + 2; dash counts accordingly
            for c_idx in range(1, num_cols):
                header_len = len(header_texts[c_idx]) if c_idx < len(header_texts) else 0
                col_widths[c_idx] = header_len
                center_dash_counts[c_idx] = max(3, header_len - 2)
        else:
            # Fallback: width from content lengths
            for r in row_text_matrix:
                for c_idx, cell in enumerate(r):
                    col_widths[c_idx] = max(col_widths[c_idx], len(cell))

        # Build header and optional alignment separator
        for i, cell_texts in enumerate(row_text_matrix):
            # Pad cell_texts to num_cols
            if len(cell_texts) < num_cols:
                cell_texts = cell_texts + [""] * (num_cols - len(cell_texts))

            # Format row with padding: first column left-aligned, others centered
            formatted_cells: List[str] = []
            for c_idx, text in enumerate(cell_texts):
                width = col_widths[c_idx] if c_idx < len(col_widths) else len(text)
                if c_idx == 0:
                    # left align: text padded to width
                    if width > len(text):
                        formatted = f"{text}{' ' * (width - len(text))}"
                    else:
                        formatted = text
                else:
                    # center align: distribute spaces on both sides
                    total_pad = max(0, width - len(text))
                    left_pad = total_pad // 2
                    right_pad = total_pad - left_pad
                    formatted = f"{' ' * left_pad}{text}{' ' * right_pad}"
                formatted_cells.append(formatted)

            row_text = f"{indent}| " + " | ".join(formatted_cells) + " |"
            lines.append(row_text)

            if i == 0 and has_header:
                # Build alignment separator using computed dash counts
                sep_cells: List[str] = []
                for c_idx in range(num_cols):
                    if c_idx == 0:
                        sep_cells.append("-" * max(1, left_dash_count))
                    else:
                        dashes = max(1, center_dash_counts[c_idx])
                        sep_cells.append(f":{'-' * dashes}:")
                separator = f"{indent}| " + " | ".join(sep_cells) + " |"
                lines.append(separator)

        return lines
    
    def _convert_toggle(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a toggle block."""
        text = self._get_block_text(block, 'toggle')
        if text:
            return [f"{indent}- [>] {text}"]
        return []
    
    def _convert_callout(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a callout block."""
        text = self._get_block_text(block, 'callout')
        callout_data = block.get('callout', {})
        
        # Get the icon
        icon_data = callout_data.get('icon', {})
        icon = ""
        if icon_data.get('type') == 'emoji':
            icon = icon_data.get('emoji', '')
        
        if text:
            return [f"{indent}<aside>"]
        return []
    
    def _convert_link_to_page(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a link to page block."""
        link_data = block.get('link_to_page', {})
        if link_data.get('type') == 'page_id':
            page_id = link_data.get('page_id', '')
            return [f"{indent}<notion-page id=\"{page_id}\"></notion-page>"]
        return []
    
    def _convert_column_list(self, block: Dict[str, Any], indent: str) -> List[str]:
        """Convert a column list block."""
        return [f"{indent}<notion-columns>"]
    
    def _get_block_text(self, block: Dict[str, Any], block_type: str) -> str:
        """Extract text from a block's rich_text field."""
        block_data = block.get(block_type, {})
        rich_text = block_data.get('rich_text', [])
        return self._convert_rich_text(rich_text)
    
    def _convert_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Convert Notion rich text format to Markdown."""
        if not rich_text:
            return ""
            
        result = []
        
        for text_obj in rich_text:
            text_type = text_obj.get('type')
            
            if text_type == 'text':
                text_data = text_obj.get('text', {})
                content = text_data.get('content', '')
                link = text_data.get('link')
                
                # Apply annotations
                annotations = text_obj.get('annotations', {})
                
                # Apply formatting in the correct order
                if annotations.get('code', False):
                    content = f"`{content}`"
                else:
                    if annotations.get('bold', False) and annotations.get('italic', False):
                        content = f"***{content}***"
                    elif annotations.get('bold', False):
                        content = f"**{content}**"
                    elif annotations.get('italic', False):
                        content = f"*{content}*"
                    
                    if annotations.get('strikethrough', False):
                        content = f"~~{content}~~"
                    
                    if annotations.get('underline', False):
                        # Markdown doesn't have native underline, using HTML
                        content = f"<u>{content}</u>"
                
                # Handle links
                if link:
                    content = f"[{content}]({link['url']})"
                
                result.append(content)
                
            elif text_type == 'equation':
                equation_data = text_obj.get('equation', {})
                expression = equation_data.get('expression', '')
                result.append(f"${expression}$")
                
            elif text_type == 'mention':
                mention_data = text_obj.get('mention', {})
                mention_type = mention_data.get('type')
                
                if mention_type == 'user':
                    user_data = mention_data.get('user', {})
                    user_id = user_data.get('id', '')
                    user_name = user_data.get('_name', 'User')
                    result.append(f'<notion-user id="{user_id}">@{user_name}</notion-user>')
                    
                elif mention_type == 'page':
                    page_data = mention_data.get('page', {})
                    page_id = page_data.get('id', '')
                    result.append(f'<notion-page id="{page_id}"></notion-page>')
                    
                elif mention_type == 'date':
                    date_data = mention_data.get('date', {})
                    start_date = date_data.get('start', '')
                    if start_date:
                        # Convert from ISO format to readable format
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(start_date)
                            formatted_date = dt.strftime('%B %d, %Y')
                            result.append(f'<notion-date>{formatted_date}</notion-date>')
                        except:
                            result.append(f'<notion-date>{start_date}</notion-date>')
            else:
                # Handle other text types by falling back to text content if available
                if 'text' in text_obj:
                    result.append(text_obj['text'].get('content', ''))
                
        return ''.join(result)


def payload_to_markdown(payload_data: Dict[str, Any]) -> str:
    """
    Convert Notion payload data to Markdown.
    
    Args:
        payload_data: Clean Notion payload data
        
    Returns:
        The converted Markdown string
    """
    converter = NotionPayloadToMarkdownConverter()
    return converter.convert_page(payload_data)


def payload_to_markdown_file(payload_file_path: str, markdown_file_path: str) -> None:
    """
    Convert a Notion payload JSON file to a Markdown file.
    
    Args:
        payload_file_path: Path to the input payload JSON file
        markdown_file_path: Path to the output Markdown file
    """
    with open(payload_file_path, 'r', encoding='utf-8') as f:
        payload_data = json.load(f)
    
    markdown_content = payload_to_markdown(payload_data)
    
    with open(markdown_file_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)


# Legacy function names for backward compatibility
def json_to_markdown(json_file_path: str) -> str:
    """Legacy function. Use payload_to_markdown_file instead."""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        notion_data = json.load(f)
    
    converter = NotionPayloadToMarkdownConverter()
    return converter.convert_page(notion_data)


def json_to_markdown_file(json_file_path: str, markdown_file_path: str) -> None:
    """Legacy function. Use payload_to_markdown_file instead."""
    payload_to_markdown_file(json_file_path, markdown_file_path)