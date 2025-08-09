# Notion Markdown Converter

A powerful bidirectional converter between Notion API JSON format and Markdown. Perfect for importing/exporting Notion content, backups, and integrations.

## Features

- 🔄 **Bidirectional Conversion**: Convert from Notion JSON to Markdown and back
- 📝 **Full Markdown Support**: Handles all standard Markdown elements
- 🎨 **Rich Text Formatting**: Bold, italic, strikethrough, code, links, and more
- 📊 **Complex Structures**: Tables, nested lists, code blocks with syntax highlighting
- ✅ **Well Tested**: Comprehensive test suite with 29+ tests
- 🚀 **Easy to Use**: Simple API for both programmatic and command-line usage

## Supported Elements

### Block Types
- **Headings** (H1, H2, H3)
- **Paragraphs**
- **Lists** (Bulleted, Numbered, Todo/Checkboxes)
- **Nested Lists** (with proper indentation)
- **Code Blocks** (with language specification)
- **Quotes/Blockquotes**
- **Tables** (with headers and alignment)
- **Horizontal Rules/Dividers**

### Text Formatting
- **Bold** (`**text**`)
- **Italic** (`*text*`)
- **Bold+Italic** (`***text***`)
- **Strikethrough** (`~~text~~`)
- **Inline Code** (`` `code` ``)
- **Underline** (`<u>text</u>`)
- **Links** (`[text](url)`)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/notion_md_converter.git
cd notion_md_converter

# Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Convert Notion JSON to Markdown

```python
from notion_markdown_converter import json_to_markdown_file

# Convert a Notion JSON export to Markdown
json_to_markdown_file('notion_export.json', 'output.md')
```

### Convert Markdown to Notion JSON

```python
from notion_markdown_converter import markdown_to_json_file

# Convert a Markdown file to Notion JSON format
markdown_to_json_file('document.md', 'notion_import.json')
```

### Programmatic Usage

```python
from notion_markdown_converter import (
    NotionToMarkdownConverter,
    MarkdownToNotionConverter
)

# JSON to Markdown
json_converter = NotionToMarkdownConverter()
markdown_text = json_converter.convert_page(notion_json_data)

# Markdown to JSON
md_converter = MarkdownToNotionConverter()
notion_json = md_converter.convert_markdown(markdown_text)
```

## Setup for Notion API Integration

1.  **Create a Notion Integration:**
    *   Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations).
    *   Click "+ New integration".
    *   Give it a name, associate it with a workspace, and submit.
    *   On the next page, under "Capabilities", make sure "Read content", "Update content", and "Insert content" are all enabled.
    *   Copy the "Internal Integration Token".

2.  **Set up environment variables:**
    *   Create a `.env` file in the project root by copying the `.env.example` file.
    *   Add your Notion token to the `.env` file:
        ```
        NOTION_TOKEN="your_internal_integration_token"
        ```

3.  **Configure Page URLs:**
    *   Create a `config.json` file by copying the `config.json.example` file.
    *   Inside `config.json`, replace the placeholder URLs with the full URLs of your source and parent pages.
        ```json
        {
            "source_page_url": "https://www.notion.so/your-workspace/Your-Source-Page-Title-24a865260e43813180f0e007bc6e0ff3",
            "parent_page_url": "https://www.notion.so/your-workspace/Your-Parent-Page-Title-some-other-id"
        }
        ```

4.  **Share the relevant pages with your integration:**
    *   You must share both the **source page** and the **parent page** with your integration.
    *   For each page, click the "..." menu -> "Add connections" -> and select your integration.

## Examples

### Basic Usage Example

Run the comprehensive example to see all features:

```bash
python examples/basic_usage.py
```

This demonstrates:
- JSON to Markdown conversion
- Markdown to JSON conversion
- Round-trip conversion with content preservation

### Notion API Integration

The library includes helper scripts for working with the Notion API:

#### Fetch a Notion Page

```bash
python examples/fetch_page.py
```

This will fetch a page from Notion and save it as JSON.

#### Create a New Notion Page from JSON

```bash
python examples/convert_and_create_page.py
```

This will create a new Notion page from a JSON file.

## Project Structure

```
notion_md_converter/
├── notion_markdown_converter/     # Main library package
│   ├── __init__.py               # Package initialization
│   ├── json_to_markdown.py       # Notion JSON to Markdown converter
│   ├── markdown_to_json.py       # Markdown to Notion JSON converter
│   └── utils.py                  # Utility functions
├── examples/                      # Example scripts
│   ├── basic_usage.py            # Basic conversion examples
│   ├── fetch_page.py             # Fetch page from Notion API
│   └── convert_and_create_page.py # Create Notion page from JSON
├── tests/                         # Test suite
│   └── test_markdown_to_json.py  # Comprehensive tests
├── references/                    # Reference files for testing
│   ├── reference_1.json          # Sample Notion JSON
│   └── reference_1.md            # Sample Markdown
└── requirements.txt              # Python dependencies
```

## Testing

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_markdown_to_json.py -v
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this in your own projects!