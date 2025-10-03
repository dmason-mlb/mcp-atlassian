#!/usr/bin/env python3
"""MCP Error Flow Testing

This test suite validates that errors are properly handled and returned through the MCP
protocol as structured JSON responses (not exceptions). AI agents need actionable error
messages with suggestions and examples to recover from failures.

These tests ensure errors are helpful, not just informative.
"""

import json
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.main import AtlassianMCP, main_lifespan
from mcp_atlassian.servers.context import MainAppContext
from tests.utils.mocks import MockEnvironment


@pytest.fixture
async def error_test_server():
    """Create test server for error flow validation."""
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
        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=mock_confluence_config,
            read_only=False,
            enabled_tools=None,
        )

        yield app_context


@pytest.mark.integration
@pytest.mark.anyio
class TestMCPErrorFlow:
    """Test error handling through MCP protocol."""

    async def test_confluence_missing_space_key_error(self, error_test_server):
        """Test structured error response when space_key is missing."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "title": "Test Page",
                        "body": "Test content"
                        # Missing space_key!
                    }
                }
            }
        }

        # Execute tool directly to test error handling
        from mcp_atlassian.servers.main import resource_manager_tool

        # Create context
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": error_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        # Execute tool (should return structured error, not raise exception)
        result = await resource_manager_tool(
            ctx,
            service="confluence",
            resource="page",
            operation="create",
            data={
                "title": "Test Page",
                "body": "Test content"
                # Missing space_key!
            }
        )

        error_data = json.loads(result)

        # Should be structured error response
        assert "error_code" in error_data
        assert error_data["error_code"] == "CONFLUENCE_MISSING_SPACE"

        # Should have actionable guidance
        assert "suggestions" in error_data
        assert len(error_data["suggestions"]) > 0

        # Should include working example
        assert "working_example" in error_data

        # Suggestions should mention space_key
        suggestions_text = " ".join(error_data["suggestions"])
        assert "space_key" in suggestions_text

        print("✅ Missing space_key returns structured error with guidance")

    async def test_confluence_missing_title_error(self, error_test_server):
        """Test structured error response when title is missing."""

        # Execute tool directly
        from mcp_atlassian.servers.main import resource_manager_tool

        # Create context
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": error_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await resource_manager_tool(
            ctx,
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "body": "Test content"
                # Missing title!
            }
        )

        error_data = json.loads(result)

        assert "error_code" in error_data
        assert error_data["error_code"] == "CONFLUENCE_MISSING_TITLE"
        assert "suggestions" in error_data
        assert "working_example" in error_data

        print("✅ Missing title returns structured error with guidance")

    async def test_confluence_missing_body_error(self, error_test_server):
        """Test structured error response when body is missing."""

        # Create context
        from mcp_atlassian.servers.main import resource_manager_tool

        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": error_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await resource_manager_tool(
            ctx,
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "title": "Test Page"
                # Missing body!
            }
        )

        error_data = json.loads(result)

        assert "error_code" in error_data
        assert error_data["error_code"] == "CONFLUENCE_MISSING_BODY"
        assert "suggestions" in error_data

        # Should specifically mention body in suggestions
        suggestions_text = " ".join(error_data["suggestions"])
        assert "body" in suggestions_text

        print("✅ Missing body returns structured error with guidance")

    async def test_jira_missing_project_key_error(self, error_test_server):
        """Test structured error response for missing Jira project_key."""

        # Create context
        from mcp_atlassian.servers.main import resource_manager_tool

        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": error_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await resource_manager_tool(
            ctx,
            service="jira",
            resource="issue",
            operation="create",
            data={
                "summary": "Test Issue",
                "issue_type": "Task"
                # Missing project_key!
            }
        )

        error_data = json.loads(result)

        assert "error_code" in error_data
        assert "MISSING" in error_data["error_code"] or "PROJECT" in error_data["error_code"]
        assert "suggestions" in error_data

        print("✅ Missing Jira project_key returns structured error")

    async def test_completely_missing_data_error(self, error_test_server):
        """Test error when data is completely missing."""

        # Create context
        from mcp_atlassian.servers.main import resource_manager_tool

        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": error_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await resource_manager_tool(
            ctx,
            service="confluence",
            resource="page",
            operation="create"
            # Missing data completely!
        )

        error_data = json.loads(result)

        assert "error_code" in error_data
        assert "suggestions" in error_data
        assert "working_example" in error_data

        # Should suggest providing data
        suggestions_text = " ".join(error_data["suggestions"])
        assert "data" in suggestions_text.lower()

        print("✅ Missing data completely returns structured error")

    async def test_invalid_service_error(self, error_test_server):
        """Test error for invalid service name."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "invalid_service",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "title": "Test"
                    }
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        assert "error" in error_data or "error_code" in error_data
        assert "suggestions" in error_data

        print("✅ Invalid service returns structured error")

    async def test_error_messages_include_working_examples(self, error_test_server):
        """Test that error messages always include working examples."""

        error_test_cases = [
            {
                "service": "confluence",
                "resource": "page",
                "operation": "create",
                "data": {"title": "Test"}  # Missing space_key and body
            },
            {
                "service": "jira",
                "resource": "issue",
                "operation": "create",
                "data": {"summary": "Test"}  # Missing project_key and issue_type
            },
        ]

        for test_case in error_test_cases:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "resource_manager_tool",
                    "arguments": test_case
                }
            }

            response = await error_test_server.request(request)
            result_content = response["result"]["content"]

            if isinstance(result_content, list):
                response_text = result_content[0]["text"]
            else:
                response_text = result_content

            error_data = json.loads(response_text)

            # Every error should include a working example
            assert "working_example" in error_data
            assert error_data["working_example"] is not None

            # Working example should be a complete structure
            working_example = error_data["working_example"]
            if isinstance(working_example, dict):
                assert "service" in working_example
                assert "resource" in working_example
                assert "operation" in working_example
                assert "data" in working_example

            print(f"✅ Working example included for {test_case['service']}/{test_case['resource']}")

    async def test_error_messages_are_actionable(self, error_test_server):
        """Test that error messages provide actionable guidance."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {"title": "Test Page"}  # Missing space_key and body
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # Check suggestions are actionable
        suggestions = error_data.get("suggestions", [])
        assert len(suggestions) > 0

        suggestions_text = " ".join(suggestions)

        # Should include specific examples
        assert "~911651470" in suggestions_text or "space_key" in suggestions_text
        assert "body" in suggestions_text

        # Should tell the user what to do (not just what's wrong)
        action_words = ["add", "include", "provide", "use", "set"]
        has_action_word = any(word in suggestions_text.lower() for word in action_words)
        assert has_action_word, "Suggestions should tell user what action to take"

        print("✅ Error messages provide actionable guidance")

    async def test_field_name_compatibility_errors(self, error_test_server):
        """Test that field name compatibility is handled in errors."""

        # Test with space_id (legacy) - should work and not give space_key error
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "space_id": "~911651470",  # Legacy field name
                        "title": "Test Page"
                        # Missing body only
                    }
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # Should NOT be a missing space error (space_id should be accepted)
        if "error_code" in error_data:
            assert error_data["error_code"] != "CONFLUENCE_MISSING_SPACE"

        # Should be missing body error instead
        if "error_code" in error_data:
            assert "BODY" in error_data["error_code"]

        print("✅ Legacy field names (space_id) are accepted")


@pytest.mark.integration
@pytest.mark.anyio
class TestErrorRecoveryGuidance:
    """Test that errors provide clear recovery guidance for AI agents."""

    async def test_error_context_includes_provided_fields(self, error_test_server):
        """Test that errors show which fields were provided vs missing."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "title": "Test Page",
                        "some_extra_field": "value"
                        # Missing space_key and body
                    }
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # Should include context about what was provided
        assert "context" in error_data

        context = error_data["context"]
        if isinstance(context, dict) and "provided_fields" in context:
            provided_fields = context["provided_fields"]
            assert "title" in provided_fields
            assert "some_extra_field" in provided_fields

        print("✅ Error context shows provided vs missing fields")

    async def test_error_messages_prevent_common_mistakes(self, error_test_server):
        """Test that error messages help prevent common AI agent mistakes."""

        # Common mistake: Using wrong field names
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "space": "~911651470",  # Wrong field name (should be space_key)
                        "title": "Test Page",
                        "content": "Test content"  # Wrong field name (should be body)
                    }
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # Should provide guidance about correct field names
        suggestions_text = " ".join(error_data.get("suggestions", []))
        assert "space_key" in suggestions_text
        assert "body" in suggestions_text

        print("✅ Error messages help prevent common field name mistakes")

    async def test_errors_provide_minimal_recovery_examples(self, error_test_server):
        """Test that errors include minimal examples for quick recovery."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {}  # Empty data
                }
            }
        }

        response = await error_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        working_example = error_data.get("working_example", {})

        # Working example should be minimal but complete
        if isinstance(working_example, dict) and "data" in working_example:
            example_data = working_example["data"]
            assert "space_key" in example_data
            assert "title" in example_data
            assert "body" in example_data

            # Values should be realistic examples, not just placeholders
            assert "~" in example_data["space_key"] or example_data["space_key"] != "string"

        print("✅ Errors provide minimal, realistic recovery examples")