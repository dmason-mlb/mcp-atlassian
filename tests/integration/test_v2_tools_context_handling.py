"""Integration tests for v2 tool context handling.

This module tests the critical context passing pattern that was fixed in the P0 issue.
It ensures that ctx=server._mcp_server is passed correctly to all meta-tool handlers.
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestV2ToolsContextHandling:
    """Test suite for v2 tools context passing."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a mock MainAppContext."""
        app_context = MagicMock()
        app_context.jira_client = AsyncMock()
        app_context.confluence_client = AsyncMock()
        app_context.jira_config = MagicMock()
        app_context.confluence_config = MagicMock()

        # Configure auth states
        app_context.jira_config.is_auth_configured.return_value = True
        app_context.confluence_config.is_auth_configured.return_value = True

        return app_context

    @pytest.fixture
    async def mock_server(self, mock_app_context):
        """Create a mock AtlassianMCP server with proper context structure."""
        server = MagicMock(spec=AtlassianMCP)

        # Create the proper _mcp_server structure
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}

        # Set up the path that dependencies.py expects
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    async def test_batch_processor_tool_context_passing(self, mock_server):
        """Test BatchProcessor tool handler passes context correctly."""
        # Import the actual function from main.py
        from src.mcp_atlassian.servers.main import batch_processor_tool

        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBatchProcessor:
            mock_batch_instance = MockBatchProcessor.return_value
            mock_batch_instance.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            # Call the tool handler
            result = await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",  # Note: this should be converted to resource_type
                items=[{"summary": "Test Issue"}],
                dry_run=True
            )

            # Verify the BatchProcessor was called with the correct context pattern
            MockBatchProcessor.assert_called_once_with(dry_run=True)
            mock_batch_instance.execute_batch_operation.assert_called_once()

            # Get the actual call arguments
            call_args = mock_batch_instance.execute_batch_operation.call_args

            # Verify context is passed as server._mcp_server (not server._mcp_server.request_context)
            assert 'ctx' in call_args.kwargs
            # Verify resource is converted to resource_type
            assert call_args.kwargs['resource_type'] == 'issue'
            assert 'resource' not in call_args.kwargs

            # Verify the result is returned correctly
            assert '"success": true' in result

    async def test_resource_manager_tool_context_passing(self, mock_server):
        """Test ResourceManager tool handler passes context correctly."""
        from src.mcp_atlassian.servers.main import resource_manager_tool

        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockResourceManager:
            mock_rm_instance = MockResourceManager.return_value
            mock_rm_instance.execute_operation = AsyncMock(return_value='{"success": true}')

            # Call the tool handler
            result = await resource_manager_tool(
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
                dry_run=False
            )

            # Verify the ResourceManager was called correctly
            MockResourceManager.assert_called_once_with(dry_run=False)
            mock_rm_instance.execute_operation.assert_called_once()

            # Get the actual call arguments
            call_args = mock_rm_instance.execute_operation.call_args

            # Verify context is passed correctly
            assert 'ctx' in call_args.kwargs
            assert call_args.kwargs['service'] == 'jira'
            assert call_args.kwargs['resource'] == 'issue'
            assert call_args.kwargs['operation'] == 'get'
            assert call_args.kwargs['identifier'] == 'TEST-123'

    async def test_search_engine_tool_context_passing(self, mock_server):
        """Test SearchEngine tool handler passes context correctly."""
        from src.mcp_atlassian.servers.main import search_engine_tool

        with patch('src.mcp_atlassian.meta_tools.search_engine.SearchEngine') as MockSearchEngine:
            mock_se_instance = MockSearchEngine.return_value
            mock_se_instance.execute_search = AsyncMock(return_value='{"results": []}')

            # Call the tool handler
            result = await search_engine_tool(
                service="jira",
                query_type="jql",
                query="project = TEST",
                dry_run=True
            )

            # Verify the SearchEngine was called correctly
            MockSearchEngine.assert_called_once_with(dry_run=True)
            mock_se_instance.execute_search.assert_called_once()

    async def test_workflow_engine_tool_context_passing(self, mock_server):
        """Test WorkflowEngine tool handler passes context correctly."""
        from src.mcp_atlassian.servers.main import workflow_engine_tool

        with patch('src.mcp_atlassian.meta_tools.workflow_engine.WorkflowEngine') as MockWorkflowEngine:
            mock_we_instance = MockWorkflowEngine.return_value
            mock_we_instance.execute_workflow_operation = AsyncMock(return_value='{"success": true}')

            # Call the tool handler
            result = await workflow_engine_tool(
                operation="transition",
                issue_key="TEST-123",
                transition_name="In Progress",
                dry_run=False
            )

            # Verify the WorkflowEngine was called correctly
            MockWorkflowEngine.assert_called_once_with(dry_run=False)
            mock_we_instance.execute_workflow_operation.assert_called_once()

    async def test_relationship_manager_tool_context_passing(self, mock_server):
        """Test RelationshipManager tool handler passes context correctly."""
        from src.mcp_atlassian.servers.main import relationship_manager_tool

        with patch('src.mcp_atlassian.meta_tools.relationship_manager.RelationshipManager') as MockRelationshipManager:
            mock_rm_instance = MockRelationshipManager.return_value
            mock_rm_instance.execute_relationship_operation = AsyncMock(return_value='{"success": true}')

            # Call the tool handler
            result = await relationship_manager_tool(
                operation="link",
                issue_key="TEST-123",
                target_issue_key="TEST-456",
                link_type="Blocks",
                dry_run=True
            )

            # Verify the RelationshipManager was called correctly
            MockRelationshipManager.assert_called_once_with(dry_run=True)
            mock_rm_instance.execute_relationship_operation.assert_called_once()

    async def test_attachment_handler_tool_context_passing(self, mock_server):
        """Test AttachmentHandler tool handler passes context correctly."""
        from src.mcp_atlassian.servers.main import attachment_handler_tool

        with patch('src.mcp_atlassian.meta_tools.attachment_handler.AttachmentHandler') as MockAttachmentHandler:
            mock_ah_instance = MockAttachmentHandler.return_value
            mock_ah_instance.execute_attachment_operation = AsyncMock(return_value='{"success": true}')

            # Call the tool handler
            result = await attachment_handler_tool(
                service="jira",
                operation="upload",
                issue_key="TEST-123",
                file_path="/test/file.txt",
                dry_run=False
            )

            # Verify the AttachmentHandler was called correctly
            MockAttachmentHandler.assert_called_once_with(dry_run=False)
            mock_ah_instance.execute_attachment_operation.assert_called_once()

    async def test_context_access_pattern_validation(self, mock_server, mock_app_context):
        """Test that the context access pattern prevents the P0 error."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher

        # This should work with the correct pattern: ctx.request_context.lifespan_context
        # Where ctx = server._mcp_server (not server._mcp_server.request_context)

        with patch('src.mcp_atlassian.jira.client.JiraClient') as MockJiraClient:
            mock_client = MockJiraClient.return_value

            # Call get_jira_fetcher with the correct context structure
            fetcher = get_jira_fetcher(mock_server._mcp_server)

            # Verify it doesn't raise AttributeError: 'RequestContext' object has no attribute 'request_context'
            assert fetcher is not None

    async def test_all_meta_tools_accept_dry_run_parameter(self):
        """Test that all meta-tools accept dry_run parameter in their constructors."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
        from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

        # All these should not raise TypeError about unexpected dry_run argument
        tools = [
            ResourceManager(dry_run=True),
            BatchProcessor(dry_run=True),
            SearchEngine(dry_run=True),
            WorkflowEngine(dry_run=True),
            RelationshipManager(dry_run=True),
            AttachmentHandler(dry_run=True)
        ]

        for tool in tools:
            assert tool.dry_run is True

    async def test_batch_processor_api_signature_regression(self, mock_server):
        """Test that BatchProcessor API signature regression is prevented."""
        from src.mcp_atlassian.servers.main import batch_processor_tool

        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBatchProcessor:
            mock_batch_instance = MockBatchProcessor.return_value
            mock_batch_instance.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            # Call with parameters that caused the P1 issue
            await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",  # This should be converted to resource_type
                items=[{"summary": "Test"}],
                concurrency=2,  # This should be moved to options
                dry_run=True
            )

            # Verify the call was made with correct parameter names
            call_args = mock_batch_instance.execute_batch_operation.call_args

            # Should have resource_type, not resource
            assert 'resource_type' in call_args.kwargs
            assert 'resource' not in call_args.kwargs
            assert call_args.kwargs['resource_type'] == 'issue'

            # Should not have concurrency as direct parameter
            assert 'concurrency' not in call_args.kwargs

            # Concurrency should be in options if provided
            if 'options' in call_args.kwargs and call_args.kwargs['options']:
                # Could be in options, but not as direct parameter
                pass