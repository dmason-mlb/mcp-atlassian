"""Layout plugins for ADF multi-column content.

This module contains plugins for layout and column structures.
"""

import re
from typing import Any

from .adf_plugin_base import BaseADFPlugin


class LayoutPlugin(BaseADFPlugin):
    """Plugin for ADF layout nodes (multi-column layouts).

    Supports syntax:
    :::layout columns=2
    ::: column
    Content for first column.
    :::
    ::: column
    Content for second column.
    :::
    :::
    """

    @property
    def name(self) -> str:
        return "layout"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        # Match the entire :::layout block including nested columns
        # This needs to be greedy and capture everything until the final :::
        return re.compile(
            r"^(:::layout(?:\s+columns=\d+)?.*?^:::)$", re.MULTILINE | re.DOTALL
        )

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        return None  # Layout is block-only

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Parse layout block match."""
        # For layout blocks, the match gives us the full block
        full_block = match.group(0)

        # Parse attributes from the first line
        lines = full_block.split("\n")
        first_line = lines[0]

        # Extract columns parameter
        import re as re_module

        cols_match = re_module.search(r"columns=(\d+)", first_line)
        num_columns = int(cols_match.group(1)) if cols_match else 2

        # Find content between :::layout and closing :::
        content_start = full_block.find("\n") + 1
        content_end = full_block.rfind("\n:::")
        inner_content = (
            full_block[content_start:content_end] if content_end > content_start else ""
        )

        # Parse individual columns with a simpler pattern
        # Match ::: column through to the next ::: (either column or end)
        column_pattern = re_module.compile(
            r"::: column\s*\n(.*?)\n:::", re_module.DOTALL
        )

        columns = []
        for col_match in column_pattern.finditer(inner_content):
            columns.append(col_match.group(1).strip())

        return {"type": "layout", "num_columns": num_columns, "columns": columns}

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Not applicable for layout blocks."""
        raise NotImplementedError("Layout is a block-only node")

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Render layout data to ADF node."""
        columns = []

        for column_content in data["columns"]:
            # Parse column content as block-level markdown
            if column_content.strip():
                section_content = render_content(column_content, block_mode=True)

                # Ensure section_content is a list
                if not isinstance(section_content, list):
                    section_content = [section_content]
            else:
                section_content = [
                    {"type": "paragraph", "content": [{"type": "text", "text": ""}]}
                ]

            # Create a layoutColumn with layoutSection
            columns.append(
                {
                    "type": "layoutColumn",
                    "attrs": {
                        "width": 100.0 / data["num_columns"]  # Equal width columns
                    },
                    "content": [{"type": "layoutSection", "content": section_content}],
                }
            )

        # Ensure we have the expected number of columns
        while len(columns) < data["num_columns"]:
            columns.append(
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 100.0 / data["num_columns"]},
                    "content": [
                        {
                            "type": "layoutSection",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": ""}],
                                }
                            ],
                        }
                    ],
                }
            )

        # Return the layout node with columns
        return {"type": "layout", "content": columns}

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Not applicable for layout blocks."""
        raise NotImplementedError("Layout is a block-only node")

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate layout node against ADF spec."""
        errors = []

        # Check required fields
        if node.get("type") != "layout":
            errors.append("Layout node must have type='layout'")

        # Check columns
        content = node.get("content", [])
        if not content:
            errors.append("Layout must have content columns")

        for column in content:
            if column.get("type") != "layoutColumn":
                errors.append(
                    f"Layout can only contain layoutColumn nodes, not {column.get('type')}"
                )

            # Check column attributes
            attrs = column.get("attrs", {})
            if "width" not in attrs:
                errors.append("LayoutColumn must have width attribute")
            elif not isinstance(attrs["width"], (int, float)):
                errors.append("LayoutColumn width must be a number")
            elif attrs["width"] < 0 or attrs["width"] > 100:
                errors.append("LayoutColumn width must be between 0 and 100")

            # Check sections
            column_content = column.get("content", [])
            if not column_content:
                errors.append("LayoutColumn must have content sections")

            for section in column_content:
                if section.get("type") != "layoutSection":
                    errors.append(
                        f"LayoutColumn can only contain layoutSection nodes, not {section.get('type')}"
                    )

        return len(errors) == 0, errors
