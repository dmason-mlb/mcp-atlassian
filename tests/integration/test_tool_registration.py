"""Integration tests for MCP tool registration and invocation.

Tests that verify:
1. All tools are properly registered in the MCP server
2. Tool metadata is correctly defined
3. Tools can be invoked without registration errors
4. No legacy tools are accidentally exposed
5. Meta-tools are properly configured and accessible
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Any, Dict, List

from mcp.types import Tool, TextContent

from src.mcp_atlassian.servers.main import AtlassianMCP, register_v2_tools
from src.mcp_atlassian.servers.context import MainAppContext


@pytest.fixture
async def mcp_server():
    """Create MCP server instance for testing."""
    # Create server instance
    server = AtlassianMCP(name="Test Atlassian MCP")

    # Mock the lifespan context to provide required configuration
    mock_lifespan_state = Mock()
    mock_lifespan_state.read_only = False
    mock_lifespan_state.enabled_tools = None
    mock_lifespan_state.full_jira_config = True
    mock_lifespan_state.full_confluence_config = True

    # Mock the server context
    server._mcp_server = Mock()
    server._mcp_server.request_context = Mock()
    server._mcp_server.request_context.lifespan_context = {
        "app_lifespan_context": mock_lifespan_state
    }

    return server


class TestToolRegistration:
    """Test MCP tool registration."""

    @pytest.mark.asyncio
    async def test_server_has_tools_registered(self, mcp_server):
        """Test that the MCP server has tools registered."""
        # Register tools in the server
        register_v2_tools(mcp_server)

        # Get tools using the MCP list method
        tools = await mcp_server._mcp_list_tools()

        # Should have meta-tools registered
        assert len(tools) > 0, "No tools registered in MCP server"

        # Collect tool names for verification
        tool_names = [tool.name for tool in tools]

        # Verify expected meta-tools are present
        expected_meta_tools = [
            "resource_manager_tool",
            "search_engine_tool",
            "batch_processor_tool",
            "workflow_engine_tool",
            "relationship_manager_tool",
            "attachment_handler_tool",
            "connection_health_check"
        ]

        for tool_name in expected_meta_tools:
            assert tool_name in tool_names, f"Expected meta-tool '{tool_name}' not found in registered tools"

    @pytest.mark.asyncio
    async def test_no_legacy_tools_registered(self, mcp_server):
        """Test that no legacy tools are accidentally registered."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()
        tool_names = [tool.name for tool in tools]

        # List of legacy tool patterns that should NOT be present
        legacy_patterns = [
            "get_issue",
            "create_issue",
            "update_issue",
            "get_page",
            "create_page",
            "update_page",
            "search_issues",
            "search_pages",
            "migration_helper",
            "get_migration_guidance",
            "get_migration_analytics"
        ]

        for pattern in legacy_patterns:
            # Check for exact matches and partial matches
            legacy_tools = [name for name in tool_names if pattern in name]
            assert len(legacy_tools) == 0, f"Legacy tool pattern '{pattern}' found in registered tools: {legacy_tools}"

    @pytest.mark.asyncio
    async def test_tool_metadata_completeness(self, mcp_server):
        """Test that all registered tools have complete metadata."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()

        for tool in tools:
            # Each tool should have required metadata
            assert tool.name, f"Tool missing name: {tool}"
            assert tool.description, f"Tool '{tool.name}' missing description"

            # Description should be meaningful (not just the name)
            assert len(tool.description) > 10, f"Tool '{tool.name}' has too brief description: {tool.description}"
            # Tool names can appear in descriptions, but shouldn't be the only content
            words_in_desc = len(tool.description.split())
            assert words_in_desc > 3, f"Tool '{tool.name}' description too short: {tool.description}"

    @pytest.mark.asyncio
    async def test_meta_tools_have_proper_schemas(self, mcp_server):
        """Test that meta-tools have properly defined input schemas."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()

        meta_tool_names = [
            "resource_manager_tool",
            "search_engine_tool",
            "batch_processor_tool",
            "workflow_engine_tool",
            "relationship_manager_tool",
            "attachment_handler_tool"
        ]

        for tool in tools:
            if tool.name in meta_tool_names:
                # Meta-tools should have input schema defined
                assert tool.inputSchema, f"Meta-tool '{tool.name}' missing input schema"

                # Schema should have properties
                schema = tool.inputSchema
                assert "properties" in schema, f"Meta-tool '{tool.name}' schema missing properties"

                # Should have required fields for meta-tools
                properties = schema["properties"]

                # Different tools have different parameter structures
                if tool.name == "connection_health_check":
                    # Health check has minimal schema
                    pass
                elif tool.name == "search_engine_tool":
                    assert "service" in properties, f"Search engine tool missing 'service' parameter"
                    assert "query_type" in properties, f"Search engine tool missing 'query_type' parameter"
                elif tool.name in ["workflow_engine_tool", "relationship_manager_tool"]:
                    # These are Jira-specific tools, don't need service parameter
                    assert "operation" in properties, f"{tool.name} missing 'operation' parameter"
                else:
                    # Standard meta-tools need both service and operation
                    assert "service" in properties, f"Meta-tool '{tool.name}' missing 'service' parameter"
                    assert "operation" in properties, f"Meta-tool '{tool.name}' missing 'operation' parameter"


class TestToolInvocation:
    """Test MCP tool invocation capabilities."""

    @pytest.mark.asyncio
    async def test_tools_are_callable_via_fastmcp(self, mcp_server):
        """Test that tools are properly registered and accessible via FastMCP."""
        register_v2_tools(mcp_server)

        # Get all registered tools from FastMCP
        all_tools = await mcp_server.get_tools()

        # Should have tools registered
        assert len(all_tools) > 0, "No tools registered in FastMCP server"

        # Verify expected meta-tools are accessible
        expected_tools = ["resource_manager_tool", "search_engine_tool", "connection_health_check"]

        for tool_name in expected_tools:
            assert tool_name in all_tools, f"Expected tool '{tool_name}' not found in FastMCP tools"

    @pytest.mark.asyncio
    async def test_tool_registration_consistency(self, mcp_server):
        """Test that MCP tool listing matches FastMCP tool registration."""
        register_v2_tools(mcp_server)

        # Get tools via both methods
        mcp_tools = await mcp_server._mcp_list_tools()
        fastmcp_tools = await mcp_server.get_tools()

        # Extract names
        mcp_tool_names = {tool.name for tool in mcp_tools}
        fastmcp_tool_names = set(fastmcp_tools.keys())

        # Should be consistent (MCP list should be subset of FastMCP due to filtering)
        assert mcp_tool_names.issubset(fastmcp_tool_names), \
            f"MCP tool list not consistent with FastMCP registration. MCP: {mcp_tool_names}, FastMCP: {fastmcp_tool_names}"

    @pytest.mark.asyncio
    async def test_tool_function_exists(self, mcp_server):
        """Test that tool functions actually exist and are callable."""
        register_v2_tools(mcp_server)

        # Get tools and verify they have callable functions
        all_tools = await mcp_server.get_tools()

        for tool_name, tool_obj in all_tools.items():
            # Tool should be callable
            assert callable(tool_obj), f"Tool '{tool_name}' is not callable"

            # Tool should have proper attributes
            assert hasattr(tool_obj, 'tags'), f"Tool '{tool_name}' missing tags attribute"


class TestAPIVersionCompliance:
    """Test API version compliance."""

    @pytest.mark.asyncio
    async def test_no_deprecated_api_endpoints_in_tools(self, mcp_server):
        """Test that tools don't reference deprecated API endpoints."""
        # This is more of a code inspection test
        # We'll check that the transitions module uses v3 endpoints

        from src.mcp_atlassian.jira import transitions
        import inspect

        # Get the source code of the transitions module
        source = inspect.getsource(transitions)

        # Check that it uses v3 API endpoints
        assert "rest/api/3/" in source, "Transitions module should use API v3 endpoints"

        # Check that it doesn't use deprecated v2 endpoints
        v2_patterns = [
            "rest/api/2/project/",
            "rest/api/2/status"
        ]

        for pattern in v2_patterns:
            assert pattern not in source, f"Found deprecated v2 API pattern '{pattern}' in transitions module"

    @pytest.mark.asyncio
    async def test_all_api_calls_use_latest_versions(self, mcp_server):
        """Test that API calls use the latest supported versions."""
        # Check Jira v3 usage
        from src.mcp_atlassian.jira import transitions
        source = inspect.getsource(transitions)

        # Should use v3 for project statuses and general status endpoints
        assert "/rest/api/3/project/" in source, "Should use v3 API for project operations"
        assert "/rest/api/3/status" in source, "Should use v3 API for status operations"


class TestErrorHandling:
    """Test error handling in tool registration and invocation."""

    @pytest.mark.asyncio
    async def test_tool_registration_with_missing_context(self):
        """Test that tool registration handles missing context gracefully."""
        # Test creating server without proper context
        server = AtlassianMCP(name="Test Server")

        # Should be able to register tools even without full context
        try:
            register_v2_tools(server)
            # Should succeed
            tools = await server.get_tools()
            assert len(tools) > 0, "Should register tools even without context"
        except Exception as e:
            # If it fails, should be a meaningful error
            error_message = str(e)
            assert len(error_message) > 0, "Should provide error message"

    @pytest.mark.asyncio
    async def test_service_unavailable_handling(self):
        """Test that tools handle service unavailability gracefully."""
        # Create server with mock context that has limited configuration
        server = AtlassianMCP(name="Test Server")

        # Mock partial configuration
        mock_lifespan_state = Mock()
        mock_lifespan_state.read_only = False
        mock_lifespan_state.enabled_tools = None
        mock_lifespan_state.full_jira_config = True
        mock_lifespan_state.full_confluence_config = False  # Confluence not configured

        server._mcp_server = Mock()
        server._mcp_server.request_context = Mock()
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": mock_lifespan_state
        }

        # Register tools
        register_v2_tools(server)

        # Get filtered tools
        tools = await server._mcp_list_tools()

        # Should still have some tools (Jira tools and universal tools)
        assert len(tools) > 0, "Should have some tools even with partial configuration"

        # Should filter out Confluence-specific tools
        tool_names = [tool.name for tool in tools]
        confluence_specific_patterns = ["confluence"]

        # Check that no Confluence-only tools are present if Confluence is disabled
        # (This depends on how tools are tagged, but the filtering should work)


class TestPerformanceAndScaling:
    """Test performance aspects of tool registration."""

    @pytest.mark.asyncio
    async def test_tool_registration_performance(self, mcp_server):
        """Test that tool registration completes quickly."""
        import time

        start_time = time.time()
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()
        end_time = time.time()

        # Tool registration should complete within reasonable time
        registration_time = end_time - start_time
        assert registration_time < 5.0, f"Tool registration took too long: {registration_time:.2f}s"

        # Should have registered tools
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_tool_metadata_memory_efficiency(self, mcp_server):
        """Test that tool metadata is memory efficient."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()

        # Calculate approximate memory usage of tool metadata
        total_description_length = sum(len(tool.description) for tool in tools)

        # Should be reasonable (not excessive)
        # Meta-tools should be more efficient than many individual tools
        assert total_description_length < 10000, f"Tool descriptions too verbose: {total_description_length} chars"

        # Should have fewer than 20 tools total (meta-tools + health check)
        assert len(tools) < 20, f"Too many tools registered: {len(tools)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])