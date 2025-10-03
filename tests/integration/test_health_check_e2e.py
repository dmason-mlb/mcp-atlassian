"""End-to-end integration tests for health check functionality.

This module tests the complete health check flow from the QA report,
ensuring that the health check tool works correctly after fixing
the "'Server' object has no attribute 'lifespan_context'" error.

Tests verify:
- Health checks work for both Jira and Confluence
- Configuration validation works properly
- Authentication testing works
- Connectivity testing works
- Error scenarios are handled correctly
- All status combinations work as expected
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP, get_tool_context, _check_service_health
from src.mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestHealthCheckE2E:
    """End-to-end test suite for health check functionality."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a mock MainAppContext with proper health check setup."""
        app_context = MagicMock()

        # Mock Jira configuration
        app_context.full_jira_config = MagicMock()
        app_context.full_jira_config.url = "https://test.atlassian.net"
        app_context.full_jira_config.auth_type = "oauth"
        app_context.full_jira_config.is_auth_configured.return_value = True

        # Mock Confluence configuration
        app_context.full_confluence_config = MagicMock()
        app_context.full_confluence_config.url = "https://test.atlassian.net"
        app_context.full_confluence_config.auth_type = "oauth"
        app_context.full_confluence_config.is_auth_configured.return_value = True

        return app_context

    @pytest.fixture
    async def mock_server(self, mock_app_context):
        """Create a mock AtlassianMCP server with proper context structure."""
        server = MagicMock(spec=AtlassianMCP)

        # Create the proper _mcp_server structure
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    async def test_health_check_both_services_healthy(self, mock_server):
        """Test health check when both services are healthy - reproduces QA test scenario."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:

            # Mock successful fetchers
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            mock_confluence_fetcher = AsyncMock()
            mock_confluence_fetcher.get_current_user.return_value = {"email": "test@example.com"}
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Test Jira health check
            jira_result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)

            # Verify successful Jira health check
            assert jira_result["service"] == "jira"
            assert jira_result["status"] == "healthy"
            assert jira_result["configuration"] == "valid"
            assert jira_result["authentication"] == "valid"
            assert jira_result["connectivity"] == "valid"
            assert jira_result["errors"] == []

            # Test Confluence health check
            confluence_result = await _check_service_health(get_tool_context(mock_server), "confluence", dry_run=False)

            # Verify successful Confluence health check
            assert confluence_result["service"] == "confluence"
            assert confluence_result["status"] == "healthy"
            assert confluence_result["configuration"] == "valid"
            assert confluence_result["authentication"] == "valid"
            assert confluence_result["connectivity"] == "valid"
            assert confluence_result["errors"] == []

    async def test_health_check_configuration_error_jira(self, mock_server):
        """Test health check when Jira configuration is invalid - matches QA report error."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            # Simulate the exact error from QA report
            mock_get_jira.side_effect = ValueError("Jira client (fetcher) not available. Ensure server is configured correctly.")

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)

            # Verify error is properly captured
            assert result["service"] == "jira"
            assert result["status"] == "unhealthy"
            assert result["configuration"] == "invalid"
            assert len(result["errors"]) > 0
            assert "Configuration error" in result["errors"][0]
            assert "Jira client (fetcher) not available" in result["errors"][0]

    async def test_health_check_configuration_error_confluence(self, mock_server):
        """Test health check when Confluence configuration is invalid."""
        with patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:
            # Simulate configuration error
            mock_get_confluence.side_effect = ValueError("Confluence client (fetcher) not available. Ensure server is configured correctly.")

            result = await _check_service_health(get_tool_context(mock_server), "confluence", dry_run=False)

            # Verify error is properly captured
            assert result["service"] == "confluence"
            assert result["status"] == "unhealthy"
            assert result["configuration"] == "invalid"
            assert len(result["errors"]) > 0
            assert "Configuration error" in result["errors"][0]

    async def test_health_check_authentication_error(self, mock_server):
        """Test health check when authentication fails."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.side_effect = MCPAtlassianAuthenticationError(
                "Authentication failed: Invalid credentials"
            )
            mock_get_jira.return_value = mock_jira_fetcher

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)

            # Verify authentication error handling
            assert result["service"] == "jira"
            assert result["status"] == "unhealthy"
            assert result["configuration"] == "valid"
            assert result["authentication"] == "invalid"
            assert len(result["errors"]) > 0
            assert "Authentication error" in result["errors"][0]

    async def test_health_check_connectivity_error(self, mock_server):
        """Test health check when connectivity fails."""
        with patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:
            mock_confluence_fetcher = AsyncMock()
            mock_confluence_fetcher.get_current_user.side_effect = ConnectionError(
                "Failed to connect to Confluence server"
            )
            mock_get_confluence.return_value = mock_confluence_fetcher

            result = await _check_service_health(get_tool_context(mock_server), "confluence", dry_run=False)

            # Verify connectivity error handling
            assert result["service"] == "confluence"
            assert result["status"] == "unhealthy"
            assert result["configuration"] == "valid"
            assert result["connectivity"] == "failed"
            assert len(result["errors"]) > 0
            assert "Connectivity error" in result["errors"][0]

    async def test_health_check_dry_run_mode(self, mock_server):
        """Test health check in dry run mode - no API calls made."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_get_jira.return_value = mock_jira_fetcher

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=True)

            # Verify dry run behavior
            assert result["service"] == "jira"
            assert result["status"] == "healthy"
            assert result["configuration"] == "valid"
            assert result["authentication"] == "not_tested"
            assert result["connectivity"] == "not_tested"
            assert result["errors"] == []

            # Verify no authentication API calls were made
            mock_jira_fetcher.get_current_user_account_id.assert_not_called()

    async def test_health_check_unexpected_error(self, mock_server):
        """Test health check handles unexpected errors gracefully."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            # Simulate unexpected error
            mock_get_jira.side_effect = RuntimeError("Unexpected system error")

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)

            # Verify error handling
            assert result["service"] == "jira"
            assert result["status"] == "unhealthy"
            assert len(result["errors"]) > 0
            assert "Unexpected error" in result["errors"][0]

    async def test_health_check_json_structure_validation(self, mock_server):
        """Test that health check returns properly structured results."""
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=True)

            # Verify JSON structure matches QA report expectations
            required_fields = ["service", "status", "configuration", "authentication", "connectivity", "errors"]
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"

            # Verify field types and values
            assert isinstance(result["service"], str)
            assert result["service"] == "jira"
            assert result["status"] in ["healthy", "unhealthy", "unknown"]
            assert result["configuration"] in ["valid", "invalid", "unknown"]
            assert result["authentication"] in ["valid", "invalid", "unknown", "not_tested"]
            assert result["connectivity"] in ["valid", "failed", "unknown", "not_tested"]
            assert isinstance(result["errors"], list)

    async def test_health_check_reproduces_qa_report_scenario(self, mock_server):
        """Test that reproduces the exact scenario from the QA report."""
        # This test simulates the exact error conditions from the QA report
        # where all operations failed with configuration errors

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:

            # Simulate the server configuration issues mentioned in QA report
            config_error_msg = "Jira client (fetcher) not available. Ensure server is configured correctly."
            mock_get_jira.side_effect = ValueError(config_error_msg)
            mock_get_confluence.side_effect = ValueError("Confluence client (fetcher) not available. Ensure server is configured correctly.")

            # Test both services
            jira_result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)
            confluence_result = await _check_service_health(get_tool_context(mock_server), "confluence", dry_run=False)

            # Verify both services show as unhealthy with configuration errors
            # This should match the QA report findings

            # Jira results
            assert jira_result["service"] == "jira"
            assert jira_result["status"] == "unhealthy"
            assert jira_result["configuration"] == "invalid"
            assert jira_result["authentication"] == "unknown"  # Not tested due to config error
            assert jira_result["connectivity"] == "unknown"   # Not tested due to config error
            assert len(jira_result["errors"]) > 0
            assert "Configuration error" in jira_result["errors"][0]

            # Confluence results
            assert confluence_result["service"] == "confluence"
            assert confluence_result["status"] == "unhealthy"
            assert confluence_result["configuration"] == "invalid"
            assert confluence_result["authentication"] == "unknown"
            assert confluence_result["connectivity"] == "unknown"
            assert len(confluence_result["errors"]) > 0
            assert "Configuration error" in confluence_result["errors"][0]

    async def test_health_check_context_access_fix(self, mock_server):
        """Test that verifies the context access fix prevents the QA report error."""
        # This is the critical test that ensures the QA report error is resolved
        context = get_tool_context(mock_server)

        # This should NOT raise: "'Server' object has no attribute 'lifespan_context'"
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user"
            mock_get_jira.return_value = mock_jira_fetcher

            try:
                # This call previously failed with the AttributeError
                result = await _check_service_health(context, "jira", dry_run=False)

                # If we get here, the error is fixed
                assert result["service"] == "jira"
                assert result["status"] == "healthy"

                # Verify the context was passed correctly to dependencies
                mock_get_jira.assert_called_once_with(context)

            except AttributeError as e:
                if "lifespan_context" in str(e):
                    pytest.fail(f"QA report error not fixed: {e}")
                else:
                    # Different AttributeError, re-raise
                    raise

    async def test_health_check_with_valid_ftest_scenario(self, mock_server):
        """Test health check with a scenario that should work for FTEST project."""
        # This test simulates a working FTEST environment scenario
        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "qa-tester-123"
            mock_get_jira.return_value = mock_jira_fetcher

            result = await _check_service_health(get_tool_context(mock_server), "jira", dry_run=False)

            # Verify this would show as healthy (unlike the QA report)
            assert result["service"] == "jira"
            assert result["status"] == "healthy"
            assert result["configuration"] == "valid"
            assert result["authentication"] == "valid"
            assert result["connectivity"] == "valid"
            assert result["errors"] == []

            # This should represent a working FTEST environment
            # where the QA tests would pass instead of fail