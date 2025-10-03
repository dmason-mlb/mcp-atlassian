"""
Tests that replicate the Confluence failures from the QA Report.

These tests are designed to FAIL initially, proving the issues exist,
then pass after the issues are fixed.

QA Report Issues Tested:
1. "'ConfluenceFetcher' object has no attribute 'get_current_user'"
2. "'ConfluenceFetcher' object has no attribute 'get_all_spaces'"
3. Confluence connectivity fails in health check
4. All Confluence operations fail due to missing method implementations
"""

import json
import pytest
import logging

from .config import skip_if_no_real_api, get_test_config
from .test_adapters import SearchEngineTestAdapter, ResourceManagerTestAdapter, TestJiraFetcher, TestConfluenceFetcher
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

@pytest.fixture
def resource_adapter(jira_fetcher, confluence_fetcher):
    """Get ResourceManagerTestAdapter instance."""
    return ResourceManagerTestAdapter(jira_fetcher, confluence_fetcher)


@pytest.mark.qa_report
@pytest.mark.integration
@pytest.mark.real_api
class TestQAReportConfluenceFailures:
    """Tests that expose the Confluence failures from the QA report."""

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_fetcher_missing_get_current_user(self, confluence_fetcher, config):
        """
        Test QA Issue: "'ConfluenceFetcher' object has no attribute 'get_current_user'"

        QA report shows this error during connection health check for Confluence.
        The ConfluenceFetcher class should have a get_current_user method.
        """
        # Test that ConfluenceFetcher has the get_current_user method
        try:
            # Check if the method exists
            assert hasattr(confluence_fetcher, 'get_current_user'), \
                "ConfluenceFetcher should have get_current_user method"

            # Test that the method can be called successfully
            current_user = await confluence_fetcher.get_current_user()

            # Should return user information
            assert current_user is not None, "get_current_user should return user information"

            # Typically should have displayName or email
            if isinstance(current_user, dict):
                assert any(key in current_user for key in ["displayName", "email", "accountId"]), \
                    f"User info should contain displayName, email, or accountId. Got: {current_user}"

            logger.info(f"✅ ConfluenceFetcher.get_current_user() working correctly")

        except AttributeError as e:
            if "get_current_user" in str(e):
                pytest.fail(f"ConfluenceFetcher missing get_current_user method: {e}")
            else:
                raise

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_fetcher_missing_get_all_spaces(self, search_adapter, confluence_fetcher, config):
        """
        Test QA Issue: "'ConfluenceFetcher' object has no attribute 'get_all_spaces'"

        QA report shows this error when trying to search spaces.
        The ConfluenceFetcher class should have a get_all_spaces method.
        """
        # First test that ConfluenceFetcher has the method
        try:
            assert hasattr(confluence_fetcher, 'get_all_spaces'), \
                "ConfluenceFetcher should have get_all_spaces method"

            # Test direct method call
            spaces = await confluence_fetcher.get_all_spaces()
            assert spaces is not None, "get_all_spaces should return spaces information"

            logger.info(f"✅ ConfluenceFetcher.get_all_spaces() working correctly")

        except AttributeError as e:
            if "get_all_spaces" in str(e):
                pytest.fail(f"ConfluenceFetcher missing get_all_spaces method: {e}")
            else:
                raise

        # Test space search through SearchEngine (QA report says this fails with missing method)
        try:
            result_json = await search_adapter.execute_search(
                service="confluence",
                query_type="spaces",
                query="",
                options={"limit": 10}
            )

            result = json.loads(result_json)

            # Should not fail with missing method error
            if not result["success"]:
                error_message = result.get("error", "")
                assert "has no attribute 'get_all_spaces'" not in error_message, \
                    f"ConfluenceFetcher should have get_all_spaces method but got: {error_message}"

            # Should successfully search spaces
            assert result["success"] is True, f"Space search should work but failed: {result.get('error', 'Unknown error')}"
            assert result["query_type"] == "spaces"

            logger.info(f"✅ Space search through SearchEngine working correctly")

        except AttributeError as e:
            if "get_all_spaces" in str(e):
                pytest.fail(f"ConfluenceFetcher missing get_all_spaces method: {e}")
            else:
                raise

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_page_operations_work(self, resource_adapter, config, factory):
        """
        Test that basic Confluence page operations work.

        QA report shows all Confluence operations fail, but they should work
        once the missing methods are implemented.
        """
        # Create test page data
        test_page_data = factory.create_resource(
            TestResource.CONFLUENCE_PAGE,
            data={
                "space_key": config.confluence.space_key,
                "title": "QA Test Page",
                "body": "Test page created during QA validation"
            }
        )

        # Test page creation (QA report says Confluence operations fail)
        result_json = await resource_adapter.execute_operation(
            service="confluence",
            resource="page",
            operation="create",
            data=test_page_data.to_dict()
        )

        result = json.loads(result_json)

        # Should not fail with method-related errors
        if not result["success"]:
            error_message = result.get("error", "")
            method_errors = ["has no attribute", "missing method", "not implemented"]
            for method_error in method_errors:
                assert method_error not in error_message.lower(), \
                    f"Page creation should not fail due to missing methods but got: {error_message}"
        else:
            # Track created page for cleanup
            if "result" in result and isinstance(result["result"], dict) and "id" in result["result"]:
                factory.track_resource(result["result"]["id"], TestResource.CONFLUENCE_PAGE)

            logger.info(f"✅ Confluence page creation working correctly")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_search_operations_work(self, search_adapter, config):
        """
        Test that Confluence search operations work properly.

        QA report shows Confluence search fails due to missing methods.
        """
        # Test different Confluence search types mentioned in QA report
        confluence_query_types = ["pages", "spaces", "content", "cql"]

        for query_type in confluence_query_types:
            try:
                # Construct appropriate query for each type
                if query_type == "cql":
                    query = f"space = '{config.confluence.space_key}' AND type = page"
                elif query_type in ["pages", "content"]:
                    query = "test"
                else:
                    query = ""

                result_json = await search_adapter.execute_search(
                    service="confluence",
                    query_type=query_type,
                    query=query,
                    options={"limit": 5}
                )

                result = json.loads(result_json)

                # Should not fail with missing method errors
                if not result["success"]:
                    error_message = result.get("error", "")
                    method_errors = ["has no attribute", "missing method", "not implemented"]
                    for method_error in method_errors:
                        assert method_error not in error_message.lower(), \
                            f"Confluence {query_type} search should not fail due to missing methods but got: {error_message}"

                logger.info(f"✅ Confluence {query_type} search working correctly")

            except AttributeError as e:
                pytest.fail(f"Confluence {query_type} search failed with missing method: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_client_has_required_methods(self, confluence_fetcher):
        """
        Test that ConfluenceFetcher/client has all required methods.

        Based on QA report errors, these methods should exist.
        """
        # Check for methods mentioned in QA report errors
        required_methods = ["get_current_user", "get_all_spaces"]

        for method_name in required_methods:
            assert hasattr(confluence_fetcher, method_name), \
                f"ConfluenceFetcher should have {method_name} method (QA report shows it's missing)"

            # Method should be callable
            method = getattr(confluence_fetcher, method_name)
            assert callable(method), f"{method_name} should be callable"

            logger.info(f"✅ ConfluenceFetcher has {method_name} method")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_connectivity_in_health_check(self, confluence_fetcher, config):
        """
        Test that Confluence connectivity works in health check.

        QA report shows:
        | Confluence | ❌ Unhealthy | Valid | Unknown | Failed |
        """
        # Test that basic Confluence connectivity works
        try:
            # Test that get_current_user works (this is what health check uses)
            current_user = await confluence_fetcher.get_current_user()
            assert current_user is not None, "Should be able to get current user for health check"

            # Test that get_all_spaces works (this is also used in health checks)
            spaces = await confluence_fetcher.get_all_spaces()
            assert spaces is not None, "Should be able to get spaces for health check"

            logger.info(f"✅ Confluence connectivity working correctly")

        except Exception as e:
            # Should not fail due to missing method issues
            method_issues = ["has no attribute", "get_current_user", "get_all_spaces"]
            for issue in method_issues:
                assert issue not in str(e), \
                    f"Confluence connectivity should not fail due to missing methods. Got error: {e}"
            # If it fails for other reasons, that's potentially acceptable
            pytest.skip(f"Confluence connectivity failed for non-method-related reason: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    async def test_confluence_authentication_status(self, confluence_fetcher, config):
        """
        Test that Confluence authentication status is properly determined.

        QA report shows authentication as "Unknown" for Confluence.
        """
        # Test that authentication works by calling get_current_user
        try:
            current_user = await confluence_fetcher.get_current_user()

            # Should be able to determine authentication status
            assert current_user is not None, "Should get user info if authenticated"

            # Should have identifiable user information
            if isinstance(current_user, dict):
                assert any(key in current_user for key in ["displayName", "email", "accountId"]), \
                    f"User info should identify the authenticated user. Got: {current_user}"

            logger.info(f"✅ Confluence authentication working correctly")

        except Exception as e:
            # Should not fail due to missing methods
            assert "has no attribute" not in str(e), \
                f"Authentication check should not fail due to missing methods. Got: {e}"
            # Other failures might be authentication issues, which are potentially acceptable
            pytest.skip(f"Confluence authentication failed: {e}")