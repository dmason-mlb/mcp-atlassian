"""Integration tests for BatchProcessor API signature validation.

This module tests the correct API signature for BatchProcessor.execute_batch_operation
to prevent the P1 issue where 'resource' parameter was used instead of 'resource_type'
and 'concurrency' was passed as a direct parameter instead of in options.
"""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

import pytest

from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
from src.mcp_atlassian.meta_tools.errors import MetaToolError

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestBatchProcessorAPISignature:
    """Test suite for BatchProcessor API signature validation."""

    @pytest.fixture
    async def mock_context(self):
        """Create a mock context with proper structure."""
        context = MagicMock()
        context.request_context = MagicMock()
        context.request_context.lifespan_context = {"app_lifespan_context": MagicMock()}
        return context

    @pytest.fixture
    async def batch_processor(self):
        """Create BatchProcessor instance."""
        return BatchProcessor(dry_run=True)

    async def test_execute_batch_operation_correct_signature(self, batch_processor, mock_context):
        """Test that execute_batch_operation accepts the correct parameters."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "TEST-123", "summary": "Test Issue"}
            mock_jira_client.create_issue.return_value = mock_issue

            # Test data
            items = [
                {
                    "summary": "Test Issue 1",
                    "issuetype": {"name": "Task"},
                    "project": {"key": "TEST"}
                }
            ]

            # This should work without raising TypeError about unexpected parameters
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",  # Correct parameter name
                items=items,
                options={"concurrency": 2},  # Correct placement for concurrency
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["operation"] == "create"
            assert result["resource_type"] == "issue"

    async def test_execute_batch_operation_rejects_wrong_resource_parameter(self, batch_processor, mock_context):
        """Test that using 'resource' instead of 'resource_type' raises TypeError."""
        items = [{"summary": "Test Issue"}]

        # This should raise TypeError because 'resource' is not a valid parameter
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource="issue",  # Wrong parameter name
                items=items,
                dry_run=True
            )

        assert "unexpected keyword argument 'resource'" in str(exc_info.value)

    async def test_execute_batch_operation_rejects_direct_concurrency_parameter(self, batch_processor, mock_context):
        """Test that passing 'concurrency' as direct parameter raises TypeError."""
        items = [{"summary": "Test Issue"}]

        # This should raise TypeError because 'concurrency' should be in options
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                concurrency=2,  # Wrong - should be in options
                dry_run=True
            )

        assert "unexpected keyword argument 'concurrency'" in str(exc_info.value)

    async def test_concurrency_in_options_dict(self, batch_processor, mock_context):
        """Test that concurrency can be passed in options dict."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "TEST-123"}
            mock_jira_client.create_issue.return_value = mock_issue

            items = [{"summary": "Test Issue"}]

            # This should work - concurrency in options
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options={"concurrency": 3, "other_option": "value"},  # Correct placement
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True

    async def test_required_parameters_validation(self, batch_processor, mock_context):
        """Test that all required parameters are validated."""
        # Missing service
        with pytest.raises(TypeError):
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                operation="create",
                resource_type="issue",
                items=[],
                dry_run=True
            )

        # Missing operation
        with pytest.raises(TypeError):
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                resource_type="issue",
                items=[],
                dry_run=True
            )

        # Missing resource_type
        with pytest.raises(TypeError):
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                items=[],
                dry_run=True
            )

        # Missing items
        with pytest.raises(TypeError):
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                dry_run=True
            )

    async def test_batch_operation_with_confluence(self, batch_processor, mock_context):
        """Test BatchProcessor with Confluence resources."""
        with patch.object(batch_processor, '_get_confluence_client') as mock_get_confluence:
            mock_confluence_client = AsyncMock()
            mock_get_confluence.return_value = mock_confluence_client

            # Mock successful page creation
            mock_page = MagicMock()
            mock_page.to_dict.return_value = {"id": "123456", "title": "Test Page"}
            mock_confluence_client.create_page.return_value = mock_page

            items = [
                {
                    "title": "Test Page",
                    "space": {"key": "TEST"},
                    "body": {"storage": {"value": "Test content", "representation": "storage"}}
                }
            ]

            # Test with Confluence - should use resource_type="page"
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="confluence",
                operation="create",
                resource_type="page",  # Correct for Confluence
                items=items,
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True
            assert result["service"] == "confluence"
            assert result["resource_type"] == "page"

    async def test_dry_run_parameter_handling(self):
        """Test that dry_run parameter is handled correctly."""
        # Should work with dry_run=True
        bp_dry = BatchProcessor(dry_run=True)
        assert bp_dry.dry_run is True

        # Should work with dry_run=False
        bp_normal = BatchProcessor(dry_run=False)
        assert bp_normal.dry_run is False

        # Should work with default (False)
        bp_default = BatchProcessor()
        assert bp_default.dry_run is False

    async def test_empty_items_list(self, batch_processor, mock_context):
        """Test handling of empty items list."""
        result_json = await batch_processor.execute_batch_operation(
            ctx=mock_context,
            service="jira",
            operation="create",
            resource_type="issue",
            items=[],  # Empty list
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["results"] == []
        assert result["summary"]["total"] == 0

    async def test_options_parameter_optional(self, batch_processor, mock_context):
        """Test that options parameter is optional."""
        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "TEST-123"}
            mock_jira_client.create_issue.return_value = mock_issue

            items = [{"summary": "Test Issue"}]

            # Should work without options parameter
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                dry_run=True
                # No options parameter
            )

            result = json.loads(result_json)
            assert result["success"] is True

            # Should also work with options=None
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                options=None,
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True

    async def test_api_signature_matches_implementation(self):
        """Test that the API signature matches what's expected in main.py."""
        import inspect
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor

        # Get the signature of execute_batch_operation
        sig = inspect.signature(BatchProcessor.execute_batch_operation)
        param_names = list(sig.parameters.keys())

        # Verify expected parameters are present
        expected_params = ['self', 'ctx', 'service', 'operation', 'resource_type', 'items']
        for param in expected_params:
            assert param in param_names, f"Missing required parameter: {param}"

        # Verify problematic parameters are NOT present
        problematic_params = ['resource', 'concurrency']
        for param in problematic_params:
            assert param not in param_names, f"Problematic parameter should not be present: {param}"

        # Verify optional parameters
        assert 'options' in param_names
        assert 'dry_run' in param_names

        # Verify default values
        assert sig.parameters['options'].default is None
        assert sig.parameters['dry_run'].default is False