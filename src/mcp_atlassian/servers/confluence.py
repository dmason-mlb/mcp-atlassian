"""Confluence FastMCP server instance and tool definitions.

This module re-exports the aggregated FastMCP service and individual tool
functions for backward compatibility with existing imports in tests and
downstream integrations.
"""

# Aggregated service
from .confluence import confluence_mcp  # noqa: F401

# Re-export individual tool functions
from .confluence.search import search, search_user  # noqa: F401
from .confluence.pages import (  # noqa: F401
    get_page,
    get_page_children,
    create_page,
    update_page,
    delete_page,
)
from .confluence.content import (  # noqa: F401
    get_comments,
    add_comment,
    get_labels,
    add_label,
)

__all__ = [
    "confluence_mcp",
    # Search tools
    "search",
    "search_user",
    # Page tools
    "get_page",
    "get_page_children",
    "create_page",
    "update_page",
    "delete_page",
    # Content tools
    "get_comments",
    "add_comment",
    "get_labels",
    "add_label",
]
