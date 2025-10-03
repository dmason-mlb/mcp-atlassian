"""
MCP Server stdio Transport Tests.

These tests verify that the MCP server works correctly when accessed via
stdio transport, exactly as real clients like Claude Desktop use it.
"""

import asyncio
import json
from typing import Dict, List, Any

import pytest

from tests.mcp_protocol.conftest import StdioMCPClient, MCPProtocolError


@pytest.mark.mcp_stdio
class TestStdioServerBasics:
    """Test basic stdio server functionality."""

    async def test_server_startup_and_connection(self, mcp_client: StdioMCPClient):
        """Test that the server starts and accepts connections via stdio."""
        # The mcp_client fixture already tests basic connection
        assert mcp_client.session is not None
        # Session is connected and functional - test by listing tools
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_server_initialization_handshake(self, mcp_client: StdioMCPClient):
        """Test the MCP initialization handshake."""
        # The session should be initialized by the fixture
        # Verify we can make basic requests
        tools = await mcp_client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    async def test_tools_discovery_via_stdio(self, mcp_client: StdioMCPClient, expected_meta_tools: List[str]):
        """Test tool discovery through stdio transport."""
        tools = await mcp_client.list_tools()

        # Verify all expected meta-tools are present
        tool_names = [tool["name"] for tool in tools]
        for expected_tool in expected_meta_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found"

        # Verify tool definitions are complete
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    async def test_tool_schemas_are_valid(self, mcp_client: StdioMCPClient):
        """Test that all tool schemas are valid JSON Schema."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            schema = tool.get("inputSchema", {})

            # Basic JSON Schema validation
            assert isinstance(schema, dict)

            if schema:  # Some tools might have empty schemas
                # Should have required JSON Schema fields
                assert "type" in schema or "properties" in schema

                # If it has properties, they should be properly defined
                if "properties" in schema:
                    properties = schema["properties"]
                    assert isinstance(properties, dict)

                    for prop_name, prop_def in properties.items():
                        assert isinstance(prop_def, dict)
                        # Each property should have a type
                        assert "type" in prop_def or "anyOf" in prop_def or "oneOf" in prop_def


@pytest.mark.mcp_stdio
class TestStdioToolExecution:
    """Test tool execution via stdio transport."""

    async def test_simple_tool_calls(self, mcp_client: StdioMCPClient):
        """Test simple tool calls that don't require external APIs."""

        # Test debug_context_info (should always work)
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert "timestamp" in json_response
        assert "context_analysis" in json_response

    async def test_capabilities_discovery(self, mcp_client: StdioMCPClient):
        """Test the capabilities discovery tool."""
        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should contain information about available services
        # The exact structure depends on the implementation

    async def test_schema_discovery(self, mcp_client: StdioMCPClient):
        """Test schema discovery for different operations."""
        response = await mcp_client.call_tool("get_resource_schema", {
            "service": "jira",
            "resource": "issue",
            "operation": "create"
        })

        assert not mcp_client.is_error_response(response)
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_tool_examples_generation(self, mcp_client: StdioMCPClient):
        """Test the tool examples generation."""
        response = await mcp_client.call_tool("get_tool_examples", {
            "operation_type": "create",
            "service": "jira"
        })

        assert not mcp_client.is_error_response(response)
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)
        assert "examples" in json_response

    async def test_connection_health_check(self, mcp_client: StdioMCPClient):
        """Test connection health check tool."""
        response = await mcp_client.call_tool("connection_health_check", {
            "service": "jira"
        })

        # This might return an error in test mode, but should be a valid response
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)
        assert "timestamp" in json_response
        assert "checks" in json_response


@pytest.mark.mcp_stdio
class TestStdioErrorHandling:
    """Test error handling via stdio transport."""

    async def test_invalid_tool_name(self, mcp_client: StdioMCPClient):
        """Test calling a non-existent tool."""
        try:
            response = await mcp_client.call_tool("nonexistent_tool", {})
            # If it doesn't raise an exception, should return an error response
            assert mcp_client.is_error_response(response), "Should return error response for nonexistent tool"
        except MCPProtocolError:
            # This is also acceptable
            pass

    async def test_invalid_tool_arguments(self, mcp_client: StdioMCPClient):
        """Test calling a tool with invalid arguments."""
        # Call resource_manager_tool with missing required arguments
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "invalid_service"
        })

        # Should return an error response, not crash
        assert mcp_client.is_error_response(response) or "error" in mcp_client.extract_json_response(response)

    async def test_malformed_arguments(self, mcp_client: StdioMCPClient):
        """Test tool calls with malformed arguments."""
        # Test with arguments that don't match the schema
        response = await mcp_client.call_tool("get_resource_schema", {
            "service": "jira",
            "resource": "issue",
            "operation": "invalid_operation"
        })

        # Should handle gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)


@pytest.mark.mcp_stdio
class TestStdioPerformance:
    """Test performance characteristics of stdio transport."""

    async def test_rapid_sequential_calls(self, mcp_client: StdioMCPClient):
        """Test making rapid sequential tool calls."""
        start_time = asyncio.get_event_loop().time()

        # Make 10 rapid calls to a simple tool
        for _ in range(10):
            response = await mcp_client.call_tool("debug_context_info", {})
            assert not mcp_client.is_error_response(response)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        assert duration < 30.0, f"10 tool calls took {duration}s, too slow"

    async def test_concurrent_tool_calls(self, mcp_client: StdioMCPClient):
        """Test concurrent tool calls via stdio."""
        # Create multiple concurrent calls
        tasks = [
            mcp_client.call_tool("debug_context_info", {}),
            mcp_client.call_tool("get_capabilities", {}),
            mcp_client.call_tool("get_tool_examples", {"service": "jira"}),
        ]

        # All should complete successfully
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            assert not isinstance(result, Exception), f"Concurrent call failed: {result}"
            assert not mcp_client.is_error_response(result)

    @pytest.mark.slow
    async def test_large_response_handling(self, mcp_client: StdioMCPClient):
        """Test handling of large responses via stdio."""
        # Get all tool examples (potentially large response)
        response = await mcp_client.call_tool("get_tool_examples", {})

        assert not mcp_client.is_error_response(response)
        json_response = mcp_client.extract_json_response(response)

        # Should handle large responses without truncation
        assert isinstance(json_response, dict)
        assert len(json.dumps(json_response)) > 1000  # Should be reasonably large


@pytest.mark.mcp_stdio
class TestStdioResourceManagement:
    """Test resource management with stdio transport."""

    async def test_session_persistence(self, mcp_client: StdioMCPClient):
        """Test that the session persists across multiple calls."""
        # Make first call
        response1 = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response1)

        # Make second call - should use the same session
        response2 = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response2)

        # Both calls should succeed with the same session
        assert mcp_client.session is not None

    async def test_memory_usage_stability(self, mcp_client: StdioMCPClient):
        """Test that repeated calls don't cause memory leaks."""
        # This is a basic test - for real memory testing you'd use memory profiling
        initial_tools = await mcp_client.list_tools()

        # Make multiple calls
        for _ in range(5):
            await mcp_client.call_tool("debug_context_info", {})
            await mcp_client.call_tool("get_capabilities", {})

        # Should still be able to list tools normally
        final_tools = await mcp_client.list_tools()
        assert len(final_tools) == len(initial_tools)


@pytest.mark.mcp_stdio
class TestStdioComplianceWithRealClients:
    """Test compliance with how real MCP clients work."""

    async def test_claude_desktop_like_workflow(self, mcp_client: StdioMCPClient):
        """Test a workflow similar to how Claude Desktop would use the server."""

        # 1. Claude Desktop discovers tools
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        # 2. Claude Desktop examines a specific tool's schema
        resource_manager_schema = await mcp_client.get_tool_schema("resource_manager_tool")
        assert resource_manager_schema is not None
        assert isinstance(resource_manager_schema, dict)

        # 3. Claude Desktop calls the tool based on user request
        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)

        # 4. Claude Desktop processes the response
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_cursor_like_workflow(self, mcp_client: StdioMCPClient):
        """Test a workflow similar to how Cursor would use the server."""

        # 1. Cursor discovers available tools
        tools = await mcp_client.list_tools()
        tool_names = [tool["name"] for tool in tools]

        # 2. Cursor looks for specific capabilities
        assert "resource_manager_tool" in tool_names
        assert "search_engine_tool" in tool_names

        # 3. Cursor makes a series of related calls
        schema_response = await mcp_client.call_tool("get_resource_schema", {
            "service": "jira",
            "resource": "issue",
            "operation": "create"
        })
        assert not mcp_client.is_error_response(schema_response)

        examples_response = await mcp_client.call_tool("get_tool_examples", {
            "operation_type": "create",
            "service": "jira"
        })
        assert not mcp_client.is_error_response(examples_response)

    async def test_json_rpc_message_format(self, mcp_client: StdioMCPClient):
        """Test that responses conform to JSON-RPC format expectations."""
        # This is tested indirectly through the MCP SDK, but we verify
        # that the content we get back is properly formatted

        response = await mcp_client.call_tool("debug_context_info", {})
        assert "content" in response
        assert "is_error" in response

        # Content should be parseable JSON for most tools
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)