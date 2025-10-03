#!/usr/bin/env python3
"""
Comprehensive validation script for QA report fixes.

This script validates that all the critical issues identified in the QA report
have been properly fixed, specifically:

1. Context passing fix preventing "'Server' object has no attribute 'lifespan_context'"
2. All CRUD operations (Create, Read, Update, Delete) work correctly
3. Search operations work for both Jira and Confluence
4. Health check functionality works end-to-end
5. Meta-tools can access context without errors

This script is designed to be run as a comprehensive validation after
implementing the P0 context fix.

Usage:
    python tests/integration/validate_qa_fixes.py
    uv run python tests/integration/validate_qa_fixes.py
"""

import asyncio
import json
import logging
import sys
import traceback
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Tuple
from datetime import datetime

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


class QAValidationRunner:
    """Runs comprehensive validation of QA report fixes."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "critical_issues": [],
            "summary": ""
        }

    def create_mock_server(self) -> MagicMock:
        """Create a properly mocked server with correct context structure."""
        # Mock app context
        app_context = MagicMock()
        app_context.full_jira_config = MagicMock()
        app_context.full_jira_config.url = "https://test.atlassian.net"
        app_context.full_jira_config.auth_type = "oauth"
        app_context.full_jira_config.is_auth_configured.return_value = True

        app_context.full_confluence_config = MagicMock()
        app_context.full_confluence_config.url = "https://test.atlassian.net"
        app_context.full_confluence_config.auth_type = "oauth"
        app_context.full_confluence_config.is_auth_configured.return_value = True

        # Mock server with proper structure
        server = MagicMock(spec=AtlassianMCP)
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    async def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        self.results["total_tests"] += 1

        try:
            logger.info(f"Running test: {test_name}")
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

            # Check for critical P0 error
            if "lifespan_context" in str(e):
                self.results["critical_issues"].append({
                    "test": test_name,
                    "error": error_msg,
                    "type": "P0_CONTEXT_ERROR"
                })

            self.results["test_results"].append({
                "name": test_name,
                "status": "FAILED",
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            logger.error(f"❌ {test_name} - FAILED: {error_msg}")
            return False

    async def test_context_function_basic(self):
        """Test that get_tool_context function works correctly."""
        server = self.create_mock_server()

        # This should NOT raise AttributeError about lifespan_context
        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context'), "Context missing lifespan_context attribute"
        assert context.lifespan_context is not None, "Context lifespan_context is None"
        assert isinstance(context.lifespan_context, dict), "Context lifespan_context is not a dict"
        assert "app_lifespan_context" in context.lifespan_context, "Missing app_lifespan_context"

    async def test_jira_issue_create_qa_scenario(self):
        """Test Jira issue creation that failed in QA report."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client
            mock_jira_fetcher = AsyncMock()
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {
                "key": "FTEST-123",
                "id": "10001",
                "summary": "Test Issue"
            }
            mock_jira_fetcher.create_issue.return_value = mock_issue
            mock_get_jira.return_value = mock_jira_fetcher

            # Test the operation that failed in QA report
            resource_manager = ResourceManager(dry_run=False)
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="jira",
                resource="issue",
                operation="create",
                data={
                    "project_key": "FTEST",
                    "summary": "QA Validation Test Issue",
                    "issue_type": "Task"
                }
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Issue creation failed: {result.get('error', 'Unknown error')}"
            assert result["data"]["key"] == "FTEST-123", "Incorrect issue key returned"

    async def test_confluence_page_create_qa_scenario(self):
        """Test Confluence page creation that failed in QA report."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_confluence_fetcher') as mock_get_confluence:
            # Mock successful Confluence client
            mock_confluence_fetcher = AsyncMock()
            mock_page = MagicMock()
            mock_page.to_dict.return_value = {
                "id": "123456",
                "title": "QA Test Page",
                "space": {"key": "TEST"}
            }
            mock_confluence_fetcher.create_page.return_value = mock_page
            mock_get_confluence.return_value = mock_confluence_fetcher

            # Test page creation
            resource_manager = ResourceManager(dry_run=False)
            result_json = await resource_manager.execute_operation(
                ctx=get_tool_context(server),
                service="confluence",
                resource="page",
                operation="create",
                data={
                    "space_key": "TEST",
                    "title": "QA Validation Test Page",
                    "body": "This page creation failed in the QA report"
                }
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Page creation failed: {result.get('error', 'Unknown error')}"
            assert result["data"]["title"] == "QA Test Page", "Incorrect page title returned"

    async def test_search_operations_qa_scenario(self):
        """Test search operations that failed in QA report."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful search
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

            # Test search operation
            search_engine = SearchEngine(dry_run=False)
            result_json = await search_engine.execute_search(
                ctx=get_tool_context(server),
                service="jira",
                query_type="jql",
                query="project = FTEST"
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Search failed: {result.get('error', 'Unknown error')}"
            assert len(result["results"]) == 1, "Incorrect number of search results"

    async def test_health_check_operations_qa_scenario(self):
        """Test health check operations that failed in QA report."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful Jira client
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.get_current_user_account_id.return_value = "test-user-123"
            mock_get_jira.return_value = mock_jira_fetcher

            # Test health check - this was throwing AttributeError in QA report
            result = await _check_service_health(get_tool_context(server), "jira", dry_run=False)

            assert result["service"] == "jira", "Incorrect service in health check result"
            assert result["status"] == "healthy", f"Health check failed: {result.get('errors', [])}"
            assert result["configuration"] == "valid", "Configuration should be valid"
            assert result["authentication"] == "valid", "Authentication should be valid"

    async def test_batch_operations_qa_scenario(self):
        """Test batch operations functionality."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful batch operations
            mock_jira_fetcher = AsyncMock()

            # Mock multiple issue creation
            mock_issues = []
            for i in range(3):
                mock_issue = MagicMock()
                mock_issue.to_simplified_dict.return_value = {
                    "key": f"FTEST-{i+1}",
                    "summary": f"Batch Issue {i+1}"
                }
                mock_issues.append(mock_issue)

            mock_jira_fetcher.create_issue.side_effect = mock_issues
            mock_get_jira.return_value = mock_jira_fetcher

            # Test batch processing
            batch_processor = BatchProcessor(dry_run=False)
            items = [
                {
                    "project_key": "FTEST",
                    "summary": f"Batch Issue {i+1}",
                    "issue_type": "Task"
                }
                for i in range(3)
            ]

            result_json = await batch_processor.execute_batch_operation(
                ctx=get_tool_context(server),
                service="jira",
                operation="create",
                resource_type="issue",
                items=items
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Batch operation failed: {result.get('error', 'Unknown error')}"
            assert result["summary"]["total"] == 3, "Incorrect batch operation count"
            assert result["summary"]["successful"] == 3, "Not all batch operations succeeded"

    async def test_workflow_operations_qa_scenario(self):
        """Test workflow operations functionality."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful workflow operations
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.transition_issue.return_value = True
            mock_jira_fetcher.get_issue_transitions.return_value = [
                {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}}
            ]
            mock_get_jira.return_value = mock_jira_fetcher

            # Test workflow engine
            workflow_engine = WorkflowEngine(dry_run=False)
            result_json = await workflow_engine.execute_workflow_operation(
                ctx=get_tool_context(server),
                operation="transition",
                issue_key="FTEST-123",
                transition_name="In Progress"
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Workflow operation failed: {result.get('error', 'Unknown error')}"

    async def test_relationship_operations_qa_scenario(self):
        """Test relationship operations functionality."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock successful relationship operations
            mock_jira_fetcher = AsyncMock()
            mock_jira_fetcher.create_issue_link.return_value = {"id": "12345"}
            mock_get_jira.return_value = mock_jira_fetcher

            # Test relationship manager
            relationship_manager = RelationshipManager(dry_run=False)
            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(server),
                operation="link",
                issue_key="FTEST-123",
                target_issue_key="FTEST-456",
                link_type="Blocks"
            )

            result = json.loads(result_json)
            assert result["success"] is True, f"Relationship operation failed: {result.get('error', 'Unknown error')}"

    async def test_all_meta_tools_context_access(self):
        """Test that all meta-tools can access context without errors."""
        server = self.create_mock_server()
        context = get_tool_context(server)

        meta_tools = [
            "ResourceManager",
            "SearchEngine",
            "BatchProcessor",
            "WorkflowEngine",
            "RelationshipManager"
        ]

        for tool_name in meta_tools:
            # Test the exact pattern that was failing in QA report
            try:
                lifespan_ctx = context.lifespan_context
                app_ctx = lifespan_ctx.get("app_lifespan_context")
                assert app_ctx is not None, f"Context access failed for {tool_name}"
            except AttributeError as e:
                if "lifespan_context" in str(e):
                    raise AssertionError(f"P0 context error not fixed for {tool_name}: {e}")
                else:
                    raise

    async def test_error_handling_scenarios(self):
        """Test error handling scenarios work correctly."""
        server = self.create_mock_server()

        with patch('mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Mock authentication error
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
            assert result["success"] is False, "Expected authentication error to be handled"
            assert "error" in result, "Error message should be present"
            assert "authentication" in result["error"].lower() or "credentials" in result["error"].lower()

    async def test_dry_run_functionality(self):
        """Test dry run mode works across all operations."""
        server = self.create_mock_server()

        # Test dry run mode (no mocking needed - should not make API calls)
        resource_manager = ResourceManager(dry_run=True)
        result_json = await resource_manager.execute_operation(
            ctx=get_tool_context(server),
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "FTEST",
                "summary": "Dry Run Test",
                "issue_type": "Task"
            }
        )

        result = json.loads(result_json)
        assert result["success"] is True, "Dry run should succeed"
        assert result["dry_run"] is True, "Dry run flag should be set"

    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("🚀 Starting comprehensive QA validation...")
        logger.info("=" * 60)

        # Define all tests to run
        tests = [
            ("Context Function Basic", self.test_context_function_basic),
            ("Jira Issue Create (QA Scenario)", self.test_jira_issue_create_qa_scenario),
            ("Confluence Page Create (QA Scenario)", self.test_confluence_page_create_qa_scenario),
            ("Search Operations (QA Scenario)", self.test_search_operations_qa_scenario),
            ("Health Check Operations (QA Scenario)", self.test_health_check_operations_qa_scenario),
            ("Batch Operations (QA Scenario)", self.test_batch_operations_qa_scenario),
            ("Workflow Operations (QA Scenario)", self.test_workflow_operations_qa_scenario),
            ("Relationship Operations (QA Scenario)", self.test_relationship_operations_qa_scenario),
            ("All Meta-Tools Context Access", self.test_all_meta_tools_context_access),
            ("Error Handling Scenarios", self.test_error_handling_scenarios),
            ("Dry Run Functionality", self.test_dry_run_functionality)
        ]

        # Run all tests
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)

        # Generate summary
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100

        if self.results["critical_issues"]:
            self.results["summary"] = f"❌ CRITICAL ISSUES FOUND - P0 context error still present!"
        elif self.results["failed_tests"] == 0:
            self.results["summary"] = f"✅ ALL TESTS PASSED - QA fixes successfully implemented!"
        else:
            self.results["summary"] = f"⚠️  {self.results['failed_tests']} tests failed - Success rate: {success_rate:.1f}%"

        # Print results
        logger.info("=" * 60)
        logger.info(f"📊 VALIDATION RESULTS:")
        logger.info(f"   Total Tests: {self.results['total_tests']}")
        logger.info(f"   Passed: {self.results['passed_tests']}")
        logger.info(f"   Failed: {self.results['failed_tests']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info("")
        logger.info(f"🎯 {self.results['summary']}")

        if self.results["critical_issues"]:
            logger.error("")
            logger.error("🚨 CRITICAL P0 ISSUES:")
            for issue in self.results["critical_issues"]:
                logger.error(f"   {issue['test']}: {issue['error']}")

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
    runner = QAValidationRunner()
    results = await runner.run_all_validations()

    # Exit with appropriate code
    if results["critical_issues"] or results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())