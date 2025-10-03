"""Utilities for parameter serialization/deserialization in MCP tools.

This module handles the conversion between JSON strings and native Python types,
which is necessary because MCP clients may serialize complex parameters as JSON strings.
"""

import json
import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def deserialize_param(param: str | T | None, expected_type: type[T]) -> T | None:
    """Deserialize a parameter that may be a JSON string or native Python type.

    MCP clients (like Claude Desktop) may serialize complex parameters (dicts, lists)
    as JSON strings. This function handles both cases, returning the deserialized
    native type or the original value if already in the correct format.

    Args:
        param: Parameter value that may be a JSON string, native type, or None
        expected_type: The expected Python type (dict, list, etc.)

    Returns:
        Deserialized parameter value or None if param is None

    Examples:
        >>> deserialize_param('{"key": "value"}', dict)
        {'key': 'value'}

        >>> deserialize_param({'key': 'value'}, dict)
        {'key': 'value'}

        >>> deserialize_param(None, dict)
        None
    """
    if param is None:
        return None

    # If already the expected type, return as-is
    if isinstance(param, expected_type):
        return param

    # If it's a string, try to parse as JSON
    if isinstance(param, str):
        try:
            parsed = json.loads(param)
            # Verify the parsed result is the expected type
            if not isinstance(parsed, expected_type):
                logger.warning(
                    f"Parsed JSON is type {type(parsed).__name__}, "
                    f"expected {expected_type.__name__}. "
                    f"Returning parsed value anyway."
                )
            return parsed
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to deserialize parameter as JSON: {e}. "
                f"Parameter value: {param[:100]}..."
                if len(param) > 100
                else f"Parameter value: {param}"
            )
            # For string parameters where JSON parsing fails, return the string
            # This handles cases where the param is legitimately a plain string
            if expected_type == str:
                return param
            raise ValueError(
                f"Parameter must be valid JSON or a {expected_type.__name__}, "
                f"got invalid JSON string: {str(e)}"
            ) from e

    # If we get here, the type doesn't match and it's not a string
    logger.warning(
        f"Parameter is type {type(param).__name__}, expected "
        f"{expected_type.__name__} or JSON string. Returning as-is."
    )
    return param
