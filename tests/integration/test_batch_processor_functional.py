"""Comprehensive functional integration tests for BatchProcessor.

This module tests the actual batch processing functionality end-to-end,
complementing the API signature tests. Covers scenarios from the QA report:
- Bulk operations with success/failure scenarios
- Concurrency handling and limits
- Error propagation and recovery
- Context passing validation (P0 fix)
- Performance limits and resource handling
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

import pytest

from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
from src.mcp_atlassian.meta_tools.errors import MetaToolError
from src.mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestBatchProcessorFunctional:
    """Test suite for BatchProcessor functional integration tests."""

    @pytest.fixture
    async def mock_app_context(self):
        """Create a mock MainAppContext with proper Jira/Confluence clients."""
        app_context = MagicMock()

        # Mock Jira configuration and client
        app_context.full_jira_config = MagicMock()
        app_context.full_jira_config.url = "https://test.atlassian.net"
        app_context.full_jira_config.auth_type = "oauth"

        # Mock Confluence configuration and client
        app_context.full_confluence_config = MagicMock()
        app_context.full_confluence_config.url = "https://test.atlassian.net"
        app_context.full_confluence_config.auth_type = "oauth"

        return app_context

    @pytest.fixture
    async def mock_context(self, mock_app_context):
        """Create a mock context with proper structure (P0 fix validated)."""
        context = MagicMock()
        # After P0 fix: use lifespan_context directly
        context.lifespan_context = {"app_lifespan_context": mock_app_context}
        return context

    @pytest.fixture
    async def batch_processor(self):
        """Create BatchProcessor instance."""
        return BatchProcessor(dry_run=False)

    async def test_batch_create_jira_issues_success(self, batch_processor, mock_context):
        """Test successful batch creation of Jira issues."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issues = []
            for i in range(3):
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"TEST-{i+1}",
                    "summary": f"Test Issue {i+1}",
                    "id": f"1000{i+1}"
                }
                mock_issues.append(mock_issue)

            mock_jira_client.create_issue.side_effect = mock_issues

            # Test data
            items = [
                {
                    "summary": "Test Issue 1",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                },
                {
                    "summary": "Test Issue 2",
                    "issuetype": {"name": "Bug"},
                    "project": {"key": "TEST"}
                },
                {
                    "summary": "Test Issue 3",
                    "issuetype": {"name": "Story"},
                    "project": {"key": "TEST"}
                }
            ]

            # Execute batch operation
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options={"concurrency": 2},
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify successful batch operation
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["operation"] == "create"
            assert result["resource_type"] == "issue"
            assert len(result["results"]) == 3
            assert result["summary"]["total"] == 3
            assert result["summary"]["successful"] == 3
            assert result["summary"]["failed"] == 0

            # Verify each result
            for i, item_result in enumerate(result["results"]):
                assert item_result["success"] is True
                assert item_result["data"]["key"] == f"TEST-{i+1}"
                assert "error" not in item_result

            # Verify all create_issue calls were made
            assert mock_jira_client.create_issue.call_count == 3

    async def test_batch_create_confluence_pages_success(self, batch_processor, mock_context):
        """Test successful batch creation of Confluence pages."""
        with patch.object(batch_processor, '_get_confluence_client') as mock_get_confluence:
            mock_confluence_client = AsyncMock()
            mock_get_confluence.return_value = mock_confluence_client

            # Mock successful page creation
            mock_pages = []
            for i in range(2):
                mock_page = MagicMock()
                mock_page.to_dict.return_value = {
                    "id": f"12345{i+1}",
                    "title": f"Test Page {i+1}",
                    "space": {"key": "TEST"}
                }
                mock_pages.append(mock_page)

            mock_confluence_client.create_page.side_effect = mock_pages

            # Test data
            items = [
                {
                    "title": "Test Page 1",
                    "space": {"key": "TEST"},
                    "body": {"storage": {"value": "Content 1", "representation": "storage"}}
                },
                {
                    "title": "Test Page 2",
                    "space": {"key": "TEST"},
                    "body": {"storage": {"value": "Content 2", "representation": "storage"}}
                }
            ]

            # Execute batch operation
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="confluence",
                operation="create",
                resource_type="page",
                items=items,
                options={"concurrency": 1},
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify successful batch operation
            assert result["success"] is True
            assert result["service"] == "confluence"
            assert result["resource_type"] == "page"
            assert len(result["results"]) == 2
            assert result["summary"]["successful"] == 2
            assert result["summary"]["failed"] == 0

    async def test_batch_operation_partial_failures(self, batch_processor, mock_context):
        """Test batch operation with partial failures."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock mixed success and failure
            def create_issue_side_effect(issue_data):
                if "fail" in issue_data.get("summary", ""):
                    raise ValueError("Invalid issue data")
                else:
                    mock_issue = MagicMock()
                    mock_issue.to_simplified_dict.return_value = {
                        "key": "TEST-SUCCESS",
                        "summary": issue_data["summary"]
                    }
                    return mock_issue

            mock_jira_client.create_issue.side_effect = create_issue_side_effect

            # Test data with one failing item
            items = [
                {
                    "summary": "Success Issue 1",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                },
                {
                    "summary": "This will fail",
                    "issuetype": {"name": "Bug"},
                    "project": {"key": "TEST"}
                },
                {
                    "summary": "Success Issue 2",
                    "issuetype": {"name": "Story"},
                    "project": {"key": "TEST"}
                }
            ]

            # Execute batch operation
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify mixed results
            assert result["success"] is True  # Batch operation itself succeeded
            assert result["summary"]["total"] == 3
            assert result["summary"]["successful"] == 2
            assert result["summary"]["failed"] == 1

            # Verify individual results
            successful_count = sum(1 for r in result["results"] if r["success"])
            failed_count = sum(1 for r in result["results"] if not r["success"])
            assert successful_count == 2
            assert failed_count == 1

            # Find and verify the failed result
            failed_results = [r for r in result["results"] if not r["success"]]
            assert len(failed_results) == 1
            assert "error" in failed_results[0]
            assert "Invalid issue data" in failed_results[0]["error"]

    async def test_batch_operation_concurrency_limits(self, batch_processor, mock_context):
        """Test that concurrency limits are respected."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Track concurrent calls
            active_calls = []
            max_concurrent = 0

            async def track_create_issue(issue_data):
                nonlocal max_concurrent
                active_calls.append(1)
                max_concurrent = max(max_concurrent, len(active_calls))

                # Simulate async work
                await asyncio.sleep(0.01)

                active_calls.pop()
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"TEST-{len(active_calls)}",
                    "summary": issue_data["summary"]
                }
                return mock_issue

            mock_jira_client.create_issue.side_effect = track_create_issue

            # Test data with many items
            items = [
                {
                    "summary": f"Test Issue {i}",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                }
                for i in range(5)
            ]

            # Execute with concurrency limit of 2
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options={"concurrency": 2},
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify concurrency was respected
            assert max_concurrent <= 2
            assert result["summary"]["successful"] == 5

    async def test_batch_operation_dry_run_mode(self, batch_processor, mock_context):
        """Test batch operation in dry run mode."""
        # No mocking needed - dry run shouldn't make actual API calls
        items = [
            {
                "summary": "Test Issue 1",
                "issuetype": {"name": "Task"},
                "project": {"key": "TEST"}
            }
        ]

        # Execute in dry run mode
        result_json = await batch_processor.execute_batch_operation(
            ctx=mock_context,
            service="jira",
            operation="create",
            resource_type="issue",
            items=items,
            dry_run=True
        )

        result = json.loads(result_json)

        # Verify dry run behavior
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["summary"]["total"] == 1
        assert len(result["results"]) == 1

        # In dry run, should return simulated success
        assert result["results"][0]["success"] is True
        assert "dry_run" in result["results"][0]

    async def test_batch_operation_authentication_error(self, batch_processor, mock_context):
        """Test batch operation with authentication error."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            # Mock authentication error
            mock_get_jira.side_effect = MCPAtlassianAuthenticationError("Invalid credentials")

            items = [{"summary": "Test Issue"}]

            # Execute batch operation
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify error handling
            assert result["success"] is False
            assert "error" in result
            assert "authentication" in result["error"].lower() or "credentials" in result["error"].lower()

    async def test_batch_operation_empty_items_list(self, batch_processor, mock_context):
        """Test batch operation with empty items list."""
        result_json = await batch_processor.execute_batch_operation(
            ctx=mock_context,
            service="jira",
            operation="create",
            resource_type="issue",
            items=[],
            dry_run=False
        )

        result = json.loads(result_json)

        # Verify empty list handling
        assert result["success"] is True
        assert result["summary"]["total"] == 0
        assert result["summary"]["successful"] == 0
        assert result["summary"]["failed"] == 0
        assert result["results"] == []

    async def test_batch_operation_invalid_service(self, batch_processor, mock_context):
        """Test batch operation with invalid service."""
        items = [{"summary": "Test Issue"}]

        with pytest.raises(ValueError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="invalid_service",  # Invalid service
                operation="create",
                resource_type="issue",
                items=items,
                dry_run=False
            )

        assert "invalid_service" in str(exc_info.value).lower()

    async def test_batch_operation_invalid_operation(self, batch_processor, mock_context):
        """Test batch operation with invalid operation."""
        items = [{"summary": "Test Issue"}]

        with pytest.raises(ValueError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="invalid_operation",  # Invalid operation
                resource_type="issue",
                items=items,
                dry_run=False
            )

        assert "invalid_operation" in str(exc_info.value).lower()

    async def test_batch_operation_context_passing_p0_fix(self, batch_processor, mock_context):
        """Test that batch processor properly handles context after P0 fix."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_jira_client.create_issue.return_value = MagicMock()
            mock_get_jira.return_value = mock_jira_client

            items = [{"summary": "Test Issue"}]

            # This should work without AttributeError after P0 fix
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                dry_run=False
            )

            # Verify successful execution (no context access errors)
            result = json.loads(result_json)
            assert result["success"] is True

            # Verify context was accessed correctly
            mock_get_jira.assert_called_once_with(mock_context)

    async def test_batch_operation_large_item_count(self, batch_processor, mock_context):
        """Test batch operation with large number of items."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful creation
            def create_issue_mock(issue_data):
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"TEST-{hash(issue_data['summary']) % 10000}",
                    "summary": issue_data["summary"]
                }
                return mock_issue

            mock_jira_client.create_issue.side_effect = create_issue_mock

            # Generate 20 items
            items = [
                {
                    "summary": f"Test Issue {i}",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                }
                for i in range(20)
            ]

            # Execute batch operation
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options={"concurrency": 5},
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify all items were processed
            assert result["success"] is True
            assert result["summary"]["total"] == 20
            assert result["summary"]["successful"] == 20
            assert len(result["results"]) == 20

    async def test_batch_operation_options_validation(self, batch_processor, mock_context):
        """Test that options are properly validated and applied."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_jira_client.create_issue.return_value = MagicMock()
            mock_get_jira.return_value = mock_jira_client

            items = [{"summary": "Test Issue"}]

            # Test with various options
            test_options = {
                "concurrency": 3,
                "timeout": 30,
                "custom_option": "value"
            }

            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options=test_options,
                dry_run=False
            )

            result = json.loads(result_json)

            # Verify options were processed
            assert result["success"] is True
            # Options should be preserved in the result metadata
            if "options" in result:
                assert result["options"]["concurrency"] == 3