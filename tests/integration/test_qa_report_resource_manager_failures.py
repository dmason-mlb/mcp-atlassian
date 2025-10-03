"""
Tests that replicate the Resource Manager failures from the QA Report.

These tests are designed to FAIL initially, proving the issues exist,
then pass after the issues are fixed.

QA Report Issues Tested:
1. Individual issue creation returns "Error calling tool" with no details
2. Issue updates fail with generic errors
3. Comment management fails with generic errors
4. Poor error handling that masks actual errors
"""

import json
import pytest
import logging

from .config import skip_if_no_real_api, get_test_config
from .test_adapters import ResourceManagerTestAdapter, TestJiraFetcher, TestConfluenceFetcher
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
def resource_adapter(jira_fetcher, confluence_fetcher):
    """Get ResourceManagerTestAdapter instance."""
    return ResourceManagerTestAdapter(jira_fetcher, confluence_fetcher)


@pytest.mark.qa_report
@pytest.mark.integration
@pytest.mark.real_api
class TestQAReportResourceManagerFailures:
    """Tests that expose the resource manager failures from the QA report."""

    @skip_if_no_real_api("Real API testing not configured")
    async def test_individual_issue_creation_generic_error(self, resource_adapter, config, factory):
        """
        Test QA Issue: Individual issue creation returns "Error calling tool" with no details

        QA report states: "Individual Issue Creation" tool returns "Error calling tool" with no details
        vs Batch Issue Creation which works fine.

        This test should FAIL initially with generic error, then PASS with proper error details.
        """
        # Create test issue data
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "QA Test Issue - Individual Creation",
                "issue_type": "Task",
                "description": "Testing individual issue creation from QA report"
            }
        )

        # Test individual issue creation (QA report says this fails)
        result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        result = json.loads(result_json)

        # Should NOT return generic "Error calling tool" message
        if not result["success"]:
            error_message = result.get("error", "")
            assert error_message != "Error calling tool", \
                f"Should not return generic 'Error calling tool' message. Got: {error_message}"

            # Error should be specific and helpful
            assert len(error_message) > 20, f"Error message should be descriptive, got: {error_message}"
            assert any(keyword in error_message.lower() for keyword in ["jira", "issue", "create", "field", "project"]), \
                f"Error should contain relevant context, got: {error_message}"
        else:
            # If it succeeds, that's good - means the issue is fixed
            assert "result" in result

            # Track created resource for cleanup
            if "result" in result and isinstance(result["result"], dict) and "key" in result["result"]:
                factory.track_resource(result["result"]["key"], TestResource.JIRA_ISSUE)

    @skip_if_no_real_api("Real API testing not configured")
    async def test_issue_update_operations_fail_generically(self, resource_adapter, config, factory):
        """
        Test QA Issue: Issue updates fail with generic errors

        QA report states: "Issue Updates" return generic errors instead of specific feedback.
        """
        # Create a test issue first for updating
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "Original Issue for Update Test",
                "issue_type": "Task",
                "description": "Original description for testing updates"
            }
        )

        # Create the issue to get an issue key
        create_result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        create_result = json.loads(create_result_json)
        if not create_result["success"]:
            pytest.skip(f"Cannot create test issue for update test: {create_result.get('error', 'Unknown error')}")

        issue_key = create_result["result"]["key"] if "result" in create_result and "key" in create_result["result"] else None
        if not issue_key:
            pytest.skip("Cannot extract issue key from create result")

        # Track for cleanup
        factory.track_resource(issue_key, TestResource.JIRA_ISSUE)

        # Test issue update (QA report says this fails with generic errors)
        result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="update",
            identifier=issue_key,
            data={
                "summary": "Updated Summary from QA Test",
                "description": "Updated description to test issue updates"
            }
        )

        result = json.loads(result_json)

        # Should NOT return generic error messages
        if not result["success"]:
            error_message = result.get("error", "")
            assert error_message != "Error calling tool", \
                f"Should not return generic 'Error calling tool' message. Got: {error_message}"

            # Error should be specific to the update operation
            assert len(error_message) > 15, f"Error message should be descriptive, got: {error_message}"
            assert any(keyword in error_message.lower() for keyword in ["update", "issue", "field", "permission"]), \
                f"Error should contain update-specific context, got: {error_message}"
        else:
            # If it succeeds, that's good - means the issue is fixed
            assert "result" in result

    @skip_if_no_real_api("Real API testing not configured")
    async def test_comment_management_fails_generically(self, resource_adapter, config, factory):
        """
        Test QA Issue: Comment management fails with generic errors

        QA report states: "Comment Management" fails with generic errors.
        """
        # Create a test issue first for adding comments
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "Issue for Comment Test",
                "issue_type": "Task",
                "description": "Issue for testing comment functionality"
            }
        )

        # Create the issue to get an issue key
        create_result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        create_result = json.loads(create_result_json)
        if not create_result["success"]:
            pytest.skip(f"Cannot create test issue for comment test: {create_result.get('error', 'Unknown error')}")

        issue_key = create_result["result"]["key"] if "result" in create_result and "key" in create_result["result"] else None
        if not issue_key:
            pytest.skip("Cannot extract issue key from create result")

        # Track for cleanup
        factory.track_resource(issue_key, TestResource.JIRA_ISSUE)

        # Test adding a comment (QA report says this fails)
        result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="comment",
            operation="add",
            identifier=issue_key,
            data={
                "body": "QA Test Comment - Testing comment addition functionality"
            }
        )

        result = json.loads(result_json)

        # Should NOT return generic error messages
        if not result["success"]:
            error_message = result.get("error", "")
            assert error_message != "Error calling tool", \
                f"Should not return generic 'Error calling tool' message. Got: {error_message}"

            # Error should be specific to comment operations
            assert len(error_message) > 15, f"Error message should be descriptive, got: {error_message}"
            assert any(keyword in error_message.lower() for keyword in ["comment", "add", "body", "permission"]), \
                f"Error should contain comment-specific context, got: {error_message}"
        else:
            # If it succeeds, that's good - means the issue is fixed
            assert "result" in result

    @skip_if_no_real_api("Real API testing not configured")
    async def test_resource_manager_error_handling_quality(self, resource_adapter, config, factory):
        """
        Test that ResourceManager provides informative error messages, not generic ones.

        QA report highlights poor error handling that makes debugging impossible.
        """
        # Test with missing required field to trigger error
        result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data={
                "summary": "Test Issue",
                # Missing project_key and issue_type - this should trigger a validation error
            }
        )

        result = json.loads(result_json)

        # Should fail but with informative error
        assert result["success"] is False
        error_message = result.get("error", "")

        # Should NOT be generic
        generic_errors = ["Error calling tool", "An error occurred", "Failed", "Error"]
        assert error_message not in generic_errors, \
            f"Error should not be generic. Got: {error_message}"

        # Should be informative
        assert len(error_message) > 10, f"Error should be descriptive, got: {error_message}"

        # Should contain relevant context about what's missing
        error_lower = error_message.lower()
        assert any(keyword in error_lower for keyword in ["field", "required", "project", "missing", "issue_type"]), \
            f"Error should contain specific context about what failed, got: {error_message}"

    @skip_if_no_real_api("Real API testing not configured")
    async def test_resource_manager_vs_batch_processor_consistency(self, resource_adapter, config, factory):
        """
        Test consistency between ResourceManager and BatchProcessor error handling.

        QA report notes that BatchProcessor works well but ResourceManager fails.
        They should have consistent error handling patterns.
        """
        # Create test issue data
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "QA Consistency Test",
                "issue_type": "Task"
            }
        )

        # Test the same operation that works in batch but fails individually
        individual_result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        individual_result = json.loads(individual_result_json)

        # ResourceManager should work as well as BatchProcessor
        # (QA report shows BatchProcessor works but ResourceManager fails)
        if not individual_result["success"]:
            error_message = individual_result.get("error", "")

            # Should not be a generic failure when the same operation works in batch
            assert "Error calling tool" not in error_message, \
                f"ResourceManager should work as well as BatchProcessor. Got error: {error_message}"

            # If it fails, should be for a specific, addressable reason
            assert len(error_message) > 20, \
                f"If ResourceManager fails, it should provide specific feedback like BatchProcessor does. Got: {error_message}"
        else:
            # If it succeeds, track for cleanup
            if "result" in individual_result and isinstance(individual_result["result"], dict) and "key" in individual_result["result"]:
                factory.track_resource(individual_result["result"]["key"], TestResource.JIRA_ISSUE)

    @skip_if_no_real_api("Real API testing not configured")
    async def test_crud_operations_completeness(self, resource_adapter, config, factory):
        """
        Test that all CRUD operations work properly for issues.

        QA report shows inconsistent CRUD operation support.
        """
        # Create test issue data for creation
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "CRUD Test",
                "issue_type": "Task"
            }
        )

        created_issue_key = None

        # Test CREATE operation
        create_result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        create_result = json.loads(create_result_json)
        if not create_result["success"]:
            error_message = create_result.get("error", "")
            assert error_message != "Error calling tool", \
                f"CRUD operation 'create' should not fail with generic error. Got: {error_message}"
        else:
            # Extract issue key for subsequent operations
            if "result" in create_result and isinstance(create_result["result"], dict) and "key" in create_result["result"]:
                created_issue_key = create_result["result"]["key"]
                factory.track_resource(created_issue_key, TestResource.JIRA_ISSUE)

        # Test GET operation if we have an issue key
        if created_issue_key:
            get_result_json = await resource_adapter.execute_operation(
                service="jira",
                resource="issue",
                operation="get",
                identifier=created_issue_key
            )

            get_result = json.loads(get_result_json)
            if not get_result["success"]:
                error_message = get_result.get("error", "")
                assert error_message != "Error calling tool", \
                    f"CRUD operation 'get' should not fail with generic error. Got: {error_message}"

            # Test UPDATE operation
            update_result_json = await resource_adapter.execute_operation(
                service="jira",
                resource="issue",
                operation="update",
                identifier=created_issue_key,
                data={"summary": "Updated CRUD Test"}
            )

            update_result = json.loads(update_result_json)
            if not update_result["success"]:
                error_message = update_result.get("error", "")
                assert error_message != "Error calling tool", \
                    f"CRUD operation 'update' should not fail with generic error. Got: {error_message}"