"""Media and expand plugins for ADF content.

This module contains plugins for media elements and expand/collapse sections.
"""

import re
from typing import Any

from .adf_plugin_base import BaseADFPlugin


class MediaPlugin(BaseADFPlugin):
    """Plugin for ADF media nodes (images, videos, files).

    Supports syntax:
    :::media
    type: image
    url: https://example.com/image.png
    alt: Description of image
    width: 800
    height: 600
    :::
    """

    @property
    def name(self) -> str:
        return "media"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        # Match :::media blocks
        return re.compile(
            r"^:::media\s*\n"
            r"((?:.*?\n)*?)"
            r"^:::$",
            re.MULTILINE | re.DOTALL,
        )

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        return None  # Media is block-only

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Parse media block match."""
        media_content = match.group(1).strip()

        # Parse YAML-like content
        attrs = {}
        for line in media_content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Convert numeric values
                if key in ("width", "height") and value.isdigit():
                    attrs[key] = int(value)
                else:
                    attrs[key] = value

        # Default to image type if not specified
        media_type = attrs.get("type", "image")

        return {"type": "media", "media_type": media_type, "attrs": attrs}

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Not applicable for media blocks."""
        raise NotImplementedError("Media is a block-only node")

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Render media data to ADF node."""
        attrs = data["attrs"]
        media_type = data["media_type"]

        # Build media single node
        media_single = {
            "type": "mediaSingle",
            "content": [
                {
                    "type": "media",
                    "attrs": {
                        "id": attrs.get("id", ""),  # Media ID in Confluence
                        "type": media_type,
                        "collection": attrs.get("collection", ""),
                    },
                }
            ],
        }

        # Add dimensions if provided
        if "width" in attrs:
            media_single["content"][0]["attrs"]["width"] = attrs["width"]
        if "height" in attrs:
            media_single["content"][0]["attrs"]["height"] = attrs["height"]

        # Add layout if specified
        if "layout" in attrs:
            media_single["attrs"] = {"layout": attrs["layout"]}

        return media_single

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Not applicable for media blocks."""
        raise NotImplementedError("Media is a block-only node")

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate media node against ADF spec."""
        errors = []

        # Check required fields
        if node.get("type") != "mediaSingle":
            errors.append("Media node must have type='mediaSingle'")

        content = node.get("content", [])
        if not content:
            errors.append("MediaSingle must have content")
        elif len(content) != 1:
            errors.append("MediaSingle must have exactly one media child")
        elif content[0].get("type") != "media":
            errors.append("MediaSingle child must be type='media'")

        # Check media attributes
        if content:
            media = content[0]
            media_attrs = media.get("attrs", {})

            if not media_attrs.get("id"):
                errors.append("Media must have an id attribute")

            media_type = media_attrs.get("type")
            if media_type not in ("file", "image", "video"):
                errors.append(f"Invalid media type: {media_type}")

        # Check layout attribute if present
        if "attrs" in node:
            layout = node["attrs"].get("layout")
            if layout and layout not in (
                "center",
                "wrap-left",
                "wrap-right",
                "wide",
                "full-width",
            ):
                errors.append(f"Invalid media layout: {layout}")

        return len(errors) == 0, errors


class ExpandPlugin(BaseADFPlugin):
    """Plugin for ADF expand (collapsible) nodes.

    Supports syntax:
    :::expand title="Click to expand"
    Content that is hidden by default.

    Can contain multiple paragraphs and formatting.
    :::
    """

    @property
    def name(self) -> str:
        return "expand"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        # Match :::expand blocks with optional title
        return re.compile(
            r'^:::expand(?:\s+title="([^"]+)")?\s*\n'
            r"(.*?)\n"
            r"^:::$",
            re.MULTILINE | re.DOTALL,
        )

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        return None  # Expand is block-only

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Parse expand block match."""
        title = match.group(1) or "Click to expand"
        expand_content = match.group(2).strip()

        return {"type": "expand", "title": title, "content": expand_content}

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Not applicable for expand blocks."""
        raise NotImplementedError("Expand is a block-only node")

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Render expand data to ADF node."""
        content = data["content"]

        if content.strip():
            # Parse as block-level content
            wrapped_content = render_content(content, block_mode=True)

            # Ensure wrapped_content is a list
            if not isinstance(wrapped_content, list):
                wrapped_content = [wrapped_content]
        else:
            wrapped_content = [
                {"type": "paragraph", "content": [{"type": "text", "text": ""}]}
            ]

        return {
            "type": "expand",
            "attrs": {"title": data["title"]},
            "content": wrapped_content,
        }

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Not applicable for expand blocks."""
        raise NotImplementedError("Expand is a block-only node")

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate expand node against ADF spec."""
        errors = []

        # Check required fields
        if node.get("type") != "expand":
            errors.append("Expand node must have type='expand'")

        attrs = node.get("attrs", {})
        if not attrs.get("title"):
            errors.append("Expand must have title attribute")

        # Check content
        content = node.get("content", [])
        if not content:
            errors.append("Expand must have content")

        # Validate content types (only certain nodes allowed in expand)
        allowed_types = {
            "bulletList",
            "heading",
            "orderedList",
            "paragraph",
            "panel",
            "blockquote",
            "codeBlock",
        }
        for child in content:
            if child.get("type") not in allowed_types:
                errors.append(f"Expand cannot contain {child.get('type')} nodes")

        return len(errors) == 0, errors