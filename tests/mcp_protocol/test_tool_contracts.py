"""
MCP Tool Contract Validation Tests.

These tests verify that each meta-tool conforms to its advertised contract:
- Schema validation
- Parameter requirements
- Response formats
- Error handling
"""

import json
from typing import Dict, Any, List

import pytest

from tests.mcp_protocol.conftest import StdioMCPClient


@pytest.mark.mcp_tools
class TestMetaToolSchemas:
    """Test that all meta-tools have valid schemas."""

    async def test_all_tools_have_schemas(self, mcp_client: StdioMCPClient, expected_meta_tools: List[str]):
        """Test that all expected tools have valid schemas."""
        tools = await mcp_client.list_tools()
        tool_schemas = {tool["name"]: tool.get("inputSchema", {}) for tool in tools}

        for tool_name in expected_meta_tools:
            assert tool_name in tool_schemas, f"Tool {tool_name} not found"

            schema = tool_schemas[tool_name]
            assert isinstance(schema, dict), f"Schema for {tool_name} should be a dict"

    async def test_resource_manager_schema(self, mcp_client: StdioMCPClient):
        """Test resource_manager_tool schema compliance."""
        schema = await mcp_client.get_tool_schema("resource_manager_tool")
        assert schema is not None

        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", []) if isinstance(schema, dict) else []

        # Required parameters
        assert "service" in properties
        assert "resource" in properties
        assert "operation" in properties
        assert "service" in required
        assert "resource" in required
        assert "operation" in required

        # Optional parameters
        assert "identifier" in properties
        assert "data" in properties
        assert "options" in properties

        # Service should be enum of jira/confluence
        service_def = properties["service"]
        assert "enum" in service_def or "type" in service_def

    async def test_search_engine_schema(self, mcp_client: StdioMCPClient):
        """Test search_engine_tool schema compliance."""
        schema = await mcp_client.get_tool_schema("search_engine_tool")
        assert schema is not None

        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", []) if isinstance(schema, dict) else []

        # Required parameters
        assert "service" in properties
        assert "query_type" in properties
        assert "service" in required
        assert "query_type" in required

        # Optional parameters
        assert "query" in properties
        assert "options" in properties

    async def test_workflow_engine_schema(self, mcp_client: StdioMCPClient):
        """Test workflow_engine_tool schema compliance."""
        schema = await mcp_client.get_tool_schema("workflow_engine_tool")
        assert schema is not None

        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", []) if isinstance(schema, dict) else []

        # Required parameters
        assert "operation" in properties
        assert "operation" in required

        # Optional parameters for different operations
        assert "issue_key" in properties
        assert "transition_id" in properties
        assert "transition_name" in properties


@pytest.mark.mcp_tools
class TestMetaToolResponses:
    """Test that meta-tools return properly formatted responses."""

    async def test_debug_context_info_response(self, mcp_client: StdioMCPClient):
        """Test debug_context_info response format."""
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)

        # Should contain expected fields
        assert "timestamp" in json_response
        assert "context_analysis" in json_response
        assert isinstance(json_response["context_analysis"], dict)

    async def test_get_capabilities_response(self, mcp_client: StdioMCPClient):
        """Test get_capabilities response format."""
        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Response should be structured information about capabilities
        # The exact structure may vary but should be consistent

    async def test_get_resource_schema_response(self, mcp_client: StdioMCPClient):
        """Test get_resource_schema response format."""
        response = await mcp_client.call_tool("get_resource_schema", {
            "service": "jira",
            "resource": "issue",
            "operation": "create"
        })
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should contain schema information
        # May contain fields like required_fields, optional_fields, examples, etc.

    async def test_get_tool_examples_response(self, mcp_client: StdioMCPClient):
        """Test get_tool_examples response format."""
        response = await mcp_client.call_tool("get_tool_examples", {
            "operation_type": "create"
        })
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should contain examples
        assert "examples" in json_response
        assert isinstance(json_response["examples"], dict)

    async def test_connection_health_check_response(self, mcp_client: StdioMCPClient):
        """Test connection_health_check response format."""
        response = await mcp_client.call_tool("connection_health_check", {})

        # May return error in test mode, but should be properly formatted
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should have health check structure
        assert "timestamp" in json_response
        assert "checks" in json_response
        assert isinstance(json_response["checks"], dict)


@pytest.mark.mcp_tools
class TestMetaToolParameterValidation:
    """Test parameter validation for meta-tools."""

    async def test_resource_manager_parameter_validation(self, mcp_client: StdioMCPClient):
        """Test resource_manager_tool parameter validation."""

        # Test missing required parameters
        response = await mcp_client.call_tool("resource_manager_tool", {})
        # Should return structured error
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or mcp_client.is_error_response(response)

        # Test invalid service
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "invalid_service",
            "resource": "issue",
            "operation": "get"
        })
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or "Invalid" in str(json_response)

    async def test_search_engine_parameter_validation(self, mcp_client: StdioMCPClient):
        """Test search_engine_tool parameter validation."""

        # Test missing required parameters
        response = await mcp_client.call_tool("search_engine_tool", {})
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or mcp_client.is_error_response(response)

        # Test invalid service
        response = await mcp_client.call_tool("search_engine_tool", {
            "service": "invalid_service",
            "query_type": "jql"
        })
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or "Invalid" in str(json_response)

    async def test_workflow_engine_parameter_validation(self, mcp_client: StdioMCPClient):
        """Test workflow_engine_tool parameter validation."""

        # Test missing required parameters
        response = await mcp_client.call_tool("workflow_engine_tool", {})
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or mcp_client.is_error_response(response)

    async def test_batch_processor_parameter_validation(self, mcp_client: StdioMCPClient):
        """Test batch_processor_tool parameter validation."""

        # Test missing required parameters
        response = await mcp_client.call_tool("batch_processor_tool", {})
        json_response = mcp_client.extract_json_response(response)
        assert "error" in json_response or mcp_client.is_error_response(response)

        # Test empty items list
        response = await mcp_client.call_tool("batch_processor_tool", {
            "service": "jira",
            "operation": "create",
            "resource": "issue",
            "items": []
        })
        # Should handle gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)


@pytest.mark.mcp_tools
class TestMetaToolErrorHandling:
    """Test error handling across all meta-tools."""

    async def test_all_tools_handle_empty_parameters(self, mcp_client: StdioMCPClient, expected_meta_tools: List[str]):
        """Test that all tools handle empty parameters gracefully."""

        for tool_name in expected_meta_tools:
            response = await mcp_client.call_tool(tool_name, {})

            # Should return a response (not crash)
            assert "content" in response

            # Parse the response
            json_response = mcp_client.extract_json_response(response)
            assert isinstance(json_response, dict)

            # If it's an error, it should be structured
            if mcp_client.is_error_response(response) or "error" in json_response:
                assert "error" in json_response or "message" in json_response

    async def test_all_tools_handle_invalid_json_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with parameters that would cause JSON issues."""

        # Test with nested structures that might cause JSON serialization issues
        complex_params = {
            "nested": {
                "deeply": {
                    "nested": {
                        "structure": "value"
                    }
                }
            },
            "list": [1, 2, 3, {"inner": "value"}],
            "unicode": "Test with émojis 🚀 and special chars: áéíóú",
        }

        # Try with a tool that accepts flexible parameters
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "options": complex_params
        })

        # Should handle without crashing
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)


@pytest.mark.mcp_tools
class TestMetaToolConsistency:
    """Test consistency across meta-tools."""

    async def test_error_response_format_consistency(self, mcp_client: StdioMCPClient):
        """Test that error responses have consistent format across tools."""

        # Generate errors from different tools
        error_responses = []

        # Resource manager with invalid service
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "invalid",
            "resource": "issue",
            "operation": "get"
        })
        error_responses.append(("resource_manager_tool", response))

        # Search engine with invalid service
        response = await mcp_client.call_tool("search_engine_tool", {
            "service": "invalid",
            "query_type": "jql"
        })
        error_responses.append(("search_engine_tool", response))

        # Workflow engine with missing parameters
        response = await mcp_client.call_tool("workflow_engine_tool", {})
        error_responses.append(("workflow_engine_tool", response))

        # Check that all errors have consistent structure
        for tool_name, response in error_responses:
            json_response = mcp_client.extract_json_response(response)

            # Should have error information
            has_error = (
                mcp_client.is_error_response(response) or
                "error" in json_response or
                "error_code" in json_response or
                "message" in json_response
            )
            assert has_error, f"Tool {tool_name} should return structured error"

    async def test_service_parameter_consistency(self, mcp_client: StdioMCPClient):
        """Test that 'service' parameter is handled consistently."""

        tools_with_service = [
            "resource_manager_tool",
            "search_engine_tool",
            "batch_processor_tool",
            "attachment_handler_tool"
        ]

        for tool_name in tools_with_service:
            # Test with valid services
            for service in ["jira", "confluence"]:
                # Create minimal valid parameters for each tool
                if tool_name == "resource_manager_tool":
                    params = {"service": service, "resource": "issue", "operation": "get", "identifier": "TEST-1"}
                elif tool_name == "search_engine_tool":
                    params = {"service": service, "query_type": "jql" if service == "jira" else "pages"}
                elif tool_name == "batch_processor_tool":
                    params = {"service": service, "operation": "create", "resource": "issue", "items": []}
                elif tool_name == "attachment_handler_tool":
                    params = {"service": service, "operation": "list", "issue_key": "TEST-1"}

                response = await mcp_client.call_tool(tool_name, params)

                # Should not fail due to service parameter itself
                # (may fail for other reasons like missing credentials in test mode)
                json_response = mcp_client.extract_json_response(response)
                assert isinstance(json_response, dict)

                # If there's an error, it shouldn't be about invalid service
                if "error" in json_response:
                    error_msg = str(json_response.get("error", "")).lower()
                    assert "invalid.*service" not in error_msg, f"Tool {tool_name} rejected valid service {service}"

    async def test_response_json_validity(self, mcp_client: StdioMCPClient, sample_tool_calls: Dict[str, Dict[str, Any]]):
        """Test that all tool responses are valid JSON."""

        for tool_name, params in sample_tool_calls.items():
            response = await mcp_client.call_tool(tool_name, params)

            # Should be able to parse JSON
            json_response = mcp_client.extract_json_response(response)
            assert isinstance(json_response, dict), f"Tool {tool_name} returned non-dict response"

            # Should be re-serializable to JSON
            try:
                json.dumps(json_response)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Tool {tool_name} response not JSON serializable: {e}")


@pytest.mark.mcp_tools
class TestMetaToolDocumentation:
    """Test that tools have proper documentation."""

    async def test_all_tools_have_descriptions(self, mcp_client: StdioMCPClient, expected_meta_tools: List[str]):
        """Test that all tools have meaningful descriptions."""
        tools = await mcp_client.list_tools()

        for tool in tools:
            tool_name = tool["name"]
            description = tool.get("description", "")

            assert description, f"Tool {tool_name} has no description"
            assert len(description) > 10, f"Tool {tool_name} description too short: '{description}'"
            assert not description.startswith("TODO"), f"Tool {tool_name} has placeholder description"

    async def test_parameter_descriptions_exist(self, mcp_client: StdioMCPClient):
        """Test that tool parameters have descriptions where expected."""
        tools = await mcp_client.list_tools()

        # Parameters that commonly don't have descriptions in meta-tools
        allowed_without_description = {
            "options", "data", "identifier", "query", "fields", "transition_id",
            "transition_name", "link_id", "epic_key", "parent_key", "target_issue_key",
            "file_path", "file_name", "file_content", "download_path", "attachment_id",
            "page_id", "issue_key", "project_key", "comment", "items", "concurrency"
        }

        missing_descriptions = []

        for tool in tools:
            tool_name = tool["name"]
            schema = tool.get("inputSchema", {})
            properties = schema.get("properties", {})

            for param_name, param_def in properties.items():
                description = param_def.get("description", "")

                # Check if parameter lacks description and it's not in allowed list
                if not description and param_name not in allowed_without_description:
                    missing_descriptions.append(f"{tool_name}.{param_name}")

        # Allow a reasonable number of missing descriptions for meta-tools
        # but ensure the majority have descriptions
        total_params = sum(len(tool.get("inputSchema", {}).get("properties", {})) for tool in tools)
        if total_params > 0:
            missing_ratio = len(missing_descriptions) / total_params
            assert missing_ratio < 0.3, f"Too many parameters missing descriptions ({len(missing_descriptions)}/{total_params}): {missing_descriptions[:10]}"