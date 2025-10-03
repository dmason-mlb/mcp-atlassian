"""
MCP Server Error Handling Tests.

These tests verify that the MCP server handles various error scenarios
gracefully and provides useful error messages to clients.
"""

import asyncio
import json
from typing import Dict, Any

import pytest

from tests.mcp_protocol.conftest import StdioMCPClient, MCPProtocolError


@pytest.mark.mcp_errors
class TestToolErrorHandling:
    """Test error handling for tool invocation scenarios."""

    async def test_nonexistent_tool_error(self, mcp_client: StdioMCPClient):
        """Test calling a tool that doesn't exist."""
        try:
            response = await mcp_client.call_tool("definitely_nonexistent_tool_12345", {})
            # If it doesn't raise an exception, should return an error response
            assert mcp_client.is_error_response(response), "Should return error response for nonexistent tool"
        except MCPProtocolError as e:
            # This is also acceptable - check the error message
            assert "not found" in str(e).lower() or "unknown" in str(e).lower()

    async def test_missing_required_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with missing required parameters."""
        # resource_manager_tool requires service, resource, operation
        response = await mcp_client.call_tool("resource_manager_tool", {})

        # Should return structured error, not crash
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should indicate missing parameters
        error_content = str(json_response).lower()
        assert any(term in error_content for term in ["required", "missing", "error"])

    async def test_invalid_parameter_types(self, mcp_client: StdioMCPClient):
        """Test tools with parameters of wrong types."""
        # Pass number where string expected
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": 123,  # Should be string
            "resource": "issue",
            "operation": "get"
        })

        # Should handle gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_invalid_enum_values(self, mcp_client: StdioMCPClient):
        """Test tools with invalid enum values."""
        # Invalid service name
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "definitely_invalid_service",
            "resource": "issue",
            "operation": "get"
        })

        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Should mention invalid service
        error_content = str(json_response).lower()
        assert "invalid" in error_content or "unknown" in error_content

    async def test_extra_unknown_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with extra unknown parameters.

        FastMCP has strict parameter validation and should reject unknown parameters.
        """
        response = await mcp_client.call_tool("debug_context_info", {
            "unknown_param_1": "value1",
            "unknown_param_2": {"nested": "value"},
            "unknown_param_3": [1, 2, 3]
        })

        # FastMCP should reject extra parameters with validation error
        assert mcp_client.is_error_response(response)
        json_response = mcp_client.extract_json_response(response)

        # Should have error information - FastMCP returns generic error for validation failures
        assert "error" in json_response
        error_content = str(json_response).lower()

        # Check that it's clearly an error response for the right tool
        assert "debug_context_info" in error_content
        assert "error" in error_content

    async def test_null_parameter_values(self, mcp_client: StdioMCPClient):
        """Test tools with null parameter values."""
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": None,  # null value
            "options": None
        })

        # Should handle null values appropriately
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)


@pytest.mark.mcp_errors
class TestParameterValidationErrors:
    """Test parameter validation error scenarios."""

    async def test_empty_string_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with empty string parameters."""
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "",  # Empty string
            "resource": "issue",
            "operation": "get"
        })

        json_response = mcp_client.extract_json_response(response)
        error_content = str(json_response).lower()
        assert "empty" in error_content or "invalid" in error_content or "error" in error_content

    async def test_extremely_long_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with extremely long parameter values."""
        long_string = "x" * 100000  # 100KB string

        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": long_string
        })

        # Should handle without crashing
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_special_characters_in_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with special characters in parameters."""
        special_chars = r'''!@#$%^&*(){}[]|\:;"'<>,.?/~`±§€‰™£¢∞§¶•ªº–≠œ∑´®†¥¨ˆøπ"'«åß∂ƒ©˙∆˚¬…æΩ≈ç√∫˜µ≤≥÷'''

        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": f"TEST-{special_chars}",
            "options": {"special": special_chars}
        })

        # Should handle special characters gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_unicode_emoji_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with unicode and emoji characters."""
        unicode_text = "Test with émojis 🚀🎉👍 and unicode: áéíóú ñÑ çÇ øØ ñ™€®"

        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-123",
            "options": {"description": unicode_text}
        })

        # Should handle unicode gracefully
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

    async def test_deeply_nested_parameters(self, mcp_client: StdioMCPClient):
        """Test tools with deeply nested parameter structures."""
        deep_nested = {"level1": {"level2": {"level3": {"level4": {"level5": {"deep": "value"}}}}}}

        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-123",
            "options": deep_nested
        })

        # Should handle deep nesting
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)


@pytest.mark.mcp_errors
class TestConcurrencyErrorHandling:
    """Test error handling under concurrent load."""

    async def test_concurrent_invalid_calls(self, mcp_client: StdioMCPClient):
        """Test multiple invalid calls happening concurrently."""
        # Create multiple invalid calls
        invalid_tasks = [
            mcp_client.call_tool("nonexistent_tool_1", {}),
            mcp_client.call_tool("resource_manager_tool", {"invalid": "params"}),
            mcp_client.call_tool("search_engine_tool", {"service": "invalid"}),
        ]

        # Some will raise exceptions, others might return error responses
        results = await asyncio.gather(*invalid_tasks, return_exceptions=True)

        # All should either be exceptions or structured error responses
        for result in results:
            if isinstance(result, Exception):
                # Expected for some invalid calls
                assert isinstance(result, MCPProtocolError)
            else:
                # Should be structured response
                json_response = mcp_client.extract_json_response(result)
                assert isinstance(json_response, dict)

        # Server should still be responsive after concurrent errors
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_mixed_valid_invalid_concurrent_calls(self, mcp_client: StdioMCPClient):
        """Test mix of valid and invalid calls concurrently."""
        mixed_tasks = [
            mcp_client.call_tool("debug_context_info", {}),  # Valid
            mcp_client.call_tool("get_capabilities", {}),     # Valid
            mcp_client.call_tool("nonexistent_tool", {}),    # Invalid
            mcp_client.call_tool("resource_manager_tool", {"invalid": "params"}),  # Invalid
        ]

        results = await asyncio.gather(*mixed_tasks, return_exceptions=True)

        # Should have mix of successful and failed results
        success_count = 0
        error_count = 0

        for result in results:
            if isinstance(result, Exception):
                error_count += 1
            else:
                try:
                    json_response = mcp_client.extract_json_response(result)
                    if not mcp_client.is_error_response(result) and "error" not in json_response:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1

        assert success_count >= 2  # At least the valid calls should succeed
        assert error_count >= 2   # At least the invalid calls should fail

    async def test_error_isolation(self, mcp_client: StdioMCPClient):
        """Test that errors in one call don't affect others."""
        # Make an invalid call
        try:
            await mcp_client.call_tool("nonexistent_tool", {})
        except MCPProtocolError:
            pass  # Expected

        # Subsequent valid calls should work normally
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)


@pytest.mark.mcp_errors
class TestResourceErrorHandling:
    """Test error handling for resource-related scenarios."""

    async def test_resource_manager_error_scenarios(self, mcp_client: StdioMCPClient):
        """Test various error scenarios for resource_manager_tool."""
        error_scenarios = [
            # Missing service
            {"resource": "issue", "operation": "get"},
            # Invalid service
            {"service": "invalid_service", "resource": "issue", "operation": "get"},
            # Invalid resource
            {"service": "jira", "resource": "invalid_resource", "operation": "get"},
            # Invalid operation
            {"service": "jira", "resource": "issue", "operation": "invalid_operation"},
            # Missing identifier for get operation
            {"service": "jira", "resource": "issue", "operation": "get"},
        ]

        for scenario in error_scenarios:
            response = await mcp_client.call_tool("resource_manager_tool", scenario)
            json_response = mcp_client.extract_json_response(response)

            # Should return structured error
            error_content = str(json_response).lower()
            assert any(term in error_content for term in ["error", "invalid", "missing", "required"])

    async def test_search_engine_error_scenarios(self, mcp_client: StdioMCPClient):
        """Test various error scenarios for search_engine_tool."""
        error_scenarios = [
            # Missing service
            {"query_type": "jql"},
            # Invalid service
            {"service": "invalid_service", "query_type": "jql"},
            # Invalid query type for service
            {"service": "jira", "query_type": "invalid_query_type"},
            {"service": "confluence", "query_type": "jql"},  # JQL not valid for Confluence
        ]

        for scenario in error_scenarios:
            response = await mcp_client.call_tool("search_engine_tool", scenario)
            json_response = mcp_client.extract_json_response(response)

            # Should return structured error
            error_content = str(json_response).lower()
            assert any(term in error_content for term in ["error", "invalid", "unsupported"])

    async def test_workflow_engine_error_scenarios(self, mcp_client: StdioMCPClient):
        """Test various error scenarios for workflow_engine_tool."""
        error_scenarios = [
            # Missing operation
            {},
            # Invalid operation
            {"operation": "invalid_operation"},
            # Missing issue_key for operations that need it
            {"operation": "transition"},
            {"operation": "get_transitions"},
        ]

        for scenario in error_scenarios:
            response = await mcp_client.call_tool("workflow_engine_tool", scenario)
            json_response = mcp_client.extract_json_response(response)

            # Should return structured error
            error_content = str(json_response).lower()
            assert any(term in error_content for term in ["error", "invalid", "missing", "required"])


@pytest.mark.mcp_errors
class TestErrorMessageQuality:
    """Test that error messages are helpful and informative."""

    async def test_error_messages_are_descriptive(self, mcp_client: StdioMCPClient):
        """Test that error messages provide useful information."""
        # Test with resource_manager_tool missing required service
        response = await mcp_client.call_tool("resource_manager_tool", {
            "resource": "issue",
            "operation": "get"
        })

        json_response = mcp_client.extract_json_response(response)
        error_text = str(json_response).lower()

        # Should indicate error with the resource_manager_tool
        assert "resource_manager_tool" in error_text
        assert "error" in error_text

    async def test_error_messages_include_valid_options(self, mcp_client: StdioMCPClient):
        """Test that error messages suggest valid alternatives."""
        # Test with invalid service
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "invalid_service",
            "resource": "issue",
            "operation": "get"
        })

        json_response = mcp_client.extract_json_response(response)
        error_text = str(json_response).lower()

        # Should suggest valid services
        assert any(service in error_text for service in ["jira", "confluence"])

    async def test_error_messages_are_not_too_verbose(self, mcp_client: StdioMCPClient):
        """Test that error messages are concise but informative."""
        response = await mcp_client.call_tool("resource_manager_tool", {})

        json_response = mcp_client.extract_json_response(response)
        error_text = str(json_response)

        # Should be informative but not overwhelming
        assert len(error_text) < 5000  # Reasonable upper bound
        assert len(error_text) > 10    # Should have some content

    async def test_error_responses_are_json_serializable(self, mcp_client: StdioMCPClient):
        """Test that all error responses can be serialized to JSON."""
        error_scenarios = [
            ("resource_manager_tool", {}),
            ("search_engine_tool", {}),
            ("workflow_engine_tool", {}),
            ("resource_manager_tool", {"service": "invalid"}),
        ]

        for tool_name, params in error_scenarios:
            response = await mcp_client.call_tool(tool_name, params)
            json_response = mcp_client.extract_json_response(response)

            # Should be able to re-serialize
            try:
                json.dumps(json_response)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Error response from {tool_name} not JSON serializable: {e}")


@pytest.mark.mcp_errors
class TestErrorRecovery:
    """Test server recovery after errors."""

    async def test_server_stability_after_errors(self, mcp_client: StdioMCPClient):
        """Test that server remains stable after multiple errors."""
        # Generate multiple errors
        for _ in range(10):
            try:
                await mcp_client.call_tool("nonexistent_tool", {})
            except MCPProtocolError:
                pass  # Expected

            # Invalid parameter errors
            await mcp_client.call_tool("resource_manager_tool", {"invalid": "params"})

        # Server should still be fully functional
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

        response = await mcp_client.call_tool("get_capabilities", {})
        assert not mcp_client.is_error_response(response)

    async def test_session_persistence_after_errors(self, mcp_client: StdioMCPClient):
        """Test that session remains usable after errors."""
        # Verify session works initially
        initial_tools = await mcp_client.list_tools()
        initial_count = len(initial_tools)

        # Generate some errors
        for _ in range(5):
            try:
                await mcp_client.call_tool("nonexistent_tool", {})
            except MCPProtocolError:
                pass

        # Session should still work
        final_tools = await mcp_client.list_tools()
        assert len(final_tools) == initial_count

        # Can still make successful calls
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)