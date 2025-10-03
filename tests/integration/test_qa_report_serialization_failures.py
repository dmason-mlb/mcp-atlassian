"""
Tests that replicate the JSON Serialization failures from the QA Report.

These tests are designed to FAIL initially, proving the issues exist,
then pass after the issues are fixed.

QA Report Issues Tested:
1. "Object of type JiraIssueLink is not JSON serializable" when retrieving links
2. Complex objects not properly handled in JSON responses
3. Serialization errors preventing data retrieval
"""

import json
import pytest
import logging

from .config import skip_if_no_real_api, get_test_config
from .test_adapters import RelationshipManagerTestAdapter, TestJiraFetcher, TestConfluenceFetcher
from .test_data_factory import get_test_factory, TestResource
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig
from src.mcp_atlassian.meta_tools.errors import MetaToolError

logger = logging.getLogger(__name__)


@pytest.fixture
def config():
    """Get test configuration."""
    return get_test_config()

@pytest.fixture
def factory():
    """Get test data factory."""
    return get_test_factory()

@pytest.fixture
def jira_fetcher(config):
    """Get TestJiraFetcher instance."""
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    return TestJiraFetcher(jira_config)

@pytest.fixture
def confluence_fetcher(config):
    """Get TestConfluenceFetcher instance."""
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )
    return TestConfluenceFetcher(confluence_config)

@pytest.fixture
def relationship_adapter(jira_fetcher, confluence_fetcher):
    """Get RelationshipManagerTestAdapter instance."""
    return RelationshipManagerTestAdapter(jira_fetcher, confluence_fetcher)


@pytest.mark.qa_report
@pytest.mark.integration
@pytest.mark.real_api
class TestQAReportSerializationFailures:
    """Tests that expose the JSON serialization failures from the QA report."""

    @skip_if_no_real_api("Real API testing not configured")
    async def test_jira_issue_link_not_json_serializable(self, relationship_adapter, factory, config):
        """
        Test QA Issue: "Object of type JiraIssueLink is not JSON serializable"

        QA report states: "Link Retrieval: JSON serialization error prevents reading existing links"
        Specifically: "Object of type JiraIssueLink is not JSON serializable"

        This happens when retrieving issue links.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            # Test link retrieval (QA report says this fails with JSON serialization error)
            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(server),
                operation="get_links",
                issue_key="FTEST-1492"  # From QA report test data
            )

            # This should not fail with JSON serialization error
            try:
                result = json.loads(result_json)

                # Should be able to parse the JSON response
                assert isinstance(result, dict), f"Result should be JSON-parseable dict, got: {type(result)}"

                # If successful, should contain link data
                if result.get("success"):
                    assert "links" in result or "result" in result or "results" in result, \
                        f"Successful link retrieval should contain link data: {result}"

                    # All returned data should be JSON serializable
                    links_data = result.get("result", result.get("links", result.get("results", [])))
                    try:
                        # Test that the returned data can be re-serialized
                        json.dumps(links_data)
                    except TypeError as e:
                        pytest.fail(f"Link data should be JSON serializable but failed: {e}. Data: {links_data}")

                # If it fails, should not be due to serialization issues
                elif not result.get("success"):
                    error_message = result.get("error", "")
                    serialization_errors = [
                        "not JSON serializable",
                        "Object of type",
                        "TypeError",
                        "serialization"
                    ]
                    for ser_error in serialization_errors:
                        assert ser_error not in error_message, \
                            f"Link retrieval should not fail due to JSON serialization. Error: {error_message}"

            except json.JSONDecodeError as e:
                pytest.fail(f"Result should be valid JSON but failed to parse: {e}. Raw result: {result_json}")

    async def test_all_relationship_operations_are_json_serializable(self, realistic_server_setup):
        """
        Test that all relationship operations return JSON-serializable data.

        QA report shows serialization issues, so we need to test all operations.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            # Test all relationship operations that return data
            operations_to_test = [
                ("get_links", {"issue_key": "FTEST-1492"}),
                ("create_link", {
                    "issue_key": "FTEST-1492",
                    "target_issue_key": "FTEST-1493",
                    "link_type": "Relates"
                }),
            ]

            for operation, params in operations_to_test:
                result_json = await relationship_manager.execute_relationship_operation(
                    ctx=get_tool_context(server),
                    operation=operation,
                    **params
                )

                # Test JSON parseability
                try:
                    result = json.loads(result_json)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Operation '{operation}' should return valid JSON but failed: {e}. Raw: {result_json}")

                # Test that all data in the result is JSON serializable
                try:
                    json.dumps(result)
                except TypeError as e:
                    pytest.fail(f"Operation '{operation}' returned non-serializable data: {e}. Result: {result}")

                # If operation succeeds, test that result data is serializable
                if result.get("success") and "result" in result:
                    try:
                        json.dumps(result["result"])
                    except TypeError as e:
                        pytest.fail(f"Operation '{operation}' result data not serializable: {e}. Data: {result['result']}")

    async def test_complex_objects_are_properly_serialized(self, realistic_server_setup):
        """
        Test that complex Jira objects are properly converted to JSON-safe formats.

        QA report indicates complex objects like JiraIssueLink cause serialization failures.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Create a mock that returns complex objects (like real Jira client does)
            mock_jira_client = MagicMock()

            # Mock a complex JiraIssueLink-like object
            mock_link = MagicMock()
            mock_link.id = "12345"
            mock_link.type = MagicMock()
            mock_link.type.name = "Relates"
            mock_link.inwardIssue = MagicMock()
            mock_link.inwardIssue.key = "FTEST-1492"
            mock_link.outwardIssue = MagicMock()
            mock_link.outwardIssue.key = "FTEST-1493"

            # This mock object would not be JSON serializable by default
            mock_jira_client.get_issue_links.return_value = [mock_link]
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            # Test that the system handles complex objects properly
            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(server),
                operation="get_links",
                issue_key="FTEST-1492"
            )

            # Should successfully convert complex objects to JSON
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError as e:
                pytest.fail(f"Complex objects should be converted to JSON-safe format: {e}")

            # Result should be parseable and re-serializable
            try:
                json.dumps(result)
            except TypeError as e:
                pytest.fail(f"Result with complex objects should be fully serializable: {e}")

    async def test_serialization_error_handling(self, realistic_server_setup):
        """
        Test that serialization errors are properly handled and don't crash the system.

        If serialization fails, it should be gracefully handled with informative errors.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Create an object that definitely can't be serialized
            class UnserializableObject:
                def __init__(self):
                    self.circular_ref = self

            mock_jira_client = MagicMock()
            mock_jira_client.get_issue_links.return_value = [UnserializableObject()]
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(server),
                operation="get_links",
                issue_key="FTEST-1492"
            )

            # Should handle serialization errors gracefully
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError:
                pytest.fail("System should handle serialization errors gracefully and return valid JSON")

            # Should indicate failure with informative error
            assert result.get("success") is False, "Should fail gracefully when serialization issues occur"

            error_message = result.get("error", "")
            assert len(error_message) > 0, "Should provide error message for serialization failures"

            # Error should be informative about the serialization issue
            assert any(keyword in error_message.lower() for keyword in ["serialize", "json", "convert"]), \
                f"Error should indicate serialization issue: {error_message}"

    async def test_json_response_structure_consistency(self, realistic_server_setup):
        """
        Test that all MCP tool responses have consistent JSON structure.

        QA report suggests inconsistent response formats causing serialization issues.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            # Test multiple operations for consistent structure
            operations = ["get_links", "create_link"]
            operation_params = [
                {"issue_key": "FTEST-1492"},
                {"issue_key": "FTEST-1492", "target_issue_key": "FTEST-1493", "link_type": "Relates"}
            ]

            for operation, params in zip(operations, operation_params):
                result_json = await relationship_manager.execute_relationship_operation(
                    ctx=get_tool_context(server),
                    operation=operation,
                    **params
                )

                # Parse JSON
                try:
                    result = json.loads(result_json)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Operation '{operation}' should return valid JSON: {e}")

                # Check consistent structure
                required_fields = ["success"]
                for field in required_fields:
                    assert field in result, f"Operation '{operation}' missing required field '{field}': {result}"

                # Success field should be boolean
                assert isinstance(result["success"], bool), \
                    f"Operation '{operation}' success field should be boolean: {result['success']}"

                # If failure, should have error field
                if not result["success"]:
                    assert "error" in result, f"Failed operation '{operation}' should have error field: {result}"
                    assert isinstance(result["error"], str), \
                        f"Error field should be string for operation '{operation}': {result['error']}"

                # Test that entire structure is serializable
                try:
                    json.dumps(result)
                except TypeError as e:
                    pytest.fail(f"Operation '{operation}' result structure not serializable: {e}")

    async def test_no_object_type_errors_in_responses(self, realistic_server_setup):
        """
        Test that responses don't contain "Object of type X" errors.

        QA report specifically mentions "Object of type JiraIssueLink is not JSON serializable"
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            relationship_manager = RelationshipManager(dry_run=False)

            result_json = await relationship_manager.execute_relationship_operation(
                ctx=get_tool_context(server),
                operation="get_links",
                issue_key="FTEST-1492"
            )

            # Parse the result
            result = json.loads(result_json)

            # Check that no "Object of type" errors appear anywhere in the response
            result_str = json.dumps(result)
            object_type_errors = [
                "Object of type",
                "is not JSON serializable",
                "TypeError:",
                "serialization error"
            ]

            for error_pattern in object_type_errors:
                assert error_pattern not in result_str, \
                    f"Response should not contain serialization error '{error_pattern}': {result}"