"""Integration tests that reproduce the exact operational failures identified in the QA report.

These tests are designed to FAIL initially, reproducing the exact issues described in the
September 19, 2025 QA report where all actual operations fail despite successful capability
discovery and health checks.

Key issues to reproduce:
1. All resource_manager_tool operations fail with "Error calling tool"
2. Even dry_run operations fail (critical issue)
3. Search engine operations fail
4. Health checks report "healthy" while operations fail
5. Error messages are generic and not actionable
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from typing import Any, Dict, List

from src.mcp_atlassian.servers.main import AtlassianMCP, register_v2_tools
from src.mcp_atlassian.servers.context import MainAppContext
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig


@pytest.fixture
async def operational_mcp_server():
    """Create MCP server configured for operational testing that reproduces QA failures."""
    # Create server instance
    server = AtlassianMCP(name="QA Test Atlassian MCP")

    # Create minimal but problematic configuration to reproduce QA issues
    mock_lifespan_state = Mock()
    mock_lifespan_state.read_only = False
    mock_lifespan_state.enabled_tools = None

    # Create minimal config objects that will cause auth failures
    # This simulates the QA environment where configs exist but are incomplete/invalid
    mock_jira_config = JiraConfig(
        url="https://test.atlassian.net",
        auth_type="oauth",  # But no actual credentials provided
    )
    mock_confluence_config = ConfluenceConfig(
        url="https://test.atlassian.net",
        auth_type="oauth",  # But no actual credentials provided
    )

    mock_lifespan_state.full_jira_config = mock_jira_config
    mock_lifespan_state.full_confluence_config = mock_confluence_config

    # Mock the server context with proper setup
    server._mcp_server = Mock()
    server._mcp_server.request_context = Mock()
    server._mcp_server.request_context.lifespan_context = {
        "app_lifespan_context": mock_lifespan_state
    }

    # Mock application context that should provide working services
    mock_app_context = Mock()
    mock_app_context.jira_client = Mock()
    mock_app_context.confluence_client = Mock()
    server.ctx = mock_app_context

    # Register tools
    register_v2_tools(server)

    # Don't mock _mcp_call_tool - let the real execution happen to see actual errors
    # This will reveal the true root cause of the QA issues

    return server


@pytest.mark.integration
class TestQAReportOperationalFailures:
    """Test suite that reproduces the exact operational failures from the QA report.

    These tests should FAIL initially, proving that the QA issues exist.
    After fixes are implemented, these tests should PASS.
    """

    @pytest.mark.asyncio
    async def test_basic_jira_issue_creation_fails(self, operational_mcp_server):
        """Reproduce QA Test Case TC-001: Basic issue creation fails.

        This test reproduces the exact parameters used in the QA report that failed.
        Expected: Should FAIL initially with "Error calling tool"
        After fix: Should succeed with proper issue creation
        """
        # Exact parameters from QA report TC-001
        params = {
            "service": "jira",
            "resource": "issue",
            "operation": "create",
            "data": {
                "project_key": "FTEST",
                "summary": "MCP Test Issue #1",
                "issue_type": "Task"
            }
        }

        try:
            # This should work but currently fails according to QA report
            result = await operational_mcp_server._mcp_call_tool("resource_manager_tool", params)

            # If we reach here, the fix worked
            assert result is not None, "Tool should return a result"

            # Verify the result contains expected data
            if isinstance(result, list) and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                assert "FTEST" in content, "Result should reference the project key"
                assert "Task" in content, "Result should reference the issue type"
            else:
                # Direct result format
                assert "FTEST" in str(result), "Result should reference the project key"

        except Exception as e:
            error_message = str(e)

            # This reproduces the QA report failure - should be specific, not generic
            if "Error calling tool" in error_message:
                pytest.fail(
                    f"QA Report Issue Reproduced: Generic 'Error calling tool' message. "
                    f"Actual error: {error_message}. "
                    f"This error should be specific and actionable, not generic."
                )

            # If it's a different error, we want specific details
            pytest.fail(
                f"Issue creation failed with error: {error_message}. "
                f"Error should be specific and actionable."
            )

    @pytest.mark.asyncio
    async def test_dry_run_operations_must_work(self, operational_mcp_server):
        """Reproduce QA Test Case TC-002: Dry run operations fail (CRITICAL ISSUE).

        This is the most critical test because dry_run operations should ALWAYS work
        regardless of external API status. If this fails, it indicates fundamental
        implementation problems in the tool layer.

        Expected: Should FAIL initially
        After fix: Should succeed with validation response
        """
        # Exact parameters from QA report TC-002 with dry_run=true
        params = {
            "service": "jira",
            "resource": "issue",
            "operation": "create",
            "dry_run": True,  # This should always work
            "data": {
                "project_key": "FTEST",
                "summary": "MCP Test Issue #1",
                "issue_type": "Task"
            }
        }

        try:
            # Dry run should ALWAYS work - this is critical
            result = await operational_mcp_server._mcp_call_tool("resource_manager_tool", params)

            # If we reach here, the fix worked
            assert result is not None, "Dry run should always return a result"

            # Verify dry run behavior
            if isinstance(result, list) and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                # Should indicate validation or dry run mode
                assert any(keyword in content.lower() for keyword in [
                    "dry", "validation", "would", "preview", "simulate"
                ]), f"Dry run should indicate validation mode. Got: {content}"
            else:
                # Direct result should indicate dry run behavior
                content = str(result)
                assert any(keyword in content.lower() for keyword in [
                    "dry", "validation", "would", "preview", "simulate"
                ]), f"Dry run should indicate validation mode. Got: {content}"

        except Exception as e:
            error_message = str(e)

            # This is CRITICAL - dry run should never fail
            pytest.fail(
                f"CRITICAL QA Issue Reproduced: Dry run operations fail. "
                f"Error: {error_message}. "
                f"Dry run operations should ALWAYS work regardless of external API status. "
                f"This indicates fundamental tool implementation problems."
            )

    @pytest.mark.asyncio
    async def test_search_operations_fail(self, operational_mcp_server):
        """Reproduce QA Test Case TC-005: Search operations fail.

        Expected: Should FAIL initially
        After fix: Should return search results
        """
        # Test search for recent issues
        params = {
            "service": "jira",
            "query_type": "recent_issues",
            "options": {
                "limit": 10,
                "project": "FTEST"
            }
        }

        try:
            result = await operational_mcp_server._mcp_call_tool("search_engine_tool", params)

            # If we reach here, the fix worked
            assert result is not None, "Search should return results"

            # Verify search results format
            if isinstance(result, list) and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                # Should contain search results or indication of search completion
                assert any(keyword in content.lower() for keyword in [
                    "issues", "found", "results", "search", "jira"
                ]), f"Search should return meaningful results. Got: {content}"

        except Exception as e:
            error_message = str(e)

            # Reproduce QA report search failure
            if "Error calling tool" in error_message:
                pytest.fail(
                    f"QA Report Issue Reproduced: Search operations fail with generic error. "
                    f"Actual error: {error_message}. "
                    f"Search errors should be specific and actionable."
                )

            pytest.fail(
                f"Search operation failed: {error_message}. "
                f"Error should provide specific details about the search failure."
            )

    @pytest.mark.asyncio
    async def test_error_messages_are_actionable(self, operational_mcp_server):
        """Test that error messages are specific and actionable, not generic.

        The QA report identified that all errors are generic "Error calling tool" messages.
        This test verifies that errors provide specific, actionable information.

        Expected: Should FAIL initially with generic errors
        After fix: Should provide specific error details
        """
        # Test with intentionally invalid parameters to trigger errors
        invalid_params = {
            "service": "jira",
            "resource": "issue",
            "operation": "create",
            "data": {
                "project_key": "NONEXISTENT_PROJECT",
                "summary": "",  # Invalid empty summary
                "issue_type": "InvalidType"
            }
        }

        # Execute the operation with invalid parameters
        result = await operational_mcp_server._mcp_call_tool("resource_manager_tool", invalid_params)

        # The system should return a structured error response, not raise an exception
        assert result is not None, "Tool should return a structured error response"

        # Parse the response content
        if isinstance(result, list) and len(result) > 0:
            content = result[0].text if hasattr(result[0], 'text') else str(result[0])
        else:
            content = str(result)

        # The response should be a structured JSON error
        try:
            import json
            error_data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pytest.fail(f"Error response should be valid JSON. Got: {content}")

        # Validate structured error response contains all required elements
        assert error_data.get("error") is True, "Response should indicate error=true"
        assert "error_code" in error_data, "Should include specific error code"
        assert "message" in error_data, "Should include error message"
        assert "suggestions" in error_data, "Should include actionable suggestions"
        assert "context" in error_data, "Should include error context"

        # Verify suggestions are specific and actionable
        suggestions = error_data.get("suggestions", [])
        assert len(suggestions) > 0, "Should provide specific suggestions"

        # Check that suggestions contain actionable guidance (not generic phrases)
        generic_patterns = ["Error calling tool", "An error occurred", "Something went wrong", "Unknown error"]
        for suggestion in suggestions:
            for pattern in generic_patterns:
                if pattern in suggestion:
                    pytest.fail(f"QA Issue: Generic suggestion detected: '{pattern}' in '{suggestion}'")

        # Verify context provides useful debugging information
        context = error_data.get("context", {})
        assert context.get("service") == "jira", "Context should include service"
        assert context.get("resource") == "issue", "Context should include resource"
        assert context.get("operation") == "create", "Context should include operation"
        assert "underlying_error" in context, "Context should include underlying error details"

        # Verify working example is provided for guidance
        if "working_example" in error_data:
            working_example = error_data["working_example"]
            assert "service" in working_example, "Working example should include service"
            assert "data" in working_example, "Working example should include sample data"

    @pytest.mark.asyncio
    async def test_capabilities_work_but_operations_fail_pattern(self, operational_mcp_server):
        """Test the core QA issue: capabilities work but operations fail.

        This reproduces the fundamental disconnect identified in the QA report where
        the server can describe what it does but can't actually do it.

        Expected: Should FAIL initially showing the disconnect
        After fix: Should show consistency between capabilities and operations
        """
        # First, verify capabilities work (this should always work)
        try:
            capabilities_result = await operational_mcp_server._mcp_call_tool("get_capabilities", {})
            assert capabilities_result is not None, "Capabilities should work"

            # Verify capabilities include resource_manager
            caps_content = str(capabilities_result)
            assert "resource_manager" in caps_content.lower(), "Should advertise resource_manager capability"

        except Exception as e:
            pytest.fail(f"Capabilities query failed: {e}. This should always work.")

        # Now test if advertised operations actually work
        try:
            # Test basic operation that capabilities claim is supported
            operation_result = await operational_mcp_server._mcp_call_tool("resource_manager_tool", {
                "service": "jira",
                "resource": "issue",
                "operation": "create",
                "dry_run": True,  # Should definitely work if capabilities are accurate
                "data": {
                    "project_key": "FTEST",
                    "summary": "Test consistency",
                    "issue_type": "Task"
                }
            })

            # If this works, the disconnect is fixed
            assert operation_result is not None, "Operations should work if capabilities advertise them"

        except Exception as e:
            # This reproduces the QA report's core issue
            pytest.fail(
                f"QA Report Core Issue Reproduced: Capabilities/Operations Disconnect. "
                f"Server advertises resource_manager capability but operations fail. "
                f"Error: {e}. "
                f"If server claims to support operations, they should actually work. "
                f"This indicates a fundamental implementation problem."
            )


@pytest.mark.integration
class TestHealthCheckAccuracy:
    """Test that health checks accurately reflect operational capability.

    The QA report identified that health checks report "healthy" while all operations fail.
    This is a critical monitoring and reliability issue.
    """

    @pytest.mark.asyncio
    async def test_health_check_correlates_with_actual_functionality(self, operational_mcp_server):
        """Test that health check results correlate with actual operational capability.

        QA Issue: Health check reports "healthy" while all operations fail.

        Expected: Should FAIL initially showing false positive health
        After fix: Health status should correlate with actual operational status
        """
        # Get health check result
        try:
            health_result = await operational_mcp_server._mcp_call_tool("connection_health_check", {})
            assert health_result is not None, "Health check should return results"

            health_content = str(health_result).lower()

            # Determine if health check claims things are healthy
            is_reported_healthy = any(indicator in health_content for indicator in [
                "healthy", "ok", "success", "valid", "connected"
            ])

            if not is_reported_healthy:
                # Health check already indicates problems - that's good
                pytest.skip("Health check correctly indicates problems, no false positive to test")

        except Exception as e:
            # Health check itself failed - that's actually good, not misleading
            pytest.skip(f"Health check failed (correctly indicating problems): {e}")

        # If health check reports healthy, verify operations actually work
        try:
            # Test basic operation that should work if system is truly healthy
            operation_result = await operational_mcp_server._mcp_call_tool("resource_manager_tool", {
                "service": "jira",
                "resource": "issue",
                "operation": "get",
                "identifier": "FTEST-1",
                "dry_run": True  # Minimal operation that should work if healthy
            })

            # If this works, health check is accurate
            assert operation_result is not None, "Operations should work if health reports healthy"

        except Exception as e:
            # This reproduces the QA issue: healthy report but operations fail
            pytest.fail(
                f"QA Report Issue Reproduced: Misleading Health Check. "
                f"Health check reports system as healthy, but basic operations fail. "
                f"Operation error: {e}. "
                f"Health checks should test actual operational capability, not just configuration."
            )

    @pytest.mark.asyncio
    async def test_health_check_tests_actual_operations(self, operational_mcp_server):
        """Test that health checks perform actual operational tests.

        Current health checks likely only validate configuration/connectivity.
        They should test actual API operations to verify real functionality.

        Expected: Should FAIL initially if health checks are superficial
        After fix: Health checks should test real operational capability
        """
        try:
            health_result = await operational_mcp_server._mcp_call_tool(
                "connection_health_check",
                {"dry_run": False}  # Request real operational test
            )

            health_content = str(health_result).lower()

            # Health check should indicate it tested actual operations
            operational_indicators = [
                "api call", "operation", "tested", "verified", "executed",
                "actual", "functional", "working", "performed"
            ]

            has_operational_test = any(indicator in health_content for indicator in operational_indicators)

            if not has_operational_test:
                pytest.fail(
                    f"QA Report Issue Reproduced: Superficial Health Check. "
                    f"Health check appears to only validate configuration, not actual operations. "
                    f"Health content: {health_content}. "
                    f"Health checks should test actual API operations to verify real functionality."
                )

            # Verify health check mentions specific operational capabilities
            capability_indicators = [
                "issue", "create", "read", "update", "search", "jira", "confluence"
            ]

            has_capability_test = any(indicator in health_content for indicator in capability_indicators)

            if not has_capability_test:
                pytest.fail(
                    f"Health check should test specific operational capabilities. "
                    f"Content: {health_content}. "
                    f"Should verify actual issue operations, searches, etc."
                )

        except Exception as e:
            pytest.fail(
                f"Health check with operational testing failed: {e}. "
                f"Health checks should be able to perform actual operational tests."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--integration"])