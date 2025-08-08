"""Base plugin class for ADF node extensions.

This module provides the abstract base class that all ADF plugins must implement.
"""

import logging
import re
from abc import ABC, abstractmethod
from re import Pattern
from typing import Any

logger = logging.getLogger(__name__)


class BaseADFPlugin(ABC):
    """Base class for ADF node plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the plugin."""
        pass

    @property
    @abstractmethod
    def block_pattern(self) -> Pattern[str] | None:
        """Regex pattern for block-level node detection.

        Returns None for inline-only plugins.
        """
        pass

    @property
    @abstractmethod
    def inline_pattern(self) -> Pattern[str] | None:
        """Regex pattern for inline node detection.

        Returns None for block-only plugins.
        """
        pass

    @abstractmethod
    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Parse a block-level match into ADF node data.

        Args:
            match: The regex match object
            content: The content within the block

        Returns:
            Dictionary containing node data
        """
        pass

    @abstractmethod
    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Parse an inline match into ADF node data.

        Args:
            match: The regex match object

        Returns:
            Dictionary containing node data
        """
        pass

    @abstractmethod
    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Render block data to ADF node.

        Args:
            data: Parsed node data
            render_content: Function to render nested content

        Returns:
            ADF node dictionary
        """
        pass

    @abstractmethod
    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Render inline data to ADF node.

        Args:
            data: Parsed node data

        Returns:
            ADF node dictionary
        """
        pass

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate the rendered ADF node.

        Args:
            node: The ADF node to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Default implementation - subclasses can override
        return True, []
