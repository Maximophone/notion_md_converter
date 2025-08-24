import json
from typing import List, Dict, Any, Optional


class NotionPayloadToMarkdownConverter:
    """Converts Notion payload JSON (clean page data) to Markdown format."""
    
    def __init__(self):
        self.numbered_list_counter = 0
        self.in_numbered_list = False
        
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
            if indent_level == 0:
                if prev_block_type == 'numbered_list_item' and block_type != 'numbered_list_item':
                    self.numbered_list_counter = 0
                    self.in_numbered_list = False
                elif block_type == 'numbered_list_item' and not self.in_numbered_list:
                    self.numbered_list_counter = 0
                    self.in_numbered_list = True
            
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
            
            # Add spacing between different block types (but not between list items or before dividers)
            if lines and block_lines and not self._is_list_continuation(prev_block_type, block_type):
                # Check if current block is a divider and previous line ends with ":"
                # In this case, don't add extra spacing
                if not (block_type == 'divider' and lines[-1].endswith(':')):
                    lines.append("")
                
            lines.extend(block_lines)
            prev_block_type = block_type
            
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
            self.numbered_list_counter += 1
            # For nested numbered lists in Markdown, use 3 spaces to align with parent text
            # Only modify if we have indentation (meaning it's nested)
            list_indent = indent
            if indent:
                # Count indent level (each level is 4 spaces)
                indent_level = len(indent) // 4
                # For numbered lists, use 3 spaces per level
                list_indent = "   " * indent_level
            return [f"{list_indent}{self.numbered_list_counter}. {text}"]
        return []
    
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
            
        lines = []
        has_header = table_data.get('has_column_header', False)
        
        for i, row in enumerate(rows):
            if row.get('type') == 'table_row':
                cells = row.get('table_row', {}).get('cells', [])
                # Convert each cell's rich text
                cell_texts = []
                for cell in cells:
                    if cell:
                        cell_text = self._convert_rich_text(cell)
                        cell_texts.append(cell_text)
                    else:
                        cell_texts.append("")
                
                # Create the table row
                row_text = f"{indent}| " + " | ".join(cell_texts) + " |"
                lines.append(row_text)
                
                # Add header separator after first row if it's a header
                if i == 0 and has_header:
                    separator_cells = ["-" * max(8, len(cell) + 2) for cell in cell_texts]
                    # Add alignment indicators
                    separator_cells = [f":{sep}:" for sep in separator_cells]
                    separator = f"{indent}| " + " | ".join(separator_cells) + " |"
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