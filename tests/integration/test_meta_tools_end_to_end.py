"""End-to-end integration tests for all meta-tools working together.

This module tests realistic workflows that use multiple meta-tools in sequence,
validating that the entire system works correctly after the P0/P1 fixes.
Tests real-world scenarios like:
- Complete issue lifecycle (create -> search -> update -> link -> transition)
- Complete page lifecycle (create -> search -> update -> attach)
- Batch operations combined with individual operations
- Cross-service operations and error handling
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

import pytest

from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.search_engine import SearchEngine
from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler
from src.mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestMetaToolsEndToEnd:
    """Test suite for end-to-end meta-tools integration."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a comprehensive mock MainAppContext."""
        app_context = MagicMock()

        # Mock Jira configuration
        app_context.full_jira_config = MagicMock()
        app_context.full_jira_config.url = "https://test.atlassian.net"
        app_context.full_jira_config.auth_type = "oauth"
        app_context.full_jira_config.is_auth_configured.return_value = True

        # Mock Confluence configuration
        app_context.full_confluence_config = MagicMock()
        app_context.full_confluence_config.url = "https://test.atlassian.net"
        app_context.full_confluence_config.auth_type = "oauth"
        app_context.full_confluence_config.is_auth_configured.return_value = True

        return app_context

    @pytest.fixture
    async def mock_context(self, mock_app_context):
        """Create a mock context with proper structure (P0 fix validated)."""
        context = MagicMock()
        # After P0 fix: use lifespan_context directly
        context.lifespan_context = {"app_lifespan_context": mock_app_context}
        return context

    @pytest.fixture
    async def all_meta_tools(self):
        """Create instances of all meta-tools."""
        return {
            "resource_manager": ResourceManager(dry_run=False),
            "search_engine": SearchEngine(dry_run=False),
            "batch_processor": BatchProcessor(dry_run=False),
            "workflow_engine": WorkflowEngine(dry_run=False),
            "relationship_manager": RelationshipManager(dry_run=False),
            "attachment_handler": AttachmentHandler(dry_run=False)
        }

    async def test_complete_jira_issue_lifecycle(self, all_meta_tools, mock_context):
        """Test complete Jira issue lifecycle using multiple meta-tools."""
        resource_manager = all_meta_tools["resource_manager"]
        search_engine = all_meta_tools["search_engine"]
        workflow_engine = all_meta_tools["workflow_engine"]
        relationship_manager = all_meta_tools["relationship_manager"]

        with patch.object(resource_manager, '_get_jira_client') as mock_get_jira, \
             patch.object(search_engine, '_get_jira_client') as mock_search_jira, \
             patch.object(workflow_engine, '_get_jira_client') as mock_workflow_jira, \
             patch.object(relationship_manager, '_get_jira_client') as mock_rel_jira:

            # Mock Jira client for all tools
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client
            mock_search_jira.return_value = mock_jira_client
            mock_workflow_jira.return_value = mock_jira_client
            mock_rel_jira.return_value = mock_jira_client

            # Step 1: Create an issue
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {
                "key": "TEST-123",
                "id": "10001",
                "summary": "Test Issue",
                "status": {"name": "To Do"}
            }
            mock_jira_client.create_issue.return_value = mock_issue

            create_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "summary": "Test Issue",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                }
            )
            create_result = json.loads(create_result_json)
            assert create_result["success"] is True
            issue_key = create_result["data"]["key"]

            # Step 2: Search for the created issue
            mock_search_result = MagicMock()
            mock_search_result.json.return_value = {
                "issues": [{"key": "TEST-123", "fields": {"summary": "Test Issue"}}],
                "total": 1
            }
            mock_jira_client.jql_search.return_value = mock_search_result

            search_result_json = await search_engine.execute_search(
                ctx=mock_context,
                service="jira",
                query_type="jql",
                query=f"key = {issue_key}"
            )
            search_result = json.loads(search_result_json)
            assert search_result["success"] is True
            assert len(search_result["results"]) == 1

            # Step 3: Update the issue
            mock_jira_client.update_issue.return_value = None
            mock_updated_issue = MagicMock()
            mock_updated_issue.to_simplified_dict.return_value = {
                "key": "TEST-123",
                "summary": "Updated Test Issue",
                "status": {"name": "To Do"}
            }
            mock_jira_client.get_issue.return_value = mock_updated_issue

            update_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="update",
                identifier=issue_key,
                data={"summary": "Updated Test Issue"}
            )
            update_result = json.loads(update_result_json)
            assert update_result["success"] is True

            # Step 4: Create a second issue to link to
            mock_issue2 = MagicMock()
            mock_issue2.to_simplified_dict.return_value = {
                "key": "TEST-124",
                "id": "10002",
                "summary": "Linked Issue"
            }
            mock_jira_client.create_issue.return_value = mock_issue2

            create2_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "summary": "Linked Issue",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                }
            )
            create2_result = json.loads(create2_result_json)
            linked_issue_key = create2_result["data"]["key"]

            # Step 5: Link the issues
            mock_jira_client.create_issue_link.return_value = {"id": "link123"}

            link_result_json = await relationship_manager.execute_relationship_operation(
                ctx=mock_context,
                operation="link",
                issue_key=issue_key,
                target_issue_key=linked_issue_key,
                link_type="Blocks"
            )
            link_result = json.loads(link_result_json)
            assert link_result["success"] is True

            # Step 6: Transition the issue workflow
            mock_transitions = [{"id": "21", "name": "In Progress"}]
            mock_jira_client.get_available_transitions.return_value = mock_transitions
            mock_jira_client.transition_issue.return_value = None

            transition_result_json = await workflow_engine.execute_workflow_operation(
                ctx=mock_context,
                operation="transition",
                issue_key=issue_key,
                transition_name="In Progress"
            )
            transition_result = json.loads(transition_result_json)
            assert transition_result["success"] is True

            # Verify all operations were called
            assert mock_jira_client.create_issue.call_count == 2
            assert mock_jira_client.update_issue.call_count == 1
            assert mock_jira_client.jql_search.call_count == 1
            assert mock_jira_client.create_issue_link.call_count == 1
            assert mock_jira_client.transition_issue.call_count == 1

    async def test_complete_confluence_page_lifecycle(self, all_meta_tools, mock_context):
        """Test complete Confluence page lifecycle using multiple meta-tools."""
        resource_manager = all_meta_tools["resource_manager"]
        search_engine = all_meta_tools["search_engine"]
        attachment_handler = all_meta_tools["attachment_handler"]

        with patch.object(resource_manager, '_get_confluence_client') as mock_get_confluence, \
             patch.object(search_engine, '_get_confluence_client') as mock_search_confluence, \
             patch.object(attachment_handler, '_get_confluence_client') as mock_attach_confluence:

            # Mock Confluence client for all tools
            mock_confluence_client = AsyncMock()
            mock_get_confluence.return_value = mock_confluence_client
            mock_search_confluence.return_value = mock_confluence_client
            mock_attach_confluence.return_value = mock_confluence_client

            # Step 1: Create a page
            mock_page = MagicMock()
            mock_page.to_dict.return_value = {
                "id": "123456",
                "title": "Test Page",
                "space": {"key": "TEST"},
                "_links": {"base": "https://test.atlassian.net"}
            }
            mock_confluence_client.create_page.return_value = mock_page

            create_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="create",
                data={
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "body": {"storage": {"value": "Test content", "representation": "storage"}}
                }
            )
            create_result = json.loads(create_result_json)
            assert create_result["success"] is True
            page_id = create_result["data"]["id"]

            # Step 2: Search for the created page
            mock_search_response = MagicMock()
            mock_search_response.json.return_value = {
                "results": [{"id": "123456", "title": "Test Page"}],
                "size": 1
            }
            mock_confluence_client.cql_search.return_value = mock_search_response

            search_result_json = await search_engine.execute_search(
                ctx=mock_context,
                service="confluence",
                query_type="cql",
                query=f"id = {page_id}"
            )
            search_result = json.loads(search_result_json)
            assert search_result["success"] is True
            assert len(search_result["results"]) == 1

            # Step 3: Update the page
            mock_confluence_client.update_page.return_value = None
            mock_updated_page = MagicMock()
            mock_updated_page.to_dict.return_value = {
                "id": "123456",
                "title": "Updated Test Page",
                "space": {"key": "TEST"}
            }
            mock_confluence_client.get_page_by_id.return_value = mock_updated_page

            update_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="update",
                identifier=page_id,
                data={"title": "Updated Test Page"}
            )
            update_result = json.loads(update_result_json)
            assert update_result["success"] is True

            # Step 4: Add an attachment to the page
            mock_attachment = {"id": "att123", "title": "test.txt"}
            mock_confluence_client.attach_file.return_value = mock_attachment

            # Mock file reading
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"test content"

                attach_result_json = await attachment_handler.execute_attachment_operation(
                    ctx=mock_context,
                    service="confluence",
                    operation="upload",
                    page_id=page_id,
                    file_path="/fake/test.txt"
                )
                attach_result = json.loads(attach_result_json)
                assert attach_result["success"] is True

            # Verify all operations were called
            assert mock_confluence_client.create_page.call_count == 1
            assert mock_confluence_client.update_page.call_count == 1
            assert mock_confluence_client.cql_search.call_count == 1
            assert mock_confluence_client.attach_file.call_count == 1

    async def test_batch_operations_with_individual_operations(self, all_meta_tools, mock_context):
        """Test combining batch operations with individual operations."""
        batch_processor = all_meta_tools["batch_processor"]
        resource_manager = all_meta_tools["resource_manager"]
        search_engine = all_meta_tools["search_engine"]

        with patch.object(batch_processor, '_get_jira_client') as mock_batch_jira, \
             patch.object(resource_manager, '_get_jira_client') as mock_rm_jira, \
             patch.object(search_engine, '_get_jira_client') as mock_search_jira:

            mock_jira_client = AsyncMock()
            mock_batch_jira.return_value = mock_jira_client
            mock_rm_jira.return_value = mock_jira_client
            mock_search_jira.return_value = mock_jira_client

            # Step 1: Batch create multiple issues
            mock_issues = []
            for i in range(3):
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"TEST-{i+1}",
                    "summary": f"Batch Issue {i+1}"
                }
                mock_issues.append(mock_issue)
            mock_jira_client.create_issue.side_effect = mock_issues

            batch_items = [
                {"summary": f"Batch Issue {i+1}", "issuetype": {"name": "Task"}, "project": {"key": "TEST"}}
                for i in range(3)
            ]

            batch_result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=batch_items
            )
            batch_result = json.loads(batch_result_json)
            assert batch_result["success"] is True
            assert batch_result["summary"]["successful"] == 3

            # Step 2: Search for the batch-created issues
            mock_search_result = MagicMock()
            mock_search_result.json.return_value = {
                "issues": [
                    {"key": "TEST-1", "fields": {"summary": "Batch Issue 1"}},
                    {"key": "TEST-2", "fields": {"summary": "Batch Issue 2"}},
                    {"key": "TEST-3", "fields": {"summary": "Batch Issue 3"}}
                ],
                "total": 3
            }
            mock_jira_client.jql_search.return_value = mock_search_result

            search_result_json = await search_engine.execute_search(
                ctx=mock_context,
                service="jira",
                query_type="jql",
                query="project = TEST AND summary ~ 'Batch Issue'"
            )
            search_result = json.loads(search_result_json)
            assert search_result["success"] is True
            assert len(search_result["results"]) == 3

            # Step 3: Individually update one of the batch-created issues
            mock_jira_client.update_issue.return_value = None
            mock_updated_issue = MagicMock()
            mock_updated_issue.to_simplified_dict.return_value = {
                "key": "TEST-1",
                "summary": "Updated Batch Issue 1"
            }
            mock_jira_client.get_issue.return_value = mock_updated_issue

            update_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="update",
                identifier="TEST-1",
                data={"summary": "Updated Batch Issue 1"}
            )
            update_result = json.loads(update_result_json)
            assert update_result["success"] is True

            # Verify call counts
            assert mock_jira_client.create_issue.call_count == 3  # Batch operations
            assert mock_jira_client.jql_search.call_count == 1   # Search operation
            assert mock_jira_client.update_issue.call_count == 1 # Individual update

    async def test_cross_service_error_handling(self, all_meta_tools, mock_context):
        """Test error handling across multiple services and tools."""
        resource_manager = all_meta_tools["resource_manager"]
        search_engine = all_meta_tools["search_engine"]

        # Test Jira authentication error
        with patch.object(resource_manager, '_get_jira_client') as mock_get_jira:
            mock_get_jira.side_effect = MCPAtlassianAuthenticationError("Jira auth failed")

            jira_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123"
            )
            jira_result = json.loads(jira_result_json)
            assert jira_result["success"] is False
            assert "authentication" in jira_result["error"].lower()

        # Test Confluence connectivity error
        with patch.object(search_engine, '_get_confluence_client') as mock_get_confluence:
            mock_confluence_client = AsyncMock()
            mock_confluence_client.cql_search.side_effect = ConnectionError("Connection failed")
            mock_get_confluence.return_value = mock_confluence_client

            confluence_result_json = await search_engine.execute_search(
                ctx=mock_context,
                service="confluence",
                query_type="cql",
                query="space = TEST"
            )
            confluence_result = json.loads(confluence_result_json)
            assert confluence_result["success"] is False
            assert "connection" in confluence_result["error"].lower() or "failed" in confluence_result["error"].lower()

    async def test_all_meta_tools_context_passing_p0_fix(self, all_meta_tools, mock_context):
        """Test that all meta-tools properly handle context after P0 fix."""
        # This test ensures no AttributeError about request_context occurs
        for tool_name, tool in all_meta_tools.items():
            if tool_name == "resource_manager":
                with patch.object(tool, '_get_jira_client') as mock_get_client:
                    mock_client = AsyncMock()
                    mock_client.get_issue.return_value = MagicMock()
                    mock_get_client.return_value = mock_client

                    # This should not raise AttributeError after P0 fix
                    result_json = await tool.execute_operation(
                        ctx=mock_context,
                        service="jira",
                        resource="issue",
                        operation="get",
                        identifier="TEST-123"
                    )
                    result = json.loads(result_json)
                    # Verify it worked (no context errors)
                    mock_get_client.assert_called_once_with(mock_context)

            elif tool_name == "search_engine":
                with patch.object(tool, '_get_jira_client') as mock_get_client:
                    mock_client = AsyncMock()
                    mock_response = MagicMock()
                    mock_response.json.return_value = {"issues": [], "total": 0}
                    mock_client.jql_search.return_value = mock_response
                    mock_get_client.return_value = mock_client

                    result_json = await tool.execute_search(
                        ctx=mock_context,
                        service="jira",
                        query_type="jql",
                        query="project = TEST"
                    )
                    result = json.loads(result_json)
                    mock_get_client.assert_called_once_with(mock_context)

    async def test_realistic_workflow_scenario(self, all_meta_tools, mock_context):
        """Test a realistic end-to-end workflow scenario."""
        resource_manager = all_meta_tools["resource_manager"]
        batch_processor = all_meta_tools["batch_processor"]
        workflow_engine = all_meta_tools["workflow_engine"]
        relationship_manager = all_meta_tools["relationship_manager"]

        # Scenario: Create epic, batch create stories, link stories to epic, transition epic

        with patch.object(resource_manager, '_get_jira_client') as mock_rm_jira, \
             patch.object(batch_processor, '_get_jira_client') as mock_batch_jira, \
             patch.object(workflow_engine, '_get_jira_client') as mock_wf_jira, \
             patch.object(relationship_manager, '_get_jira_client') as mock_rel_jira:

            mock_jira_client = AsyncMock()
            mock_rm_jira.return_value = mock_jira_client
            mock_batch_jira.return_value = mock_jira_client
            mock_wf_jira.return_value = mock_jira_client
            mock_rel_jira.return_value = mock_jira_client

            # Step 1: Create epic
            mock_epic = MagicMock()
            mock_epic.to_simplified_dict.return_value = {
                "key": "TEST-100",
                "summary": "Test Epic",
                "issuetype": {"name": "Epic"}
            }
            mock_jira_client.create_issue.return_value = mock_epic

            epic_result_json = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "summary": "Test Epic",
                    "issuetype": {"name": "Epic"},
                    "project": {"key": "TEST"}
                }
            )
            epic_result = json.loads(epic_result_json)
            epic_key = epic_result["data"]["key"]

            # Step 2: Batch create stories
            story_items = [
                {"summary": f"Story {i}", "issuetype": {"name": "Story"}, "project": {"key": "TEST"}}
                for i in range(1, 4)
            ]

            mock_stories = []
            for i in range(1, 4):
                mock_story = MagicMock()
                mock_story.to_simplified_dict.return_value = {
                    "key": f"TEST-{100+i}",
                    "summary": f"Story {i}",
                    "issuetype": {"name": "Story"}
                }
                mock_stories.append(mock_story)
            mock_jira_client.create_issue.side_effect = mock_stories

            batch_result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=story_items
            )
            batch_result = json.loads(batch_result_json)
            assert batch_result["summary"]["successful"] == 3

            # Step 3: Link stories to epic
            mock_jira_client.create_issue_link.return_value = {"id": "link123"}

            for i in range(1, 4):
                story_key = f"TEST-{100+i}"
                link_result_json = await relationship_manager.execute_relationship_operation(
                    ctx=mock_context,
                    operation="add_to_epic",
                    issue_key=story_key,
                    epic_key=epic_key
                )
                link_result = json.loads(link_result_json)
                assert link_result["success"] is True

            # Step 4: Transition epic
            mock_transitions = [{"id": "31", "name": "In Progress"}]
            mock_jira_client.get_available_transitions.return_value = mock_transitions
            mock_jira_client.transition_issue.return_value = None

            transition_result_json = await workflow_engine.execute_workflow_operation(
                ctx=mock_context,
                operation="transition",
                issue_key=epic_key,
                transition_name="In Progress"
            )
            transition_result = json.loads(transition_result_json)
            assert transition_result["success"] is True

            # Verify complete workflow
            assert mock_jira_client.create_issue.call_count == 4  # 1 epic + 3 stories
            assert mock_jira_client.create_issue_link.call_count == 3  # 3 story-epic links
            assert mock_jira_client.transition_issue.call_count == 1  # 1 epic transition