"""Helper utilities for tool error handling and response formatting."""

import json
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def safe_tool_result(func: F) -> F:
    """
    Decorator to ensure tool functions always return JSON responses.

    This decorator catches any exceptions raised within a tool function
    and converts them to JSON error responses. This ensures that FastMCP
    can properly emit tool_result messages with is_error=true, preventing
    API 400 errors about missing tool_result blocks.

    The decorator should be applied to all MCP tool functions after the
    @tool decorator but before any other decorators like @check_write_access.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            result = await func(*args, **kwargs)
            # Ensure result is a string (JSON)
            if not isinstance(result, str):
                result = json.dumps(result, indent=2, ensure_ascii=False)
            return result
        except MCPAtlassianAuthenticationError as e:
            # Authentication errors get special treatment
            logger.error(f"Authentication error in tool '{func.__name__}': {e}")
            return json.dumps(
                {
                    "error": str(e),
                    "success": False,
                    "error_type": "authentication_error",
                    "tool": func.__name__,
                },
                indent=2,
                ensure_ascii=False,
            )
        except ValueError as e:
            # ValueError often indicates configuration or validation issues
            logger.warning(f"ValueError in tool '{func.__name__}': {e}")
            return json.dumps(
                {
                    "error": str(e),
                    "success": False,
                    "error_type": "validation_error",
                    "tool": func.__name__,
                },
                indent=2,
                ensure_ascii=False,
            )
        except Exception as e:
            # Catch all other exceptions
            logger.error(
                f"Unexpected error in tool '{func.__name__}': {e}", exc_info=True
            )
            return json.dumps(
                {
                    "error": f"An unexpected error occurred: {str(e)}",
                    "success": False,
                    "error_type": "unexpected_error",
                    "tool": func.__name__,
                },
                indent=2,
                ensure_ascii=False,
            )

    return wrapper  # type: ignore
