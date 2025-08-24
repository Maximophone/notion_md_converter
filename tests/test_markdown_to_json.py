import json
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from notion_markdown_converter import (
    NotionPayloadToMarkdownConverter,
    NotionMarkdownToPayloadConverter,
)
import tempfile


class TestMarkdownToNotionConverter:
    """Test suite for the Markdown to Notion JSON converter."""
    
    def test_simple_paragraph(self):
        """Test conversion of a simple paragraph."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "This is a simple paragraph."
        result = converter.convert_markdown(markdown)
        
        assert len(result["children"]) == 1
        assert result["children"][0]["type"] == "paragraph"
        assert result["children"][0]["paragraph"]["rich_text"][0]["text"]["content"] == "This is a simple paragraph."
    
    def test_headings(self):
        """Test conversion of different heading levels."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = """# Heading 1
## Heading 2
### Heading 3"""
        
        result = converter.convert_markdown(markdown)
        
        # First heading should be extracted as page title
        assert result["properties"]["title"]["title"][0]["text"]["content"] == "Heading 1"
        
        # Other headings should be in children
        assert len(result["children"]) == 2
        assert result["children"][0]["type"] == "heading_2"
        assert result["children"][0]["heading_2"]["rich_text"][0]["text"]["content"] == "Heading 2"
        assert result["children"][1]["type"] == "heading_3"
        assert result["children"][1]["heading_3"]["rich_text"][0]["text"]["content"] == "Heading 3"
    
    def test_bold_italic_formatting(self):
        """Test bold and italic text formatting."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "This has **bold**, *italic*, and ***bold italic*** text."
        
        result = converter.convert_markdown(markdown)
        
        rich_text = result["children"][0]["paragraph"]["rich_text"]
        
        # Check that we have multiple text segments
        assert len(rich_text) > 1
        
        # Find and check bold text
        bold_found = False
        italic_found = False
        bold_italic_found = False
        
        for text_obj in rich_text:
            if text_obj.get("text", {}).get("content") == "bold":
                assert text_obj["annotations"]["bold"] == True
                assert text_obj["annotations"]["italic"] == False
                bold_found = True
            elif text_obj.get("text", {}).get("content") == "italic":
                assert text_obj["annotations"]["bold"] == False
                assert text_obj["annotations"]["italic"] == True
                italic_found = True
            elif text_obj.get("text", {}).get("content") == "bold italic":
                assert text_obj["annotations"]["bold"] == True
                assert text_obj["annotations"]["italic"] == True
                bold_italic_found = True
        
        assert bold_found
        assert italic_found
        assert bold_italic_found
    
    def test_code_formatting(self):
        """Test inline code and code blocks."""
        converter = NotionMarkdownToPayloadConverter()
        
        # Test inline code
        markdown = "This has `inline code` in it."
        result = converter.convert_markdown(markdown)
        
        rich_text = result["children"][0]["paragraph"]["rich_text"]
        code_found = False
        for text_obj in rich_text:
            if text_obj.get("text", {}).get("content") == "inline code":
                assert text_obj["annotations"]["code"] == True
                code_found = True
        assert code_found
        
        # Test code block
        markdown = """```python
def hello():
    print("Hello")
```"""
        
        result = converter.convert_markdown(markdown)
        
        assert result["children"][0]["type"] == "code"
        assert result["children"][0]["code"]["language"] == "python"
        assert "def hello():" in result["children"][0]["code"]["rich_text"][0]["text"]["content"]
    
    def test_lists(self):
        """Test different list types."""
        converter = NotionMarkdownToPayloadConverter()
        
        # Test bulleted list
        markdown = """- Item 1
- Item 2
- Item 3"""
        
        result = converter.convert_markdown(markdown)
        
        assert len(result["children"]) == 3
        for i, block in enumerate(result["children"]):
            assert block["type"] == "bulleted_list_item"
            assert f"Item {i+1}" in block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        
        # Test numbered list
        markdown = """1. First
2. Second
3. Third"""
        
        result = converter.convert_markdown(markdown)
        
        assert len(result["children"]) == 3
        for block in result["children"]:
            assert block["type"] == "numbered_list_item"
        
        # Test todo list
        markdown = """- [ ] Unchecked
- [x] Checked"""
        
        result = converter.convert_markdown(markdown)
        
        assert len(result["children"]) == 2
        assert result["children"][0]["type"] == "to_do"
        assert result["children"][0]["to_do"]["checked"] == False
        assert result["children"][1]["type"] == "to_do"
        assert result["children"][1]["to_do"]["checked"] == True
    
    def test_nested_lists(self):
        """Test nested list structures."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = """- Item 1
  - Sub-item 1.1
  - Sub-item 1.2
- Item 2"""
        
        result = converter.convert_markdown(markdown)
        
        assert len(result["children"]) == 2
        
        # First item should have children
        assert "children" in result["children"][0]["bulleted_list_item"]
        children = result["children"][0]["bulleted_list_item"]["children"]
        assert len(children) == 2
        assert children[0]["type"] == "bulleted_list_item"
        assert "Sub-item 1.1" in children[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    
    def test_quote_block(self):
        """Test quote block conversion."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "> This is a quote"
        
        result = converter.convert_markdown(markdown)
        
        assert result["children"][0]["type"] == "quote"
        assert result["children"][0]["quote"]["rich_text"][0]["text"]["content"] == "This is a quote"
    
    def test_horizontal_rule(self):
        """Test horizontal rule conversion."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "---"
        
        result = converter.convert_markdown(markdown)
        
        assert result["children"][0]["type"] == "divider"
    
    def test_links(self):
        """Test link conversion."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "This is a [link to Google](https://www.google.com)."
        
        result = converter.convert_markdown(markdown)
        
        rich_text = result["children"][0]["paragraph"]["rich_text"]
        link_found = False
        
        for text_obj in rich_text:
            if text_obj.get("text", {}).get("content") == "link to Google":
                assert text_obj["text"].get("link", {}).get("url") == "https://www.google.com"
                link_found = True
        
        assert link_found
    
    def test_table(self):
        """Test table conversion."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = """| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""
        
        result = converter.convert_markdown(markdown)
        
        assert result["children"][0]["type"] == "table"
        table = result["children"][0]["table"]
        assert table["has_column_header"] == True
        assert len(table["children"]) == 3  # Header + 2 data rows
        
        # Check first row
        first_row = table["children"][0]
        assert first_row["type"] == "table_row"
        cells = first_row["table_row"]["cells"]
        assert len(cells) == 2
        assert cells[0][0]["text"]["content"] == "Header 1"
        assert cells[1][0]["text"]["content"] == "Header 2"
    
    def test_strikethrough_and_underline(self):
        """Test strikethrough and underline formatting."""
        converter = NotionMarkdownToPayloadConverter()
        markdown = "This has ~~strikethrough~~ and <u>underline</u> text."
        
        result = converter.convert_markdown(markdown)
        
        rich_text = result["children"][0]["paragraph"]["rich_text"]
        
        strikethrough_found = False
        underline_found = False
        
        for text_obj in rich_text:
            if text_obj.get("text", {}).get("content") == "strikethrough":
                assert text_obj["annotations"]["strikethrough"] == True
                strikethrough_found = True
            elif text_obj.get("text", {}).get("content") == "underline":
                assert text_obj["annotations"]["underline"] == True
                underline_found = True
        
        assert strikethrough_found
        assert underline_found
    
    def test_round_trip_conversion(self):
        """Test that markdown -> JSON -> markdown preserves content."""
        # Create a sample markdown
        original_markdown = """# Test Document

This is a paragraph with **bold** and *italic* text.

## Lists

- Item 1
- Item 2
  - Nested item

1. First
2. Second

## Code

Here is `inline code` and a block:

```python
def test():
    return True
```

> A quote

---

| Column 1 | Column 2 |
| -------- | -------- |
| Data 1   | Data 2   |"""
        
        # Convert to JSON
        md_to_json_converter = NotionMarkdownToPayloadConverter()
        json_data = md_to_json_converter.convert_markdown(original_markdown)
        
        # Convert back to Markdown
        json_to_md_converter = NotionPayloadToMarkdownConverter()
        result_markdown = json_to_md_converter.convert_page(json_data)
        
        # The result should contain all the main elements
        assert "# Test Document" in result_markdown or "Test Document" in result_markdown  # Might be in title
        assert "**bold**" in result_markdown
        assert "*italic*" in result_markdown
        assert "Item 1" in result_markdown
        assert "Item 2" in result_markdown
        assert "Nested item" in result_markdown
        assert "First" in result_markdown or "1. First" in result_markdown
        assert "`inline code`" in result_markdown
        assert "```python" in result_markdown
        assert "def test():" in result_markdown
        assert "> A quote" in result_markdown
        assert "---" in result_markdown
        assert "| Column 1" in result_markdown
        assert "| Data 1" in result_markdown
    
    def test_with_reference_file(self):
        """Test conversion with the reference markdown file."""
        # First, convert the reference JSON to Markdown
        json_to_md_converter = NotionPayloadToMarkdownConverter()
        
        # Read the reference JSON
        with open('references/reference_1_payload.json', 'r', encoding='utf-8') as f:
            original_json = json.load(f)
        
        # Convert to Markdown
        markdown_from_json = json_to_md_converter.convert_page(original_json)

        # Read the reference markdown
        with open('references/reference_1.md', 'r', encoding='utf-8') as f:
            original_markdown = f.read()

        # Compare the markdown from the JSON with the original markdown
        assert markdown_from_json == original_markdown
        
        # Now convert that Markdown back to JSON
        md_to_json_converter = NotionMarkdownToPayloadConverter()
        result_json = md_to_json_converter.convert_markdown(markdown_from_json)
        
        # Verify the structure is similar
        assert "children" in result_json
        assert len(result_json["children"]) > 0
        
        # Check that main block types are preserved
        block_types = [block["type"] for block in result_json["children"]]
        
        # Original has various block types
        expected_types = {"heading_1", "heading_2", "paragraph", "bulleted_list_item", 
                         "numbered_list_item", "to_do", "quote", "divider", "code", "table"}
        
        # Check that we have at least some of these types
        found_types = set(block_types)
        assert len(found_types.intersection(expected_types)) > 5  # Should have most block types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])