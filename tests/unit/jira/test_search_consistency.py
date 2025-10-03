"""Tests for Jira search operations with consistency features."""

from unittest.mock import Mock, patch

import pytest

from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.jira.search import SearchMixin
from src.mcp_atlassian.models.jira import JiraSearchResult


class MockJiraClient:
    """Mock Jira client for testing."""

    def __init__(self, config):
        self.config = config
        self.jira = Mock()

    def markdown_to_jira(self, text, return_raw_adf=False):
        return text


class MockSearchMixin(SearchMixin, MockJiraClient):
    """Mock SearchMixin for testing."""

    def __init__(self, config):
        super().__init__(config)

    def get_issue(self, issue_key: str, fields: str | None = None, expand: str | None = None):
        """Mock implementation of get_issue method."""
        return {"key": issue_key, "summary": f"Mock issue {issue_key}"}


class TestSearchConsistencyFeatures:
    """Test search operations with consistency features."""

    @pytest.fixture
    def cloud_config(self):
        """Create a Cloud configuration."""
        return JiraConfig(
            url="https://test.atlassian.net",
            auth_type="basic",
            username="test@example.com",
            api_token="token123",
            consistency_strategy="reconcile",
            consistency_max_retries=3,
            consistency_timeout=10.0,
        )

    @pytest.fixture
    def server_config(self):
        """Create a Server configuration."""
        return JiraConfig(
            url="https://jira.company.com",
            auth_type="basic",
            username="test",
            api_token="token123",
            consistency_strategy="hybrid",
        )

    @pytest.fixture
    def search_mixin_cloud(self, cloud_config):
        """Create SearchMixin with Cloud config."""
        return MockSearchMixin(cloud_config)

    @pytest.fixture
    def search_mixin_server(self, server_config):
        """Create SearchMixin with Server config."""
        return MockSearchMixin(server_config)

    def test_search_issues_with_reconcile_issues_parameter(self, search_mixin_cloud):
        """Test that reconcile_issues parameter is passed through correctly."""
        # Mock the adapter's enhanced_jql_get_list_of_tickets method
        mock_issues = [{"key": "TEST-123", "summary": "Test issue"}]
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets = Mock(return_value=mock_issues)
        search_mixin_cloud.jira.get = Mock(return_value={"total": 1})

        # Call search_issues with reconcile_issues parameter
        result = search_mixin_cloud.search_issues(
            jql="project = TEST",
            reconcile_issues=["TEST-123", "TEST-124"]
        )

        # Verify the reconcile_issues parameter was passed through
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.assert_called_once()
        call_kwargs = search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") == ["TEST-123", "TEST-124"]

        # Verify result structure
        assert isinstance(result, JiraSearchResult)

    def test_search_issues_server_instance_with_reconcile_issues(self, search_mixin_server):
        """Test reconcile_issues parameter on Server/DC instance."""
        # Mock the adapter's jql method
        mock_response = {
            "issues": [{"key": "TEST-123"}],
            "total": 1,
            "startAt": 0,
            "maxResults": 50
        }
        search_mixin_server.jira.jql = Mock(return_value=mock_response)

        # Call search_issues with reconcile_issues parameter
        result = search_mixin_server.search_issues(
            jql="project = TEST",
            reconcile_issues=["TEST-123"]
        )

        # Verify the reconcile_issues parameter was passed through
        search_mixin_server.jira.jql.assert_called_once()
        call_kwargs = search_mixin_server.jira.jql.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") == ["TEST-123"]

        # Verify result structure
        assert isinstance(result, JiraSearchResult)

    def test_search_issues_without_reconcile_issues(self, search_mixin_cloud):
        """Test search without reconcile_issues parameter."""
        mock_issues = [{"key": "TEST-123"}]
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets = Mock(return_value=mock_issues)
        search_mixin_cloud.jira.get = Mock(return_value={"total": 1})

        result = search_mixin_cloud.search_issues(jql="project = TEST")

        # Verify reconcile_issues is None when not provided
        call_kwargs = search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") is None

    @patch('src.mcp_atlassian.jira.search.IndexingDelayMessageHelper')
    def test_empty_search_results_warning_cloud(self, mock_message_helper, search_mixin_cloud):
        """Test warning message for empty search results on Cloud."""
        # Mock empty search results
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets = Mock(return_value=[])
        search_mixin_cloud.jira.get = Mock(return_value={"total": 0})

        mock_message_helper.create_general_delay_warning.return_value = "Test warning message"

        with patch('src.mcp_atlassian.jira.search.logger') as mock_logger:
            result = search_mixin_cloud.search_issues(jql="project = TEST")

            # Verify warning was logged
            mock_logger.info.assert_called()
            log_message = mock_logger.info.call_args[0][0]
            assert "Search returned 0 results" in log_message

            # Verify message helper was called
            mock_message_helper.create_general_delay_warning.assert_called_with(
                is_cloud=True,
                operation="search"
            )

        assert result.total == 0

    def test_no_warning_for_server_instance(self, search_mixin_server):
        """Test that no indexing delay warning is shown for Server/DC instances."""
        mock_response = {
            "issues": [],
            "total": 0,
            "startAt": 0,
            "maxResults": 50
        }
        search_mixin_server.jira.jql = Mock(return_value=mock_response)

        with patch('src.mcp_atlassian.jira.search.logger') as mock_logger:
            result = search_mixin_server.search_issues(jql="project = TEST")

            # Should not log indexing delay warnings for server instances
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "Search returned 0 results" in log_message

        assert result.total == 0

    def test_projects_filter_with_reconcile_issues(self, search_mixin_cloud):
        """Test that projects filter works correctly with reconcile_issues parameter."""
        search_mixin_cloud.config.projects_filter = "PROJ1,PROJ2"
        mock_issues = []
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets = Mock(return_value=mock_issues)
        search_mixin_cloud.jira.get = Mock(return_value={"total": 0})

        search_mixin_cloud.search_issues(
            jql="status = Open",
            reconcile_issues=["PROJ1-123"]
        )

        # Verify the JQL was modified to include project filter
        call_args = search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.call_args[0]
        jql_used = call_args[0]
        assert 'project IN ("PROJ1", "PROJ2")' in jql_used
        assert "status = Open" in jql_used

        # Verify reconcile_issues parameter was preserved
        call_kwargs = search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") == ["PROJ1-123"]

    def test_search_with_all_parameters(self, search_mixin_cloud):
        """Test search with all parameters including reconcile_issues."""
        mock_issues = [{"key": "TEST-123"}]
        search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets = Mock(return_value=mock_issues)
        search_mixin_cloud.jira.get = Mock(return_value={"total": 1})

        result = search_mixin_cloud.search_issues(
            jql="project = TEST",
            fields=["summary", "status"],
            start=10,
            limit=25,
            expand="changelog",
            projects_filter="TEST",
            reconcile_issues=["TEST-123", "TEST-124"]
        )

        # Verify all parameters were passed correctly
        call_kwargs = search_mixin_cloud.jira.enhanced_jql_get_list_of_tickets.call_args.kwargs
        assert call_kwargs.get("fields") == "summary,status"
        assert call_kwargs.get("limit") == 25
        assert call_kwargs.get("expand") == "changelog"
        assert call_kwargs.get("reconcile_issues") == ["TEST-123", "TEST-124"]

        assert isinstance(result, JiraSearchResult)
        assert result.total == 1


class TestAdapterReconcileIssuesIntegration:
    """Test that reconcile_issues parameter works through the adapter layer."""

    def test_jira_adapter_jql_method_with_reconcile_issues(self):
        """Test that JiraAdapter.jql method accepts reconcile_issues parameter."""
        from src.mcp_atlassian.rest.jira_adapter import JiraAdapter

        # Create mock client
        mock_client = Mock()
        mock_client.search_issues.return_value = {"issues": [], "total": 0}

        # Create adapter
        adapter = JiraAdapter(
            url="https://test.atlassian.net",
            username="test",
            password="token"
        )
        adapter.client = mock_client

        # Call jql method with reconcile_issues
        adapter.jql(
            jql="project = TEST",
            reconcile_issues=["TEST-123"]
        )

        # Verify parameter was passed to underlying client
        mock_client.search_issues.assert_called_once()
        call_kwargs = mock_client.search_issues.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") == ["TEST-123"]

    def test_jira_adapter_enhanced_jql_with_reconcile_issues(self):
        """Test that enhanced_jql_get_list_of_tickets accepts reconcile_issues parameter."""
        from src.mcp_atlassian.rest.jira_adapter import JiraAdapter

        # Create mock client
        mock_client = Mock()
        mock_client.search_issues.return_value = {"issues": [{"key": "TEST-123"}], "total": 1}

        # Create adapter
        adapter = JiraAdapter(
            url="https://test.atlassian.net",
            username="test",
            password="token"
        )
        adapter.client = mock_client

        # Call enhanced method with reconcile_issues
        result = adapter.enhanced_jql_get_list_of_tickets(
            jql="project = TEST",
            reconcile_issues=["TEST-123"]
        )

        # Verify parameter was passed to underlying client
        mock_client.search_issues.assert_called_once()
        call_kwargs = mock_client.search_issues.call_args.kwargs
        assert call_kwargs.get("reconcile_issues") == ["TEST-123"]

        # Verify result format
        assert result == [{"key": "TEST-123"}]


class TestJiraV3ClientReconcileIssues:
    """Test that JiraV3Client properly handles reconcile_issues parameter."""

    def test_jira_v3_client_search_issues_with_reconcile_issues(self):
        """Test that JiraV3Client includes reconcile_issues in API request."""
        from src.mcp_atlassian.rest.jira_v3 import JiraV3Client

        # Create client with mock session
        client = JiraV3Client(
            base_url="https://test.atlassian.net",
            auth_type="basic",
            username="test",
            password="token"
        )

        # Mock the post method
        mock_response = {"issues": [], "total": 0}
        client.post = Mock(return_value=mock_response)

        # Call search_issues with reconcile_issues
        result = client.search_issues(
            jql="project = TEST",
            reconcile_issues=["TEST-123", "TEST-124"]
        )

        # Verify the API call included reconcileIssues in the JSON payload
        client.post.assert_called_once_with("/rest/api/3/search", json_data={
            "jql": "project = TEST",
            "startAt": 0,
            "maxResults": 50,
            "fieldsByKeys": False,
            "validateQuery": True,
            "reconcileIssues": ["TEST-123", "TEST-124"]
        })

        assert result == mock_response

    def test_jira_v3_client_search_issues_without_reconcile_issues(self):
        """Test that reconcileIssues is not included when parameter is None."""
        from src.mcp_atlassian.rest.jira_v3 import JiraV3Client

        # Create client with mock session
        client = JiraV3Client(
            base_url="https://test.atlassian.net",
            auth_type="basic",
            username="test",
            password="token"
        )

        # Mock the post method
        mock_response = {"issues": [], "total": 0}
        client.post = Mock(return_value=mock_response)

        # Call search_issues without reconcile_issues
        result = client.search_issues(jql="project = TEST")

        # Verify reconcileIssues is not in the payload
        client.post.assert_called_once_with("/rest/api/3/search", json_data={
            "jql": "project = TEST",
            "startAt": 0,
            "maxResults": 50,
            "fieldsByKeys": False,
            "validateQuery": True,
        })

        assert result == mock_response