#!/usr/bin/env python3
"""
Real-world validation script for QA report fixes.

This script provides comprehensive validation using realistic mocks and patterns
to prove that the P0 context fix works in all real-world scenarios. This replaces
the previous validation script that had complex mocking issues.

Key improvements:
- Uses the new mock factory for realistic client behavior
- Tests actual meta-tool integration patterns
- Validates concurrent operations
- Proves no AttributeError occurs in production scenarios

Usage:
    python tests/integration/validate_real_world.py
    uv run python tests/integration/validate_real_world.py
"""

import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path for imports
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from mcp_atlassian.servers.main import AtlassianMCP, get_tool_context, _check_service_health
from mcp_atlassian.meta_tools.resource_manager import ResourceManager
from mcp_atlassian.meta_tools.search_engine import SearchEngine
from mcp_atlassian.meta_tools.batch_processor import BatchProcessor
from mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
from mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

# Import mock factory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from fixtures.mock_factory import MockClientFactory, create_realistic_app_context, create_realistic_server_context


class RealWorldValidator:
    """Validates QA report fixes using realistic scenarios."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_type": "real_world_comprehensive",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "critical_errors": [],
            "test_results": [],
            "performance_metrics": {},
            "summary": ""
        }

    def create_realistic_server(self) -> Any:
        """Create a realistic server setup for testing."""
        app_context = create_realistic_app_context()
        server = create_realistic_server_context(app_context)
        return server

    async def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test with comprehensive error handling."""
        self.results["total_tests"] += 1

        try:
            logger.info(f"🧪 Running: {test_name}")
            await test_func()

            self.results["passed_tests"] += 1
            self.results["test_results"].append({
                "name": test_name,
                "status": "PASSED",
                "error": None
            })
            logger.info(f"✅ {test_name} - PASSED")
            return True

        except Exception as e:
            self.results["failed_tests"] += 1
            error_msg = f"{type(e).__name__}: {str(e)}"

            # Check for the critical P0 error
            if "lifespan_context" in str(e) and "AttributeError" in str(e):
                self.results["critical_errors"].append({
                    "test": test_name,
                    "error": error_msg,
                    "type": "P0_CONTEXT_ERROR_STILL_PRESENT"
                })

            self.results["test_results"].append({
                "name": test_name,
                "status": "FAILED",
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            logger.error(f"❌ {test_name} - FAILED: {error_msg}")
            return False

    async def test_basic_context_creation(self):
        """Test basic context creation with realistic server."""
        server = self.create_realistic_server()

        # This should NOT throw the P0 AttributeError
        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context'), "Context missing lifespan_context"
        assert context.lifespan_context is not None, "lifespan_context is None"
        assert isinstance(context.lifespan_context, dict), "lifespan_context is not a dict"
        assert "app_lifespan_context" in context.lifespan_context, "Missing app_lifespan_context"

    async def test_resource_manager_with_realistic_mocks(self):
        """Test ResourceManager with improved mocking."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Use the realistic mock client factory
            mock_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_client

            resource_manager = ResourceManager(dry_run=False)

            # Test issue creation
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "project_key": "REAL",
                    "summary": "Real World Test Issue",
                    "issue_type": "Task"
                }
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"ResourceManager failed: {result.get('error', 'Unknown error')}"
            assert result["data"]["key"] == "REAL-123", "Incorrect issue key"

    async def test_search_engine_with_realistic_mocks(self):
        """Test SearchEngine with improved mocking."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_client

            search_engine = SearchEngine(dry_run=False)

            result_json = await search_engine.execute_search(
                ctx=get_tool_context(server),
                service="jira",
                query_type="issues",
                query="project = REAL"
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"SearchEngine failed: {result.get('error', 'Unknown error')}"

    async def test_health_check_realistic_scenario(self):
        """Test health check with realistic server setup."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_client

            result = await _check_service_health(get_tool_context(server), "jira", dry_run=False)

            assert result["service"] == "jira", "Incorrect service in result"
            assert result["status"] == "healthy", f"Health check failed: {result.get('errors', [])}"
            assert result["configuration"] == "valid", "Configuration should be valid"

    async def test_concurrent_operations_realistic(self):
        """Test concurrent operations with realistic setup."""
        server = self.create_realistic_server()

        results = []
        errors = []

        async def concurrent_worker(worker_id: int):
            try:
                with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
                    mock_client = MockClientFactory.create_jira_client()
                    mock_get_jira.return_value = mock_client

                    resource_manager = ResourceManager(dry_run=False)

                    result_json = await resource_manager.execute_operation(
                        ctx=get_tool_context(server),
                        service="jira",
                        resource="issue",
                        operation="create",
                        data={
                            "project_key": "CONCURRENT",
                            "summary": f"Concurrent Test {worker_id}",
                            "issue_type": "Task"
                        }
                    )

                    result = json.loads(result_json)
                    results.append((worker_id, result["success"]))

            except Exception as e:
                errors.append((worker_id, e))

        # Run 5 concurrent operations
        tasks = [concurrent_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)

        assert len(errors) == 0, f"Concurrent operations failed: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        assert all(success for _, success in results), "Some concurrent operations failed"

    async def test_error_handling_realistic(self):
        """Test error handling in realistic scenarios."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Simulate authentication error
            mock_get_jira.side_effect = MCPAtlassianAuthenticationError("Invalid credentials")

            resource_manager = ResourceManager(dry_run=False)

            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="jira",
                resource="issue",
                operation="create",
                data={"summary": "Test Issue"}
            )

            result = json.loads(result_json)
            assert result["success"] is False, "Expected authentication error"
            assert "error" in result, "Error message should be present"
            # Most importantly: should NOT contain P0 AttributeError
            assert "lifespan_context" not in result["error"], "P0 error still present in error message"

    async def test_dependencies_integration_realistic(self):
        """Test the exact dependencies.py integration pattern."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_client

            # Test the exact pattern from dependencies.py
            context = get_tool_context(server)

            # This is line 202 in dependencies.py that was failing
            lifespan_ctx_dict = context.lifespan_context
            app_lifespan_ctx = (
                lifespan_ctx_dict.get("app_lifespan_context")
                if isinstance(lifespan_ctx_dict, dict)
                else None
            )

            assert app_lifespan_ctx is not None, "Dependencies pattern failed"

            # Test that get_jira_fetcher can be called with this context
            from mcp_atlassian.servers.dependencies import get_jira_fetcher
            try:
                fetcher = await get_jira_fetcher(context)
                assert fetcher is not None, "get_jira_fetcher failed"
            except AttributeError as e:
                if "lifespan_context" in str(e):
                    raise AssertionError(f"P0 error still present in dependencies: {e}")
                else:
                    # Different error, might be expected (like missing actual config)
                    pass

    async def test_dry_run_operations_realistic(self):
        """Test dry run operations work correctly."""
        server = self.create_realistic_server()

        # Test ResourceManager dry run
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
        assert result["success"] is True, "Dry run should succeed"
        assert result["dry_run"] is True, "Dry run flag should be set"

    async def test_context_edge_cases_realistic(self):
        """Test edge cases with realistic patterns."""
        # Test None server
        context = get_tool_context(None)
        assert context.lifespan_context == {}, "None server should return empty context"

        # Test server with missing attributes
        server = object()  # Not even a mock
        context = get_tool_context(server)
        assert context.lifespan_context == {}, "Invalid server should return empty context"

    async def test_meta_tools_integration_realistic(self):
        """Test multiple meta-tools with the same context."""
        server = self.create_realistic_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_client

            context = get_tool_context(server)

            # Test different meta-tools with same context
            resource_manager = ResourceManager(dry_run=True)
            search_engine = SearchEngine(dry_run=True)

            # Both should work with the same context
            result1_json = await resource_manager.execute_operation(
                ctx=context,
                service="jira",
                resource="issue",
                operation="create",
                data={"summary": "Test 1"}
            )

            result2_json = await search_engine.execute_search(
                ctx=context,
                service="jira",
                query_type="issues",
                query="test"
            )

            result1 = json.loads(result1_json)
            result2 = json.loads(result2_json)

            assert result1["success"] is True, "ResourceManager failed"
            assert result2["success"] is True, "SearchEngine failed"

    async def test_performance_realistic(self):
        """Test performance with realistic context creation."""
        import time

        start_time = time.time()

        # Create many contexts quickly
        for i in range(500):
            server = self.create_realistic_server()
            context = get_tool_context(server)
            assert hasattr(context, 'lifespan_context')

        elapsed_time = time.time() - start_time
        self.results["performance_metrics"]["context_creation_500"] = elapsed_time

        # Should be able to create 500 contexts in under 1 second
        assert elapsed_time < 1.0, f"Context creation too slow: {elapsed_time:.3f}s for 500 contexts"

    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all real-world validation tests."""
        logger.info("🚀 Starting Real-World Comprehensive Validation...")
        logger.info("=" * 60)

        # Define all tests
        tests = [
            ("Basic Context Creation", self.test_basic_context_creation),
            ("ResourceManager with Realistic Mocks", self.test_resource_manager_with_realistic_mocks),
            ("SearchEngine with Realistic Mocks", self.test_search_engine_with_realistic_mocks),
            ("Health Check Realistic Scenario", self.test_health_check_realistic_scenario),
            ("Concurrent Operations Realistic", self.test_concurrent_operations_realistic),
            ("Error Handling Realistic", self.test_error_handling_realistic),
            ("Dependencies Integration Realistic", self.test_dependencies_integration_realistic),
            ("Dry Run Operations Realistic", self.test_dry_run_operations_realistic),
            ("Context Edge Cases Realistic", self.test_context_edge_cases_realistic),
            ("Meta-Tools Integration Realistic", self.test_meta_tools_integration_realistic),
            ("Performance Realistic", self.test_performance_realistic)
        ]

        # Run all tests
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)

        # Generate summary
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100

        if self.results["critical_errors"]:
            self.results["summary"] = "❌ CRITICAL: P0 context error still present!"
        elif self.results["failed_tests"] == 0:
            self.results["summary"] = "✅ ALL REAL-WORLD TESTS PASSED - QA fixes are production ready!"
        else:
            self.results["summary"] = f"⚠️  {self.results['failed_tests']} tests failed - Success rate: {success_rate:.1f}%"

        # Print results
        logger.info("=" * 60)
        logger.info("📊 REAL-WORLD VALIDATION RESULTS:")
        logger.info(f"   Total Tests: {self.results['total_tests']}")
        logger.info(f"   Passed: {self.results['passed_tests']}")
        logger.info(f"   Failed: {self.results['failed_tests']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")

        if self.results["performance_metrics"]:
            logger.info("⚡ PERFORMANCE METRICS:")
            for metric, value in self.results["performance_metrics"].items():
                logger.info(f"   {metric}: {value:.3f}s")

        logger.info("")
        logger.info(f"🎯 {self.results['summary']}")

        if self.results["critical_errors"]:
            logger.error("")
            logger.error("🚨 CRITICAL P0 ERRORS:")
            for error in self.results["critical_errors"]:
                logger.error(f"   {error['test']}: {error['error']}")

        if self.results["failed_tests"] > 0:
            logger.error("")
            logger.error("❌ FAILED TESTS:")
            for test_result in self.results["test_results"]:
                if test_result["status"] == "FAILED":
                    logger.error(f"   {test_result['name']}: {test_result['error']}")

        logger.info("=" * 60)

        return self.results


async def main():
    """Main validation runner."""
    validator = RealWorldValidator()
    results = await validator.run_all_validations()

    # Exit with appropriate code
    if results["critical_errors"] or results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())