"""Inline ADF plugins for text-level elements.

This module contains plugins for inline ADF nodes like status badges,
dates, mentions, and emojis.
"""

import re
from typing import Any

from .adf_plugin_base import BaseADFPlugin


class StatusPlugin(BaseADFPlugin):
    """Plugin for ADF status inline nodes.

    Supports syntax:
    {status:color=green}Done{/status}
    {status:color=yellow}In Progress{/status}
    {status:color=red}Blocked{/status}
    """

    @property
    def name(self) -> str:
        return "status"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        return None  # Status is inline-only

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        # Match {status:color=X}text{/status}
        return re.compile(
            r"\{status:color=(green|yellow|red|blue|purple|grey)\}"
            r"([^{]+?)"
            r"\{/status\}"
        )

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Not applicable for status inline nodes."""
        raise NotImplementedError("Status is an inline-only node")

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Parse status inline match."""
        color = match.group(1)
        text = match.group(2)

        return {"type": "status", "color": color, "text": text}

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Not applicable for status inline nodes."""
        raise NotImplementedError("Status is an inline-only node")

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Render status data to ADF node."""
        return {
            "type": "status",
            "attrs": {"text": data["text"], "color": data["color"]},
        }

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate status node against ADF spec."""
        errors = []

        if node.get("type") != "status":
            errors.append("Status node must have type='status'")

        attrs = node.get("attrs", {})
        if not attrs.get("text"):
            errors.append("Status must have text attribute")

        color = attrs.get("color")
        if color not in ("green", "yellow", "red", "blue", "purple", "grey"):
            errors.append(f"Invalid status color: {color}")

        return len(errors) == 0, errors


class DatePlugin(BaseADFPlugin):
    """Plugin for ADF date inline nodes.

    Supports syntax:
    {date:2024-03-15}
    """

    @property
    def name(self) -> str:
        return "date"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        return None  # Date is inline-only

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        # Match {date:YYYY-MM-DD}
        return re.compile(r"\{date:(\d{4}-\d{2}-\d{2})\}")

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Not applicable for date inline nodes."""
        raise NotImplementedError("Date is an inline-only node")

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Parse date inline match."""
        date_str = match.group(1)

        # Convert to timestamp (milliseconds since epoch)
        try:
            from datetime import datetime

            dt = datetime.strptime(date_str, "%Y-%m-%d")
            timestamp = int(dt.timestamp() * 1000)
        except ValueError:
            # Invalid date, use current timestamp
            from datetime import datetime

            timestamp = int(datetime.now().timestamp() * 1000)

        return {"type": "date", "timestamp": timestamp}

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Not applicable for date inline nodes."""
        raise NotImplementedError("Date is an inline-only node")

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Render date data to ADF node."""
        return {"type": "date", "attrs": {"timestamp": data["timestamp"]}}

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate date node against ADF spec."""
        errors = []

        if node.get("type") != "date":
            errors.append("Date node must have type='date'")

        attrs = node.get("attrs", {})
        if "timestamp" not in attrs:
            errors.append("Date must have timestamp attribute")
        elif not isinstance(attrs["timestamp"], (int, float)):
            errors.append("Date timestamp must be a number")

        return len(errors) == 0, errors


class MentionPlugin(BaseADFPlugin):
    """Plugin for ADF mention inline nodes.

    Supports syntax:
    @username
    @[John Doe]
    """

    @property
    def name(self) -> str:
        return "mention"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        return None  # Mention is inline-only

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        # Match @username or @[Full Name]
        # Allow dots in usernames
        return re.compile(r"@(?:([a-zA-Z0-9_.-]+)|\[([^\]]+)\])")

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Not applicable for mention inline nodes."""
        raise NotImplementedError("Mention is an inline-only node")

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Parse mention inline match."""
        # Either simple username or bracketed full name
        username = match.group(1)
        full_name = match.group(2)

        text = username or full_name

        return {
            "type": "mention",
            "text": text,
            "id": text.lower().replace(" ", "."),  # Simple ID generation
        }

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Not applicable for mention inline nodes."""
        raise NotImplementedError("Mention is an inline-only node")

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Render mention data to ADF node."""
        return {
            "type": "mention",
            "attrs": {"id": data["id"], "text": f"@{data['text']}"},
        }

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate mention node against ADF spec."""
        errors = []

        if node.get("type") != "mention":
            errors.append("Mention node must have type='mention'")

        attrs = node.get("attrs", {})
        if not attrs.get("id"):
            errors.append("Mention must have id attribute")

        return len(errors) == 0, errors


class EmojiPlugin(BaseADFPlugin):
    """Plugin for ADF emoji inline nodes.

    Supports syntax:
    :smile:
    :thumbsup:
    :warning:
    """

    # Common emoji mappings
    EMOJI_MAP = {
        "smile": "😊",
        "thumbsup": "👍",
        "thumbsdown": "👎",
        "warning": "⚠️",
        "info": "ℹ️",
        "check": "✅",
        "cross": "❌",
        "star": "⭐",
        "heart": "❤️",
        "fire": "🔥",
    }

    @property
    def name(self) -> str:
        return "emoji"

    @property
    def block_pattern(self) -> re.Pattern[str] | None:
        return None  # Emoji is inline-only

    @property
    def inline_pattern(self) -> re.Pattern[str] | None:
        # Match :emoji_name:
        return re.compile(r":([a-zA-Z0-9_]+):")

    def parse_block(self, match: re.Match[str], content: str) -> dict[str, Any]:
        """Not applicable for emoji inline nodes."""
        raise NotImplementedError("Emoji is an inline-only node")

    def parse_inline(self, match: re.Match[str]) -> dict[str, Any]:
        """Parse emoji inline match."""
        shortname = match.group(1)

        return {
            "type": "emoji",
            "shortname": shortname,
            "text": self.EMOJI_MAP.get(shortname, f":{shortname}:"),
        }

    def render_block(self, data: dict[str, Any], render_content) -> dict[str, Any]:
        """Not applicable for emoji inline nodes."""
        raise NotImplementedError("Emoji is an inline-only node")

    def render_inline(self, data: dict[str, Any]) -> dict[str, Any]:
        """Render emoji data to ADF node."""
        return {
            "type": "emoji",
            "attrs": {"shortName": f":{data['shortname']}:", "text": data["text"]},
        }

    def validate(self, node: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate emoji node against ADF spec."""
        errors = []

        if node.get("type") != "emoji":
            errors.append("Emoji node must have type='emoji'")

        attrs = node.get("attrs", {})
        if not attrs.get("shortName"):
            errors.append("Emoji must have shortName attribute")

        return len(errors) == 0, errors
