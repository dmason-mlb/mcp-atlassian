#!/usr/bin/env python3
"""Version-based tool loader for MCP Atlassian server.

This module handles loading of different tool versions:
- v1: Legacy tools (42 individual tools from existing Jira/Confluence servers)
- v2: Meta-tools (6-10 consolidated tools for token optimization)

Only one version can be loaded at a time to prevent token waste.
"""

import logging
import os
from enum import Enum
from typing import Literal, Optional

logger = logging.getLogger(__name__)


class ToolVersion(Enum):
    """Supported tool versions."""
    
    V1 = "v1"
    V2 = "v2"


def get_tool_version() -> ToolVersion:
    """Get the tool version to load based on CLI flags and environment variables.
    
    Priority order:
    1. MCP_VERSION environment variable
    2. Default to v1 for backward compatibility
    
    Returns:
        ToolVersion: The version to load (v1 or v2)
        
    Raises:
        ValueError: If an invalid version is specified
    """
    version_str = os.getenv("MCP_VERSION", "v1").lower()
    
    try:
        version = ToolVersion(version_str)
        logger.debug(f"Tool version determined: {version.value}")
        return version
    except ValueError:
        valid_versions = [v.value for v in ToolVersion]
        logger.error(
            f"Invalid tool version '{version_str}'. Valid options: {valid_versions}"
        )
        raise ValueError(
            f"Invalid tool version '{version_str}'. Valid options: {valid_versions}"
        )


def should_load_v1_tools() -> bool:
    """Check if v1 (legacy) tools should be loaded."""
    return get_tool_version() == ToolVersion.V1


def should_load_v2_tools() -> bool:
    """Check if v2 (meta) tools should be loaded."""
    return get_tool_version() == ToolVersion.V2


def validate_version_exclusivity() -> None:
    """Validate that only one version is loaded.
    
    This is a safety check to ensure we don't accidentally load both
    v1 and v2 tools simultaneously.
    
    Raises:
        RuntimeError: If both versions are set to load
    """
    v1_enabled = should_load_v1_tools()
    v2_enabled = should_load_v2_tools()
    
    if v1_enabled and v2_enabled:
        raise RuntimeError(
            "Both v1 and v2 tools are set to load. This should never happen."
        )
    
    if not v1_enabled and not v2_enabled:
        raise RuntimeError(
            "Neither v1 nor v2 tools are set to load. This should never happen."
        )
    
    logger.debug(f"Version exclusivity validated: v1={v1_enabled}, v2={v2_enabled}")


def get_version_tag() -> Literal["v1", "v2"]:
    """Get the version tag for tool filtering.
    
    Returns:
        str: Version tag ("v1" or "v2")
    """
    return get_tool_version().value


def log_tool_loading_decision() -> None:
    """Log the tool loading decision for debugging."""
    version = get_tool_version()
    tool_count_estimate = 42 if version == ToolVersion.V1 else 10
    
    logger.info(
        f"Tool version selected: {version.value} "
        f"(~{tool_count_estimate} tools estimated)"
    )
    
    if version == ToolVersion.V1:
        logger.info("Loading legacy tools for backward compatibility")
    else:
        logger.info("Loading optimized meta-tools for token efficiency")


# Export commonly used functions
__all__ = [
    "ToolVersion",
    "get_tool_version", 
    "should_load_v1_tools",
    "should_load_v2_tools",
    "validate_version_exclusivity",
    "get_version_tag",
    "log_tool_loading_decision"
]