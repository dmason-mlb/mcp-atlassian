class MCPAtlassianError(Exception):
    """Base exception for all MCP Atlassian errors."""
    pass


class MCPAtlassianAuthenticationError(MCPAtlassianError):
    """Raised when Atlassian API authentication fails (401/403)."""
    pass


class MCPAtlassianNotFoundError(MCPAtlassianError):
    """Raised when requested resource is not found (404)."""
    pass


class MCPAtlassianPermissionError(MCPAtlassianError):
    """Raised when user lacks permission for operation (403)."""
    pass


class MCPAtlassianValidationError(MCPAtlassianError):
    """Raised when request validation fails (400)."""
    pass
