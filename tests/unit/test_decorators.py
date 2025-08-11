"""Unit tests for decorator behavior, especially error handling."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import Context

from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.utils.decorators import check_write_access


@pytest.mark.anyio
class TestCheckWriteAccessDecorator:
    """Test the check_write_access decorator behavior."""

    async def test_check_write_access_returns_json_error_in_read_only_mode(self):
        """Test that check_write_access returns JSON error instead of raising exception."""
        # Create a mock function
        mock_func = AsyncMock(return_value="success")
        mock_func.__name__ = "create_issue"

        # Apply decorator
        decorated_func = check_write_access(mock_func)

        # Create context with read-only mode
        app_context = MainAppContext(
            full_jira_config=None,
            full_confluence_config=None,
            read_only=True,  # Enable read-only mode
            enabled_tools=None,
        )

        # Mock the FastMCP context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.request_context.lifespan_context = {
            "app_lifespan_context": app_context
        }

        # Call the decorated function
        result = await decorated_func(mock_ctx)

        # Verify it returns JSON error instead of raising
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert error_data["error"] == "Cannot create issue in read-only mode."
        assert error_data["success"] is False
        assert error_data["read_only_mode"] is True

        # Verify the original function was not called
        mock_func.assert_not_called()

    async def test_check_write_access_allows_execution_when_not_read_only(self):
        """Test that check_write_access allows execution when not in read-only mode."""
        # Create a mock function
        expected_result = json.dumps({"success": True, "data": "test"})
        mock_func = AsyncMock(return_value=expected_result)
        mock_func.__name__ = "create_issue"

        # Apply decorator
        decorated_func = check_write_access(mock_func)

        # Create context with read-only mode disabled
        app_context = MainAppContext(
            full_jira_config=None,
            full_confluence_config=None,
            read_only=False,  # Disable read-only mode
            enabled_tools=None,
        )

        # Mock the FastMCP context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.request_context.lifespan_context = {
            "app_lifespan_context": app_context
        }

        # Call the decorated function
        result = await decorated_func(mock_ctx, "arg1", kwarg1="value1")

        # Verify it returns the expected result
        assert result == expected_result

        # Verify the original function was called with correct args
        mock_func.assert_called_once_with(mock_ctx, "arg1", kwarg1="value1")

    async def test_check_write_access_handles_missing_context_gracefully(self):
        """Test that check_write_access handles missing context gracefully."""
        # Create a mock function
        expected_result = json.dumps({"success": True})
        mock_func = AsyncMock(return_value=expected_result)
        mock_func.__name__ = "create_issue"

        # Apply decorator
        decorated_func = check_write_access(mock_func)

        # Mock the FastMCP context with no lifespan context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.request_context.lifespan_context = {}

        # Call the decorated function
        result = await decorated_func(mock_ctx)

        # Should allow execution when context is missing
        assert result == expected_result
        mock_func.assert_called_once()

    async def test_check_write_access_handles_none_context(self):
        """Test that check_write_access handles None app context."""
        # Create a mock function
        expected_result = json.dumps({"success": True})
        mock_func = AsyncMock(return_value=expected_result)
        mock_func.__name__ = "update_issue"

        # Apply decorator
        decorated_func = check_write_access(mock_func)

        # Mock the FastMCP context with None app context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.request_context.lifespan_context = {"app_lifespan_context": None}

        # Call the decorated function
        result = await decorated_func(mock_ctx)

        # Should allow execution when app context is None
        assert result == expected_result
        mock_func.assert_called_once()
