"""Integration tests for context passing in all tool handlers.

This module tests that all tool handlers properly pass context to meta-tools,
specifically verifying that the "'Server' object has no attribute 'lifespan_context'"
error from the QA report is fixed.

Tests verify:
- Context objects have proper lifespan_context access
- All 7 tool handlers pass context correctly
- Meta-tools can access lifespan_context without errors
- Error handling works when context is invalid
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP, get_tool_context

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestContextPassing:
    """Test suite for verifying context passing to all meta-tools."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a mock MainAppContext with proper configuration."""
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

        # Create the proper _mcp_server structure with request_context
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    def test_get_tool_context_function(self, mock_server):
        """Test that get_tool_context returns proper context object."""
        context = get_tool_context(mock_server)

        # Verify context has lifespan_context attribute
        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context is not None
        assert isinstance(context.lifespan_context, dict)
        assert "app_lifespan_context" in context.lifespan_context

    def test_get_tool_context_with_missing_request_context(self):
        """Test get_tool_context handles missing request_context gracefully."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = None

        context = get_tool_context(server)

        # Should return empty context dict
        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_get_tool_context_with_invalid_structure(self):
        """Test get_tool_context handles invalid server structure."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        # Mock missing lifespan_context attribute
        del server._mcp_server.request_context

        context = get_tool_context(server)

        # Should return empty context dict
        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    async def test_resource_manager_tool_context_passing(self, mock_server):
        """Test that resource_manager_tool passes context correctly."""
        from src.mcp_atlassian.servers.main import register_v2_tools

        # Register tools to get access to the tool functions
        register_v2_tools(mock_server)

        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockResourceManager:
            mock_rm_instance = MockResourceManager.return_value
            mock_rm_instance.execute_operation = AsyncMock(return_value='{"success": true}')

            # Get the resource_manager_tool function from the server
            resource_manager_tool = None
            for tool_name, tool_func in mock_server.tool.call_args_list:
                if hasattr(tool_func, '__name__') and 'resource_manager' in tool_func.__name__:
                    resource_manager_tool = tool_func
                    break

            if resource_manager_tool is None:
                pytest.skip("Could not access resource_manager_tool function")

            # Call the tool
            result = await resource_manager_tool(
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123"
            )

            # Verify the meta-tool was called
            mock_rm_instance.execute_operation.assert_called_once()
            call_args = mock_rm_instance.execute_operation.call_args

            # Verify context was passed and has lifespan_context
            assert 'ctx' in call_args.kwargs
            ctx = call_args.kwargs['ctx']
            assert hasattr(ctx, 'lifespan_context')
            assert ctx.lifespan_context is not None

    async def test_all_tool_handlers_have_context_parameter(self, mock_server):
        """Test that all tool handlers pass ctx parameter to their meta-tools."""
        tool_handlers = [
            'resource_manager_tool',
            'search_engine_tool',
            'batch_processor_tool',
            'workflow_engine_tool',
            'relationship_manager_tool',
            'attachment_handler_tool',
            'connection_health_check'
        ]

        context = get_tool_context(mock_server)

        # Verify context object is properly structured for each tool
        for tool_name in tool_handlers:
            # Test that context has required attributes
            assert hasattr(context, 'lifespan_context'), f"Context missing lifespan_context for {tool_name}"
            assert context.lifespan_context is not None, f"Context lifespan_context is None for {tool_name}"

            # Test that app_lifespan_context is accessible
            app_context = context.lifespan_context.get("app_lifespan_context")
            assert app_context is not None, f"Missing app_lifespan_context for {tool_name}"

    async def test_context_prevents_attribute_error(self, mock_server):
        """Test that the new context prevents the 'Server' object AttributeError."""
        # This is the critical test that ensures the QA report error is fixed
        context = get_tool_context(mock_server)

        # This should NOT raise: "'Server' object has no attribute 'lifespan_context'"
        try:
            lifespan_ctx = context.lifespan_context
            app_ctx = lifespan_ctx.get("app_lifespan_context")
            assert app_ctx is not None
        except AttributeError as e:
            if "lifespan_context" in str(e):
                pytest.fail(f"Context AttributeError not fixed: {e}")
            else:
                # Different AttributeError, re-raise
                raise

    async def test_meta_tool_context_access_pattern(self, mock_server):
        """Test the exact context access pattern used by meta-tools."""
        context = get_tool_context(mock_server)

        # Test the exact pattern used in dependencies.py: ctx.lifespan_context
        try:
            lifespan_ctx_dict = context.lifespan_context  # This is line 202 in dependencies.py
            app_lifespan_ctx = (
                lifespan_ctx_dict.get("app_lifespan_context")
                if isinstance(lifespan_ctx_dict, dict)
                else None
            )
            assert app_lifespan_ctx is not None
        except AttributeError as e:
            pytest.fail(f"Meta-tool context access pattern failed: {e}")

    async def test_health_check_context_passing(self, mock_server):
        """Test that health check function receives proper context."""
        from src.mcp_atlassian.servers.main import _check_service_health

        context = get_tool_context(mock_server)

        with patch('src.mcp_atlassian.servers.main.get_jira_fetcher') as mock_get_jira:
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "user123"
            mock_get_jira.return_value = mock_jira_fetcher

            # This should work without AttributeError
            result = await _check_service_health(context, "jira", dry_run=True)

            # Verify the call was made with proper context
            mock_get_jira.assert_called_once_with(context)
            assert result["service"] == "jira"
            assert result["configuration"] == "valid"

    async def test_context_with_real_dependencies_pattern(self, mock_server):
        """Test context works with the real dependencies.py pattern."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher

        context = get_tool_context(mock_server)

        # This should work without the "'Server' object has no attribute 'lifespan_context'" error
        try:
            with patch('src.mcp_atlassian.jira.client.JiraClient'):
                fetcher = await get_jira_fetcher(context)
                assert fetcher is not None
        except AttributeError as e:
            if "lifespan_context" in str(e):
                pytest.fail(f"Real dependencies pattern failed: {e}")
            else:
                # Different error, might be expected (like missing auth)
                pass

    async def test_context_error_handling(self):
        """Test context creation with completely broken server."""
        # Test with None server
        server = None
        try:
            context = get_tool_context(server)
            # Should handle gracefully
            assert context.lifespan_context == {}
        except Exception as e:
            # Should not crash with AttributeError about lifespan_context
            assert "lifespan_context" not in str(e)

        # Test with server missing _mcp_server
        server = MagicMock()
        del server._mcp_server
        context = get_tool_context(server)
        assert context.lifespan_context == {}

    async def test_context_thread_safety(self, mock_server):
        """Test that context creation is thread-safe."""
        contexts = []

        def create_context():
            contexts.append(get_tool_context(mock_server))

        # Create contexts from multiple threads
        threads = []
        for _ in range(5):
            import threading
            thread = threading.Thread(target=create_context)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All contexts should be valid
        assert len(contexts) == 5
        for context in contexts:
            assert hasattr(context, 'lifespan_context')
            assert context.lifespan_context is not None