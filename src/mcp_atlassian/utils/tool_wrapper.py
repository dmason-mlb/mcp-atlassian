"""Utility to automatically wrap all MCP tools with error handling."""

import logging
from typing import Any

from fastmcp import FastMCP

from .tool_helpers import safe_tool_result

logger = logging.getLogger(__name__)


def wrap_all_tools_with_error_handling(mcp_server: FastMCP[Any]) -> None:
    """
    Wrap all tools in the MCP server with safe_tool_result decorator.
    
    This ensures that all tools return JSON responses even when exceptions occur,
    preventing the "missing tool_result" API errors.
    
    Args:
        mcp_server: The FastMCP server instance whose tools should be wrapped.
    """
    # Get all tools from the server
    tools = mcp_server._tool_manager._tools
    
    wrapped_count = 0
    for tool_name, tool in tools.items():
        # Check if the tool function is already wrapped
        if hasattr(tool.fn, "__wrapped__"):
            # Check if it's wrapped by safe_tool_result
            current = tool.fn
            while hasattr(current, "__wrapped__"):
                if current.__name__ == "wrapper" and "safe_tool_result" in str(current.__code__.co_filename):
                    logger.debug(f"Tool '{tool_name}' is already wrapped with safe_tool_result")
                    break
                current = current.__wrapped__
            else:
                # Not wrapped with safe_tool_result, wrap it
                tool.fn = safe_tool_result(tool.fn)
                wrapped_count += 1
                logger.debug(f"Wrapped tool '{tool_name}' with safe_tool_result")
        else:
            # Tool is not wrapped at all, wrap it
            tool.fn = safe_tool_result(tool.fn)
            wrapped_count += 1
            logger.debug(f"Wrapped tool '{tool_name}' with safe_tool_result")
    
    logger.info(f"Wrapped {wrapped_count} tools with safe_tool_result error handling")