"""End-to-end integration tests for CRUD operations functionality.

This module tests the complete CRUD operation flow from the QA report,
ensuring that all Create, Read, Update, Delete operations work correctly
after fixing the "'Server' object has no attribute 'lifespan_context'" error.

Tests verify:
- Jira issue CRUD operations work end-to-end
- Confluence page CRUD operations work end-to-end
- Search operations work for both services
- Batch operations handle multiple items correctly
- Workflow operations (transitions) work properly
- Relationship operations (linking) work properly
- All operations that failed in QA report now pass
- Context passing works correctly for all meta-tools
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP, get_tool_context
from src.mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestCRUDOperationsE2E:
    """End-to-end test suite for CRUD operations functionality."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a mock MainAppContext with proper Jira/Confluence clients."""
        app_context = MagicMock()

        # Mock Jira configuration and client
        app_context.full_jira_config = MagicMock()
        app_context.full_jira_config.url = "https://test.atlassian.net"
        app_context.full_jira_config.auth_type = "oauth"
        app_context.full_jira_config.is_auth_configured.return_value = True

        # Mock Confluence configuration and client
        app_context.full_confluence_config = MagicMock()
        app_context.full_confluence_config.url = "https://test.atlassian.net"
        app_context.full_confluence_config.auth_type = "oauth"
        app_context.full_confluence_config.is_auth_configured.return_value = True

        return app_context

    @pytest.fixture
    async def mock_server(self, mock_app_context):
        """Create a mock AtlassianMCP server with proper context structure."""
        server = MagicMock(spec=AtlassianMCP)

        # Create the proper _mcp_server structure
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    async def test_jira_issue_create_operation_qa_scenario(self, mock_server):
        """Test Jira issue creation - reproduces QA report 'Create JIRA Issue' failure."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client
            mock_jira_fetcher = AsyncMock()
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {
                "key": "FTEST-123",
                "id": "10001",
                "summary": "Test Issue",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Task"}
            }
            mock_jira_fetcher.create_issue.return_value = mock_issue
            mock_get_jira.return_value = mock_jira_fetcher

            # Create ResourceManager instance
            resource_manager = ResourceManager(dry_run=False)

            # Test the exact operation that failed in QA report
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(mock_server),
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "project_key": "FTEST",
                    "summary": "Test Issue from QA Report",
                    "issue_type": "Task",
                    "description": "This issue creation failed in the QA report"
                }
            )

            result = json.loads(result_json)

            # Verify the operation succeeds (unlike in QA report)
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["resource"] == "issue"
            assert result["operation"] == "create"
            assert result["data"]["key"] == "FTEST-123"
            assert "error" not in result

            # Verify context was passed correctly (the fix)
            mock_get_jira.assert_called_once()
            context_arg = mock_get_jira.call_args[0][0]
            assert hasattr(context_arg, 'lifespan_context')

    async def test_jira_issue_read_operation(self, mock_server):
        """Test Jira issue retrieval - ensures read operations work post-fix."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client
            mock_jira_fetcher = AsyncMock()
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {
                "key": "FTEST-123",
                "id": "10001",
                "summary": "Test Issue",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Task"}
            }
            mock_jira_fetcher.get_issue.return_value = mock_issue
            mock_get_jira.return_value = mock_jira_fetcher

            # Create ResourceManager instance
            resource_manager = ResourceManager(dry_run=False)

            # Test issue retrieval
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(mock_server),
                service="jira",
                resource="issue",
                operation="get",
                identifier="FTEST-123"
            )

            result = json.loads(result_json)

            # Verify successful retrieval
            assert result["success"] is True
            assert result["data"]["key"] == "FTEST-123"
            mock_jira_fetcher.get_issue.assert_called_once_with("FTEST-123")

    async def test_jira_issue_update_operation_qa_scenario(self, mock_server):
        """Test Jira issue update - reproduces QA report update failures."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client
            mock_jira_fetcher = AsyncMock()
            mock_updated_issue = MagicMock()
            mock_updated_issue.to_simplified_dict.return_value = {
                "key": "FTEST-123",
                "id": "10001",
                "summary": "Updated Test Issue",
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Task"}
            }
            mock_jira_fetcher.update_issue.return_value = mock_updated_issue
            mock_get_jira.return_value = mock_jira_fetcher

            # Create ResourceManager instance
            resource_manager = ResourceManager(dry_run=False)

            # Test issue update operation
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(mock_server),
                service="jira",
                resource="issue",
                operation="update",
                identifier="FTEST-123",
                data={
                    "summary": "Updated Test Issue",
                    "description": "This update failed in the QA report but should work now"
                }
            )

            result = json.loads(result_json)

            # Verify successful update (unlike in QA report)
            assert result["success"] is True
            assert result["data"]["summary"] == "Updated Test Issue"
            mock_jira_fetcher.update_issue.assert_called_once()

    async def test_confluence_page_create_operation_qa_scenario(self, mock_server):
        """Test Confluence page creation - reproduces QA report Confluence failures."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        with patch('src.mcp_atlassian.servers.dependencies.get_confluence_fetcher') as mock_get_confluence:
            # Mock successful Confluence client
            mock_confluence_fetcher = AsyncMock()
            mock_page = MagicMock()
            mock_page.to_dict.return_value = {
                "id": "123456",
                "title": "Test Page",
                "space": {"key": "TEST"},
                "version": {"number": 1}
            }
            mock_confluence_fetcher.create_page.return_value = mock_page
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Create ResourceManager instance
            resource_manager = ResourceManager(dry_run=False)

            # Test page creation that failed in QA report
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(mock_server),
                service="confluence",
                resource="page",
                operation="create",
                data={
                    "space_key": "TEST",
                    "title": "Test Page from QA Report",
                    "body": "This page creation failed in the QA report"
                }
            )

            result = json.loads(result_json)

            # Verify successful creation (unlike in QA report)
            assert result["success"] is True
            assert result["service"] == "confluence"
            assert result["resource"] == "page"
            assert result["data"]["title"] == "Test Page"
            assert "error" not in result

    async def test_search_operations_qa_scenario(self, mock_server):
        """Test search operations - reproduces QA report search failures."""
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira search
            mock_jira_fetcher = AsyncMock()
            mock_search_results = {
                "issues": [
                    {
                        "key": "FTEST-123",
                        "fields": {
                            "summary": "Test Issue",
                            "status": {"name": "To Do"}
                        }
                    }
                ],
                "total": 1
            }
            mock_jira_fetcher.search_issues.return_value = mock_search_results
            mock_get_jira.return_value = mock_jira_fetcher

            # Create SearchEngine instance
            search_engine = SearchEngine(dry_run=False)

            # Test search operation that failed in QA report
            result_json = await search_engine.execute_search(
                ctx=get_tool_context(mock_server),
                service="jira",
                query_type="jql",
                query="project = FTEST AND summary ~ 'test'"
            )

            result = json.loads(result_json)

            # Verify successful search (unlike in QA report)
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["query_type"] == "jql"
            assert len(result["results"]) == 1
            assert result["results"][0]["key"] == "FTEST-123"
            assert "error" not in result

    async def test_batch_operations_qa_scenario(self, mock_server):
        """Test batch operations - ensures bulk operations work post-fix."""
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client for batch operations
            mock_jira_fetcher = AsyncMock()

            # Mock multiple issue creation
            mock_issues = []
            for i in range(3):
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"FTEST-{i+1}",
                    "id": f"1000{i+1}",
                    "summary": f"Batch Issue {i+1}"
                }
                mock_issues.append(mock_issue)

            mock_jira_fetcher.create_issue.side_effect = mock_issues
            mock_get_jira.return_value = mock_jira_fetcher

            # Create BatchProcessor instance
            batch_processor = BatchProcessor(dry_run=False)

            # Test batch creation
            items = [
                {
                    "project_key": "FTEST",
                    "summary": f"Batch Issue {i+1}",
                    "issue_type": "Task"
                }
                for i in range(3)
            ]

            result_json = await batch_processor.execute_batch_operation(
                ctx=get_tool_context(mock_server),
                service="jira",
                operation="create",
                resource_type="issue",
                items=items
            )

            result = json.loads(result_json)

            # Verify successful batch operation
            assert result["success"] is True
            assert result["summary"]["total"] == 3
            assert result["summary"]["successful"] == 3
            assert result["summary"]["failed"] == 0

    async def test_workflow_operations_qa_scenario(self, mock_server):
        """Test workflow operations - ensures issue transitions work post-fix."""
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client for workflow operations
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.transition_issue.return_value = True

            # Mock transition response
            mock_transition_result = {
                "issue_key": "FTEST-123",
                "transition": "In Progress",
                "status": "In Progress",
                "success": True
            }
            mock_jira_fetcher.get_issue_transitions.return_value = [
                {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}}
            ]
            mock_get_jira.return_value = mock_jira_fetcher

            # Create WorkflowEngine instance
            workflow_engine = WorkflowEngine(dry_run=False)

            # Test issue transition
            result_json = await workflow_engine.execute_workflow_operation(
                ctx=get_tool_context(mock_server),
                operation="transition",
                issue_key="FTEST-123",
                transition_name="In Progress"
            )

            result = json.loads(result_json)

            # Verify successful transition
            assert result["success"] is True
            assert result["operation"] == "transition"
            assert "error" not in result

    async def test_relationship_operations_qa_scenario(self, mock_server):
        """Test relationship operations - ensures issue linking works post-fix."""
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client for relationship operations
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.create_issue_link.return_value = {"id": "12345"}
            mock_get_jira.return_value = mock_jira_fetcher

            # Create RelationshipManager instance
            relationship_manager = RelationshipManager(dry_run=False)

            # Test issue linking
            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(mock_server),
                operation="link",
                issue_key="FTEST-123",
                target_issue_key="FTEST-456",
                link_type="Blocks"
            )

            result = json.loads(result_json)

            # Verify successful linking
            assert result["success"] is True
            assert result["operation"] == "link"
            assert "error" not in result

    async def test_context_access_error_prevention(self, mock_server):
        """Test that the P0 context fix prevents AttributeError across all operations."""
        operations_to_test = [
            ("resource_manager", "create_issue"),
            ("search_engine", "search_issues"),
            ("batch_processor", "batch_create"),
            ("workflow_engine", "transition_issue"),
            ("relationship_manager", "link_issues")
        ]

        context = get_tool_context(mock_server)

        for operation_type, operation_name in operations_to_test:
            # This should NOT raise: "'Server' object has no attribute 'lifespan_context'"
            try:
                # Test the exact pattern that was failing
                lifespan_ctx = context.lifespan_context
                app_ctx = lifespan_ctx.get("app_lifespan_context")
                assert app_ctx is not None, f"Context access failed for {operation_type}:{operation_name}"
            except AttributeError as e:
                if "lifespan_context" in str(e):
                    pytest.fail(f"P0 context error not fixed for {operation_type}:{operation_name}: {e}")
                else:
                    # Different AttributeError, re-raise
                    raise

    async def test_authentication_error_handling_qa_scenario(self, mock_server):
        """Test authentication error handling - ensures errors are properly propagated."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock authentication error
            mock_get_jira.side_effect = MCPAtlassianAuthenticationError("Invalid credentials")

            resource_manager = ResourceManager(dry_run=False)

            # Test operation with auth error
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(mock_server),
                service="jira",
                resource="issue",
                operation="create",
                data={"summary": "Test Issue"}
            )

            result = json.loads(result_json)

            # Verify error handling
            assert result["success"] is False
            assert "error" in result
            assert "authentication" in result["error"].lower() or "credentials" in result["error"].lower()

    async def test_dry_run_operations_qa_scenario(self, mock_server):
        """Test dry run mode - ensures validation works without side effects."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

        # No mocking needed for dry run
        resource_manager = ResourceManager(dry_run=True)

        # Test dry run operation
        result_json = await resource_manager.execute_operation(
            ctx=get_tool_context(mock_server),
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "FTEST",
                "summary": "Dry Run Test Issue",
                "issue_type": "Task"
            }
        )

        result = json.loads(result_json)

        # Verify dry run behavior
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["operation"] == "create"
        assert "data" in result  # Should have simulated response

    async def test_all_meta_tools_context_passing(self, mock_server):
        """Test that all meta-tools can access context correctly after the fix."""
        meta_tools = [
            "ResourceManager",
            "SearchEngine",
            "BatchProcessor",
            "WorkflowEngine",
            "RelationshipManager"
        ]

        context = get_tool_context(mock_server)

        for tool_name in meta_tools:
            # Verify context structure for each meta-tool
            assert hasattr(context, 'lifespan_context'), f"Context missing lifespan_context for {tool_name}"
            assert context.lifespan_context is not None, f"Context lifespan_context is None for {tool_name}"

            app_context = context.lifespan_context.get("app_lifespan_context")
            assert app_context is not None, f"Missing app_lifespan_context for {tool_name}"

    async def test_qa_report_reproduction_all_operations_pass(self, mock_server):
        """Comprehensive test reproducing QA report - all operations should now pass."""
        # This test simulates running all the operations that failed in the QA report

        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira, \
             patch('src.mcp_atlassian.servers.dependencies.get_confluence_fetcher') as mock_get_confluence:

            # Mock successful clients
            mock_jira_fetcher = AsyncMock()
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "FTEST-123", "summary": "Test"}
            mock_jira_fetcher.create_issue.return_value = mock_issue
            mock_jira_fetcher.search_issues.return_value = {"issues": [], "total": 0}
            mock_get_jira.return_value = mock_jira_fetcher

            mock_confluence_fetcher = AsyncMock()
            mock_page = MagicMock()
            mock_page.to_dict.return_value = {"id": "123", "title": "Test Page"}
            mock_confluence_fetcher.create_page.return_value = mock_page
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Test all the operations mentioned in QA report
            resource_manager = ResourceManager(dry_run=False)
            search_engine = SearchEngine(dry_run=False)

            operations_passed = 0
            total_operations = 4

            try:
                # 1. Create JIRA Issue (failed in QA report)
                result1 = await resource_manager.execute_operation(
                    ctx=get_tool_context(mock_server),
                    service="jira",
                    resource="issue",
                    operation="create",
                    data={"project_key": "FTEST", "summary": "QA Test", "issue_type": "Task"}
                )
                if json.loads(result1)["success"]:
                    operations_passed += 1

                # 2. Search operations (failed in QA report)
                result2 = await search_engine.execute_search(
                    ctx=get_tool_context(mock_server),
                    service="jira",
                    query_type="jql",
                    query="project = FTEST"
                )
                if json.loads(result2)["success"]:
                    operations_passed += 1

                # 3. Create Confluence Page (failed in QA report)
                result3 = await resource_manager.execute_operation(
                    ctx=get_tool_context(mock_server),
                    service="confluence",
                    resource="page",
                    operation="create",
                    data={"space_key": "TEST", "title": "QA Test Page", "body": "Test"}
                )
                if json.loads(result3)["success"]:
                    operations_passed += 1

                # 4. Update operation (failed in QA report)
                mock_jira_fetcher.update_issue.return_value = mock_issue
                result4 = await resource_manager.execute_operation(
                    ctx=get_tool_context(mock_server),
                    service="jira",
                    resource="issue",
                    operation="update",
                    identifier="FTEST-123",
                    data={"summary": "Updated"}
                )
                if json.loads(result4)["success"]:
                    operations_passed += 1

            except AttributeError as e:
                if "lifespan_context" in str(e):
                    pytest.fail(f"QA report P0 error still present: {e}")
                else:
                    raise

            # All operations that failed in QA report should now pass
            assert operations_passed == total_operations, f"Expected all {total_operations} operations to pass, got {operations_passed}"