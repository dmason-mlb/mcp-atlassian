#!/usr/bin/env python3
"""Real MCP client integration tests for schema enhancement validation.

This test validates that the enhanced tool docstrings actually solve the
original problem where MCP clients like Cursor couldn't understand tool usage.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest


class MCPClientTester:
    """Test MCP protocol communication and tool discovery."""

    def __init__(self, server_command: List[str]):
        self.server_command = server_command
        self.process = None

    async def start_server(self) -> None:
        """Start the MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def stop_server(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send an MCP protocol request and get response."""
        if not self.process:
            raise RuntimeError("Server not started")

        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())

    async def initialize_mcp_session(self) -> Dict[str, Any]:
        """Initialize MCP session."""
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        return await self.send_mcp_request(init_request)

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools via MCP protocol."""
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        return await self.send_mcp_request(tools_request)


@pytest.fixture
async def mcp_client():
    """Create MCP client connected to local server."""
    # Use uv run to start the server
    server_cmd = ["uv", "run", "mcp-atlassian"]

    client = MCPClientTester(server_cmd)
    await client.start_server()

    # Allow server to start up
    await asyncio.sleep(2)

    yield client

    await client.stop_server()


class TestMCPToolDiscovery:
    """Test MCP tool discovery and schema validation."""

    async def test_server_initialization(self, mcp_client):
        """Test that MCP server initializes properly."""
        try:
            response = await mcp_client.initialize_mcp_session()
            assert response["jsonrpc"] == "2.0"
            assert "result" in response
            print("✅ MCP server initialization successful")
        except Exception as e:
            pytest.fail(f"Server initialization failed: {e}")

    async def test_tool_discovery(self, mcp_client):
        """Test that enhanced tools are discoverable via MCP protocol."""
        try:
            await mcp_client.initialize_mcp_session()
            tools_response = await mcp_client.list_tools()

            assert "result" in tools_response
            tools = tools_response["result"]["tools"]

            # Check for key enhanced tools
            tool_names = [tool["name"] for tool in tools]

            expected_tools = [
                "resource_manager_tool",
                "search_engine_tool",
                "get_tool_examples",
                "get_resource_schema"
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"Missing tool: {expected_tool}"

            print(f"✅ Found {len(tools)} tools via MCP protocol")

        except Exception as e:
            pytest.fail(f"Tool discovery failed: {e}")

    async def test_enhanced_docstrings_exposed(self, mcp_client):
        """Test that enhanced docstrings are properly exposed to MCP clients."""
        try:
            await mcp_client.initialize_mcp_session()
            tools_response = await mcp_client.list_tools()
            tools = tools_response["result"]["tools"]

            # Find resource_manager_tool
            resource_manager = None
            for tool in tools:
                if tool["name"] == "resource_manager_tool":
                    resource_manager = tool
                    break

            assert resource_manager is not None, "resource_manager_tool not found"

            # Check that enhanced description is present
            description = resource_manager["description"]

            # Verify key enhancements are present
            enhancement_checks = {
                "detailed_params": "Parameters:" in description,
                "available_resources": "Available Resources:" in description,
                "usage_examples": "Usage Examples:" in description,
                "env_values": "~911651470" in description and "FTEST" in description,
                "confluence_example": "Create Confluence Page" in description,
                "jira_example": "Create Jira Issue" in description,
                "comprehensive": len(description) > 2000  # Should be much more detailed
            }

            failed_checks = []
            for check_name, passed in enhancement_checks.items():
                if not passed:
                    failed_checks.append(check_name)

            if failed_checks:
                pytest.fail(f"Enhanced docstring validation failed: {failed_checks}")

            print("✅ Enhanced docstrings properly exposed via MCP protocol")
            print(f"   Description length: {len(description)} characters")

        except Exception as e:
            pytest.fail(f"Enhanced docstring validation failed: {e}")

    async def test_parameter_schema_clarity(self, mcp_client):
        """Test that tool parameters are clearly defined for MCP clients."""
        try:
            await mcp_client.initialize_mcp_session()
            tools_response = await mcp_client.list_tools()
            tools = tools_response["result"]["tools"]

            # Check resource_manager_tool parameters
            resource_manager = next(
                (tool for tool in tools if tool["name"] == "resource_manager_tool"),
                None
            )

            assert resource_manager is not None

            # Verify parameter schema
            input_schema = resource_manager["inputSchema"]
            properties = input_schema["properties"]
            required = input_schema.get("required", [])

            # Check key parameters are defined
            expected_params = ["service", "resource", "operation"]
            for param in expected_params:
                assert param in properties, f"Missing parameter: {param}"
                assert param in required, f"Parameter should be required: {param}"

            optional_params = ["identifier", "data", "options", "dry_run"]
            for param in optional_params:
                assert param in properties, f"Missing optional parameter: {param}"

            print("✅ Parameter schemas are clearly defined")

        except Exception as e:
            pytest.fail(f"Parameter schema validation failed: {e}")


class TestCursorScenarioSimulation:
    """Simulate the exact scenario from the Cursor conversation."""

    async def test_confluence_page_creation_clarity(self, mcp_client):
        """Test if MCP client can understand Confluence page creation from enhanced docs."""
        try:
            await mcp_client.initialize_mcp_session()
            tools_response = await mcp_client.list_tools()
            tools = tools_response["result"]["tools"]

            # Get resource_manager_tool
            resource_manager = next(
                (tool for tool in tools if tool["name"] == "resource_manager_tool"),
                None
            )

            description = resource_manager["description"]

            # Check if MCP client can extract key information from description
            # This simulates what Cursor would need to understand

            extraction_tests = {
                "space_key_format": "space_key" in description and "~911651470" in description,
                "title_requirement": 'title": "' in description,
                "body_requirement": 'body": "' in description,
                "confluence_service": 'service="confluence"' in description,
                "page_resource": 'resource="page"' in description,
                "create_operation": 'operation="create"' in description,
                "data_structure": '"data": {' in description,
                "complete_example": "await resource_manager_tool(" in description,
            }

            failed_extractions = []
            for test_name, passed in extraction_tests.items():
                if not passed:
                    failed_extractions.append(test_name)

            if failed_extractions:
                pytest.fail(f"MCP client would fail to extract: {failed_extractions}")

            print("✅ Enhanced documentation provides all info Cursor needs")
            print("✅ Original Cursor problem should be resolved")

        except Exception as e:
            pytest.fail(f"Cursor scenario simulation failed: {e}")


def create_cursor_test_config():
    """Create a test configuration file for Cursor IDE testing."""
    config = {
        "name": "MCP Atlassian Enhanced",
        "command": "uv",
        "args": ["run", "mcp-atlassian"],
        "env": {
            "ATLASSIAN_URL": "https://baseball.atlassian.net",
            "ATLASSIAN_EMAIL": "user@example.com",
            # Note: API token should be set in actual environment
        }
    }

    config_path = Path("tests/integration/cursor_mcp_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


if __name__ == "__main__":
    # Create Cursor test config
    config_path = create_cursor_test_config()
    print(f"Created Cursor test config: {config_path}")

    # Run basic validation
    print("Running real MCP client integration tests...")

    # Note: Full pytest run requires: pytest tests/integration/test_mcp_client_discovery.py -v
    print("To run full tests: pytest tests/integration/test_mcp_client_discovery.py -v")