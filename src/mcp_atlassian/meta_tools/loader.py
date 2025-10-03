#!/usr/bin/env python3
"""Meta-tools loader for MCP Atlassian server.

Legacy v1 tools have been removed. Only v2 meta-tools are available.
This module maintains backward compatibility for imports.
"""

import logging

logger = logging.getLogger(__name__)


def log_tool_loading_decision() -> None:
    """Log that only v2 meta-tools are available."""
    logger.info("Loading v2 meta-tools (legacy tools have been removed)")


# Backward compatibility exports - all return v2 since legacy tools are removed
__all__ = [
    "log_tool_loading_decision"
]