"""Integration tests for tool_result sequencing with FastMCP."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.context import MainAppContext


@pytest.mark.integration
@pytest.mark.anyio
class TestToolResultSequencing:
    """Test that tools properly return results in all scenarios."""

    async def test_write_tool_in_read_only_mode_returns_error_result(self):
        """Test that write tools return JSON error in read-only mode."""
        # Create app context in read-only mode WITH Jira config (so dependency check passes)
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,  # Provide config so get_jira_fetcher succeeds
            full_confluence_config=None,
            read_only=True,  # But set read-only mode
            enabled_tools=None,
        )

        # Mock FastMCP context - need to properly set up the context chain
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        mock_fastmcp = MagicMock()
        mock_fastmcp.request_context = mock_request_context

        # Create context
        ctx = Context(fastmcp=mock_fastmcp)

        # Mock the JiraFetcher to avoid actual API calls
        mock_issue = MagicMock()
        mock_issue.to_simplified_dict.return_value = {
            "key": "TEST-123",
            "summary": "Test Issue",
        }

        mock_fetcher = MagicMock()
        mock_fetcher.create_issue.return_value = mock_issue

        # Import and patch get_jira_fetcher
        from mcp_atlassian.servers.jira import create_issue

        with patch(
            "mcp_atlassian.servers.jira.get_jira_fetcher", return_value=mock_fetcher
        ):
            # Call the tool - it should return JSON error, not raise
            result = await create_issue(
                ctx, project_key="TEST", summary="Test Issue", issue_type="Task"
            )

        # Verify it returns JSON error
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "Cannot create issue in read-only mode" in error_data["error"]
        assert error_data["success"] is False
        assert error_data["read_only_mode"] is True

    async def test_tool_with_missing_configuration_returns_error_result(self):
        """Test that tools return JSON error when configuration is missing."""
        # Create app context with no Jira config
        app_context = MainAppContext(
            full_jira_config=None,  # No Jira config
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Mock FastMCP context - need to properly set up the context chain
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        mock_fastmcp = MagicMock()
        mock_fastmcp.request_context = mock_request_context

        # Create context
        ctx = Context(fastmcp=mock_fastmcp)

        # Import a read tool function
        from mcp_atlassian.servers.jira import get_issue

        # Call the tool - it should handle the ValueError from get_jira_fetcher
        result = await get_issue(ctx, issue_key="TEST-123")

        # Verify it returns JSON error
        assert isinstance(result, str)
        error_data = json.loads(result)
        assert "error" in error_data
        assert "not available" in error_data["error"].lower()

    async def test_tool_with_valid_config_executes_successfully(self):
        """Test that tools execute successfully with valid configuration."""
        # Mock Jira configuration
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        # Create app context with Jira config
        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Mock FastMCP context - need to properly set up the context chain
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        mock_fastmcp = MagicMock()
        mock_fastmcp.request_context = mock_request_context

        # Create context
        ctx = Context(fastmcp=mock_fastmcp)

        # Mock the JiraFetcher
        mock_issue = MagicMock()
        mock_issue.to_simplified_dict.return_value = {
            "key": "TEST-123",
            "summary": "Test Issue",
            "status": "Open",
        }

        mock_fetcher = MagicMock()
        mock_fetcher.get_issue.return_value = mock_issue

        # Import and patch get_jira_fetcher
        from mcp_atlassian.servers.jira import get_issue

        with patch(
            "mcp_atlassian.servers.jira.get_jira_fetcher", return_value=mock_fetcher
        ):
            # Call the tool
            result = await get_issue(ctx, issue_key="TEST-123")

        # Verify it returns valid JSON
        assert isinstance(result, str)
        result_data = json.loads(result)
        assert result_data["key"] == "TEST-123"
        assert result_data["summary"] == "Test Issue"

    async def test_multiple_error_scenarios_all_return_json(self):
        """Test various error scenarios all return JSON responses."""
        # Test data for different error scenarios
        test_scenarios = [
            {
                "name": "read_only_write_tool",
                "app_context": MainAppContext(
                    full_jira_config=MagicMock(),
                    full_confluence_config=None,
                    read_only=True,
                    enabled_tools=None,
                ),
                "tool_func": "create_issue",
                "expected_error_pattern": "Cannot create issue in read-only mode",
            },
            {
                "name": "missing_config",
                "app_context": MainAppContext(
                    full_jira_config=None,
                    full_confluence_config=None,
                    read_only=False,
                    enabled_tools=None,
                ),
                "tool_func": "get_issue",
                "expected_error_pattern": "not available",
            },
        ]

        for scenario in test_scenarios:
            # Mock FastMCP context
            mock_fastmcp = MagicMock()
            mock_fastmcp.request_context.lifespan_context = {
                "app_lifespan_context": scenario["app_context"]
            }
            ctx = Context(fastmcp=mock_fastmcp)

            # Import the tool function
            if scenario["tool_func"] == "create_issue":
                from mcp_atlassian.servers.jira import create_issue

                result = await create_issue(
                    ctx, project_key="TEST", summary="Test", issue_type="Task"
                )
            else:
                from mcp_atlassian.servers.jira import get_issue

                result = await get_issue(ctx, issue_key="TEST-123")

            # All scenarios should return JSON
            assert isinstance(result, str), (
                f"Scenario {scenario['name']} didn't return string"
            )
            try:
                error_data = json.loads(result)
                assert "error" in error_data, (
                    f"Scenario {scenario['name']} missing error field"
                )
                assert scenario["expected_error_pattern"] in error_data["error"], (
                    f"Scenario {scenario['name']} error message doesn't match pattern"
                )
            except json.JSONDecodeError:
                pytest.fail(
                    f"Scenario {scenario['name']} returned invalid JSON: {result}"
                )
