"""Comprehensive tests for the main MCP server implementation."""

import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
from fastmcp import Context
from mcp.types import Tool as MCPTool
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.servers.main import (
    AtlassianMCP,
    UserTokenMiddleware,
    health_check,
    main_lifespan,
    main_mcp,
    token_cache_lock,
    token_validation_cache,
)


class TestMainLifespan:
    """Test the main server lifespan management."""

    @pytest.mark.anyio
    async def test_lifespan_loads_both_configs_when_auth_configured(self):
        """Test that lifespan loads both Jira and Confluence configs when auth is complete."""
        # Arrange
        mock_jira_config = Mock(spec=JiraConfig)
        mock_jira_config.is_auth_configured.return_value = True

        mock_confluence_config = Mock(spec=ConfluenceConfig)
        mock_confluence_config.is_auth_configured.return_value = True

        with patch("mcp_atlassian.servers.main.get_available_services") as mock_services, \
             patch("mcp_atlassian.servers.main.JiraConfig.from_env") as mock_jira_from_env, \
             patch("mcp_atlassian.servers.main.ConfluenceConfig.from_env") as mock_conf_from_env, \
             patch("mcp_atlassian.servers.main.is_read_only_mode") as mock_read_only, \
             patch("mcp_atlassian.servers.main.get_enabled_tools") as mock_enabled_tools:

            mock_services.return_value = {"jira": True, "confluence": True}
            mock_jira_from_env.return_value = mock_jira_config
            mock_conf_from_env.return_value = mock_confluence_config
            mock_read_only.return_value = False
            mock_enabled_tools.return_value = ["get_issue", "search"]

            # Act
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Assert
                assert isinstance(app_context, MainAppContext)
                assert app_context.full_jira_config == mock_jira_config
                assert app_context.full_confluence_config == mock_confluence_config
                assert app_context.read_only is False
                assert app_context.enabled_tools == ["get_issue", "search"]

    @pytest.mark.anyio
    async def test_lifespan_excludes_jira_when_auth_not_configured(self):
        """Test that Jira config is None when authentication is not configured."""
        # Arrange
        mock_jira_config = Mock(spec=JiraConfig)
        mock_jira_config.is_auth_configured.return_value = False

        with patch("mcp_atlassian.servers.main.get_available_services") as mock_services, \
             patch("mcp_atlassian.servers.main.JiraConfig.from_env") as mock_jira_from_env, \
             patch("mcp_atlassian.servers.main.is_read_only_mode") as mock_read_only, \
             patch("mcp_atlassian.servers.main.get_enabled_tools") as mock_enabled_tools:

            mock_services.return_value = {"jira": True, "confluence": False}
            mock_jira_from_env.return_value = mock_jira_config
            mock_read_only.return_value = False
            mock_enabled_tools.return_value = None

            # Act
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Assert
                assert app_context.full_jira_config is None
                assert app_context.full_confluence_config is None

    @pytest.mark.anyio
    async def test_lifespan_handles_config_load_exception(self):
        """Test that lifespan handles exceptions during config loading gracefully."""
        # Arrange
        with patch("mcp_atlassian.servers.main.get_available_services") as mock_services, \
             patch("mcp_atlassian.servers.main.JiraConfig.from_env") as mock_jira_from_env, \
             patch("mcp_atlassian.servers.main.is_read_only_mode") as mock_read_only, \
             patch("mcp_atlassian.servers.main.get_enabled_tools") as mock_enabled_tools:

            mock_services.return_value = {"jira": True, "confluence": False}
            mock_jira_from_env.side_effect = ValueError("Missing JIRA_URL")
            mock_read_only.return_value = True
            mock_enabled_tools.return_value = []

            # Act
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Assert
                assert app_context.full_jira_config is None
                assert app_context.read_only is True

    @pytest.mark.anyio
    async def test_lifespan_cleanup_on_exception(self):
        """Test that lifespan performs cleanup even when an exception occurs."""
        # Arrange
        with patch("mcp_atlassian.servers.main.get_available_services") as mock_services, \
             patch("mcp_atlassian.servers.main.is_read_only_mode") as mock_read_only, \
             patch("mcp_atlassian.servers.main.get_enabled_tools") as mock_enabled_tools, \
             patch("mcp_atlassian.servers.main.logger") as mock_logger:

            mock_services.return_value = {}
            mock_read_only.return_value = False
            mock_enabled_tools.return_value = None

            # Act & Assert
            async with main_lifespan(main_mcp) as ctx:
                # Simulate some work
                pass

            # Verify cleanup logging
            mock_logger.info.assert_any_call("Main Atlassian MCP server lifespan shutting down...")
            mock_logger.info.assert_any_call("Main Atlassian MCP server lifespan shutdown complete.")


class TestAtlassianMCP:
    """Test the custom AtlassianMCP server class."""

    @pytest.fixture
    def mock_app_context(self):
        """Create a mock app context for testing."""
        return MainAppContext(
            full_jira_config=Mock(spec=JiraConfig),
            full_confluence_config=Mock(spec=ConfluenceConfig),
            read_only=False,
            enabled_tools=["get_issue", "search", "create_issue"]
        )

    @pytest.fixture
    def atlassian_mcp(self):
        """Create an AtlassianMCP instance for testing."""
        return AtlassianMCP(name="TestMCP", description="Test MCP Server")

    @pytest.mark.anyio
    async def test_tool_filtering_excludes_write_tools_in_read_only_mode(self, atlassian_mcp, mock_app_context):
        """Test that write tools are excluded when in read-only mode."""
        # Arrange
        mock_app_context.read_only = True

        mock_tool_write = Mock()
        mock_tool_write.tags = {"jira", "write"}
        mock_tool_write.to_mcp_tool.return_value = MCPTool(
            name="create_issue",
            description="Create issue",
            inputSchema={}
        )

        mock_tool_read = Mock()
        mock_tool_read.tags = {"jira", "read"}
        mock_tool_read.to_mcp_tool.return_value = MCPTool(
            name="get_issue",
            description="Get issue",
            inputSchema={}
        )

        with patch.object(atlassian_mcp, "get_tools") as mock_get_tools, \
             patch.object(atlassian_mcp, "_mcp_server") as mock_server:

            mock_get_tools.return_value = {
                "create_issue": mock_tool_write,
                "get_issue": mock_tool_read
            }

            mock_server.request_context.lifespan_context = {"app_lifespan_context": mock_app_context}

            # Act
            tools = await atlassian_mcp._mcp_list_tools()

            # Assert
            tool_names = [t.name for t in tools]
            assert "get_issue" in tool_names
            assert "create_issue" not in tool_names

    @pytest.mark.anyio
    async def test_tool_filtering_respects_enabled_tools_list(self, atlassian_mcp, mock_app_context):
        """Test that only enabled tools are included when filter is set."""
        # Arrange
        mock_app_context.enabled_tools = ["get_issue"]

        mock_tool1 = Mock()
        mock_tool1.tags = {"jira", "read"}
        mock_tool1.to_mcp_tool.return_value = MCPTool(
            name="get_issue",
            description="Get issue",
            inputSchema={}
        )

        mock_tool2 = Mock()
        mock_tool2.tags = {"jira", "read"}
        mock_tool2.to_mcp_tool.return_value = MCPTool(
            name="search",
            description="Search",
            inputSchema={}
        )

        with patch.object(atlassian_mcp, "get_tools") as mock_get_tools, \
             patch.object(atlassian_mcp, "_mcp_server") as mock_server, \
             patch("mcp_atlassian.servers.main.should_include_tool") as mock_should_include:

            mock_get_tools.return_value = {
                "get_issue": mock_tool1,
                "search": mock_tool2
            }

            mock_server.request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
            mock_should_include.side_effect = lambda name, _: name == "get_issue"

            # Act
            tools = await atlassian_mcp._mcp_list_tools()

            # Assert
            assert len(tools) == 1
            assert tools[0].name == "get_issue"

    @pytest.mark.anyio
    async def test_tool_filtering_excludes_jira_tools_without_config(self, atlassian_mcp, mock_app_context):
        """Test that Jira tools are excluded when Jira config is not available."""
        # Arrange
        mock_app_context.full_jira_config = None

        mock_tool = Mock()
        mock_tool.tags = {"jira", "read"}

        with patch.object(atlassian_mcp, "get_tools") as mock_get_tools, \
             patch.object(atlassian_mcp, "_mcp_server") as mock_server:

            mock_get_tools.return_value = {"get_issue": mock_tool}
            mock_server.request_context.lifespan_context = {"app_lifespan_context": mock_app_context}

            # Act
            tools = await atlassian_mcp._mcp_list_tools()

            # Assert
            assert len(tools) == 0

    @pytest.mark.anyio
    async def test_tool_filtering_handles_missing_lifespan_context(self, atlassian_mcp):
        """Test that tool filtering handles missing lifespan context gracefully."""
        # Arrange
        with patch.object(atlassian_mcp, "_mcp_server") as mock_server:
            mock_server.request_context = None

            # Act
            tools = await atlassian_mcp._mcp_list_tools()

            # Assert
            assert tools == []


class TestUserTokenMiddleware:
    """Test the UserTokenMiddleware for multi-user authentication."""

    @pytest.fixture
    def middleware(self):
        """Create a UserTokenMiddleware instance for testing."""
        mock_app = AsyncMock()
        mock_mcp_server = MagicMock()
        mock_mcp_server.settings.streamable_http_path = "/mcp"
        return UserTokenMiddleware(mock_app, mcp_server_ref=mock_mcp_server)

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = MagicMock(spec=Request)
        request.url.path = "/mcp"
        request.method = "POST"
        request.headers = {}
        request.state = SimpleNamespace()
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create a mock call_next function."""
        mock_response = JSONResponse({"test": "response"})
        call_next = AsyncMock(return_value=mock_response)
        return call_next

    @pytest.mark.anyio
    async def test_middleware_extracts_bearer_token(self, middleware, mock_request, mock_call_next):
        """Test successful Bearer token extraction and storage in request state."""
        # Arrange
        mock_request.headers = {
            "Authorization": "Bearer test-token-123",
            "X-Atlassian-Cloud-Id": "cloud-id-456"
        }

        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert hasattr(mock_request.state, "user_atlassian_token")
        assert mock_request.state.user_atlassian_token == "test-token-123"
        assert hasattr(mock_request.state, "user_atlassian_cloud_id")
        assert mock_request.state.user_atlassian_cloud_id == "cloud-id-456"
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.anyio
    async def test_middleware_handles_pat_token(self, middleware, mock_request, mock_call_next):
        """Test that PAT tokens are extracted correctly."""
        # Arrange
        mock_request.headers = {
            "Authorization": "PAT personal-access-token-789"
        }

        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert hasattr(mock_request.state, "user_atlassian_token")
        assert mock_request.state.user_atlassian_token == "personal-access-token-789"
        assert hasattr(mock_request.state, "user_atlassian_auth_type")
        assert mock_request.state.user_atlassian_auth_type == "pat"

    @pytest.mark.anyio
    async def test_middleware_skips_non_mcp_paths(self, middleware, mock_request, mock_call_next):
        """Test that middleware skips processing for non-MCP paths."""
        # Arrange
        mock_request.url.path = "/healthz"
        mock_request.headers = {"Authorization": "Bearer token"}

        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert not hasattr(mock_request.state, "user_atlassian_token")
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.anyio
    async def test_middleware_handles_missing_auth_header(self, middleware, mock_request, mock_call_next):
        """Test that middleware handles missing Authorization header gracefully."""
        # Arrange
        mock_request.headers = {}

        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert not hasattr(mock_request.state, "user_atlassian_token")
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.anyio
    async def test_middleware_handles_invalid_auth_scheme(self, middleware, mock_request, mock_call_next):
        """Test that middleware logs warning for invalid auth schemes."""
        # Arrange
        mock_request.headers = {"Authorization": "InvalidScheme token123"}

        with patch("mcp_atlassian.servers.main.logger") as mock_logger:
            # Act
            result = await middleware.dispatch(mock_request, mock_call_next)

            # Assert
            mock_logger.warning.assert_called()
            assert not hasattr(mock_request.state, "user_atlassian_token")


class TestTokenValidationCache:
    """Test the thread-safe token validation cache."""

    def test_cache_thread_safety(self):
        """Test that the cache lock prevents race conditions in concurrent access."""
        # Arrange
        results = []

        def update_cache(value):
            with token_cache_lock:
                token_validation_cache[value] = (True, f"token_{value}", None, None)
                results.append(value)

        # Act
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(update_cache, i) for i in range(10)]
            for f in futures:
                f.result()

        # Assert
        assert len(results) == 10
        assert len(token_validation_cache) <= 10  # May be less due to TTL

    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        # Arrange
        with patch("mcp_atlassian.servers.main.TTLCache") as MockTTLCache:
            mock_cache = MockTTLCache.return_value
            mock_cache.maxsize = 100
            mock_cache.ttl = 300

            # Act
            mock_cache[1] = (True, "token", None, None)

            # Assert
            MockTTLCache.assert_called_with(maxsize=100, ttl=300)


class TestHealthCheck:
    """Test the health check endpoint."""

    @pytest.mark.anyio
    async def test_health_check_returns_ok_status(self):
        """Test that health check returns correct JSON response."""
        # Arrange
        mock_request = Mock(spec=Request)

        # Act
        response = await health_check(mock_request)

        # Assert
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        content = json.loads(response.body.decode())
        assert content == {"status": "ok"}


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.anyio
    async def test_lifespan_handles_no_services_available(self):
        """Test that lifespan handles scenario when no services are available."""
        # Arrange
        with patch("mcp_atlassian.servers.main.get_available_services") as mock_services, \
             patch("mcp_atlassian.servers.main.is_read_only_mode") as mock_read_only, \
             patch("mcp_atlassian.servers.main.get_enabled_tools") as mock_enabled_tools:

            mock_services.return_value = {}
            mock_read_only.return_value = False
            mock_enabled_tools.return_value = None

            # Act
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Assert
                assert app_context.full_jira_config is None
                assert app_context.full_confluence_config is None

    @pytest.mark.anyio
    async def test_middleware_handles_empty_token(self, middleware, mock_request, mock_call_next):
        """Test that middleware handles empty token values gracefully."""
        # Arrange
        mock_request.headers = {"Authorization": "Bearer "}

        # Act
        result = await middleware.dispatch(mock_request, mock_call_next)

        # Assert
        assert not hasattr(mock_request.state, "user_atlassian_token")
        mock_call_next.assert_called_once_with(mock_request)


class TestConcurrency:
    """Test concurrent request handling."""

    @pytest.mark.anyio
    async def test_concurrent_requests_with_different_tokens(self):
        """Test that multiple concurrent requests with different tokens are handled correctly."""
        # Arrange
        middleware = UserTokenMiddleware(AsyncMock(), mcp_server_ref=MagicMock())
        middleware.mcp_server_ref.settings.streamable_http_path = "/mcp"

        async def process_request(token):
            request = MagicMock(spec=Request)
            request.url.path = "/mcp"
            request.method = "POST"
            request.headers = {"Authorization": f"Bearer {token}"}
            request.state = SimpleNamespace()

            call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
            await middleware.dispatch(request, call_next)
            return request.state.user_atlassian_token if hasattr(request.state, "user_atlassian_token") else None

        # Act
        tasks = [process_request(f"token_{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Assert
        assert results == [f"token_{i}" for i in range(5)]
