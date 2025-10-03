"""
Tests that replicate the Workflow Engine failures from the QA Report.

These tests are designed to FAIL initially, proving the issues exist,
then pass after the issues are fixed.

QA Report Issues Tested:
1. Transition dry run passes but execution fails
2. get_statuses returns "STATUS_LIST_NOT_SUPPORTED"
3. All actual transition attempts fail while discovery works
4. Inconsistency between validation and execution
"""

import json
import pytest
import logging

from .config import skip_if_no_real_api, get_test_config
from .test_adapters import WorkflowEngineTestAdapter, TestJiraFetcher, TestConfluenceFetcher
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
def workflow_adapter(jira_fetcher, confluence_fetcher):
    """Get WorkflowEngineTestAdapter instance."""
    return WorkflowEngineTestAdapter(jira_fetcher, confluence_fetcher)


@pytest.mark.qa_report
@pytest.mark.integration
@pytest.mark.real_api
class TestQAReportWorkflowFailures:
    """Tests that expose the workflow engine failures from the QA report."""

    @skip_if_no_real_api("Real API testing not configured")
    async def test_transition_dry_run_passes_but_execution_fails(self, workflow_adapter, factory, config):
        """
        Test QA Issue: Transition dry run passes but execution fails

        QA report states: "Dry Run Validation: Transition validation passes"
        but "Transition Execution: All actual transition attempts fail"

        This inconsistency suggests the dry run validation doesn't match the actual execution logic.
        """
        # Create a test issue first for transitioning
        test_issue_data = factory.create_resource(
            TestResource.JIRA_ISSUE,
            data={
                "project_key": config.jira.project_key,
                "summary": "Workflow Test Issue - Dry Run vs Execution",
                "issue_type": "Task",
                "description": "Issue for testing workflow transition consistency"
            }
        )

        # Create the issue
        from .test_adapters import ResourceManagerTestAdapter
        resource_adapter = ResourceManagerTestAdapter(workflow_adapter.jira_fetcher, workflow_adapter.confluence_fetcher)

        create_result_json = await resource_adapter.execute_operation(
            service="jira",
            resource="issue",
            operation="create",
            data=test_issue_data.to_dict()
        )

        create_result = json.loads(create_result_json)
        if not create_result["success"]:
            pytest.skip(f"Cannot create test issue for workflow test: {create_result.get('error', 'Unknown error')}")

        issue_key = create_result["result"]["key"] if "result" in create_result and "key" in create_result["result"] else None
        if not issue_key:
            pytest.skip("Cannot extract issue key from create result")

        # Track for cleanup
        factory.track_resource(issue_key, TestResource.JIRA_ISSUE)

        # First test dry run (QA report says this passes)
        dry_run_result_json = await workflow_adapter.execute_workflow_operation(
            operation="transition",
            issue_key=issue_key,
            transition_name="Done",  # Common transition
            dry_run=True
        )

        dry_run_result = json.loads(dry_run_result_json)

        # Now test actual execution (QA report says this fails)
        execution_result_json = await workflow_adapter.execute_workflow_operation(
            operation="transition",
            issue_key=issue_key,
            transition_name="Done",
            dry_run=False
        )

        execution_result = json.loads(execution_result_json)

        # Execution should NOT fail if dry run passes
        # This tests the consistency between validation and execution
        if dry_run_result["success"] and not execution_result["success"]:
            error_message = execution_result.get("error", "")
            pytest.fail(
                f"Execution failed while dry run passed - this indicates inconsistent validation logic. "
                f"Dry run result: {dry_run_result}, Execution error: {error_message}"
            )

        # Both should have the same success status for consistency
        assert dry_run_result["success"] == execution_result["success"], \
            f"Dry run and execution should have consistent results. Dry run: {dry_run_result['success']}, Execution: {execution_result['success']}"

        logger.info(f"✅ Workflow dry run and execution consistency verified")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_get_statuses_not_supported_error(self, workflow_adapter, config):
        """
        Test QA Issue: get_statuses returns "STATUS_LIST_NOT_SUPPORTED"

        QA report states: "Status Queries: `get_statuses` returns `STATUS_LIST_NOT_SUPPORTED`"

        This operation should be supported and return actual status information.
        """
        # Test get_statuses operation (QA report says returns STATUS_LIST_NOT_SUPPORTED)
        result_json = await workflow_adapter.execute_workflow_operation(
            operation="get_statuses",
            project_key=config.jira.project_key
        )

            result = json.loads(result_json)

            # Should NOT return STATUS_LIST_NOT_SUPPORTED
            if result["success"]:
                assert "STATUS_LIST_NOT_SUPPORTED" not in str(result), \
                    f"get_statuses should not return STATUS_LIST_NOT_SUPPORTED but did: {result}"

                # Should return actual status data
                assert "statuses" in result or "result" in result or "results" in result, \
                    f"get_statuses should return status information: {result}"
            else:
                error_message = result.get("error", "")
                assert "STATUS_LIST_NOT_SUPPORTED" not in error_message, \
                    f"get_statuses should not return STATUS_LIST_NOT_SUPPORTED error: {error_message}"

                # If it fails, should fail for a legitimate reason, not "not supported"
                assert "not supported" not in error_message.lower(), \
                    f"get_statuses should be supported operation: {error_message}"

    @skip_if_no_real_api("Real API testing not configured")
    async def test_transition_discovery_vs_execution_consistency(self, workflow_adapter, factory, config):
        """
        Test consistency between transition discovery and execution.

        QA report shows: "Transition Discovery: Successfully retrieved available transitions"
        but "Transition Execution: All actual transition attempts fail"

        If we can discover transitions, we should be able to execute them.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            workflow_engine = WorkflowEngine(dry_run=False)

            # First, get available transitions (QA report says this works)
            discovery_result_json = await workflow_engine.execute_workflow_operation(
                ctx=get_tool_context(server),
                operation="get_transitions",
                issue_key="FTEST-1492"  # From QA report
            )

            discovery_result = json.loads(discovery_result_json)

            # Discovery should work (according to QA report)
            assert discovery_result["success"] is True, \
                f"Transition discovery should work according to QA report: {discovery_result.get('error', 'Unknown error')}"

            # Should return available transitions
            assert "transitions" in discovery_result or "result" in discovery_result or "results" in discovery_result, \
                f"Discovery should return transition information: {discovery_result}"

            # Extract available transitions
            transitions_data = discovery_result.get("result", discovery_result.get("transitions", discovery_result.get("results", [])))
            assert len(transitions_data) > 0, f"Should find available transitions: {discovery_result}"

            # QA report shows these transitions should be available:
            # [{"id": "21", "name": "To Do"}, {"id": "41", "name": "Done"}, {"id": "2", "name": "Start Work"}]

            # Try to execute one of the discovered transitions
            if isinstance(transitions_data, list) and len(transitions_data) > 0:
                first_transition = transitions_data[0]
                transition_name = first_transition.get("name", "Done")  # Default from QA report

                execution_result_json = await workflow_engine.execute_workflow_operation(
                    ctx=get_tool_context(server),
                    operation="transition",
                    issue_key="FTEST-1492",
                    transition_name=transition_name,
                    dry_run=False
                )

                execution_result = json.loads(execution_result_json)

                # If we can discover the transition, we should be able to execute it
                if not execution_result["success"]:
                    error_message = execution_result.get("error", "")
                    pytest.fail(
                        f"If transition '{transition_name}' can be discovered, it should be executable. "
                        f"Discovery result: {discovery_result}, Execution error: {error_message}"
                    )

    @skip_if_no_real_api("Real API testing not configured")
    async def test_workflow_operations_are_implemented(self, workflow_adapter, config):
        """
        Test that all workflow operations mentioned in QA report are properly implemented.

        QA report tests these operations: get_transitions, transition, get_statuses
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            workflow_engine = WorkflowEngine(dry_run=False)

            # Test all workflow operations
            workflow_operations = [
                ("get_transitions", {"issue_key": "FTEST-1492"}),
                ("get_statuses", {"project_key": "FTEST"}),
                # Transition operation tested separately due to complexity
            ]

            for operation, params in workflow_operations:
                result_json = await workflow_engine.execute_workflow_operation(
                    ctx=get_tool_context(server),
                    operation=operation,
                    **params
                )

                result = json.loads(result_json)

                # Should not fail with "not supported" or "not implemented"
                if not result["success"]:
                    error_message = result.get("error", "")
                    unsupported_indicators = ["not supported", "not implemented", "STATUS_LIST_NOT_SUPPORTED"]

                    for indicator in unsupported_indicators:
                        assert indicator not in error_message, \
                            f"Operation '{operation}' should be implemented, not unsupported: {error_message}"

                # Should return appropriate operation result
                assert result.get("operation") == operation or operation in str(result), \
                    f"Result should indicate operation type for {operation}: {result}"

    @skip_if_no_real_api("Real API testing not configured")
    async def test_transition_parameter_validation_consistency(self, workflow_adapter, factory, config):
        """
        Test that transition parameter validation is consistent between dry run and execution.

        QA report suggests validation issues between dry run and actual execution.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            mock_jira_client = MockClientFactory.create_jira_client()
            mock_get_jira.return_value = mock_jira_client

            workflow_engine = WorkflowEngine(dry_run=False)

            # Test various parameter combinations
            test_cases = [
                {"issue_key": "FTEST-1492", "transition_name": "Done"},
                {"issue_key": "FTEST-1492", "transition_id": "41"},  # From QA report data
                {"issue_key": "FTEST-1492", "transition_name": "In Progress", "fields": {"assignee": "test"}},
            ]

            for test_params in test_cases:
                # Test dry run validation
                dry_run_result_json = await workflow_engine.execute_workflow_operation(
                    ctx=get_tool_context(server),
                    operation="transition",
                    dry_run=True,
                    **test_params
                )

                dry_run_result = json.loads(dry_run_result_json)

                # Test actual execution
                execution_result_json = await workflow_engine.execute_workflow_operation(
                    ctx=get_tool_context(server),
                    operation="transition",
                    dry_run=False,
                    **test_params
                )

                execution_result = json.loads(execution_result_json)

                # Validation consistency check
                if dry_run_result["success"] != execution_result["success"]:
                    # If results differ, the validation logic is inconsistent
                    pytest.fail(
                        f"Validation inconsistency for params {test_params}: "
                        f"Dry run: {dry_run_result['success']}, "
                        f"Execution: {execution_result['success']}. "
                        f"Dry run result: {dry_run_result}, "
                        f"Execution result: {execution_result}"
                    )

    @skip_if_no_real_api("Real API testing not configured")
    async def test_workflow_error_messages_are_informative(self, workflow_adapter):
        """
        Test that workflow error messages are informative and actionable.

        QA report suggests poor error handling across the system.
        """
        server, app_context = realistic_server_setup

        with patch('src.mcp_atlassian.servers.dependencies.get_jira_fetcher') as mock_get_jira:
            # Force error conditions
            mock_jira_client = MagicMock()
            mock_jira_client.get_transitions.side_effect = Exception("Transition not found")
            mock_get_jira.return_value = mock_jira_client

            workflow_engine = WorkflowEngine(dry_run=False)

            # Test with invalid transition to trigger error
            result_json = await workflow_engine.execute_workflow_operation(
                ctx=get_tool_context(server),
                operation="transition",
                issue_key="INVALID-ISSUE",
                transition_name="NonexistentTransition"
            )

            result = json.loads(result_json)

            # Should fail with informative error
            assert result["success"] is False
            error_message = result.get("error", "")

            # Should not be generic
            generic_errors = ["Error calling tool", "An error occurred", "Failed"]
            assert error_message not in generic_errors, \
                f"Workflow error should be specific, not generic. Got: {error_message}"

            # Should be informative
            assert len(error_message) > 15, f"Error should be descriptive: {error_message}"

            # Should contain workflow-related context
            workflow_keywords = ["transition", "workflow", "issue", "status"]
            assert any(keyword in error_message.lower() for keyword in workflow_keywords), \
                f"Error should contain workflow context: {error_message}"