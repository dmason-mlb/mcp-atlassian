"""Confluence-specific text preprocessing module."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from md2conf.converter import (
    ConfluenceConverterOptions,
    ConfluenceStorageFormatConverter,
    elements_from_string,
    elements_to_string,
    markdown_to_html,
)

from ..formatting.router import FormatRouter
from .base import BasePreprocessor

logger = logging.getLogger("mcp-atlassian")


class ConfluencePreprocessor(BasePreprocessor):
    """Handles text preprocessing for Confluence content."""

    def __init__(self, base_url: str) -> None:
        """
        Initialize the Confluence text preprocessor.

        Args:
            base_url: Base URL for Confluence API
        """
        super().__init__(base_url=base_url)
        self.format_router = FormatRouter()

    def markdown_to_confluence_storage(
        self, markdown_content: str, *, enable_heading_anchors: bool = False
    ) -> str:
        """
        Convert Markdown content to Confluence storage format (XHTML)

        Args:
            markdown_content: Markdown text to convert
            enable_heading_anchors: Whether to enable automatic heading anchor generation (default: False)

        Returns:
            Confluence storage format (XHTML) string
        """
        try:
            # First convert markdown to HTML
            html_content = markdown_to_html(markdown_content)

            # Create a temporary directory for any potential attachments
            temp_dir = tempfile.mkdtemp()

            try:
                # Parse the HTML into an element tree
                root = elements_from_string(html_content)

                # Create converter options
                options = ConfluenceConverterOptions(
                    ignore_invalid_url=True,
                    heading_anchors=enable_heading_anchors,
                    render_mermaid=False,
                )

                # Create a converter
                converter = ConfluenceStorageFormatConverter(
                    options=options,
                    path=Path(temp_dir) / "temp.md",
                    root_dir=Path(temp_dir),
                    page_metadata={},
                )

                # Transform the HTML to Confluence storage format
                converter.visit(root)

                # Convert the element tree back to a string
                storage_format = elements_to_string(root)

                return str(storage_format)
            finally:
                # Clean up the temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Error converting markdown to Confluence storage format: {e}")
            logger.exception(e)

            # Fall back to a simpler method if the conversion fails
            html_content = markdown_to_html(markdown_content)

            # Use a different approach that doesn't rely on the HTML macro
            # This creates a proper Confluence storage format document
            storage_format = f"""<p>{html_content}</p>"""

            return str(storage_format)

    def markdown_to_confluence(
        self,
        markdown_content: str,
        *,
        enable_heading_anchors: bool = False,
        enable_adf: bool = True,
    ) -> str | dict[str, Any]:
        """
        Convert Markdown content to appropriate Confluence format (ADF or storage format).

        Uses FormatRouter to automatically detect deployment type and choose format:
        - Cloud instances: Returns ADF JSON dictionary
        - Server/DC instances: Returns Confluence storage format (XHTML) string

        Args:
            markdown_content: Markdown text to convert
            enable_heading_anchors: Whether to enable automatic heading anchor generation (default: False)
            enable_adf: Whether to enable ADF conversion (default: True)

        Returns:
            For Cloud: Dictionary containing ADF JSON structure
            For Server/DC: String in Confluence storage format (XHTML)
        """
        if not markdown_content:
            if enable_adf:
                # Try to determine if we should return ADF or storage format
                result = self.format_router.convert_markdown("", self.base_url)
                if result["format"] == "adf":
                    return result["content"]  # Return ADF JSON
                else:
                    return ""  # Return empty string for storage format
            return ""

        if not enable_adf:
            # Fall back to legacy storage format conversion
            return self.markdown_to_confluence_storage(
                markdown_content, enable_heading_anchors=enable_heading_anchors
            )

        try:
            # Use format router to convert based on deployment type
            result = self.format_router.convert_markdown(
                markdown_content, self.base_url
            )

            if result["format"] == "adf":
                # Return ADF JSON for Cloud instances
                return result["content"]
            else:
                # For Server/DC instances, fall back to storage format conversion
                # since Confluence Server/DC doesn't use wiki markup like Jira
                return self.markdown_to_confluence_storage(
                    markdown_content, enable_heading_anchors=enable_heading_anchors
                )

        except Exception as e:
            logger.error(
                f"Format conversion failed, falling back to storage format: {e}"
            )
            # Fallback to legacy storage format conversion
            return self.markdown_to_confluence_storage(
                markdown_content, enable_heading_anchors=enable_heading_anchors
            )

    # Confluence-specific methods can be added here
