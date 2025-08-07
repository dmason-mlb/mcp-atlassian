"""Confluence server module with organized tool categories."""

from fastmcp import FastMCP

from .search import SearchServer
from .pages import PagesServer
from .content import ContentServer

# Create main confluence_mcp aggregating all modules
confluence_mcp = FastMCP(
    name="Confluence MCP Service", 
    description="Provides tools for interacting with Atlassian Confluence.",
)

# Create server instances
search_server = SearchServer()
pages_server = PagesServer()
content_server = ContentServer()

# Mount all modules to aggregate their tools
confluence_mcp.mount("search", search_server.mcp)  # 2 tools: search, search_user
confluence_mcp.mount("pages", pages_server.mcp)    # 5 tools: get_page, get_page_children, create_page, update_page, delete_page
confluence_mcp.mount("content", content_server.mcp) # 4 tools: get_comments, get_labels, add_label, add_comment

__all__ = [
    "confluence_mcp",     # Main aggregated service
    "search_server",      # Individual modules for direct access
    "pages_server", 
    "content_server",
]