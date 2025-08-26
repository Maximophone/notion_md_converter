# Notion Markdown Converter

A powerful bidirectional converter between Notion pages and Markdown with comprehensive support for Notion-specific features like toggles, callouts, mentions, and columns.

## Features

### 🔄 Three Core Conversions
- **API → Payload**: Clean raw Notion API responses for creation
- **Payload ↔ Markdown**: Bidirectional conversion with extended syntax
- **Full Round-trip**: API → Payload → Markdown → Payload → API

### 📝 Extended Markdown Syntax
Support for Notion-specific elements through extended markdown:

```markdown
# Standard Markdown
**bold** *italic* `code` [links](url)

# Notion Extensions
- [>] Toggle blocks
### [>] Toggle headers  
<aside>💡 Callout with emoji</aside>
<notion-user id="123">@username</notion-user>
<notion-page id="456"></notion-page>
<notion-date>August 10, 2025</notion-date>
$E = mc^2$ (equations)

<notion-columns>
<notion-column>Left column</notion-column>
<notion-column>Right column</notion-column>
</notion-columns>
```

### 🎯 Comprehensive Block Support
- **Text**: Paragraphs, headings (H1-H3), rich formatting
- **Lists**: Bulleted, numbered, todo lists with nesting
- **Blocks**: Quotes, code blocks, dividers, tables
- **Notion-specific**: Toggles, callouts, mentions, columns, equations

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/notion_md_converter.git
cd notion_md_converter

# Create and activate virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Install the package (installs CLI: notion-fetch, notion-upload)
pip install -e .
```

## Quick Start

### Basic Usage

```python
from notion_markdown_converter import (
    api_to_payload,
    payload_to_markdown,
    markdown_to_payload
)

# Clean API response
clean_payload = api_to_payload(raw_api_data)

# Convert to Markdown
markdown_content = payload_to_markdown(clean_payload)

# Convert back to Payload
new_payload = markdown_to_payload(markdown_content)
```

### With Notion API Integration

```python
from notion_markdown_converter import (
    fetch_page_as_payload,
    create_page_from_markdown,
    create_notion_client
)

# Setup client
client = create_notion_client(token="your_token")

# Fetch page as clean payload
payload = fetch_page_as_payload("page_id", client)

# Convert to markdown
markdown = payload_to_markdown(payload)

# Create new page from markdown
new_page = create_page_from_markdown(
    markdown, 
    parent_id="parent_page_id",
    client=client,
    parent_type="onPage",
)

# Or create inside a database
new_db_page = create_page_from_markdown(
    markdown,
    parent_id="parent_database_id",
    client=client,
    parent_type="inDatabase",
)
```

## Extended Syntax Guide

### Toggle Blocks
```markdown
- [>] This is a toggle
    Content inside the toggle

### [>] Toggle Header
    Content under toggle header
```

### Callouts
```markdown
<aside>
💡 This is a callout with a light bulb icon
Additional callout content here
</aside>
```

### Mentions
```markdown
User: <notion-user id="user-uuid">@username</notion-user>
Page: <notion-page id="page-uuid"></notion-page>
Date: <notion-date>August 10, 2025</notion-date>
```

### Math Equations
```markdown
Inline math: $E = mc^2$
```

### Front Matter for Properties
Pages can include Notion properties via YAML front matter at the top of the markdown using typed keys:

```yaml
---
"ntn:title:Name": "My Page Title"
"ntn:url:URL": "https://example.com"
"ntn:multi_select:Tags":
  - "Tag A"
  - "Tag B"
"ntn:files:Files":
  - "https://example.com/image.png"
"ntn:date:Date":
  start: "2025-08-24"
  end: null
  time_zone: null
"ntn:people:Assignees":
  - "user-id-1"
"ntn:select:Status": "In progress"
"ntn:status:Status": "In progress"
"ntn:email:Email": "test@example.com"
"ntn:checkbox:Published": true
"ntn:number:Estimate": 5
"ntn:phone_number:Phone": "+123456789"
---
```

Notes:
- The first H1 in the document is no longer treated as title; the title comes exclusively from front matter.
- Only explicit empty paragraphs in Notion map to blank lines in markdown.

### Multi-column Layout
```markdown
<notion-columns>
<notion-column>
Content for left column.
Can contain multiple paragraphs.
</notion-column>
<notion-column>
Content for right column.
Also supports **rich formatting**.
</notion-column>
</notion-columns>
```

## API Reference

### Core Conversion Functions

#### `api_to_payload(api_data: Dict) -> Dict`
Cleans raw Notion API response by removing IDs, timestamps, and metadata.

```python
clean_data = api_to_payload(raw_api_response)
```

#### `payload_to_markdown(payload: Dict) -> str`
Converts clean Notion payload to Markdown with extended syntax.

```python
markdown = payload_to_markdown(notion_payload)
```

#### `markdown_to_payload(markdown: str) -> Dict`
Converts Markdown (with extended syntax) back to Notion payload format.

```python
payload = markdown_to_payload(markdown_content)
```

### API Integration Functions

#### `create_notion_client(token: str) -> Client`
Creates authenticated Notion client.

#### `fetch_page_as_payload(page_id: str, client: Client) -> Dict`
Fetches a complete page as clean payload data.

#### `create_page_from_payload(payload: Dict, client: Client) -> Dict`
Creates a new Notion page from payload data.

#### `create_page_from_markdown(markdown: str, parent_id: str, title: Optional[str] = None, parent_type: str = "onPage", client: Client = None) -> Dict`
Creates a new Notion page directly from Markdown.

Parameters:
- `markdown`: Markdown content
- `parent_id`: The ID of the parent page or database
- `title` (optional): Overrides the page title
- `parent_type` (optional): Where to create the page. Accepts `"onPage"`/`"page"` or `"inDatabase"`/`"database"`. Defaults to `"onPage"`.

### File Conversion Functions

```python
from notion_markdown_converter import (
    payload_to_markdown_file,
    markdown_to_payload_file
)

# File conversions
payload_to_markdown_file('page.json', 'page.md')
markdown_to_payload_file('page.md', 'page.json')
```

## Setup for Notion API Integration

1. **Create a Notion Integration:**
   - Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
   - Click "+ New integration"
   - Give it a name, associate it with a workspace, and submit
   - Copy the "Internal Integration Token"

2. **Set up environment variables:**
   ```bash
   # Create .env file
   echo 'NOTION_TOKEN="your_internal_integration_token"' > .env
   ```

3. **Share pages with your integration:**
   - For each page you want to access, click "..." menu → "Add connections" → select your integration

## Examples

### Basic Page Conversion
```python
import json
from notion_markdown_converter import payload_to_markdown

# Load a Notion page payload
with open('my_page.json', 'r') as f:
    payload = json.load(f)

# Convert to Markdown
markdown = payload_to_markdown(payload)
print(markdown)
```

### Round-trip Conversion
```python
from notion_markdown_converter import (
    payload_to_markdown,
    markdown_to_payload
)

# Start with payload
original_payload = {...}

# Convert to Markdown and back
markdown = payload_to_markdown(original_payload)
reconstructed_payload = markdown_to_payload(markdown)

# Should be equivalent to original
```

### Working with Notion API
```python
import os
from notion_markdown_converter import (
    create_notion_client,
    fetch_page_as_payload,
    payload_to_markdown
)

# Setup
client = create_notion_client(os.getenv('NOTION_TOKEN'))

# Export page to Markdown
payload = fetch_page_as_payload('your-page-id', client)
markdown = payload_to_markdown(payload)

# Save to file
with open('exported_page.md', 'w', encoding='utf-8') as f:
    f.write(markdown)
```

### Command Line Interface (installed via pip)

```bash
# Fetch a page from Notion (output: payload JSON by default)
notion-fetch "https://www.notion.so/Page-Title-0123456789abcdef0123456789abcdef" -f payload -o clean_page.json

# Fetch as raw API JSON
notion-fetch "https://www.notion.so/Page-Title-0123456789abcdef0123456789abcdef" -f api -o page_api.json

# Fetch as Markdown
notion-fetch "https://www.notion.so/Page-Title-0123456789abcdef0123456789abcdef" -f markdown -o page.md

# Upload from Markdown under a parent page
notion-upload path/to/file.md "https://www.notion.so/Parent-Page-URL" --type markdown --title "Optional Title"

# Upload from Markdown into a parent database (new parent_type support)
notion-upload path/to/file.md "https://www.notion.so/Parent-Database-URL" --type markdown --parent-type database --title "Optional Title"

# Upload from payload JSON under a parent database
notion-upload path/to/payload.json "https://www.notion.so/Parent-Database-URL" --type payload --parent-type database

# Upload from raw API JSON (will be cleaned first) under a parent page
notion-upload path/to/api.json "https://www.notion.so/Parent-Page-URL" --type api --title "Optional Title"
```

Legacy scripts remain available under `scripts/` and can be run with Python if you prefer not to install the package:

```bash
python scripts/fetch_page.py "https://www.notion.so/Page-Title-..." -f markdown -o page.md
python scripts/upload_page.py path/to/file.md "https://www.notion.so/Parent-Page-URL" --type markdown
```

## Architecture

### Data Types
- **NotionApiResponse**: Raw API data with IDs, timestamps, metadata
- **NotionPayload**: Clean page data suitable for creation/conversion  
- **MarkdownContent**: Text with extended syntax for Notion elements

### Module Structure
```
notion_markdown_converter/
├── converters/
│   ├── api_to_payload.py      # API response cleaning
│   ├── payload_to_markdown.py # Payload → Markdown  
│   ├── markdown_to_payload.py # Markdown → Payload
│   └── __init__.py            # Core exports
├── api.py                     # Notion API integration
├── plugins/                   # Future extensibility
└── __init__.py               # Main exports
```

## Supported Notion Blocks

### Text Blocks
- ✅ Paragraph
- ✅ Heading 1, 2, 3 (including toggle headers)
- ✅ Rich text formatting (bold, italic, strikethrough, code, underline)
- ✅ Links

### List Blocks  
- ✅ Bulleted lists (with nesting)
- ✅ Numbered lists (with nesting)
- ✅ Todo lists (checked/unchecked)

### Media & Layout
- ✅ Code blocks (with syntax highlighting)
- ✅ Tables (with headers)
- ✅ Quotes
- ✅ Dividers
- ✅ Multi-column layouts

### Notion-Specific
- ✅ Toggle blocks
- ✅ Toggle headers
- ✅ Callouts (with emoji icons)
- ✅ User mentions
- ✅ Page mentions  
- ✅ Date mentions
- ✅ Equations (LaTeX)

## Development

### Running Tests
```bash
# Install development dependencies
pip install pytest

# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_converters.py -v

# Run legacy tests
pytest tests/test_markdown_to_json.py -v
```

### Project Structure
```
notion_md_converter/
├── notion_markdown_converter/    # Main library
│   ├── converters/              # Core conversion modules
│   ├── api.py                   # Notion API wrapper
│   └── __init__.py             # Main exports
├── tests/                       # Test suites
│   ├── test_converters.py      # New comprehensive tests
│   └── test_markdown_to_json.py # Legacy tests
├── references/                  # Reference files for testing
│   ├── *_api.json              # Raw API responses
│   ├── *_payload.json          # Clean payloads
│   └── *.md                    # Markdown with extended syntax
├── scripts/                     # Utility scripts
├── examples/                    # Usage examples
└── README.md                   # This file
```

## Backward Compatibility

The library maintains backward compatibility with v1.0 APIs:

```python
# Legacy imports still work
from notion_markdown_converter import (
    NotionToMarkdownConverter,
    MarkdownToNotionConverter,
    json_to_markdown,
    markdown_to_json
)
```

## Limitations & Known Issues

- Character encoding edge cases may need refinement (smart quotes)
- Idempotency is validated on the provided references; additional edge cases may remain
- Some advanced Notion blocks not yet supported (embeds, databases)
- Blank lines are preserved only when represented as explicit empty paragraph blocks in Notion; arbitrary visual spacing between blocks is not inferred

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### v2.0.0 (2025-08-24) - Major Refactoring
- 🚀 **Breaking**: New three-function API architecture
- ✨ **New**: Extended syntax support for Notion-specific elements
- 🔧 **New**: Integrated Notion API wrapper
- 📊 **New**: Auto-discovering comprehensive test suite
- 🏗️ **New**: Modular converter architecture for extensibility
- 🎯 **New**: Support for toggles, callouts, mentions, columns, equations
- 📝 **New**: Clean separation of API responses, payloads, and markdown

### v1.0.0 (2025-08-10) - Initial Release
- 🎉 Initial bidirectional conversion between Notion JSON and Markdown
- 📝 Support for all standard Markdown elements
- ✅ Comprehensive test coverage (29+ tests)
- 📖 Complete documentation and examples
- 🔄 Round-trip conversion support