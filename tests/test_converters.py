"""
Comprehensive test suite for all three core conversion types:
1. NotionApiResponse → NotionPayload
2. NotionPayload → MarkdownContent  
3. MarkdownContent → NotionPayload

Tests auto-discover reference files and verify idempotency.
"""

import json
import pytest
import sys
import os
import glob
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_markdown_converter import (
    NotionApiToPayloadConverter,
    api_to_payload,
    NotionPayloadToMarkdownConverter,
    payload_to_markdown, 
    NotionMarkdownToPayloadConverter,
    markdown_to_payload
)


class TestReferenceDiscovery:
    """Test reference file discovery and validation."""
    
    @staticmethod
    def discover_references():
        """
        Discover all reference sets in the references directory.
        
        Returns:
            List of reference set names (e.g., ['reference_1', 'reference_3'])
        """
        references_dir = Path(__file__).parent.parent / "references"
        
        # Find all _api.json files
        api_files = glob.glob(str(references_dir / "*_api.json"))
        reference_names = []
        
        for api_file in api_files:
            # Extract base name (e.g., "reference_1" from "reference_1_api.json")
            base_name = Path(api_file).stem.replace("_api", "")
            
            # Check if corresponding payload and markdown files exist
            payload_file = references_dir / f"{base_name}_payload.json"
            markdown_file = references_dir / f"{base_name}.md"
            
            if payload_file.exists() and markdown_file.exists():
                reference_names.append(base_name)
            else:
                print(f"Warning: Incomplete reference set for {base_name}")
        
        return sorted(reference_names)
    
    def test_reference_discovery(self):
        """Test that reference files are discovered correctly."""
        references = self.discover_references()
        assert len(references) > 0, "No reference sets found"
        print(f"Discovered {len(references)} reference sets: {references}")


class TestApiToPayloadConversion:
    """Test NotionApiResponse → NotionPayload conversion."""
    
    def get_references(self):
        """Get discovered reference sets."""
        return TestReferenceDiscovery.discover_references()
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references())
    def test_api_to_payload_conversion(self, reference_name):
        """Test API response to payload conversion for each reference."""
        references_dir = Path(__file__).parent.parent / "references"
        
        api_file = references_dir / f"{reference_name}_api.json"
        expected_payload_file = references_dir / f"{reference_name}_payload.json"
        
        # Load the files
        with open(api_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        
        with open(expected_payload_file, 'r', encoding='utf-8') as f:
            expected_payload = json.load(f)
        
        # Convert API response to payload
        converter = NotionApiToPayloadConverter()
        actual_payload = converter.convert_page(api_data)
        
        # Verify conversion (ignoring placeholder parent IDs)
        assert "children" in actual_payload
        assert len(actual_payload["children"]) == len(expected_payload["children"])
        
        # Test convenience function
        convenience_result = api_to_payload(api_data)
        assert convenience_result["children"] == actual_payload["children"]
    
    def test_api_to_payload_cleaning(self):
        """Test that API-specific fields are properly removed."""
        # Create a mock API response with fields that should be cleaned
        api_response = {
            "children": [{
                "id": "block-id-123",
                "type": "paragraph", 
                "created_time": "2023-01-01T00:00:00.000Z",
                "last_edited_time": "2023-01-01T00:00:00.000Z",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "Test paragraph"}
                    }]
                }
            }]
        }
        
        converter = NotionApiToPayloadConverter()
        payload = converter.convert_page(api_response)
        
        # Verify API-specific fields are removed
        block = payload["children"][0]
        assert "id" not in block
        assert "created_time" not in block
        assert "last_edited_time" not in block
        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Test paragraph"


class TestPayloadToMarkdownConversion:
    """Test NotionPayload → MarkdownContent conversion."""
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references())
    def test_payload_to_markdown_conversion(self, reference_name):
        """Test payload to markdown conversion for each reference."""
        references_dir = Path(__file__).parent.parent / "references"
        
        payload_file = references_dir / f"{reference_name}_payload.json"
        expected_markdown_file = references_dir / f"{reference_name}.md"
        
        # Load the files
        with open(payload_file, 'r', encoding='utf-8') as f:
            payload_data = json.load(f)
        
        with open(expected_markdown_file, 'r', encoding='utf-8') as f:
            expected_markdown = f.read()
        
        # Convert payload to markdown
        converter = NotionPayloadToMarkdownConverter()
        actual_markdown = converter.convert_page(payload_data)
        
        # Compare results (normalize whitespace)
        expected_lines = [line.rstrip() for line in expected_markdown.split('\n')]
        actual_lines = [line.rstrip() for line in actual_markdown.split('\n')]
        
        assert actual_lines == expected_lines, f"Markdown conversion mismatch for {reference_name}"
        
        # Test convenience function
        convenience_result = payload_to_markdown(payload_data)
        assert convenience_result == actual_markdown


class TestMarkdownToPayloadConversion:
    """Test MarkdownContent → NotionPayload conversion."""
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references())
    def test_markdown_to_payload_conversion(self, reference_name):
        """Test markdown to payload conversion for each reference."""
        references_dir = Path(__file__).parent.parent / "references"
        
        markdown_file = references_dir / f"{reference_name}.md"
        expected_payload_file = references_dir / f"{reference_name}_payload.json"
        
        # Load the files
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        with open(expected_payload_file, 'r', encoding='utf-8') as f:
            expected_payload = json.load(f)
        
        # Convert markdown to payload
        converter = NotionMarkdownToPayloadConverter()
        actual_payload = converter.convert_markdown(markdown_content)
        
        # Compare structure (focus on children since properties might differ)
        assert "children" in actual_payload
        assert len(actual_payload["children"]) == len(expected_payload["children"])
        
        # Test convenience function
        convenience_result = markdown_to_payload(markdown_content)
        assert len(convenience_result["children"]) == len(actual_payload["children"])


class TestIdempotency:
    """Test idempotency of composed operations."""
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references())
    def test_payload_markdown_roundtrip(self, reference_name):
        """Test that payload → markdown → payload is idempotent."""
        references_dir = Path(__file__).parent.parent / "references"
        
        # Load original payload
        payload_file = references_dir / f"{reference_name}_payload.json"
        with open(payload_file, 'r', encoding='utf-8') as f:
            original_payload = json.load(f)
        
        # Convert: payload → markdown → payload
        markdown_content = payload_to_markdown(original_payload)
        roundtrip_payload = markdown_to_payload(markdown_content)
        
        # Compare key structures (children count and types)
        assert len(roundtrip_payload["children"]) == len(original_payload["children"])
        
        for orig_block, roundtrip_block in zip(original_payload["children"], roundtrip_payload["children"]):
            assert orig_block.get("type") == roundtrip_block.get("type")
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references()) 
    def test_markdown_payload_roundtrip(self, reference_name):
        """Test that markdown → payload → markdown is idempotent."""
        references_dir = Path(__file__).parent.parent / "references"
        
        # Load original markdown
        markdown_file = references_dir / f"{reference_name}.md"
        with open(markdown_file, 'r', encoding='utf-8') as f:
            original_markdown = f.read()
        
        # Convert: markdown → payload → markdown
        payload_data = markdown_to_payload(original_markdown)
        roundtrip_markdown = payload_to_markdown(payload_data)
        
        # Compare normalized content
        def normalize_markdown(content):
            # Remove trailing whitespace and normalize line endings
            lines = [line.rstrip() for line in content.split('\n')]
            # Remove empty lines at the end
            while lines and not lines[-1]:
                lines.pop()
            return '\n'.join(lines)
        
        original_normalized = normalize_markdown(original_markdown)
        roundtrip_normalized = normalize_markdown(roundtrip_markdown)
        
        assert roundtrip_normalized == original_normalized, f"Roundtrip failed for {reference_name}"


class TestFullChainConversion:
    """Test the complete conversion chain: API → Payload → Markdown → Payload."""
    
    @pytest.mark.parametrize("reference_name", TestReferenceDiscovery.discover_references())
    def test_full_conversion_chain(self, reference_name):
        """Test API → payload → markdown → payload chain."""
        references_dir = Path(__file__).parent.parent / "references"
        
        # Load API response
        api_file = references_dir / f"{reference_name}_api.json"
        with open(api_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        
        # Execute full chain
        payload1 = api_to_payload(api_data)
        markdown_content = payload_to_markdown(payload1)
        payload2 = markdown_to_payload(markdown_content)
        
        # Verify that payload1 and payload2 have same structure
        assert len(payload1["children"]) == len(payload2["children"])
        
        for block1, block2 in zip(payload1["children"], payload2["children"]):
            assert block1.get("type") == block2.get("type")


if __name__ == "__main__":
    # Run discovery test first
    discovery = TestReferenceDiscovery()
    discovery.test_reference_discovery()
    
    # Run a basic test
    api_test = TestApiToPayloadConversion()
    references = api_test.get_references()
    if references:
        print(f"Testing with reference: {references[0]}")
        api_test.test_api_to_payload_conversion(references[0])