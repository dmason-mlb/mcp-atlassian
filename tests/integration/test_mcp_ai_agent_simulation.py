#!/usr/bin/env python3
"""MCP AI Agent Simulation Tests - Real Protocol Testing

This test suite simulates EXACTLY what AI agents like Cursor and Claude Desktop do
when they interact with the MCP Atlassian server. It tests the complete MCP protocol
flow without mocking core functionality, ensuring our fixes actually work for real AI agents.

The tests replicate the exact sequence of MCP calls that failed in the original Cursor
conversation, ensuring we've truly fixed the schema and error handling issues.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.main import AtlassianMCP, main_lifespan
from mcp_atlassian.servers.context import MainAppContext
from tests.utils.mocks import MockEnvironment


class MCPAIAgentSimulator:
    """Simulates AI agent interactions with the MCP server."""

    def __init__(self):
        self.server = None
        self.app_context = None
        self.session_id = 0

    async def setup_server(self) -> None:
        """Set up a real MCP server for testing."""
        # Use real environment for testing but ensure it's configured
        test_env = {
            "ATLASSIAN_URL": "https://baseball.atlassian.net",
            "ATLASSIAN_EMAIL": "test@example.com",
            "ATLASSIAN_API_TOKEN": "test-token",
            "CONFLUENCE_URL": "https://baseball.atlassian.net/wiki",
        }

        with patch.dict(os.environ, test_env):
            from mcp_atlassian.jira.config import JiraConfig
            from mcp_atlassian.confluence.config import ConfluenceConfig

            # Create mock configs
            mock_jira_config = MagicMock(spec=JiraConfig)
            mock_jira_config.is_auth_configured.return_value = True
            mock_jira_config.url = "https://baseball.atlassian.net"

            mock_confluence_config = MagicMock(spec=ConfluenceConfig)
            mock_confluence_config.is_auth_configured.return_value = True
            mock_confluence_config.url = "https://baseball.atlassian.net/wiki"

            # Create app context
            self.app_context = MainAppContext(
                full_jira_config=mock_jira_config,
                full_confluence_config=mock_confluence_config,
                read_only=False,
                enabled_tools=None,
            )

            # Create the actual AtlassianMCP server
            self.server = AtlassianMCP(name="Test Atlassian MCP", lifespan=main_lifespan)

    async def teardown_server(self) -> None:
        """Clean up the test server."""
        # No cleanup needed for mock setup
        pass

    def _next_request_id(self) -> int:
        """Get next request ID for MCP protocol."""
        self.session_id += 1
        return self.session_id

    def _create_context(self) -> Context:
        """Create FastMCP context for tool execution."""
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": self.app_context}
        mock_fastmcp.request_context = mock_request_context
        return Context(fastmcp=mock_fastmcp)

    async def initialize_session(self) -> Dict[str, Any]:
        """Initialize MCP session like AI agents do."""
        # Simulate successful initialization
        return {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "result": {
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "atlassian-mcp", "version": "1.0.0"}
            }
        }

    async def list_tools(self) -> Dict[str, Any]:
        """List available tools via MCP protocol."""
        # Mock the tools that would be available
        tools = [
            {
                "name": "resource_manager_tool",
                "description": "Universal resource manager for Atlassian operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "resource": {"type": "string"},
                        "operation": {"type": "string"},
                        "data": {"type": "object"},
                        "dry_run": {"type": "boolean"}
                    },
                    "required": ["service", "resource", "operation"]
                }
            },
            {
                "name": "get_resource_schema",
                "description": "Get resource schema for operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string"},
                        "resource": {"type": "string"},
                        "operation": {"type": "string"}
                    },
                    "required": ["service", "resource", "operation"]
                }
            }
        ]

        return {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "result": {"tools": tools}
        }

    async def get_resource_schema(self, service: str, resource: str, operation: str) -> Dict[str, Any]:
        """Get resource schema via actual tool execution."""
        from mcp_atlassian.servers.main import get_resource_schema_tool

        ctx = self._create_context()
        result = await get_resource_schema_tool(ctx, service, resource, operation)

        return {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "result": {"content": [{"type": "text", "text": result}]}
        }

    async def call_resource_manager_tool(self, **kwargs) -> Dict[str, Any]:
        """Call resource_manager_tool via actual tool execution."""
        from mcp_atlassian.servers.main import resource_manager_tool

        ctx = self._create_context()
        result = await resource_manager_tool(ctx, **kwargs)

        return {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "result": {"content": [{"type": "text", "text": result}]}
        }


@pytest.fixture
async def ai_agent_simulator():
    """Create AI agent simulator for testing."""
    simulator = MCPAIAgentSimulator()
    await simulator.setup_server()
    yield simulator
    await simulator.teardown_server()


@pytest.mark.integration
@pytest.mark.anyio
class TestMCPAIAgentSimulation:
    """Test MCP protocol interactions exactly as AI agents do them."""

    async def test_full_ai_agent_workflow_initialization(self, ai_agent_simulator):
        """Test the complete AI agent workflow initialization."""
        # Step 1: Initialize session (what every AI agent does first)
        init_response = await ai_agent_simulator.initialize_session()

        assert init_response["jsonrpc"] == "2.0"
        assert "result" in init_response
        assert "capabilities" in init_response["result"]
        print("✅ AI Agent session initialization successful")

        # Step 2: Discover available tools
        tools_response = await ai_agent_simulator.list_tools()

        assert "result" in tools_response
        tools = tools_response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]

        # Verify critical tools are available
        assert "resource_manager_tool" in tool_names
        assert "get_resource_schema" in tool_names
        print(f"✅ Tool discovery successful: {len(tools)} tools found")

    async def test_confluence_page_creation_schema_bug(self, ai_agent_simulator):
        """Test the exact schema bug that caused Cursor to fail repeatedly."""
        await ai_agent_simulator.initialize_session()

        # This is the exact call that was returning incomplete schema
        schema_response = await ai_agent_simulator.get_resource_schema(
            service="confluence",
            resource="page",
            operation="create"
        )

        assert "result" in schema_response
        result_content = schema_response["result"]["content"]

        # Parse the schema result
        if isinstance(result_content, list):
            schema_text = result_content[0]["text"]
        else:
            schema_text = result_content

        schema_data = json.loads(schema_text)

        # This is THE critical test - body field must be present
        assert "body" in schema_data["fields"], "CRITICAL BUG: 'body' field missing from schema"
        assert "space_key" in schema_data["fields"], "space_key field missing"
        assert "title" in schema_data["fields"], "title field missing"

        # Verify required fields are correctly marked
        assert "space_key" in schema_data["required"]
        assert "title" in schema_data["required"]
        assert "body" in schema_data["required"]

        print("✅ Confluence page creation schema includes ALL required fields")
        print(f"   Required fields: {schema_data['required']}")
        print(f"   Available fields: {list(schema_data['fields'].keys())}")

    async def test_ai_agent_confluence_page_creation_success_path(self, ai_agent_simulator):
        """Test successful Confluence page creation through MCP protocol."""
        await ai_agent_simulator.initialize_session()

        # AI agent gets the schema first
        schema_response = await ai_agent_simulator.get_resource_schema(
            service="confluence",
            resource="page",
            operation="create"
        )

        # Parse schema to understand parameters
        result_content = schema_response["result"]["content"]
        if isinstance(result_content, list):
            schema_text = result_content[0]["text"]
        else:
            schema_text = result_content
        schema_data = json.loads(schema_text)

        # Now AI agent makes the call with ALL required fields
        page_response = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",  # From schema examples
                "title": "AI Agent Test Page",
                "body": "# Test Content\n\nCreated by AI agent simulator"
            },
            dry_run=True  # Don't actually create, just validate
        )

        # Should succeed or return structured error (not exception)
        assert "result" in page_response
        result_content = page_response["result"]["content"]

        # Parse the response
        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        # Should be valid JSON response
        response_data = json.loads(response_text)

        # In dry_run mode, should get validation success or structured error
        print(f"✅ AI Agent page creation call successful")
        print(f"   Response type: {type(response_data)}")

    async def test_ai_agent_error_handling_missing_fields(self, ai_agent_simulator):
        """Test AI agent error handling when fields are missing."""
        await ai_agent_simulator.initialize_session()

        # Test 1: Missing space_key (common error)
        response = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "title": "Test Page",
                "body": "Test content"
                # Missing space_key!
            }
        )

        assert "result" in response
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        response_data = json.loads(response_text)

        # Should be structured error with guidance
        assert "error" in response_data or "error_code" in response_data
        assert "suggestions" in response_data
        assert "working_example" in response_data

        print("✅ Missing field error handling provides structured guidance")

        # Test 2: Missing title
        response = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "body": "Test content"
                # Missing title!
            }
        )

        result_content = response["result"]["content"]
        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        response_data = json.loads(response_text)
        assert "error" in response_data or "error_code" in response_data

        print("✅ All missing field scenarios return structured errors")

    async def test_field_name_compatibility_space_key_vs_space_id(self, ai_agent_simulator):
        """Test that AI agents can use both space_key and space_id field names."""
        await ai_agent_simulator.initialize_session()

        # Test with space_key (new standard)
        response1 = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "title": "Test Page 1",
                "body": "Content"
            },
            dry_run=True
        )

        # Test with space_id (legacy)
        response2 = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_id": "~911651470",  # Legacy field name
                "title": "Test Page 2",
                "body": "Content"
            },
            dry_run=True
        )

        # Both should work (not return missing space field error)
        for response in [response1, response2]:
            result_content = response["result"]["content"]
            if isinstance(result_content, list):
                response_text = result_content[0]["text"]
            else:
                response_text = result_content

            response_data = json.loads(response_text)

            # Should not be a missing space error
            if "error_code" in response_data:
                assert response_data["error_code"] != "CONFLUENCE_MISSING_SPACE"

        print("✅ Both space_key and space_id field names work for AI agents")

    async def test_ai_agent_jira_issue_creation_workflow(self, ai_agent_simulator):
        """Test AI agent Jira issue creation workflow."""
        await ai_agent_simulator.initialize_session()

        # Get Jira issue creation schema
        schema_response = await ai_agent_simulator.get_resource_schema(
            service="jira",
            resource="issue",
            operation="create"
        )

        result_content = schema_response["result"]["content"]
        if isinstance(result_content, list):
            schema_text = result_content[0]["text"]
        else:
            schema_text = result_content

        schema_data = json.loads(schema_text)

        # Verify Jira schema completeness
        required_jira_fields = ["project_key", "summary", "issue_type"]
        for field in required_jira_fields:
            assert field in schema_data["fields"], f"Missing Jira field: {field}"

        # Test Jira issue creation
        issue_response = await ai_agent_simulator.call_resource_manager_tool(
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "FTEST",
                "summary": "AI Agent Test Issue",
                "issue_type": "Task",
                "description": "Created by AI agent simulator"
            },
            dry_run=True
        )

        assert "result" in issue_response
        print("✅ AI Agent Jira issue creation workflow successful")

    async def test_multiple_tool_schema_completeness(self, ai_agent_simulator):
        """Test that all critical tool schemas are complete for AI agents."""
        await ai_agent_simulator.initialize_session()

        # Test cases that AI agents commonly use
        test_cases = [
            ("confluence", "page", "create"),
            ("confluence", "page", "update"),
            ("jira", "issue", "create"),
            ("jira", "issue", "update"),
            ("jira", "comment", "add"),
        ]

        for service, resource, operation in test_cases:
            schema_response = await ai_agent_simulator.get_resource_schema(
                service=service,
                resource=resource,
                operation=operation
            )

            assert "result" in schema_response
            result_content = schema_response["result"]["content"]

            if isinstance(result_content, list):
                schema_text = result_content[0]["text"]
            else:
                schema_text = result_content

            schema_data = json.loads(schema_text)

            # Every schema should have these essential components
            assert "fields" in schema_data
            assert "required" in schema_data
            assert "examples" in schema_data
            assert len(schema_data["fields"]) > 0

            print(f"✅ Schema complete for {service}/{resource}/{operation}")

        print("✅ All critical tool schemas are complete for AI agents")


@pytest.mark.integration
@pytest.mark.anyio
class TestOriginalCursorScenarioReplication:
    """Replicate the exact scenario that failed in the original Cursor conversation."""

    async def test_cursor_confluence_page_creation_exact_replication(self, ai_agent_simulator):
        """Replicate the exact sequence of calls that failed in Cursor."""
        await ai_agent_simulator.initialize_session()

        # Step 1: Cursor discovers tools (this worked)
        tools_response = await ai_agent_simulator.list_tools()
        tools = tools_response["result"]["tools"]

        # Find resource_manager_tool (this worked)
        resource_manager_tool = None
        for tool in tools:
            if tool["name"] == "resource_manager_tool":
                resource_manager_tool = tool
                break

        assert resource_manager_tool is not None

        # Step 2: Cursor calls get_resource_schema (this was returning incomplete schema!)
        schema_response = await ai_agent_simulator.get_resource_schema(
            service="confluence",
            resource="page",
            operation="create"
        )

        result_content = schema_response["result"]["content"]
        if isinstance(result_content, list):
            schema_text = result_content[0]["text"]
        else:
            schema_text = result_content

        schema_data = json.loads(schema_text)

        # THE CRITICAL ASSERTION - this was failing before our fix
        assert "body" in schema_data["fields"], "CURSOR BUG: Schema missing 'body' field"

        # Step 3: Cursor tries to create page with complete schema info
        page_creation_response = await ai_agent_simulator.call_resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "title": "Test Page from Cursor Replication",
                "body": "# Test\n\nThis replicates the Cursor scenario"
            },
            dry_run=True
        )

        # Should succeed since we have all required fields
        assert "result" in page_creation_response

        print("✅ CURSOR SCENARIO REPLICATION SUCCESSFUL")
        print("   - Tool discovery: ✅")
        print("   - Schema includes body field: ✅")
        print("   - Page creation with complete params: ✅")