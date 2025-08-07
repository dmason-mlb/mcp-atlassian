"""Plugin architecture for ADF node extensions.

This module provides a plugin system for extending the ADF AST generator with
support for additional ADF nodes like panel, expand, status, etc.
"""

# Import components from modular files
from .adf_plugin_base import BaseADFPlugin
from .adf_plugin_registry import PluginRegistry, registry

# Import all plugins for backward compatibility
from .adf_block_plugins import PanelPlugin
from .adf_inline_plugins import DatePlugin, EmojiPlugin, MentionPlugin, StatusPlugin
from .adf_layout_plugins import LayoutPlugin
from .adf_media_plugins import ExpandPlugin, MediaPlugin

__all__ = [
    "BaseADFPlugin",
    "PanelPlugin",
    "MediaPlugin",
    "ExpandPlugin",
    "StatusPlugin",
    "DatePlugin",
    "MentionPlugin",
    "EmojiPlugin",
    "LayoutPlugin",
    "PluginRegistry",
    "registry",
]
