"""
MCP JSON-RPC Protocol Compliance Tests.

These tests verify that the MCP server properly implements the JSON-RPC 2.0
specification and MCP protocol requirements as used by real clients.
"""

import asyncio
import json
from typing import Dict, Any, List

import pytest

from tests.mcp_protocol.conftest import StdioMCPClient


@pytest.mark.mcp_protocol
class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 compliance."""

    async def test_tools_list_response_format(self, mcp_client: StdioMCPClient):
        """Test that tools/list follows MCP response format."""
        tools = await mcp_client.list_tools()

        # Should be a list
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Each tool should have required fields
        for tool in tools:
            assert isinstance(tool, dict)
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

            # Name should be non-empty string
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0

            # Description should be non-empty string
            assert isinstance(tool["description"], str)
            assert len(tool["description"]) > 0

            # inputSchema should be a dict (JSON Schema)
            assert isinstance(tool["inputSchema"], dict)

    async def test_tool_call_response_format(self, mcp_client: StdioMCPClient):
        """Test that tool calls follow MCP response format."""
        response = await mcp_client.call_tool("debug_context_info", {})

        # Response should have expected structure
        assert isinstance(response, dict)
        assert "content" in response
        assert "is_error" in response

        # Content should be parseable
        content = response["content"]
        assert isinstance(content, str)

        # Should be valid JSON
        json_content = json.loads(content)
        assert isinstance(json_content, dict)

        # is_error should be boolean
        assert isinstance(response["is_error"], bool)

    async def test_json_serialization_compliance(self, mcp_client: StdioMCPClient):
        """Test that all responses are properly JSON serializable."""
        # Test various tool calls
        test_calls = [
            ("debug_context_info", {}),
            ("get_capabilities", {}),
            ("get_tool_examples", {"service": "jira"}),
            ("get_resource_schema", {"service": "jira", "resource": "issue", "operation": "create"}),
        ]

        for tool_name, params in test_calls:
            response = await mcp_client.call_tool(tool_name, params)

            # Should be JSON serializable
            try:
                serialized = json.dumps(response)
                # Should be deserializable
                deserialized = json.loads(serialized)
                assert deserialized == response
            except (TypeError, ValueError) as e:
                pytest.fail(f"Response from {tool_name} not JSON serializable: {e}")

    async def test_unicode_handling(self, mcp_client: StdioMCPClient):
        """Test proper Unicode handling in JSON-RPC."""
        # Test with Unicode parameters
        unicode_params = {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-123",
            "options": {
                "unicode_test": "Test with émojis 🚀 and special chars: áéíóú ñÑ çÇ"
            }
        }

        response = await mcp_client.call_tool("resource_manager_tool", unicode_params)

        # Should handle Unicode properly
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Response should be JSON serializable with Unicode
        serialized = json.dumps(response, ensure_ascii=False)
        deserialized = json.loads(serialized)
        assert isinstance(deserialized, dict)

    async def test_large_response_handling(self, mcp_client: StdioMCPClient):
        """Test handling of large JSON responses."""
        # Get tool examples (potentially large response)
        response = await mcp_client.call_tool("get_tool_examples", {})

        # Should handle large responses
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should be JSON serializable even if large
        serialized = json.dumps(json_response)
        assert len(serialized) > 100  # Should be reasonably substantial

        # Should be deserializable
        deserialized = json.loads(serialized)
        assert deserialized == json_response


@pytest.mark.mcp_protocol
class TestMCPProtocolSpecifics:
    """Test MCP-specific protocol requirements."""

    async def test_tool_schema_format(self, mcp_client: StdioMCPClient):
        """Test that tool schemas follow JSON Schema format."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            schema = tool["inputSchema"]

            if schema:  # Some tools might have empty schemas
                # Should have valid JSON Schema structure
                assert isinstance(schema, dict)

                # Common JSON Schema fields
                if "type" in schema:
                    assert isinstance(schema["type"], str)

                if "properties" in schema:
                    assert isinstance(schema["properties"], dict)
                    for prop_name, prop_def in schema["properties"].items():
                        assert isinstance(prop_def, dict)

                if "required" in schema:
                    assert isinstance(schema["required"], list)
                    for req_field in schema["required"]:
                        assert isinstance(req_field, str)

    async def test_tool_parameter_validation(self, mcp_client: StdioMCPClient):
        """Test that tools validate parameters according to their schemas."""
        # Get resource_manager_tool schema
        schema = await mcp_client.get_tool_schema("resource_manager_tool")
        assert schema is not None

        required_fields = schema.get("required", []) if isinstance(schema, dict) else []
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}

        # Test with missing required field
        if "service" in required_fields:
            response = await mcp_client.call_tool("resource_manager_tool", {
                "resource": "issue",
                "operation": "get"
                # Missing 'service'
            })

            # Should return validation error
            json_response = mcp_client.extract_json_response(response)
            error_content = str(json_response).lower()
            # Check that it's an error response for the resource_manager_tool
            assert "resource_manager_tool" in error_content
            assert "error" in error_content

    async def test_tool_response_consistency(self, mcp_client: StdioMCPClient):
        """Test that tool responses are consistent across calls."""
        # Make the same call multiple times
        responses = []
        for _ in range(3):
            response = await mcp_client.call_tool("debug_context_info", {})
            responses.append(response)

        # All responses should have the same structure
        for response in responses:
            assert "content" in response
            assert "is_error" in response

            json_response = mcp_client.extract_json_response(response)
            assert "timestamp" in json_response
            assert "context_analysis" in json_response

    async def test_concurrent_request_handling(self, mcp_client: StdioMCPClient):
        """Test that concurrent requests are handled properly."""
        # Create concurrent requests
        tasks = [
            mcp_client.call_tool("debug_context_info", {}),
            mcp_client.call_tool("get_capabilities", {}),
            mcp_client.call_tool("get_tool_examples", {"service": "jira"}),
        ]

        # All should complete successfully
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        for response in responses:
            assert "content" in response
            assert "is_error" in response
            assert not mcp_client.is_error_response(response)


@pytest.mark.mcp_protocol
class TestMCPInitialization:
    """Test MCP initialization protocol."""

    async def test_server_capabilities_after_init(self, mcp_client: StdioMCPClient):
        """Test that server exposes expected capabilities after initialization."""
        # After initialization, should be able to list tools
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        # Should have all expected meta-tools
        tool_names = [tool["name"] for tool in tools]
        expected_core_tools = [
            "debug_context_info",
            "resource_manager_tool",
            "search_engine_tool",
            "get_capabilities"
        ]

        for expected_tool in expected_core_tools:
            assert expected_tool in tool_names

    async def test_tool_discovery_stability(self, mcp_client: StdioMCPClient):
        """Test that tool discovery is stable across multiple calls."""
        # Get tools multiple times
        tool_lists = []
        for _ in range(5):
            tools = await mcp_client.list_tools()
            tool_lists.append(tools)

        # All lists should be identical
        first_list = tool_lists[0]
        for tool_list in tool_lists[1:]:
            assert len(tool_list) == len(first_list)

            # Sort by name for comparison
            first_sorted = sorted(first_list, key=lambda t: t["name"])
            current_sorted = sorted(tool_list, key=lambda t: t["name"])

            for first_tool, current_tool in zip(first_sorted, current_sorted):
                assert first_tool["name"] == current_tool["name"]
                assert first_tool["description"] == current_tool["description"]
                assert first_tool["inputSchema"] == current_tool["inputSchema"]


@pytest.mark.mcp_protocol
class TestMCPErrorProtocol:
    """Test MCP error handling protocol."""

    async def test_error_response_format(self, mcp_client: StdioMCPClient):
        """Test that error responses follow proper format."""
        # Generate an error by calling with invalid parameters
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "invalid_service",
            "resource": "issue",
            "operation": "get"
        })

        # Should be a valid response structure
        assert isinstance(response, dict)
        assert "content" in response
        assert "is_error" in response

        # Content should be parseable JSON
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Error information should be present
        error_content = str(json_response).lower()
        assert any(term in error_content for term in ["error", "invalid", "unknown"])

    async def test_exception_handling(self, mcp_client: StdioMCPClient):
        """Test that exceptions are properly handled and converted."""
        # Try to call a non-existent tool
        try:
            response = await mcp_client.call_tool("definitely_nonexistent_tool", {})
            # If no exception is raised, should return error response
            assert mcp_client.is_error_response(response), "Should return error for nonexistent tool"
        except Exception:
            # Some kind of exception is also acceptable
            pass

        # Server should still be responsive after exception
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_malformed_request_recovery(self, mcp_client: StdioMCPClient):
        """Test recovery from malformed requests."""
        # Make several potentially problematic calls
        problematic_calls = [
            # Very large parameter
            ("resource_manager_tool", {
                "service": "jira",
                "resource": "issue",
                "operation": "get",
                "identifier": "x" * 10000
            }),
            # Deeply nested structure
            ("resource_manager_tool", {
                "service": "jira",
                "resource": "issue",
                "operation": "get",
                "options": {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
            }),
        ]

        for tool_name, params in problematic_calls:
            try:
                response = await mcp_client.call_tool(tool_name, params)
                # If it succeeds, should be valid response
                json_response = mcp_client.extract_json_response(response)
                assert isinstance(json_response, dict)
            except Exception:
                # If it fails, that's also acceptable
                pass

        # Server should still be responsive
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)


@pytest.mark.mcp_protocol
class TestMCPCompatibility:
    """Test compatibility with real MCP clients."""

    async def test_claude_desktop_compatibility(self, mcp_client: StdioMCPClient):
        """Test compatibility with Claude Desktop usage patterns."""
        # 1. Claude discovers tools
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        # 2. Claude examines a specific tool
        resource_tool = None
        for tool in tools:
            if tool["name"] == "resource_manager_tool":
                resource_tool = tool
                break

        assert resource_tool is not None
        assert "inputSchema" in resource_tool
        assert "properties" in resource_tool["inputSchema"]

        # 3. Claude calls the tool with user-derived parameters
        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_cursor_compatibility(self, mcp_client: StdioMCPClient):
        """Test compatibility with Cursor usage patterns."""
        # 1. Cursor discovers available tools
        tools = await mcp_client.list_tools()
        tool_names = [tool["name"] for tool in tools]

        # 2. Cursor looks for specific capabilities
        assert "resource_manager_tool" in tool_names
        assert "search_engine_tool" in tool_names

        # 3. Cursor makes schema queries
        schema_response = await mcp_client.call_tool("get_resource_schema", {
            "service": "jira",
            "resource": "issue",
            "operation": "create"
        })
        assert not mcp_client.is_error_response(schema_response)

        # 4. Cursor gets examples
        examples_response = await mcp_client.call_tool("get_tool_examples", {
            "operation_type": "create",
            "service": "jira"
        })
        assert not mcp_client.is_error_response(examples_response)

    async def test_generic_mcp_client_compatibility(self, mcp_client: StdioMCPClient):
        """Test compatibility with generic MCP client patterns."""
        # Standard MCP client workflow:

        # 1. List tools
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        # 2. For each tool, examine schema
        for tool in tools[:3]:  # Test first 3 tools
            schema = tool.get("inputSchema", {})
            assert isinstance(schema, dict)

            # Schema should be valid JSON Schema if present
            if schema and "properties" in schema:
                properties = schema["properties"]
                assert isinstance(properties, dict)

        # 3. Call tools based on schema
        simple_tools = ["debug_context_info", "get_capabilities"]
        for tool_name in simple_tools:
            if tool_name in [tool["name"] for tool in tools]:
                response = await mcp_client.call_tool(tool_name, {})
                assert "content" in response

    async def test_batch_operations_compatibility(self, mcp_client: StdioMCPClient):
        """Test that batch operations work as expected by clients."""
        # Test batch processor tool
        response = await mcp_client.call_tool("batch_processor_tool", {
            "service": "jira",
            "operation": "create",
            "resource": "issue",
            "items": [],  # Empty list for testing
            "concurrency": 1
        })

        # Should handle gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_streaming_compatibility(self, mcp_client: StdioMCPClient):
        """Test compatibility with streaming responses."""
        # Make a call that might return a large response
        response = await mcp_client.call_tool("get_tool_examples", {})

        # Should be able to handle the full response
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Response should be complete, not truncated
        if "examples" in json_response:
            assert isinstance(json_response["examples"], dict)
            assert len(json_response["examples"]) > 0