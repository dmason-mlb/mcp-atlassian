"""
Tests that replicate the Search Engine failures from the QA Report.

These tests are designed to FAIL initially, proving the issues exist,
then pass after the issues are fixed.

QA Report Issues Tested:
1. JQL search fails: "Query type 'jql' is not supported"
2. Issues search fails: "SearchMixin.search_issues() got an unexpected keyword argument 'start_at'"
3. Projects search fails: "ProjectsMixin.get_all_projects() got an unexpected keyword argument 'expand'"
"""

import json
import pytest
import logging

from .config import skip_if_no_real_api, get_test_config
from .test_adapters import SearchEngineTestAdapter, TestJiraFetcher, TestConfluenceFetcher
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
def search_adapter(jira_fetcher, confluence_fetcher):
    """Get SearchEngineTestAdapter instance."""
    return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)


@pytest.mark.qa_report
@pytest.mark.integration
@pytest.mark.real_api
class TestQAReportSearchFailures:
    """Tests that expose the search engine failures from the QA report."""

    @skip_if_no_real_api("Real API testing not configured")
    async def test_jql_query_type_not_supported(self, search_adapter, config):
        """
        Test QA Issue: JQL search fails with "Query type 'jql' is not supported"

        According to QA report, this search should work:
        search_engine_tool(service="jira", query_type="jql", query="project = FTEST")

        But it fails with "Query type 'jql' is not supported"
        """
        try:
            # Test that JQL query type is actually supported
            result_json = await search_adapter.execute_search(
                service="jira",
                query_type="jql",  # QA report says this is not supported
                query=f"project = {config.jira.project_key} ORDER BY created DESC",
                options={"limit": 5}
            )

            result = json.loads(result_json)

            # This test should PASS - JQL should be supported
            assert result["success"] is True, f"JQL query type should be supported but failed: {result.get('error', 'Unknown error')}"
            assert result["query_type"] == "jql"
            assert "results" in result

            logger.info(f"✅ JQL search successful with {len(result.get('results', []))} results")

        except MetaToolError as e:
            if "not supported" in str(e).lower():
                pytest.fail(f"JQL query type should be supported but got error: {e}")
            else:
                # Other errors might be expected (e.g., permission issues)
                logger.warning(f"JQL search failed with non-support error: {e}")
                pytest.skip(f"JQL search failed due to configuration/permission issue: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_issues_search_start_at_parameter_mismatch(self, search_adapter, config):
        """
        Test QA Issue: Issues search fails with parameter mismatch

        According to QA report:
        "SearchMixin.search_issues() got an unexpected keyword argument 'start_at'"

        This suggests the search implementation doesn't accept standard pagination parameters.
        """
        try:
            # Test that pagination parameters work correctly
            result_json = await search_adapter.execute_search(
                service="jira",
                query_type="issues",
                query=f"project = {config.jira.project_key} ORDER BY created DESC",
                options={
                    "start_at": 0,  # QA report says this parameter causes failure
                    "limit": 5
                }
            )

            result = json.loads(result_json)

            # This test should PASS - start_at should be accepted
            assert result["success"] is True, f"Issues search with start_at parameter should work but failed: {result.get('error', 'Unknown error')}"
            assert result["query_type"] == "issues"
            assert "results" in result

            logger.info(f"✅ Issues search with pagination successful")

        except MetaToolError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Issues search should accept start_at parameter but got error: {e}")
            else:
                logger.warning(f"Issues search failed with non-parameter error: {e}")
                pytest.skip(f"Issues search failed due to configuration/permission issue: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_projects_search_expand_parameter_mismatch(self, search_adapter, config):
        """
        Test QA Issue: Projects search fails with parameter mismatch

        According to QA report:
        "ProjectsMixin.get_all_projects() got an unexpected keyword argument 'expand'"

        This suggests the projects search doesn't accept the expand parameter.
        """
        try:
            # Test that projects search accepts expand parameter
            result_json = await search_adapter.execute_search(
                service="jira",
                query_type="projects",
                query="",  # Empty query for all projects
                options={
                    "expand": "description,lead,issueTypes",  # QA report says this parameter causes failure
                    "limit": 10
                }
            )

            result = json.loads(result_json)

            # This test should PASS - expand should be accepted
            assert result["success"] is True, f"Projects search with expand parameter should work but failed: {result.get('error', 'Unknown error')}"
            assert result["query_type"] == "projects"
            assert "results" in result

            logger.info(f"✅ Projects search with expand parameter successful")

        except MetaToolError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Projects search should accept expand parameter but got error: {e}")
            else:
                logger.warning(f"Projects search failed with non-parameter error: {e}")
                pytest.skip(f"Projects search failed due to configuration/permission issue: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_search_engine_available_query_types(self, search_adapter, config):
        """
        Test that all query types mentioned in QA report are actually supported.

        QA report shows available types: issues, fields, users, projects, boards,
        sprints, versions, components, issue_types, statuses, priorities, resolutions

        But JQL is missing from this list even though it should be supported.
        """
        # Test that JQL is supported (currently fails according to QA)
        essential_query_types = [
            "jql",  # This should be supported but QA report says it's not
            "issues",
            "projects",
            "users"
        ]

        for query_type in essential_query_types:
            try:
                # Test with minimal query to see if query type is recognized
                query = f"project = {config.jira.project_key}" if query_type == "jql" else ""
                result_json = await search_adapter.execute_search(
                    service="jira",
                    query_type=query_type,
                    query=query,
                    options={"limit": 1}
                )

                result = json.loads(result_json)

                # Should not fail with "Query type not supported"
                if not result["success"] and "not supported" in result.get("error", "").lower():
                    pytest.fail(f"Query type '{query_type}' should be supported but is not: {result['error']}")

                logger.info(f"✅ Query type '{query_type}' is supported")

            except MetaToolError as e:
                # Should not fail with query type support issues
                if "not supported" in str(e).lower():
                    pytest.fail(f"Query type '{query_type}' should be supported but failed: {e}")
                else:
                    logger.warning(f"Query type '{query_type}' failed with non-support error: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_search_pagination_parameters_work(self, search_adapter, config):
        """
        Test that standard pagination parameters work across all search types.

        QA report shows parameter mismatches. Standard pagination should work.
        """
        # Test standard pagination parameters
        pagination_tests = [
            {"start_at": 0, "limit": 5},  # QA report says start_at fails
            {"limit": 10},
            {"max_results": 5}
        ]

        for params in pagination_tests:
            try:
                result_json = await search_adapter.execute_search(
                    service="jira",
                    query_type="issues",
                    query=f"project = {config.jira.project_key}",
                    options=params
                )

                result = json.loads(result_json)

                # Should not fail due to parameter issues
                if not result["success"] and "unexpected keyword argument" in result.get("error", ""):
                    pytest.fail(f"Pagination parameters {params} should be accepted but failed: {result['error']}")

                logger.info(f"✅ Pagination parameters {params} work correctly")

            except MetaToolError as e:
                if "unexpected keyword argument" in str(e):
                    pytest.fail(f"Pagination parameters {params} should be accepted but got error: {e}")
                else:
                    logger.warning(f"Pagination test failed with non-parameter error: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_search_error_messages_are_informative(self, search_adapter, config):
        """
        Test that search errors provide informative messages, not generic ones.

        QA report mentions that error messages are not helpful for debugging.
        """
        try:
            # Test with an invalid JQL query to trigger a specific error
            result_json = await search_adapter.execute_search(
                service="jira",
                query_type="jql",
                query="invalid_field = 'test' AND project = NONEXISTENT",  # This should cause a JQL error
                options={"limit": 1}
            )

            result = json.loads(result_json)

            # Check if we got an error response
            if not result["success"]:
                error_message = result.get("error", "")

                # Error should be informative, not generic
                assert error_message != "Error calling tool", "Error should not be generic 'Error calling tool'"
                assert len(error_message) > 10, f"Error should be descriptive, got: {error_message}"

                # Should include helpful context
                error_lower = error_message.lower()
                informative_keywords = ["jql", "field", "query", "syntax", "project"]
                assert any(keyword in error_lower for keyword in informative_keywords), \
                    f"Error message should contain search context but got: {error_message}"

                logger.info(f"✅ Error message is informative: {error_message[:100]}...")
            else:
                # If the query succeeded despite being intended to fail, that's also okay
                logger.info("✅ Query succeeded (no error to test message quality)")

        except MetaToolError as e:
            # If we get a MetaToolError, check that it's informative
            error_message = str(e)
            assert "Error calling tool" not in error_message, "MetaToolError should not be generic"
            assert len(error_message) > 10, f"MetaToolError should be descriptive: {error_message}"

            logger.info(f"✅ MetaToolError is informative: {error_message[:100]}...")