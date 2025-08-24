"""
Plugin system for extending conversion capabilities.

This module provides base classes for creating plugins that can extend
the conversion behavior between different formats.
"""

from .base import ConverterPlugin

__all__ = ["ConverterPlugin"]