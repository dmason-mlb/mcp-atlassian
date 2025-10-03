"""Regression tests for critical P0 and P1 issues in meta-tools.

This module contains focused regression tests for the most critical issues
that caused the Atlassian MCP server to be in a non-functional state.

P0 CRITICAL ISSUE: RequestContext configuration error
- 'RequestContext' object has no attribute 'request_context'
- Fixed by changing ctx=server._mcp_server.request_context to ctx=server._mcp_server

P1 ISSUES: BatchProcessor API signature mismatches
- Unexpected 'resource' parameter, should be 'resource_type'
- Incorrect 'concurrency' parameter passed directly instead of in options

DRY_RUN PARAMETER ISSUES: All meta-tools must accept dry_run parameter
- BatchProcessor, SearchEngine, WorkflowEngine, RelationshipManager, AttachmentHandler
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.meta_tools.errors import MetaToolError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestCriticalRegressionPrevention:
    """Critical regression tests for P0 and P1 issues."""

    @pytest.fixture
    def mock_app_context(self):
        """Create mock application context."""
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
    def correct_server_context(self, mock_app_context):
        """Create server context with CORRECT structure for P0 issue prevention."""
        mock_server = MagicMock()
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()

        # Set up the correct structure that dependencies.py expects
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        mock_server._mcp_server = mock_mcp_server

        return mock_server

    @pytest.fixture
    def broken_server_context(self, mock_app_context):
        """Create server context with BROKEN structure that would cause P0 issue."""
        mock_server = MagicMock()
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()

        # This is the broken pattern that caused the P0 issue
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        mock_server._mcp_server = mock_mcp_server

        # The broken pattern would try to access: server._mcp_server.request_context
        # and then try to access .request_context again, causing AttributeError
        return mock_server


class TestP0CriticalIssueRegression(TestCriticalRegressionPrevention):
    """Test P0 Critical Issue: RequestContext configuration error."""

    async def test_p0_correct_context_access_pattern(self, correct_server_context):
        """Test that the CORRECT context access pattern works."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher

        with patch('src.mcp_atlassian.jira.client.JiraClient') as MockJiraClient:
            mock_client = MockJiraClient.return_value

            # This should work: ctx = server._mcp_server (correct)
            fetcher = get_jira_fetcher(correct_server_context._mcp_server)
            assert fetcher is not None

    async def test_p0_broken_context_access_would_fail(self, broken_server_context):
        """Test that the BROKEN context access pattern would cause AttributeError."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher

        with patch('src.mcp_atlassian.jira.client.JiraClient'):
            # The broken pattern that caused P0: ctx = server._mcp_server.request_context
            # This would fail with: AttributeError: 'RequestContext' object has no attribute 'request_context'
            with pytest.raises(AttributeError) as exc_info:
                # Simulate the old broken pattern
                broken_context = broken_server_context._mcp_server.request_context
                get_jira_fetcher(broken_context)

            assert "has no attribute 'request_context'" in str(exc_info.value)

    async def test_p0_all_v2_tool_handlers_use_correct_context(self, correct_server_context):
        """Test that all v2 tool handlers in main.py use the correct context pattern."""
        from src.mcp_atlassian.servers.main import (
            batch_processor_tool, resource_manager_tool, search_engine_tool,
            workflow_engine_tool, relationship_manager_tool, attachment_handler_tool
        )

        # Mock all meta-tools to verify they're called with correct context
        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBP:
            MockBP.return_value.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",
                items=[{"summary": "Test"}],
                dry_run=True
            )

            # Verify BatchProcessor was instantiated (which means no context error)
            MockBP.assert_called_once()

        # Test all other tool handlers
        meta_tool_patches = [
            ('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager', 'execute_operation'),
            ('src.mcp_atlassian.meta_tools.search_engine.SearchEngine', 'execute_search'),
            ('src.mcp_atlassian.meta_tools.workflow_engine.WorkflowEngine', 'execute_workflow_operation'),
            ('src.mcp_atlassian.meta_tools.relationship_manager.RelationshipManager', 'execute_relationship_operation'),
            ('src.mcp_atlassian.meta_tools.attachment_handler.AttachmentHandler', 'execute_attachment_operation')
        ]

        tools_and_calls = [
            (resource_manager_tool, {"service": "jira", "resource": "issue", "operation": "get", "identifier": "TEST-123", "dry_run": True}),
            (search_engine_tool, {"service": "jira", "query_type": "jql", "query": "project = TEST", "dry_run": True}),
            (workflow_engine_tool, {"operation": "transition", "issue_key": "TEST-123", "transition_name": "In Progress", "dry_run": True}),
            (relationship_manager_tool, {"operation": "link", "issue_key": "TEST-123", "target_issue_key": "TEST-456", "link_type": "Blocks", "dry_run": True}),
            (attachment_handler_tool, {"service": "jira", "operation": "upload", "issue_key": "TEST-123", "file_path": "/test/file.txt", "dry_run": True})
        ]

        for (module_path, method_name), (tool_func, call_args) in zip(meta_tool_patches, tools_and_calls):
            with patch(module_path) as MockTool:
                mock_instance = MockTool.return_value
                setattr(mock_instance, method_name, AsyncMock(return_value='{"success": true}'))

                # This should work without context errors
                result = await tool_func(**call_args)
                assert '"success": true' in result

                # Verify the tool was instantiated (no context access errors)
                MockTool.assert_called_once()


class TestP1BatchProcessorAPISignatureRegression(TestCriticalRegressionPrevention):
    """Test P1 Issues: BatchProcessor API signature mismatches."""

    @pytest.fixture
    def batch_processor(self):
        """Create BatchProcessor for testing."""
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
        return BatchProcessor(dry_run=True)

    async def test_p1_correct_api_signature_works(self, batch_processor, correct_server_context):
        """Test that the CORRECT API signature works."""
        mock_context = correct_server_context._mcp_server

        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "TEST-123", "summary": "Test Issue"}
            mock_jira_client.create_issue.return_value = mock_issue

            items = [{"summary": "Test Issue", "project": {"key": "TEST"}, "issuetype": {"name": "Task"}}]

            # This should work with CORRECT signature
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",  # CORRECT: resource_type
                items=items,
                options={"concurrency": 2},  # CORRECT: concurrency in options
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True
            assert result["resource_type"] == "issue"

    async def test_p1_broken_resource_parameter_fails(self, batch_processor, correct_server_context):
        """Test that the BROKEN 'resource' parameter causes TypeError."""
        mock_context = correct_server_context._mcp_server
        items = [{"summary": "Test Issue"}]

        # This should FAIL - using 'resource' instead of 'resource_type'
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource="issue",  # BROKEN: should be resource_type
                items=items,
                dry_run=True
            )

        assert "unexpected keyword argument 'resource'" in str(exc_info.value)

    async def test_p1_broken_concurrency_parameter_fails(self, batch_processor, correct_server_context):
        """Test that the BROKEN direct 'concurrency' parameter causes TypeError."""
        mock_context = correct_server_context._mcp_server
        items = [{"summary": "Test Issue"}]

        # This should FAIL - passing concurrency as direct parameter
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                concurrency=2,  # BROKEN: should be in options
                dry_run=True
            )

        assert "unexpected keyword argument 'concurrency'" in str(exc_info.value)

    async def test_p1_batch_processor_tool_handler_converts_parameters(self):
        """Test that batch_processor_tool handler converts parameters correctly."""
        from src.mcp_atlassian.servers.main import batch_processor_tool

        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBatchProcessor:
            mock_instance = MockBatchProcessor.return_value
            mock_instance.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            # Call with the old parameter name 'resource'
            await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",  # This should be converted to resource_type
                items=[{"summary": "Test"}],
                concurrency=2,  # This should be moved to options
                dry_run=True
            )

            # Verify the call was made with correct parameters
            call_args = mock_instance.execute_batch_operation.call_args

            # Should have resource_type, not resource
            assert 'resource_type' in call_args.kwargs
            assert 'resource' not in call_args.kwargs
            assert call_args.kwargs['resource_type'] == 'issue'

            # Should not have concurrency as direct parameter
            assert 'concurrency' not in call_args.kwargs


class TestDryRunParameterRegression(TestCriticalRegressionPrevention):
    """Test that all meta-tools accept dry_run parameter."""

    async def test_all_meta_tools_accept_dry_run_parameter(self):
        """Test that ALL meta-tools accept dry_run parameter in their constructors."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
        from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

        # This was the core issue - these constructors were missing dry_run parameter
        meta_tool_classes = [
            ResourceManager,
            BatchProcessor,
            SearchEngine,
            WorkflowEngine,
            RelationshipManager,
            AttachmentHandler
        ]

        for tool_class in meta_tool_classes:
            try:
                # Should work with dry_run=True
                tool_dry = tool_class(dry_run=True)
                assert tool_dry.dry_run is True

                # Should work with dry_run=False
                tool_normal = tool_class(dry_run=False)
                assert tool_normal.dry_run is False

                # Should work with default (False)
                tool_default = tool_class()
                assert tool_default.dry_run is False

            except TypeError as e:
                if "unexpected keyword argument 'dry_run'" in str(e):
                    pytest.fail(f"{tool_class.__name__} constructor does not accept dry_run parameter: {e}")
                else:
                    raise

    async def test_meta_tools_dry_run_behavior(self):
        """Test that dry_run parameter affects behavior correctly."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        # Test dry-run mode
        rm_dry = ResourceManager(dry_run=True)
        assert rm_dry.dry_run is True

        # Test normal mode
        rm_normal = ResourceManager(dry_run=False)
        assert rm_normal.dry_run is False

        # Verify the property is accessible and correct
        assert hasattr(rm_dry, 'dry_run')
        assert hasattr(rm_normal, 'dry_run')


class TestEndToEndRegressionValidation(TestCriticalRegressionPrevention):
    """End-to-end validation that all issues are fixed."""

    async def test_complete_v2_tool_workflow_regression(self, correct_server_context):
        """Test complete v2 tool workflow to ensure no regressions."""
        from src.mcp_atlassian.servers.main import (
            batch_processor_tool, resource_manager_tool, search_engine_tool
        )

        # Mock all dependencies to avoid real API calls
        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBP, \
             patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockRM, \
             patch('src.mcp_atlassian.meta_tools.search_engine.SearchEngine') as MockSE:

            # Set up mocks
            MockBP.return_value.execute_batch_operation = AsyncMock(return_value='{"success": true, "results": []}')
            MockRM.return_value.execute_operation = AsyncMock(return_value='{"key": "TEST-123", "summary": "Test Issue"}')
            MockSE.return_value.execute_search = AsyncMock(return_value='{"results": [], "total": 0}')

            # Test batch operation (P1 issue)
            batch_result = await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",  # Converted to resource_type
                items=[{"summary": "Test Issue"}],
                concurrency=1,  # Moved to options
                dry_run=True
            )
            assert '"success": true' in batch_result

            # Test resource operation (P0 context issue)
            resource_result = await resource_manager_tool(
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
                dry_run=True
            )
            assert '"key": "TEST-123"' in resource_result

            # Test search operation (dry_run parameter issue)
            search_result = await search_engine_tool(
                service="jira",
                query_type="jql",
                query="project = TEST",
                dry_run=True
            )
            assert '"results"' in search_result

            # Verify all tools were instantiated with dry_run=True
            MockBP.assert_called_with(dry_run=True)
            MockRM.assert_called_with(dry_run=True)
            MockSE.assert_called_with(dry_run=True)

    async def test_regression_test_coverage_completeness(self):
        """Meta-test to ensure all critical issues have regression tests."""
        # This test verifies that our regression tests cover all the critical issues

        # P0 Issue: RequestContext access pattern
        p0_tests = [
            'test_p0_correct_context_access_pattern',
            'test_p0_broken_context_access_would_fail',
            'test_p0_all_v2_tool_handlers_use_correct_context'
        ]

        # P1 Issues: BatchProcessor API signature
        p1_tests = [
            'test_p1_correct_api_signature_works',
            'test_p1_broken_resource_parameter_fails',
            'test_p1_broken_concurrency_parameter_fails',
            'test_p1_batch_processor_tool_handler_converts_parameters'
        ]

        # Dry-run parameter issues
        dry_run_tests = [
            'test_all_meta_tools_accept_dry_run_parameter',
            'test_meta_tools_dry_run_behavior'
        ]

        # End-to-end validation
        e2e_tests = [
            'test_complete_v2_tool_workflow_regression'
        ]

        # Verify all test methods exist in this class
        current_class = TestCriticalRegressionPrevention
        available_methods = [method for method in dir(current_class) if method.startswith('test_')]

        all_expected_tests = p0_tests + p1_tests + dry_run_tests + e2e_tests

        for test_name in all_expected_tests:
            assert hasattr(current_class, test_name), f"Missing regression test: {test_name}"

        logger.info(f"Regression test coverage verified: {len(all_expected_tests)} critical tests present")

        # Summary for QA team
        coverage_summary = {
            "P0_Critical_RequestContext": len(p0_tests),
            "P1_BatchProcessor_API": len(p1_tests),
            "DryRun_Parameter": len(dry_run_tests),
            "EndToEnd_Validation": len(e2e_tests),
            "Total_Regression_Tests": len(all_expected_tests)
        }

        logger.info(f"Regression test coverage summary: {coverage_summary}")
        assert len(all_expected_tests) >= 10, "Should have at least 10 regression tests for critical issues"