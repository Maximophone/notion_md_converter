# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT: Read Development Logs First

**ALWAYS read these files at the start of each session:**
- `AI_DEVELOPMENT_LOG.md` - Contains AI session history, completed work, and known issues
- `DEV_LOG.md` - Human developer's log with current goals and context

These logs contain critical context about ongoing work, architectural decisions, and project direction. Pay attention to dates as older information may be outdated.

## Development Commands

### Testing
```bash
# Run all tests with the virtual environment's pytest
.venv/Scripts/python -m pytest -v

# Run specific test file
.venv/Scripts/python -m pytest tests/test_markdown_to_json.py -v

# Run specific test class or method
.venv/Scripts/python -m pytest tests/test_markdown_to_json.py::TestMarkdownToNotionConverter -v
.venv/Scripts/python -m pytest tests/test_markdown_to_json.py::TestMarkdownToNotionConverter::test_round_trip_conversion -v
```

### Virtual Environment
The project uses a virtual environment at `.venv/`. Always use:
- `.venv/Scripts/python` for running Python scripts on Windows
- `.venv/Scripts/pytest` for running tests directly

### Installation
```bash
# Install dependencies in virtual environment
.venv/Scripts/pip install -r requirements.txt

# Install package in development mode
.venv/Scripts/pip install -e .
```

## Project Structure

### Main Components
- `notion_markdown_converter/` - Core library package
  - `json_to_markdown.py` - Notion JSON to Markdown conversion
  - `markdown_to_json.py` - Markdown to Notion JSON conversion
  - `utils.py` - Utility functions
- `examples/` - Example scripts for Notion API integration
- `tests/` - Test suite
- `references/` - Reference files for testing conversions

### Configuration
- `.env` - Notion API token (create from `.env.example`)
- `config.json` - Page URLs for API scripts (create from `config.json.example`)

## Notes

- Check the development logs for current architectural decisions and ongoing refactoring
- The codebase structure and purpose may evolve - refer to recent log entries for context
- Test coverage exists in `tests/test_markdown_to_json.py`