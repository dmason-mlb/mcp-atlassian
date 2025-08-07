"""Confluence FastMCP server instance and tool definitions."""

# Import the aggregated confluence_mcp from the modular structure
from .confluence.confluence_server import confluence_mcp

# For backward compatibility, export confluence_mcp
__all__ = [
    "confluence_mcp",
]
