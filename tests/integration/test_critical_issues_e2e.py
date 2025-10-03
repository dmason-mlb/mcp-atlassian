"""End-to-end integration tests for critical P0/P1 issue validation.

This module provides comprehensive end-to-end tests that validate the specific
critical issues identified in the QA report are properly fixed and won't regress.
These tests use real MCP server instances and exercise the full integration path.
"""

import asyncio
import json
import logging
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from .config import skip_if_no_real_api, get_test_config
from src.mcp_atlassian.servers.main import AtlassianMCP
from src.mcp_atlassian.servers.context import MainAppContext
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig

logger = logging.getLogger(__name__)


@pytest.fixture
async def mock_app_context():
    """Create a proper mock application context."""
    context = MagicMock()
    context.jira_client = AsyncMock()
    context.confluence_client = AsyncMock()
    context.jira_config = MagicMock()
    context.confluence_config = MagicMock()

    # Configure auth states
    context.jira_config.is_auth_configured.return_value = True
    context.confluence_config.is_auth_configured.return_value = True

    return context


@pytest.fixture
async def mcp_server(mock_app_context):
    """Create real AtlassianMCP server instance with mock context."""
    server = AtlassianMCP()

    # Set up proper context structure that dependencies.py expects
    mock_mcp_server = MagicMock()
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
    mock_mcp_server.request_context = mock_request_context
    server._mcp_server = mock_mcp_server

    return server


@pytest.mark.integration
@pytest.mark.anyio
class TestCriticalIssuesE2E:
    """End-to-end tests for critical P0/P1 issues."""

    async def test_p0_request_context_e2e(self, mcp_server):
        """E2E test for P0: RequestContext configuration error.

        This test exercises the full path from MCP tool call to dependencies.py
        to ensure the context structure is correct throughout.
        """
        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockRM:
            mock_rm_instance = MockRM.return_value
            mock_rm_instance.execute_operation = AsyncMock(return_value='{"success": true}')

            # Call through the actual MCP server tool interface
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "resource_manager_tool",
                    "arguments": {
                        "service": "jira",
                        "resource": "issue",
                        "operation": "get",
                        "identifier": "TEST-123",
                        "dry_run": True
                    }
                }
            }

            # This should work without the P0 error
            response = await mcp_server.request(request)

            # Verify no error occurred
            assert "error" not in response
            assert "result" in response

            # Verify the context was passed correctly to ResourceManager
            MockRM.assert_called_once_with(dry_run=True)
            mock_rm_instance.execute_operation.assert_called_once()

            # Verify context structure is correct
            call_args = mock_rm_instance.execute_operation.call_args
            ctx = call_args.kwargs['ctx']

            # This should work - if P0 bug existed, this would fail
            assert hasattr(ctx, 'request_context')
            assert hasattr(ctx.request_context, 'lifespan_context')

    async def test_p1_batch_processor_parameter_flow_e2e(self, mcp_server):
        """E2E test for P1: BatchProcessor parameter flow through tool handler.

        This test validates that parameters are correctly transformed and passed
        from the tool handler to the underlying implementation.
        """
        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBP:
            mock_bp_instance = MockBP.return_value
            mock_bp_instance.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            # Call through the actual MCP server tool interface with problematic parameters
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "batch_processor_tool",
                    "arguments": {
                        "service": "jira",
                        "operation": "create",
                        "resource": "issue",  # Should be converted to resource_type
                        "items": [{"summary": "Test Issue"}],
                        "concurrency": 8,  # Should be passed in options
                        "dry_run": True
                    }
                }
            }

            response = await mcp_server.request(request)

            # Verify no error occurred
            assert "error" not in response
            assert "result" in response

            # Verify BatchProcessor was called with correct parameters
            MockBP.assert_called_once_with(dry_run=True)
            mock_bp_instance.execute_batch_operation.assert_called_once()

            call_args = mock_bp_instance.execute_batch_operation.call_args

            # CRITICAL: Verify parameter transformations
            assert call_args.kwargs['resource_type'] == 'issue'  # Not 'resource'
            assert 'resource' not in call_args.kwargs  # Old parameter shouldn't exist

            # CRITICAL: Verify concurrency is passed in options
            assert 'options' in call_args.kwargs
            assert call_args.kwargs['options'] is not None
            assert call_args.kwargs['options']['concurrency'] == 8
            assert 'concurrency' not in call_args.kwargs  # Not as direct parameter

    async def test_p1_concurrency_clamping_e2e(self, mcp_server):
        """E2E test that concurrency is properly clamped to valid range."""
        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBP:
            mock_bp_instance = MockBP.return_value
            mock_bp_instance.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            # Test with concurrency > 10 (should be clamped to 10)
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "batch_processor_tool",
                    "arguments": {
                        "service": "jira",
                        "operation": "create",
                        "resource": "issue",
                        "items": [{"summary": "Test"}],
                        "concurrency": 50,  # Should be clamped to 10
                        "dry_run": True
                    }
                }
            }

            await mcp_server.request(request)

            call_args = mock_bp_instance.execute_batch_operation.call_args
            assert call_args.kwargs['options']['concurrency'] == 10  # Clamped

    async def test_all_meta_tools_dry_run_e2e(self, mcp_server):
        """E2E test that all meta-tools accept dry_run parameter correctly."""
        tool_tests = [
            ("resource_manager_tool", {
                "service": "jira",
                "resource": "issue",
                "operation": "get",
                "identifier": "TEST-123"
            }),
            ("search_engine_tool", {
                "service": "jira",
                "query_type": "jql",
                "query": "project = TEST"
            }),
            ("workflow_engine_tool", {
                "operation": "transition",
                "issue_key": "TEST-123",
                "transition_name": "In Progress"
            }),
            ("relationship_manager_tool", {
                "operation": "link",
                "issue_key": "TEST-123",
                "target_issue_key": "TEST-456",
                "link_type": "Blocks"
            }),
            ("attachment_handler_tool", {
                "service": "jira",
                "operation": "list",
                "issue_key": "TEST-123"
            })
        ]

        for tool_name, args in tool_tests:
            with patch(f'src.mcp_atlassian.meta_tools.{tool_name.replace("_tool", "")}.{tool_name.replace("_tool", "").title().replace("_", "")}') as MockTool:
                mock_instance = MockTool.return_value
                # Set up appropriate method name based on tool
                if "resource_manager" in tool_name:
                    mock_instance.execute_operation = AsyncMock(return_value='{"success": true}')
                elif "search_engine" in tool_name:
                    mock_instance.execute_search = AsyncMock(return_value='{"results": []}')
                elif "workflow_engine" in tool_name:
                    mock_instance.execute_workflow_operation = AsyncMock(return_value='{"success": true}')
                elif "relationship_manager" in tool_name:
                    mock_instance.execute_relationship_operation = AsyncMock(return_value='{"success": true}')
                elif "attachment_handler" in tool_name:
                    mock_instance.execute_attachment_operation = AsyncMock(return_value='{"success": true}')

                # Add dry_run parameter
                args["dry_run"] = True

                request = {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": args
                    }
                }

                response = await mcp_server.request(request)

                # Should not fail with dry_run parameter
                assert "error" not in response, f"Tool {tool_name} failed with dry_run parameter"

                # Verify tool was instantiated with dry_run=True
                MockTool.assert_called_once_with(dry_run=True)

    async def test_error_handling_structure_e2e(self, mcp_server):
        """E2E test that errors return structured JSON, not MCP exceptions."""
        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockRM:
            mock_rm_instance = MockRM.return_value
            # Simulate a MetaToolError with proper structure
            from src.mcp_atlassian.meta_tools.errors import MetaToolError
            error = MetaToolError(
                error_code="TEST_ERROR",
                user_message="Test error message",
                suggestions=["Try again"],
                context={"test": "data"}
            )
            mock_rm_instance.execute_operation = AsyncMock(side_effect=error)

            request = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "resource_manager_tool",
                    "arguments": {
                        "service": "jira",
                        "resource": "issue",
                        "operation": "get",
                        "identifier": "INVALID-123",
                        "dry_run": True
                    }
                }
            }

            response = await mcp_server.request(request)

            # Should get successful MCP response with error content, not MCP error
            assert "error" not in response
            assert "result" in response

            # Parse the error content
            content = response["result"]["content"]
            if isinstance(content, list):
                error_text = content[0]["text"]
            else:
                error_text = content

            error_data = json.loads(error_text)

            # Verify structured error format
            assert "error_code" in error_data
            assert "user_message" in error_data
            assert "suggestions" in error_data
            assert error_data["error_code"] == "TEST_ERROR"


@pytest.mark.integration
@skip_if_no_real_api("Real API testing not configured")
class TestCriticalIssuesRealAPI:
    """Real API tests for critical issues with actual Atlassian instances."""

    async def test_p0_p1_issues_with_real_api(self):
        """Test P0/P1 issues with real API to ensure complete integration works."""
        config = get_test_config()

        # Create real configs
        jira_config = JiraConfig(
            url=config.jira.url,
            auth_type="basic",
            username=config.jira.username,
            api_token=config.jira.api_token,
        )

        confluence_config = ConfluenceConfig(
            url=config.confluence.url,
            auth_type="basic",
            username=config.confluence.username,
            api_token=config.confluence.api_token,
        )

        # Create real app context
        app_context = MainAppContext(
            full_jira_config=jira_config,
            full_confluence_config=confluence_config,
            read_only=False,
            enabled_tools=None
        )

        # Create real server
        server = AtlassianMCP()

        # Set up real context
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        # Test P0 issue with real context access
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "jira",
                    "resource": "project",
                    "operation": "list",
                    "dry_run": True  # Use dry_run to avoid side effects
                }
            }
        }

        # This should work without P0 context error
        response = await server.request(request)
        assert "error" not in response

        # Test P1 issue with batch processor
        batch_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "batch_processor_tool",
                "arguments": {
                    "service": "jira",
                    "operation": "create",
                    "resource": "issue",
                    "items": [
                        {
                            "project_key": config.jira.project_key,
                            "summary": "Test P1 Issue",
                            "issuetype": {"name": "Task"}
                        }
                    ],
                    "concurrency": 3,
                    "dry_run": True  # Use dry_run to avoid creating real issues
                }
            }
        }

        # This should work with concurrency parameter properly passed
        batch_response = await server.request(batch_request)
        assert "error" not in batch_response

        # Parse response to verify concurrency was handled
        content = batch_response["result"]["content"]
        if isinstance(content, list):
            result_text = content[0]["text"]
        else:
            result_text = content

        result_data = json.loads(result_text)
        assert result_data["success"] is True

        logger.info("P0/P1 issues validated successfully with real API")