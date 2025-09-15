"""Simplified format routing for Atlassian deployments.

This module provides simple format detection and conversion without over-engineering.
"""

import logging
from typing import Any

from .adf_ast import ASTBasedADFGenerator

logger = logging.getLogger(__name__)


class SimpleFormatRouter:
    """Simplified router for text formatting based on deployment type.

    Detects Cloud vs Server/DC deployments and converts markdown accordingly:
    - Cloud (.atlassian.net/.atlassian.com): ADF format
    - Server/DC (custom domains): Wiki markup format
    """

    def __init__(self):
        """Initialize the router with ADF generator."""
        self.adf_generator = ASTBasedADFGenerator()

    def convert_markdown(self, markdown_text: str, base_url: str) -> dict[str, Any]:
        """Convert markdown to appropriate format based on deployment type.

        Args:
            markdown_text: Markdown content to convert
            base_url: Base URL to determine deployment type

        Returns:
            Dictionary with converted content, format type, and deployment type
        """
        try:
            if self._is_cloud_deployment(base_url):
                # Cloud deployment - use ADF
                adf_content = self.adf_generator.markdown_to_adf(markdown_text)
                return {
                    "content": adf_content,
                    "format": "adf",
                    "deployment_type": "cloud"
                }
            else:
                # Server/DC deployment - use wiki markup
                wiki_content = self._markdown_to_wiki_markup(markdown_text)
                return {
                    "content": wiki_content,
                    "format": "wiki_markup",
                    "deployment_type": "server"
                }
        except Exception as e:
            logger.warning(f"Format conversion failed, using plain text: {e}")
            return {
                "content": markdown_text,
                "format": "plain_text",
                "deployment_type": "unknown"
            }

    def _is_cloud_deployment(self, base_url: str) -> bool:
        """Check if URL indicates Atlassian Cloud deployment.

        Args:
            base_url: URL to check

        Returns:
            True if Cloud deployment, False for Server/DC
        """
        if not base_url:
            return False

        return ('.atlassian.net' in base_url.lower() or
                '.atlassian.com' in base_url.lower())

    def _markdown_to_wiki_markup(self, markdown: str) -> str:
        """Convert markdown to Confluence wiki markup.

        Args:
            markdown: Markdown text to convert

        Returns:
            Wiki markup string
        """
        if not markdown:
            return ""

        # Basic markdown to wiki markup conversion
        wiki = markdown

        # Headers
        wiki = wiki.replace('# ', 'h1. ')
        wiki = wiki.replace('## ', 'h2. ')
        wiki = wiki.replace('### ', 'h3. ')
        wiki = wiki.replace('#### ', 'h4. ')
        wiki = wiki.replace('##### ', 'h5. ')
        wiki = wiki.replace('###### ', 'h6. ')

        # Bold and italic
        wiki = wiki.replace('**', '*')  # Bold
        wiki = wiki.replace('__', '_')  # Italic

        # Code blocks
        wiki = wiki.replace('```', '{code}')
        wiki = wiki.replace('`', '{{')
        wiki = wiki.replace('`', '}}')

        # Lists (basic conversion)
        lines = wiki.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('- '):
                lines[i] = line.replace('- ', '* ', 1)
            elif line.strip().startswith('* '):
                lines[i] = line.replace('* ', '* ', 1)

        return '\n'.join(lines)


# Create a default instance for backward compatibility
format_router = SimpleFormatRouter()

def convert_markdown(markdown_text: str, base_url: str) -> dict[str, Any]:
    """Convert markdown using the default router instance."""
    return format_router.convert_markdown(markdown_text, base_url)

def is_cloud_deployment(base_url: str) -> bool:
    """Check if URL indicates Cloud deployment using default router."""
    return format_router._is_cloud_deployment(base_url)


# Backward compatibility alias
FormatRouter = SimpleFormatRouter