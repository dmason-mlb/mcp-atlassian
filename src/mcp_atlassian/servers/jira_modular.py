"""Modular Jira FastMCP server with core functions extracted to focused modules."""

# Import the shared FastMCP instance and common dependencies
# Import agile functions from focused modules

# Import core CRUD functions from focused modules

# Import linking functions from focused modules

# Import project functions from focused modules

# Import search functions from focused modules
from .jira_shared import jira_mcp

# Import workflow functions from focused modules

# Export the FastMCP app instance
__all__ = ["jira_mcp"]
