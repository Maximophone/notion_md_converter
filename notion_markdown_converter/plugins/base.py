"""
Base classes for converter plugins.

This module defines the interface for creating plugins that can customize
conversion behavior between different formats.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple


class ConverterPlugin(ABC):
    """Base class for converter plugins that can customize conversion behavior."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this plugin."""
        pass
    
    def can_handle_block(self, block_type: str, block_data: Dict[str, Any]) -> bool:
        """
        Check if this plugin can handle a specific block type.
        
        Args:
            block_type: The type of block (e.g., 'callout', 'toggle')
            block_data: The block data
            
        Returns:
            True if this plugin can handle the block, False otherwise
        """
        return False
    
    def notion_to_markdown(self, block_type: str, block_data: Dict[str, Any]) -> Optional[str]:
        """
        Convert a Notion block to Markdown.
        
        Args:
            block_type: The type of block
            block_data: The block data
            
        Returns:
            Markdown string if handled, None otherwise
        """
        return None
    
    def markdown_to_notion(self, line: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Convert a Markdown line to a Notion block.
        
        Args:
            line: The Markdown line
            
        Returns:
            Tuple of (block_type, block_data) if handled, None otherwise
        """
        return None
    
    def get_unknown_block_markdown(self, block_type: str, block_data: Dict[str, Any]) -> str:
        """
        Generate Markdown for an unknown block type that preserves the data.
        
        Args:
            block_type: The type of block
            block_data: The block data
            
        Returns:
            Markdown string that preserves the block data
        """
        import json
        preserved_data = {
            "type": block_type,
            "data": block_data
        }
        return f"<!-- NOTION_BLOCK: {json.dumps(preserved_data, separators=(',', ':'))} -->"
    
    def parse_preserved_block(self, markdown_line: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parse a preserved block from Markdown back to Notion format.
        
        Args:
            markdown_line: The Markdown line containing preserved block data
            
        Returns:
            Tuple of (block_type, block_data) if this is a preserved block, None otherwise
        """
        import json
        import re
        
        pattern = r'<!-- NOTION_BLOCK: (.*?) -->'
        match = re.search(pattern, markdown_line.strip())
        if match:
            try:
                preserved_data = json.loads(match.group(1))
                return preserved_data.get("type"), preserved_data.get("data", {})
            except json.JSONDecodeError:
                pass
        return None


class DefaultPlugin(ConverterPlugin):
    """Default plugin that handles preservation of unknown blocks."""
    
    def get_name(self) -> str:
        return "default"
    
    def can_handle_block(self, block_type: str, block_data: Dict[str, Any]) -> bool:
        # Default plugin can handle unknown blocks by preserving them
        return True
    
    def notion_to_markdown(self, block_type: str, block_data: Dict[str, Any]) -> Optional[str]:
        # For unknown blocks, preserve them in comments
        return self.get_unknown_block_markdown(block_type, block_data)
    
    def markdown_to_notion(self, line: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        # Try to parse preserved blocks
        return self.parse_preserved_block(line)