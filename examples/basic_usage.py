#!/usr/bin/env python3
"""
Notion Markdown Converter Example - New API

This example demonstrates the three core conversion types:
1. NotionApiResponse → NotionPayload (cleaning API data)
2. NotionPayload → MarkdownContent (structured data to text)  
3. MarkdownContent → NotionPayload (text to structured data)
4. Round-trip conversion testing
5. API integration examples
"""

import json
import sys
import os
# Add parent directory to path to import the library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_markdown_converter import (
    # New core API
    api_to_payload,
    payload_to_markdown, 
    markdown_to_payload,
    NotionApiToPayloadConverter,
    NotionPayloadToMarkdownConverter,
    NotionMarkdownToPayloadConverter,
    
    # Legacy compatibility
    NotionToMarkdownConverter,
    MarkdownToNotionConverter
)


def demo_api_to_payload():
    """Demonstrate API response to payload conversion."""
    print("=" * 60)
    print("1. NotionApiResponse → NotionPayload (Core Function 1)")
    print("=" * 60)
    
    # Load API response
    with open('references/reference_1_api.json', 'r', encoding='utf-8') as f:
        api_data = json.load(f)
    
    print(f"API response has {len(api_data)} blocks with API-specific fields")
    print("Sample API block fields:", list(api_data[0].keys())[:5], "...")
    
    # Convert using core function
    payload = api_to_payload(api_data)
    
    print(f"Payload has {len(payload['children'])} clean blocks")
    print("Sample payload block fields:", list(payload['children'][0].keys()))
    print("API-specific fields removed: id, created_time, last_edited_time, etc.")
    
    # Save result
    with open('output/reference_1_payload.json', 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print("Payload saved to: output/reference_1_payload.json")


def demo_payload_to_markdown():
    """Demonstrate payload to markdown conversion."""
    print("\n" + "=" * 60)
    print("2. NotionPayload → MarkdownContent (Core Function 2)")
    print("=" * 60)
    
    # Load clean payload
    with open('references/reference_1_payload.json', 'r', encoding='utf-8') as f:
        payload_data = json.load(f)
    
    print(f"Payload has {len(payload_data['children'])} blocks")
    
    # Convert using core function
    markdown_content = payload_to_markdown(payload_data)
    
    print("Converted to Markdown (first 500 chars):")
    print(markdown_content[:500])
    print("...")
    
    # Save result
    with open('output/reference_1_markdown.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print("Markdown saved to: output/reference_1_markdown.md")


def demo_markdown_to_payload():
    """Demonstrate Markdown to payload conversion."""
    print("\n" + "=" * 60)
    print("3. MarkdownContent → NotionPayload (Core Function 3)")
    print("=" * 60)
    
    # Create a sample Markdown file
    sample_markdown = """# Sample Notion Page

This demonstrates the **Markdown to JSON** converter with various formatting options.

## Features

### Text Formatting
- **Bold text**
- *Italic text*
- ***Bold and italic***
- ~~Strikethrough~~
- `inline code`
- [Link to Notion](https://notion.so)

### Lists

#### Unordered List
- First item
- Second item
  - Nested item 1
  - Nested item 2
- Third item

#### Ordered List
1. Step one
2. Step two
3. Step three

#### Todo List
- [ ] Uncompleted task
- [x] Completed task
- [ ] Another task

### Code Block

```python
def hello_notion():
    print("Hello from Notion!")
    return True
```

### Quote

> This is a blockquote.
> It can span multiple lines.

### Table

| Feature | Supported | Notes |
|---------|-----------|-------|
| Bold | Yes | **Works** |
| Links | Yes | [Example](https://example.com) |
| Code | Yes | `print()` |

---

End of document."""
    
    # Save the sample markdown
    with open('output/sample.md', 'w', encoding='utf-8') as f:
        f.write(sample_markdown)
    
    # Convert to JSON
    markdown_to_json_file('output/sample.md', 'output/sample_converted.json')
    
    # Read and display the result
    with open('output/sample_converted.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print("\nConverted JSON structure:")
    print(f"- Page title: {json_data['properties']['title']['title'][0]['text']['content']}")
    print(f"- Number of blocks: {len(json_data['children'])}")
    print(f"- Block types: {[block['type'] for block in json_data['children'][:5]]}...")
    print("\nFull JSON saved to: output/sample_converted.json")


def demo_round_trip():
    """Demonstrate round-trip conversion."""
    print("\n" + "=" * 60)
    print("Round-Trip Conversion Test")
    print("=" * 60)
    
    # Original Markdown
    original_md = """# Round Trip Test

This text has **bold**, *italic*, and `code` formatting.

## List Example
- Item 1
- Item 2
  - Nested item

> A quote block

```python
print("Code block")
```

| Col1 | Col2 |
|------|------|
| A    | B    |"""
    
    print("\n1. Original Markdown:")
    print(original_md)
    
    # MD -> JSON
    md_converter = MarkdownToNotionConverter()
    json_data = md_converter.convert_markdown(original_md)
    
    print("\n2. Converted to JSON (block types):")
    print([block['type'] for block in json_data['children']])
    
    # JSON -> MD
    json_converter = NotionToMarkdownConverter()
    result_md = json_converter.convert_page(json_data)
    
    print("\n3. Converted back to Markdown:")
    print(result_md)
    
    # Check if content is preserved
    print("\n4. Content preservation check:")
    key_elements = ['**bold**', '*italic*', '`code`', 'Item 1', 'Nested item', 
                   '> A quote', '```python', '| Col1']
    
    for element in key_elements:
        if element in result_md:
            print(f"  [OK] {element[:20]}... preserved")
        else:
            print(f"  [FAIL] {element[:20]}... lost")


def main():
    """Run all demonstrations."""
    import os
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    print("\n" + "=" * 60)
    print("BIDIRECTIONAL NOTION-MARKDOWN CONVERTER DEMONSTRATION")
    print("=" * 60)
    
    # Run demonstrations
    demo_json_to_markdown()
    demo_markdown_to_json()
    demo_round_trip()
    
    print("\n" + "=" * 60)
    print("Demonstration complete!")
    print("Check the 'output' directory for generated files.")
    print("=" * 60)


if __name__ == "__main__":
    main()