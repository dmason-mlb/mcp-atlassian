"""Meta-tools for MCP Atlassian server.

This package contains meta-tools that consolidate multiple individual tools
into unified interfaces, reducing token usage while maintaining full functionality.
"""

from .errors import MetaToolError
from .resource_manager import ResourceManager
from .schema_discovery import MinimalSchema, SchemaDiscovery, schema_discovery

__all__ = [
    "MetaToolError",
    "ResourceManager",
    "schema_discovery",
    "SchemaDiscovery",
    "MinimalSchema",
]
