"""Plugin registry for managing ADF plugins.

This module provides the registry system for managing and processing
ADF plugins for block and inline content.
"""

import logging
from typing import Any

from .adf_plugin_base import BaseADFPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing ADF plugins."""

    def __init__(self):
        self.plugins: dict[str, BaseADFPlugin] = {}
        self._block_plugins: list[BaseADFPlugin] = []
        self._inline_plugins: list[BaseADFPlugin] = []

    def register(self, plugin: BaseADFPlugin) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin to register
        """
        if plugin.name in self.plugins:
            logger.warning(f"Overriding existing plugin: {plugin.name}")

        self.plugins[plugin.name] = plugin

        # Categorize by type
        if plugin.block_pattern:
            self._block_plugins.append(plugin)
        if plugin.inline_pattern:
            self._inline_plugins.append(plugin)

        logger.debug(f"Registered plugin: {plugin.name}")

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name.

        Args:
            name: The plugin name
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            del self.plugins[name]

            # Remove from categorized lists
            if plugin in self._block_plugins:
                self._block_plugins.remove(plugin)
            if plugin in self._inline_plugins:
                self._inline_plugins.remove(plugin)

            logger.debug(f"Unregistered plugin: {name}")

    def get_block_plugins(self) -> list[BaseADFPlugin]:
        """Get all plugins that handle block nodes."""
        return self._block_plugins.copy()

    def get_inline_plugins(self) -> list[BaseADFPlugin]:
        """Get all plugins that handle inline nodes."""
        return self._inline_plugins.copy()

    def process_block_text(self, text: str, render_content) -> list[dict[str, Any]]:
        """Process text for block-level plugin matches.

        Args:
            text: The markdown text to process
            render_content: Function to render nested content

        Returns:
            List of ADF nodes found by plugins
        """
        nodes = []

        for plugin in self._block_plugins:
            pattern = plugin.block_pattern
            if not pattern:
                continue

            for match in pattern.finditer(text):
                try:
                    data = plugin.parse_block(match, text)
                    node = plugin.render_block(data, render_content)

                    # Validate if enabled
                    is_valid, errors = plugin.validate(node)
                    if not is_valid:
                        logger.warning(
                            f"Plugin {plugin.name} validation errors: {errors}"
                        )

                    nodes.append(node)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}", exc_info=True)

        return nodes

    def process_inline_text(self, text: str) -> list[dict[str, Any]]:
        """Process text for inline plugin matches.

        Args:
            text: The text to process

        Returns:
            List of inline ADF nodes found by plugins
        """
        nodes = []

        for plugin in self._inline_plugins:
            pattern = plugin.inline_pattern
            if not pattern:
                continue

            for match in pattern.finditer(text):
                try:
                    data = plugin.parse_inline(match)
                    node = plugin.render_inline(data)

                    # Validate if enabled
                    is_valid, errors = plugin.validate(node)
                    if not is_valid:
                        logger.warning(
                            f"Plugin {plugin.name} validation errors: {errors}"
                        )

                    nodes.append(node)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin.name}: {e}")

        return nodes


# Global registry instance
registry = PluginRegistry()


def register_default_plugins():
    """Register all default ADF plugins."""
    from .adf_block_plugins import PanelPlugin
    from .adf_inline_plugins import DatePlugin, EmojiPlugin, MentionPlugin, StatusPlugin
    from .adf_layout_plugins import LayoutPlugin
    from .adf_media_plugins import ExpandPlugin, MediaPlugin

    # Register default plugins
    registry.register(PanelPlugin())
    registry.register(MediaPlugin())
    registry.register(ExpandPlugin())
    registry.register(StatusPlugin())
    registry.register(DatePlugin())
    registry.register(MentionPlugin())
    registry.register(EmojiPlugin())
    registry.register(LayoutPlugin())


# Register plugins on module import
register_default_plugins()
