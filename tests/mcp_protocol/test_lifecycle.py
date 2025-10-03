"""
MCP Server Lifecycle Management Tests.

These tests verify proper server lifecycle management including:
- Startup and initialization
- Context management
- Resource cleanup
- Graceful shutdown
- Error recovery
"""

import asyncio
import os
import signal
import time
from typing import Dict

import pytest

from tests.mcp_protocol.conftest import StdioMCPClient, MCPServerTimeoutError, MCPServerCrashError


@pytest.mark.mcp_lifecycle
class TestServerStartup:
    """Test server startup and initialization."""

    async def test_server_starts_with_valid_config(self, server_command, test_env):
        """Test that server starts successfully with valid configuration."""
        client = StdioMCPClient(server_command, test_env)

        async with client.connect(timeout=30.0) as connected_client:
            # Should be able to list tools immediately after connection
            tools = await connected_client.list_tools()
            assert len(tools) > 0

    async def test_server_startup_time(self, server_command, test_env):
        """Test that server starts within reasonable time."""
        client = StdioMCPClient(server_command, test_env)

        start_time = time.time()
        async with client.connect(timeout=30.0) as connected_client:
            startup_time = time.time() - start_time

            # Should start within 15 seconds (adjust as needed)
            assert startup_time < 15.0, f"Server took {startup_time}s to start"

            # Verify it's actually working
            tools = await connected_client.list_tools()
            assert len(tools) > 0

    async def test_server_starts_with_minimal_env(self, server_command):
        """Test server startup with minimal environment configuration."""
        minimal_env = {
            "ATLASSIAN_URL": "https://test.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test_token",
            "MCP_PROTOCOL_TEST_MODE": "true",
        }

        client = StdioMCPClient(server_command, minimal_env)

        async with client.connect(timeout=30.0) as connected_client:
            tools = await connected_client.list_tools()
            assert len(tools) > 0

    async def test_server_handles_missing_optional_config(self, server_command):
        """Test server behavior with missing optional configuration."""
        # Only provide required minimum
        minimal_env = {
            "ATLASSIAN_URL": "https://test.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test_token",
            "MCP_PROTOCOL_TEST_MODE": "true",
            # Intentionally omit optional configs like READ_ONLY_MODE, etc.
        }

        client = StdioMCPClient(server_command, minimal_env)

        async with client.connect(timeout=30.0) as connected_client:
            # Should work with defaults
            tools = await connected_client.list_tools()
            assert len(tools) > 0

            # Should be able to call basic tools
            response = await connected_client.call_tool("debug_context_info", {})
            assert not connected_client.is_error_response(response)


@pytest.mark.mcp_lifecycle
class TestServerInitialization:
    """Test the MCP initialization handshake."""

    async def test_initialization_handshake_completes(self, mcp_client: StdioMCPClient):
        """Test that the MCP initialization handshake completes properly."""
        # The fixture handles initialization, but we can verify it worked
        assert mcp_client.session is not None

        # Should be able to immediately use the session
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_capabilities_negotiation(self, mcp_client: StdioMCPClient):
        """Test that capabilities are properly negotiated."""
        # After initialization, we should have access to all server capabilities
        tools = await mcp_client.list_tools()

        # Should have all expected meta-tools
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "debug_context_info",
            "resource_manager_tool",
            "search_engine_tool"
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    async def test_server_info_available(self, mcp_client: StdioMCPClient):
        """Test that server provides information about itself."""
        # Try to get server information through available tools
        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

        json_response = mcp_client.extract_json_response(response)
        assert "timestamp" in json_response


@pytest.mark.mcp_lifecycle
class TestServerShutdown:
    """Test graceful server shutdown."""

    async def test_graceful_shutdown_on_context_exit(self, server_command, test_env):
        """Test that server shuts down gracefully when context exits."""
        client = StdioMCPClient(server_command, test_env)

        # Connect and do some work
        async with client.connect(timeout=30.0) as connected_client:
            await connected_client.list_tools()
            await connected_client.call_tool("debug_context_info", {})

        # After context exit, session should be cleaned up
        assert client.session is None

    async def test_multiple_rapid_connections(self, server_command, test_env):
        """Test rapid connection and disconnection cycles."""
        for i in range(3):
            client = StdioMCPClient(server_command, test_env)

            async with client.connect(timeout=30.0) as connected_client:
                tools = await connected_client.list_tools()
                assert len(tools) > 0

                # Do a quick operation
                response = await connected_client.call_tool("get_capabilities", {})
                assert not connected_client.is_error_response(response)

            # Brief pause between connections
            await asyncio.sleep(0.1)

    async def test_server_resource_cleanup(self, server_command, test_env):
        """Test that server properly cleans up resources."""
        # This is a basic test - for real resource testing you'd monitor file handles, etc.

        for _ in range(5):
            client = StdioMCPClient(server_command, test_env)

            async with client.connect(timeout=30.0) as connected_client:
                # Create some "state" in the server
                await connected_client.list_tools()
                await connected_client.call_tool("debug_context_info", {})
                await connected_client.call_tool("get_capabilities", {})

        # Server should handle multiple connection cycles without issues


@pytest.mark.mcp_lifecycle
class TestServerRecovery:
    """Test server recovery from various failure scenarios."""

    async def test_recovery_from_invalid_tool_calls(self, mcp_client: StdioMCPClient):
        """Test that server recovers from invalid tool calls."""
        # Make several invalid calls
        invalid_calls = [
            ("nonexistent_tool", {}),
            ("resource_manager_tool", {"invalid": "params"}),
            ("search_engine_tool", {"service": "invalid"}),
        ]

        for tool_name, params in invalid_calls:
            try:
                response = await mcp_client.call_tool(tool_name, params)
                # Some may succeed with error responses, others may raise exceptions
                # Both are acceptable as long as the server doesn't crash
            except Exception:
                # Expected for truly invalid calls
                pass

        # Server should still be responsive after invalid calls
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

        response = await mcp_client.call_tool("debug_context_info", {})
        assert not mcp_client.is_error_response(response)

    async def test_recovery_from_malformed_json(self, mcp_client: StdioMCPClient):
        """Test server recovery from operations that might cause JSON issues."""
        # Test with parameters that might cause JSON serialization problems
        problematic_params = {
            "unicode_test": "Test with émojis 🚀 and special chars: áéíóú ñÑ",
            "large_string": "x" * 10000,  # Large string
            "deeply_nested": {"a": {"b": {"c": {"d": {"e": "deep"}}}}},
            "mixed_types": [1, "string", True, None, {"key": "value"}],
        }

        # Try with a tool that accepts flexible parameters
        response = await mcp_client.call_tool("resource_manager_tool", {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-1",
            "options": problematic_params
        })

        # Should handle without crashing the server
        json_response = mcp_client.extract_json_response(response)
        assert isinstance(json_response, dict)

        # Server should still be responsive
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_concurrent_operations_stability(self, mcp_client: StdioMCPClient):
        """Test server stability under concurrent operations."""
        # Create multiple concurrent operations
        async def make_calls():
            return await asyncio.gather(
                mcp_client.call_tool("debug_context_info", {}),
                mcp_client.call_tool("get_capabilities", {}),
                mcp_client.call_tool("get_tool_examples", {"service": "jira"}),
                mcp_client.call_tool("get_resource_schema", {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "create"
                }),
                return_exceptions=True
            )

        # Run concurrent operations multiple times
        for _ in range(3):
            results = await make_calls()

            # Some operations might fail, but server should remain stable
            # Check that we got some responses
            assert len(results) == 4

            # Brief pause between rounds
            await asyncio.sleep(0.1)

        # Server should still be responsive after concurrent load
        tools = await mcp_client.list_tools()
        assert len(tools) > 0


@pytest.mark.mcp_lifecycle
@pytest.mark.slow
class TestServerLongRunning:
    """Test long-running server behavior."""

    async def test_extended_session_stability(self, mcp_client: StdioMCPClient):
        """Test server stability during extended sessions."""
        # Keep session open and make periodic calls
        start_time = time.time()
        call_count = 0

        while time.time() - start_time < 60:  # Run for 1 minute
            try:
                tools = await mcp_client.list_tools()
                assert len(tools) > 0

                response = await mcp_client.call_tool("debug_context_info", {})
                assert not mcp_client.is_error_response(response)

                call_count += 1

                # Brief pause between calls
                await asyncio.sleep(1)

            except Exception as e:
                pytest.fail(f"Server became unstable after {call_count} calls: {e}")

        assert call_count > 50, f"Only made {call_count} calls in 60 seconds"

    async def test_memory_stability_over_time(self, mcp_client: StdioMCPClient):
        """Test that server doesn't accumulate memory over time."""
        # This is a basic test - real memory testing would use memory profiling

        # Get baseline
        initial_tools = await mcp_client.list_tools()
        initial_count = len(initial_tools)

        # Make many calls to potentially accumulate memory
        for i in range(100):
            await mcp_client.call_tool("debug_context_info", {})
            await mcp_client.call_tool("get_capabilities", {})

            if i % 20 == 0:  # Check periodically
                tools = await mcp_client.list_tools()
                assert len(tools) == initial_count, "Tool count changed during test"

        # Final check
        final_tools = await mcp_client.list_tools()
        assert len(final_tools) == initial_count


@pytest.mark.mcp_lifecycle
class TestServerConfiguration:
    """Test server behavior with different configurations."""

    async def test_read_only_mode(self, server_command):
        """Test server behavior in read-only mode."""
        read_only_env = {
            "ATLASSIAN_URL": "https://test.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test_token",
            "READ_ONLY_MODE": "true",
            "MCP_PROTOCOL_TEST_MODE": "true",
        }

        client = StdioMCPClient(server_command, read_only_env)

        async with client.connect(timeout=30.0) as connected_client:
            tools = await connected_client.list_tools()
            assert len(tools) > 0

            # Should still be able to call read-only tools
            response = await connected_client.call_tool("debug_context_info", {})
            assert not connected_client.is_error_response(response)

            response = await connected_client.call_tool("get_capabilities", {})
            assert not connected_client.is_error_response(response)

    async def test_verbose_logging_mode(self, server_command):
        """Test server with verbose logging enabled."""
        verbose_env = {
            "ATLASSIAN_URL": "https://test.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test_token",
            "MCP_VERBOSE": "true",
            "MCP_VERY_VERBOSE": "true",
            "MCP_PROTOCOL_TEST_MODE": "true",
        }

        client = StdioMCPClient(server_command, verbose_env)

        async with client.connect(timeout=30.0) as connected_client:
            # Should work normally with verbose logging
            tools = await connected_client.list_tools()
            assert len(tools) > 0

            response = await connected_client.call_tool("debug_context_info", {})
            assert not connected_client.is_error_response(response)

    async def test_tool_filtering(self, server_command):
        """Test server with tool filtering enabled."""
        filtered_env = {
            "ATLASSIAN_URL": "https://test.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test_token",
            "ENABLED_TOOLS": "debug_context_info,get_capabilities",
            "MCP_PROTOCOL_TEST_MODE": "true",
        }

        client = StdioMCPClient(server_command, filtered_env)

        async with client.connect(timeout=30.0) as connected_client:
            tools = await connected_client.list_tools()
            tool_names = [tool["name"] for tool in tools]

            # Should only have the enabled tools
            assert "debug_context_info" in tool_names
            assert "get_capabilities" in tool_names

            # Other tools should be filtered out
            assert "resource_manager_tool" not in tool_names