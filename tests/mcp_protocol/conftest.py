"""
Shared MCP Protocol Testing Infrastructure.

This module provides the core infrastructure for testing MCP servers using
stdio transport, exactly as real clients like Claude Desktop use them.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager, AsyncExitStack
from typing import Any, AsyncIterator, Dict, List, Optional
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = logging.getLogger(__name__)


class MCPProtocolError(Exception):
    """Base exception for MCP protocol testing errors."""
    pass


class MCPServerTimeoutError(MCPProtocolError):
    """Raised when MCP server operations timeout."""
    pass


class MCPServerCrashError(MCPProtocolError):
    """Raised when MCP server process crashes."""
    pass


class StdioMCPClient:
    """
    MCP Client that uses stdio transport exactly like real clients.

    This client mirrors how Claude Desktop communicates with MCP servers:
    - Launches server as subprocess
    - Uses stdin/stdout for JSON-RPC communication
    - Handles proper lifecycle management
    """

    def __init__(self, server_command: List[str], env: Optional[Dict[str, str]] = None):
        """Initialize the stdio MCP client.

        Args:
            server_command: Command to launch the MCP server (e.g., ["uv", "run", "mcp-atlassian"])
            env: Environment variables for the server process
        """
        self.server_command = server_command
        self.env = env or {}
        self.session: Optional[ClientSession] = None
        self._process: Optional[subprocess.Popen] = None
        self._tools: Optional[List[Any]] = None  # Store actual Tool objects
        self._exit_stack: Optional[AsyncExitStack] = None

    @asynccontextmanager
    async def connect(self, timeout: float = 30.0) -> AsyncIterator["StdioMCPClient"]:
        """Connect to the MCP server using stdio transport.

        Args:
            timeout: Connection timeout in seconds

        Yields:
            Connected StdioMCPClient instance

        Raises:
            MCPServerTimeoutError: If connection times out
            MCPServerCrashError: If server process crashes
        """
        # Prepare environment
        server_env = os.environ.copy()
        server_env.update(self.env)

        # Create server parameters
        params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:] if len(self.server_command) > 1 else [],
            env=server_env
        )

        self._exit_stack = AsyncExitStack()
        connection_successful = False

        try:
            # Start stdio client with timeout for connection only
            try:
                async with asyncio.timeout(timeout):
                    transport = await self._exit_stack.enter_async_context(
                        stdio_client(params)
                    )
                    read, write = transport

                    # Create session
                    self.session = await self._exit_stack.enter_async_context(
                        ClientSession(read, write)
                    )

                    # Initialize the session
                    await self.session.initialize()
                    logger.info("MCP server connected successfully via stdio")
                    connection_successful = True

            except asyncio.TimeoutError:
                raise MCPServerTimeoutError(f"MCP server connection timed out after {timeout}s")

            # If connection successful, yield the client (outside timeout scope)
            if connection_successful:
                yield self

        except MCPServerTimeoutError:
            # Re-raise timeout errors as-is
            raise
        except Exception as e:
            # Handle other connection errors
            raise MCPServerCrashError(f"MCP server failed to start: {e}")
        finally:
            # Enhanced cleanup to avoid cancel scope warnings
            if self._exit_stack:
                try:
                    # Use asyncio.shield to protect cleanup from cancellation
                    await asyncio.shield(self._exit_stack.aclose())
                except asyncio.CancelledError:
                    # If shield fails, try basic cleanup
                    logger.warning("Cleanup was cancelled, attempting force cleanup")
                    try:
                        await self._exit_stack.aclose()
                    except Exception as force_cleanup_error:
                        logger.error(f"Force cleanup failed: {force_cleanup_error}")
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup: {cleanup_error}")

            # Reset state
            self.session = None
            self._exit_stack = None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from the server.

        Returns:
            List of tool definitions with names, descriptions, and schemas

        Raises:
            MCPProtocolError: If tools/list request fails
        """
        if not self.session:
            raise MCPProtocolError("Client not connected")

        try:
            result = await self.session.list_tools()
            self._tools = result.tools
            # Convert Tool objects to dictionaries for compatibility
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in result.tools
            ]
        except Exception as e:
            raise MCPProtocolError(f"Failed to list tools: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result

        Raises:
            MCPProtocolError: If tool call fails
        """
        if not self.session:
            raise MCPProtocolError("Client not connected")

        try:
            # Convert arguments to proper format
            call_result = await self.session.call_tool(tool_name, arguments)

            # Extract content from the result
            if hasattr(call_result, 'content') and call_result.content:
                # If it's a list of content items, get the first text content
                if isinstance(call_result.content, list) and call_result.content:
                    content = call_result.content[0]
                    if hasattr(content, 'text'):
                        return {"content": content.text, "is_error": call_result.isError or False}
                    elif hasattr(content, 'data'):
                        return {"content": content.data, "is_error": call_result.isError or False}
                    else:
                        # Fallback to string representation
                        return {"content": str(content), "is_error": call_result.isError or False}
                else:
                    return {"content": str(call_result.content), "is_error": call_result.isError or False}
            else:
                # Handle empty content - provide structured error info when it's an error
                is_error = getattr(call_result, 'isError', False)
                if is_error:
                    # Create structured error response for empty error content
                    error_info = {
                        "error": f"Tool '{tool_name}' returned empty error response",
                        "tool_name": tool_name,
                        "error_type": "empty_error_content"
                    }
                    return {"content": json.dumps(error_info), "is_error": True}
                else:
                    # Empty non-error response
                    return {"content": json.dumps({"message": "Tool returned empty response"}), "is_error": False}

        except Exception as e:
            # Enhanced error handling for different types of exceptions
            error_msg = str(e)
            exception_type = type(e).__name__

            # Handle specific MCP errors
            if "Tool" in error_msg and "not found" in error_msg:
                raise MCPProtocolError(f"Tool '{tool_name}' not found")

            # Handle ValidationError specifically (from Pydantic/FastMCP)
            if exception_type == "ValidationError" or "validation error" in error_msg.lower() or "field required" in error_msg.lower() or "missing" in error_msg.lower() or "unexpected keyword" in error_msg.lower():
                error_info = {
                    "error": f"Parameter validation failed for tool '{tool_name}': {error_msg}",
                    "tool_name": tool_name,
                    "error_type": "validation_error",
                    "validation_details": error_msg,
                    "exception_type": exception_type
                }
                return {"content": json.dumps(error_info), "is_error": True}

            # Handle other exceptions with structured error info
            error_info = {
                "error": f"Error calling tool '{tool_name}': {error_msg}",
                "tool_name": tool_name,
                "error_type": "execution_error",
                "exception_type": exception_type,
                "details": error_msg
            }
            return {"content": json.dumps(error_info), "is_error": True}

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool's input schema or None if tool not found
        """
        if self._tools is None:
            await self.list_tools()

        # Search through actual Tool objects
        for tool in self._tools or []:
            if tool.name == tool_name:
                return tool.inputSchema
        return None

    def extract_json_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and parse JSON from tool response.

        Args:
            response: Raw tool response

        Returns:
            Parsed JSON data or structured error information

        Raises:
            MCPProtocolError: If response is not valid JSON and not a known error format
        """
        content = response.get("content", "")
        is_error = response.get("is_error", False)

        # Handle empty content gracefully
        if not content or content == "":
            if is_error:
                return {
                    "error": "Tool returned empty error response",
                    "error_type": "empty_content",
                    "is_error": True
                }
            else:
                return {
                    "message": "Tool returned empty response",
                    "content": "",
                    "is_error": False
                }

        # Handle non-string content
        if not isinstance(content, str):
            return content if isinstance(content, dict) else {"content": content}

        # Try to parse as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If it's not JSON but is an error, create structured error
            if is_error:
                return {
                    "error": content,
                    "error_type": "non_json_error",
                    "is_error": True
                }
            else:
                # Non-JSON non-error content, wrap it
                return {
                    "message": content,
                    "content": content,
                    "is_error": False
                }

    def is_error_response(self, response: Dict[str, Any]) -> bool:
        """Check if a tool response indicates an error.

        Args:
            response: Tool response to check

        Returns:
            True if response indicates an error
        """
        return response.get("is_error", False)


@pytest.fixture
def server_command() -> List[str]:
    """Get the command to launch the MCP server."""
    # Use the same command that real clients would use
    return ["uv", "run", "mcp-atlassian"]


@pytest.fixture
def test_env() -> Dict[str, str]:
    """Get test environment variables for the MCP server."""
    return {
        # Mock Atlassian URLs for testing
        "ATLASSIAN_URL": "https://test.atlassian.net",
        "JIRA_BASE_URL": "https://test.atlassian.net",
        "CONFLUENCE_BASE_URL": "https://test.atlassian.net/wiki",

        # Mock authentication (these would be overridden in real tests)
        "ATLASSIAN_EMAIL": "test@example.com",
        "ATLASSIAN_API_TOKEN": "test_token_12345",

        # Test-specific settings
        "READ_ONLY_MODE": "false",
        "MCP_VERBOSE": "true",

        # Disable actual API calls for protocol tests
        "MCP_PROTOCOL_TEST_MODE": "true",
    }


@pytest.fixture
async def mcp_client(server_command: List[str], test_env: Dict[str, str]) -> AsyncIterator[StdioMCPClient]:
    """Create a connected MCP client for testing.

    This fixture provides a real MCP client connected via stdio transport,
    exactly as Claude Desktop would connect to the server.
    """
    client = StdioMCPClient(server_command, test_env)

    async with client.connect(timeout=30.0) as connected_client:
        # Verify basic connectivity
        tools = await connected_client.list_tools()
        assert len(tools) > 0, "Server should provide at least one tool"

        yield connected_client


@pytest.fixture
def expected_meta_tools() -> List[str]:
    """List of expected meta-tools that should be available."""
    return [
        "debug_context_info",
        "resource_manager_tool",
        "get_resource_schema",
        "get_capabilities",
        "get_tool_examples",
        "search_engine_tool",
        "batch_processor_tool",
        "workflow_engine_tool",
        "relationship_manager_tool",
        "attachment_handler_tool",
        "connection_health_check",
    ]


@pytest.fixture
def sample_tool_calls() -> Dict[str, Dict[str, Any]]:
    """Sample tool calls for testing each meta-tool."""
    return {
        "debug_context_info": {},

        "get_capabilities": {},

        "get_tool_examples": {
            "operation_type": "create",
            "service": "jira"
        },

        "get_resource_schema": {
            "service": "jira",
            "resource": "issue",
            "operation": "create"
        },

        "connection_health_check": {
            "service": "jira"
        },

        "resource_manager_tool": {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-123",
            "options": {"fields": "summary,status"}
        },

        "search_engine_tool": {
            "service": "jira",
            "query_type": "jql",
            "query": "project = TEST",
            "options": {"limit": 10}
        },

        "workflow_engine_tool": {
            "operation": "get_transitions",
            "issue_key": "TEST-123"
        },

        "relationship_manager_tool": {
            "operation": "get_links",
            "issue_key": "TEST-123"
        },

        "batch_processor_tool": {
            "service": "jira",
            "operation": "create",
            "resource": "issue",
            "items": [
                {
                    "project_key": "TEST",
                    "summary": "Test Issue 1",
                    "issue_type": "Task"
                }
            ],
            "concurrency": 1
        },

        "attachment_handler_tool": {
            "service": "jira",
            "operation": "list",
            "issue_key": "TEST-123"
        }
    }


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers for MCP protocol tests."""
    config.addinivalue_line("markers", "mcp_protocol: MCP protocol compliance tests")
    config.addinivalue_line("markers", "mcp_stdio: stdio transport specific tests")
    config.addinivalue_line("markers", "mcp_tools: meta-tool contract tests")
    config.addinivalue_line("markers", "mcp_lifecycle: server lifecycle tests")
    config.addinivalue_line("markers", "mcp_errors: error handling tests")
    config.addinivalue_line("markers", "slow: tests that take more than 10 seconds")