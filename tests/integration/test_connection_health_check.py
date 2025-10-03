"""Integration tests for connection health check functionality.

This module tests the connection_health_check tool to validate:
- Configuration validation for Jira and Confluence
- Authentication testing (success and failure scenarios)
- Connectivity validation
- Dry run mode functionality
- Error handling and status aggregation
- Context passing after P0 fix
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP
from src.mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestConnectionHealthCheck:
    """Test suite for connection health check functionality."""

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

        # Create the proper _mcp_server structure that was fixed in P0
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    async def test_connection_health_check_both_services_healthy(self, mock_server):
        """Test health check when both services are healthy."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:

            # Mock successful fetchers
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            mock_confluence_fetcher = AsyncMock()
            mock_confluence_fetcher.get_current_user.return_value = {"email": "test@example.com"}
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Call the health check
            result_json = await connection_health_check(service=None, dry_run=False)
            result = json.loads(result_json)

            # Verify overall structure
            assert "timestamp" in result
            assert "checks" in result
            assert "overall_status" in result
            assert result["overall_status"] == "healthy"

            # Verify Jira health check
            jira_check = result["checks"]["jira"]
            assert jira_check["service"] == "jira"
            assert jira_check["status"] == "healthy"
            assert jira_check["configuration"] == "valid"
            assert jira_check["authentication"] == "valid"
            assert jira_check["connectivity"] == "valid"
            assert jira_check["errors"] == []

            # Verify Confluence health check
            confluence_check = result["checks"]["confluence"]
            assert confluence_check["service"] == "confluence"
            assert confluence_check["status"] == "healthy"
            assert confluence_check["configuration"] == "valid"
            assert confluence_check["authentication"] == "valid"
            assert confluence_check["connectivity"] == "valid"
            assert confluence_check["errors"] == []

    async def test_connection_health_check_single_service(self, mock_server):
        """Test health check for a single service."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            # Call health check for Jira only
            result_json = await connection_health_check(service="jira", dry_run=False)
            result = json.loads(result_json)

            # Should only have Jira check
            assert "jira" in result["checks"]
            assert "confluence" not in result["checks"]
            assert result["overall_status"] == "healthy"

    async def test_connection_health_check_dry_run_mode(self, mock_server):
        """Test health check in dry run mode (no API calls)."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:

            # Mock fetchers (but they shouldn't be called for auth/connectivity in dry run)
            mock_jira_fetcher = AsyncMock()
            mock_get_jira.return_value = mock_jira_fetcher

            mock_confluence_fetcher = AsyncMock()
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Call health check in dry run mode
            result_json = await connection_health_check(service=None, dry_run=True)
            result = json.loads(result_json)

            # Verify dry run behavior
            for service_check in result["checks"].values():
                assert service_check["configuration"] == "valid"
                assert service_check["authentication"] == "not_tested"
                assert service_check["connectivity"] == "not_tested"
                assert service_check["status"] == "healthy"

            # Verify fetchers were created but auth methods not called
            mock_get_jira.assert_called_once()
            mock_get_confluence.assert_called_once()
            mock_jira_fetcher.get_current_user_account_id.assert_not_called()
            mock_confluence_fetcher.get_current_user.assert_not_called()

    async def test_connection_health_check_configuration_error(self, mock_server):
        """Test health check when configuration is invalid."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            # Mock configuration error
            mock_get_jira.side_effect = ValueError("Jira client (fetcher) not available. Ensure server is configured correctly.")

            # Call health check
            result_json = await connection_health_check(service="jira", dry_run=False)
            result = json.loads(result_json)

            # Verify error handling
            jira_check = result["checks"]["jira"]
            assert jira_check["status"] == "unhealthy"
            assert jira_check["configuration"] == "invalid"
            assert len(jira_check["errors"]) > 0
            assert "Configuration error" in jira_check["errors"][0]
            assert result["overall_status"] == "unhealthy"

    async def test_connection_health_check_authentication_error(self, mock_server):
        """Test health check when authentication fails."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.side_effect = MCPAtlassianAuthenticationError(
                "Authentication failed: Invalid credentials"
            )
            mock_get_jira.return_value = mock_jira_fetcher

            # Call health check
            result_json = await connection_health_check(service="jira", dry_run=False)
            result = json.loads(result_json)

            # Verify authentication error handling
            jira_check = result["checks"]["jira"]
            assert jira_check["status"] == "unhealthy"
            assert jira_check["configuration"] == "valid"
            assert jira_check["authentication"] == "invalid"
            assert len(jira_check["errors"]) > 0
            assert "Authentication error" in jira_check["errors"][0]
            assert result["overall_status"] == "unhealthy"

    async def test_connection_health_check_connectivity_error(self, mock_server):
        """Test health check when connectivity fails."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:
            mock_confluence_fetcher = AsyncMock()
            mock_confluence_fetcher.get_current_user.side_effect = ConnectionError(
                "Failed to connect to Confluence server"
            )
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Call health check
            result_json = await connection_health_check(service="confluence", dry_run=False)
            result = json.loads(result_json)

            # Verify connectivity error handling
            confluence_check = result["checks"]["confluence"]
            assert confluence_check["status"] == "unhealthy"
            assert confluence_check["configuration"] == "valid"
            assert confluence_check["connectivity"] == "failed"
            assert len(confluence_check["errors"]) > 0
            assert "Connectivity error" in confluence_check["errors"][0]
            assert result["overall_status"] == "unhealthy"

    async def test_connection_health_check_mixed_status(self, mock_server):
        """Test health check when one service is healthy and one is unhealthy."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.main.get_confluence_fetcher') as mock_get_confluence:

            # Mock successful Jira
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            # Mock failed Confluence
            mock_confluence_fetcher = AsyncMock()
            mock_confluence_fetcher.get_current_user.side_effect = MCPAtlassianAuthenticationError(
                "Invalid Confluence credentials"
            )
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Call health check
            result_json = await connection_health_check(service=None, dry_run=False)
            result = json.loads(result_json)

            # Verify mixed status
            assert result["checks"]["jira"]["status"] == "healthy"
            assert result["checks"]["confluence"]["status"] == "unhealthy"
            assert result["overall_status"] == "unhealthy"  # Should be unhealthy if any service is unhealthy

    async def test_connection_health_check_context_passing_regression(self, mock_server):
        """Test that health check properly passes context after P0 fix."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            # Call health check
            result_json = await connection_health_check(service="jira", dry_run=False)

            # Verify the context was passed correctly (no AttributeError)
            mock_get_jira.assert_called_once()

            # Verify the context passed has lifespan_context access (the P0 fix)
            call_args = mock_get_jira.call_args[0]
            context = call_args[0]
            assert hasattr(context, 'lifespan_context')
            assert context.lifespan_context is not None

            # Verify successful result
            result = json.loads(result_json)
            assert result["checks"]["jira"]["status"] == "healthy"

    async def test_connection_health_check_unexpected_error(self, mock_server):
        """Test health check handles unexpected errors gracefully."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            # Mock unexpected error
            mock_get_jira.side_effect = RuntimeError("Unexpected system error")

            # Call health check
            result_json = await connection_health_check(service="jira", dry_run=False)
            result = json.loads(result_json)

            # Verify error handling
            jira_check = result["checks"]["jira"]
            assert jira_check["status"] == "unhealthy"
            assert len(jira_check["errors"]) > 0
            assert "Unexpected error" in jira_check["errors"][0]
            assert result["overall_status"] == "unhealthy"

    async def test_connection_health_check_json_structure_validation(self, mock_server):
        """Test that health check returns properly structured JSON."""
        from src.mcp_atlassian.servers.main import connection_health_check

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            # Call health check
            result_json = await connection_health_check(service="jira", dry_run=True)

            # Verify JSON is valid and well-structured
            result = json.loads(result_json)

            # Required top-level fields
            assert "timestamp" in result
            assert "checks" in result
            assert "overall_status" in result

            # Each service check should have required fields
            for service_name, service_check in result["checks"].items():
                assert "service" in service_check
                assert "status" in service_check
                assert "configuration" in service_check
                assert "authentication" in service_check
                assert "connectivity" in service_check
                assert "errors" in service_check
                assert isinstance(service_check["errors"], list)
                assert service_check["service"] == service_name
                assert service_check["status"] in ["healthy", "unhealthy", "unknown"]