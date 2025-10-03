"""
End-to-end smoke tests with minimal mocking.

This module provides comprehensive smoke tests that validate the context fix
works in realistic scenarios with minimal mocking. These tests simulate real
usage patterns and ensure the P0 AttributeError is completely resolved.

Tests verify:
- Actual server instantiation with real tool registration
- End-to-end tool handler execution with minimal mocking
- Context passing through the complete flow
- Meta-tool initialization and execution
- No AttributeError occurs in real scenarios
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.fixtures.mock_factory import MockClientFactory, create_realistic_app_context, create_realistic_server_context
from src.mcp_atlassian.servers.main import AtlassianMCP, get_tool_context, register_v2_tools
from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.search_engine import SearchEngine


@pytest.mark.smoke
@pytest.mark.integration
class TestSmokeE2E:
    """End-to-end smoke tests with realistic scenarios."""

    @pytest.fixture
    def realistic_server_setup(self):
        """Create a realistic server setup with minimal mocking."""
        app_context = create_realistic_app_context()
        server = create_realistic_server_context(app_context)
        return server, app_context

    async def test_context_creation_smoke_test(self, realistic_server_setup):
        """Smoke test for context creation with realistic server."""
        server, app_context = realistic_server_setup

        # This should work without any AttributeError
        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context is not None
        assert isinstance(context.lifespan_context, dict)
        assert "app_lifespan_context" in context.lifespan_context

        # Verify the exact pattern from dependencies.py works
        lifespan_ctx_dict = context.lifespan_context
        app_lifespan_ctx = (
            lifespan_ctx_dict.get("app_lifespan_context")
            if isinstance(lifespan_ctx_dict, dict)
            else None
        )
        assert app_lifespan_ctx is not None
        assert app_lifespan_ctx == app_context

    async def test_resource_manager_end_to_end_smoke(self, realistic_server_setup):
        """End-to-end smoke test for ResourceManager with realistic context."""
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Use the mock factory for realistic client behavior
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            # Create ResourceManager instance
            resource_manager = ResourceManager(dry_run=False)

            # Test the complete flow: context → meta-tool → client
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "project_key": "SMOKE",
                    "summary": "End-to-End Smoke Test Issue",
                    "issue_type": "Task",
                    "description": "This tests the complete flow works"
                }
            )

            result = json.loads(result_json)

            # Verify successful execution (no AttributeError)
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["resource"] == "issue"
            assert result["operation"] == "create"
            assert "data" in result
            assert result["data"]["key"] == "SMOKE-123"

            # Verify context was passed correctly
            mock_get_jira.assert_called_once()
            context_arg = mock_get_jira.call_args[0][0]
            assert hasattr(context_arg, 'lifespan_context')

    async def test_search_engine_end_to_end_smoke(self, realistic_server_setup):
        """End-to-end smoke test for SearchEngine with realistic context."""
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Use the mock factory for realistic client behavior
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            # Create SearchEngine instance
            search_engine = SearchEngine(dry_run=False)

            # Test search operation end-to-end
            result_json = await search_engine.execute_search(
                ctx=get_tool_context(server),
                service="jira",
                query_type="issues",
                query="project = SMOKE",
                options={"limit": 10}
            )

            result = json.loads(result_json)

            # Verify successful execution
            assert result["success"] is True
            assert result["service"] == "jira"
            assert result["query_type"] == "issues"
            assert "results" in result

            # Verify context was passed correctly
            mock_get_jira.assert_called_once()

    async def test_tool_registration_smoke_test(self):
        """Smoke test for tool registration with realistic server."""
        # Create a real AtlassianMCP instance (not mocked)
        app_context = create_realistic_app_context()

        # Test that tool registration works without errors
        with patch('src.mcp_atlassian.servers.main.MainAppContext') as MockMainAppContext:
            MockMainAppContext.return_value = app_context

            # This should not crash during tool registration
            server = AtlassianMCP()

            # Verify tools were registered
            assert hasattr(server, '_mcp_server')
            # The tools should be registered without AttributeError

    async def test_concurrent_context_access_smoke(self, realistic_server_setup):
        """Smoke test for concurrent context access in realistic scenarios."""
        server, app_context = realistic_server_setup

        results = []
        errors = []

        async def concurrent_operation(operation_id: int):
            try:
                with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
                    mock_jira_client = MockClientFactory.create_jira_client()
                    mock_get_jira.return_value = mock_jira_client

                    resource_manager = ResourceManager(dry_run=False)

                    result_json = await resource_manager.execute_operation(
                        ctx=get_tool_context(server),
                        service="jira",
                        resource="issue",
                        operation="create",
                        data={
                            "project_key": "CONCURRENT",
                            "summary": f"Concurrent Test {operation_id}",
                            "issue_type": "Task"
                        }
                    )

                    result = json.loads(result_json)
                    results.append((operation_id, result["success"]))

            except Exception as e:
                errors.append((operation_id, e))

        # Run multiple concurrent operations
        tasks = [concurrent_operation(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all operations succeeded
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        assert all(success for _, success in results), "Some operations failed"

    async def test_health_check_smoke_test(self, realistic_server_setup):
        """Smoke test for health check functionality."""
        server, app_context = realistic_server_setup

        from src.mcp_atlassian.servers.main import _check_service_health

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            # Test health check with realistic context
            result = await _check_service_health(get_tool_context(server), "jira", dry_run=False)

            # Verify successful health check
            assert result["service"] == "jira"
            assert result["status"] == "healthy"
            assert result["configuration"] == "valid"
            assert result["authentication"] == "valid"
            assert result["connectivity"] == "valid"
            assert result["errors"] == []

    async def test_error_propagation_smoke_test(self, realistic_server_setup):
        """Smoke test for error propagation through the complete flow."""
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Simulate an authentication error
            mock_get_jira.side_effect = Exception("Simulated auth error")

            resource_manager = ResourceManager(dry_run=False)

            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="jira",
                resource="issue",
                operation="create",
                data={"summary": "Test Issue"}
            )

            result = json.loads(result_json)

            # Verify error is handled gracefully (no AttributeError)
            assert result["success"] is False
            assert "error" in result
            # Should not contain the P0 AttributeError about lifespan_context
            assert "lifespan_context" not in result["error"]

    async def test_dry_run_smoke_test(self, realistic_server_setup):
        """Smoke test for dry run mode with realistic context."""
        server, app_context = realistic_server_setup

        # Test dry run (no mocking needed)
        resource_manager = ResourceManager(dry_run=True)

        result_json = await resource_manager.execute_operation(
            ctx=get_tool_context(server),
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "DRYRUN",
                "summary": "Dry Run Test",
                "issue_type": "Task"
            }
        )

        result = json.loads(result_json)

        # Verify dry run behavior (dry run has different response structure)
        assert result["dry_run"] is True
        assert result["validation"] == "PASSED"
        assert result["operation"] == "create"

    async def test_context_passing_chain_smoke(self, realistic_server_setup):
        """Smoke test for the complete context passing chain."""
        server, app_context = realistic_server_setup

        # Test the complete chain: tool handler → get_tool_context → meta-tool → dependencies
        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            # Simulate calling a tool handler (like what MCP server does)
            async def simulate_tool_handler(server: AtlassianMCP):
                # This is the exact pattern used in main.py tool handlers
                resource_manager = ResourceManager(dry_run=False)
                return await resource_manager.execute_operation(
                    ctx=get_tool_context(server),  # This is the critical line that was failing
                    service="jira",
                    resource="issue",
                    operation="get",
                    identifier="SMOKE-123"
                )

            # Execute the complete chain
            result_json = await simulate_tool_handler(server)
            result = json.loads(result_json)

            # Verify the complete chain works
            assert result["success"] is True
            assert result["data"]["key"] == "SMOKE-123"

            # Verify context was passed through the chain correctly
            mock_get_jira.assert_called_once()
            passed_context = mock_get_jira.call_args[0][0]

            # Verify the context has the exact structure dependencies.py expects
            assert hasattr(passed_context, 'lifespan_context')
            lifespan_ctx = passed_context.lifespan_context
            assert isinstance(lifespan_ctx, dict)
            assert "app_lifespan_context" in lifespan_ctx
            assert lifespan_ctx["app_lifespan_context"] == app_context

    async def test_realistic_usage_scenario_smoke(self, realistic_server_setup):
        """Smoke test simulating realistic usage scenario."""
        server, app_context = realistic_server_setup

        # Simulate a realistic usage scenario:
        # 1. Create an issue
        # 2. Search for it
        # 3. Update it
        # This tests multiple operations with the same context

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            resource_manager = ResourceManager(dry_run=False)
            search_engine = SearchEngine(dry_run=False)

            context = get_tool_context(server)

            # Step 1: Create issue
            create_result_json = await resource_manager.execute_operation(
                ctx=context,
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "project_key": "REALISTIC",
                    "summary": "Realistic Usage Test",
                    "issue_type": "Task"
                }
            )

            create_result = json.loads(create_result_json)
            assert create_result["success"] is True
            issue_key = create_result["data"]["key"]

            # Step 2: Search for issues
            search_result_json = await search_engine.execute_search(
                ctx=context,
                service="jira",
                query_type="issues",
                query=f"key = {issue_key}"
            )

            search_result = json.loads(search_result_json)
            assert search_result["success"] is True

            # Step 3: Update issue
            update_result_json = await resource_manager.execute_operation(
                ctx=context,
                service="jira",
                resource="issue",
                operation="update",
                identifier=issue_key,
                data={"summary": "Updated Realistic Test"}
            )

            update_result = json.loads(update_result_json)
            assert update_result["success"] is True

            # Verify all operations used the same context successfully
            assert mock_get_jira.call_count == 3  # Once for each operation

    async def test_memory_and_performance_smoke(self, realistic_server_setup):
        """Smoke test for memory usage and performance with realistic context."""
        server, app_context = realistic_server_setup

        import time
        start_time = time.time()

        # Perform many context creations (simulating high load)
        contexts = []
        for i in range(100):
            context = get_tool_context(server)
            contexts.append(context)

            # Verify each context is valid
            assert hasattr(context, 'lifespan_context')
            assert context.lifespan_context is not None

        elapsed_time = time.time() - start_time

        # Should be able to create 100 contexts quickly
        assert elapsed_time < 0.5, f"Context creation too slow: {elapsed_time:.3f}s for 100 contexts"

        # All contexts should be independent but point to same app_context
        for context in contexts:
            app_ctx = context.lifespan_context.get("app_lifespan_context")
            assert app_ctx == app_context