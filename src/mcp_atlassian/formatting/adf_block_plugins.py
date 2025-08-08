"""Block-level ADF plugins for structured content elements.

This module contains plugins for block-level ADF nodes like panels,
media, expand sections, and layouts.
"""

import re
from typing import Any

from .adf_plugin_base import BaseADFPlugin


class PanelPlugin(BaseADFPlugin):
    """Plugin for ADF panel nodes.

    Supports syntax:
    :::panel type="info"
    Panel content here
    :::
    """

    @property
    def name(self) -> str:
        return "panel"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        # Match :::panel blocks with optional type attribute
        # Updated to handle empty panels (no content between markers)
        return re.compile(
            r'^:::panel(?:\s+type="(info|note|warning|success|error)")?\s*\n'
            r"(.*?)"
            r"^:::$",
            re.MULTILINE | re.DOTALL,
        )

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        return None  # Panel is block-only

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Parse panel block match."""
        # The match groups are:
        # Group 1: panel type (info, note, warning, success, error) or None
        # Group 2: panel content
        panel_type = match.group(1) or "info"  # Default to info
        panel_content = match.group(2) if match.group(2) else ""

        return {
            "type": "panel",
            "panel_type": panel_type,
            "content": panel_content.strip(),
        }

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Not applicable for panel blocks."""
        raise NotImplementedError("Panel is a block-only node")

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Render panel data to ADF node."""
        # The render_content function passed in should handle block-level content
        # when called with block_mode=True
        content = data["content"]

        if content.strip():
            # Ask render_content to parse as blocks, not inline
            wrapped_content = render_content(content, block_mode=True)

            # Ensure wrapped_content is a list
            if not isinstance(wrapped_content, list):
                wrapped_content = [wrapped_content]
        else:
            wrapped_content = [
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]}
            ]

        return {
            "type": "panel",
            "attrs": {"panelType": data["panel_type"]},
            "content": wrapped_content,
        }

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Not applicable for panel blocks."""
        raise NotImplementedError("Panel is a block-only node")

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate panel node against ADF spec."""
        errors = []

        # Check required fields
        if node.get("type") != "panel":
            errors.append("Panel node must have type='panel'")

        attrs = node.get("attrs", {})
        panel_type = attrs.get("panelType")

        if not panel_type:
            errors.append("Panel must have panelType attribute")
        elif panel_type not in ("info", "note", "warning", "success", "error"):
            errors.append(f"Invalid panelType: {panel_type}")

        # Check content
        content = node.get("content", [])
        if not content:
            errors.append("Panel must have content")

        # Validate content types (only certain nodes allowed in panels)
        allowed_types = {"bulletList", "heading", "orderedList", "paragraph"}
        for child in content:
            if child.get("type") not in allowed_types:
                errors.append(f"Panel cannot contain {child.get('type')} nodes")

        return len(errors) == 0, errors
