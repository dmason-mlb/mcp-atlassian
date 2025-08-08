"""Tests for Jira Issues mixin - Field Processing and Utility functionality."""

from unittest.mock import ANY, MagicMock

import pytest

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.issues import IssuesMixin
from mcp_atlassian.models.jira import JiraIssue


class TestIssuesFieldsMixin:
    """Tests for the IssuesMixin class - Field Processing and Utility functionality."""

    @pytest.fixture
    def issues_mixin(self, jira_fetcher: JiraFetcher) -> IssuesMixin:
        """Create an IssuesMixin instance with mocked dependencies."""
        mixin = jira_fetcher

        # Add mock methods that would be provided by other mixins
        mixin._get_account_id = MagicMock(return_value="test-account-id")
        mixin.get_available_transitions = MagicMock(
            return_value=[{"id": "10", "name": "In Progress"}]
        )
        mixin.transition_issue = MagicMock(
            return_value=JiraIssue(id="123", key="TEST-123", summary="Test Issue")
        )

        return mixin

    def test_normalize_comment_limit(self, issues_mixin: IssuesMixin):
        """Test normalizing comment limit."""
        # Test with None
        assert issues_mixin._normalize_comment_limit(None) is None

        # Test with integer
        assert issues_mixin._normalize_comment_limit(5) == 5

        # Test with "all"
        assert issues_mixin._normalize_comment_limit("all") is None

        # Test with string number
        assert issues_mixin._normalize_comment_limit("10") == 10

        # Test with invalid string
        assert issues_mixin._normalize_comment_limit("invalid") == 10

    def test_get_issue_with_custom_fields(self, issues_mixin: IssuesMixin):
        """Test get_issue with custom fields parameter."""
        # Mock the response with custom fields
        mock_issue = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue with custom field",
                "customfield_10049": "Custom value",
                "customfield_10050": {"value": "Option value"},
                "description": "Issue description",
            },
        }
        issues_mixin.jira.get_issue.return_value = mock_issue

        # Test with string format
        issue = issues_mixin.get_issue("TEST-123", fields="summary,customfield_10049")

        # Verify the API call
        issues_mixin.jira.get_issue.assert_called_with(
            "TEST-123",
            expand=None,
            fields="summary,customfield_10049",
            properties=None,
            update_history=True,
        )

        # Check the result
        simplified = issue.to_simplified_dict()
        assert "customfield_10049" in simplified
        assert simplified["customfield_10049"] == {"value": "Custom value"}
        assert "description" not in simplified

        # Test with list format
        issues_mixin.jira.get_issue.reset_mock()
        issue = issues_mixin.get_issue(
            "TEST-123", fields=["summary", "customfield_10050"]
        )

        # Verify API call converts list to comma-separated string
        issues_mixin.jira.get_issue.assert_called_with(
            "TEST-123",
            expand=None,
            fields="summary,customfield_10050",
            properties=None,
            update_history=True,
        )

        # Check the result
        simplified = issue.to_simplified_dict()
        assert "customfield_10050" in simplified
        assert simplified["customfield_10050"] == {"value": "Option value"}

    def test_get_issue_with_all_fields(self, issues_mixin: IssuesMixin):
        """Test get_issue with '*all' fields parameter."""
        # Mock the response
        mock_issue = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue",
                "description": "Description",
                "customfield_10049": "Custom value",
            },
        }
        issues_mixin.jira.get_issue.return_value = mock_issue

        # Test with "*all" parameter
        issue = issues_mixin.get_issue("TEST-123", fields="*all")

        # Check that all fields are included
        simplified = issue.to_simplified_dict()
        assert "summary" in simplified
        assert "description" in simplified
        assert "customfield_10049" in simplified

    def test_get_issue_with_properties(self, issues_mixin: IssuesMixin):
        """Test get_issue with properties parameter."""
        # Mock the response
        issues_mixin.jira.get_issue.return_value = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {},
        }

        # Test with properties parameter as string
        issues_mixin.get_issue("TEST-123", properties="property1,property2")

        # Verify API call - should include properties parameter and add 'properties' to fields
        issues_mixin.jira.get_issue.assert_called_with(
            "TEST-123",
            expand=None,
            fields=ANY,
            properties="property1,property2",
            update_history=True,
        )

        # Test with properties parameter as list
        issues_mixin.jira.get_issue.reset_mock()
        issues_mixin.get_issue("TEST-123", properties=["property1", "property2"])

        # Verify API call - should include properties parameter as comma-separated string and add 'properties' to fields
        issues_mixin.jira.get_issue.assert_called_with(
            "TEST-123",
            expand=None,
            fields=ANY,
            properties="property1,property2",
            update_history=True,
        )

    def test_get_issue_with_update_history(self, issues_mixin: IssuesMixin):
        """Test get_issue with update_history parameter."""
        # Mock the response
        issues_mixin.jira.get_issue.return_value = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {},
        }

        # Test with update_history=False
        issues_mixin.get_issue("TEST-123", update_history=False)

        # Verify API call - should include update_history parameter
        issues_mixin.jira.get_issue.assert_called_with(
            "TEST-123",
            expand=None,
            fields=ANY,
            properties=None,
            update_history=False,
        )

    def test_get_issue_with_config_projects_filter_restricted(
        self, issues_mixin: IssuesMixin
    ):
        """Test get_issue with projects filter from config - restricted case."""
        # Setup mock response
        mock_issues = {
            "issues": [
                {
                    "id": "10001",
                    "key": "TEST-123",
                    "fields": {
                        "summary": "Test issue",
                        "issuetype": {"name": "Bug"},
                        "status": {"name": "Open"},
                    },
                }
            ],
            "total": 1,
            "startAt": 0,
            "maxResults": 50,
        }
        issues_mixin.jira.jql.return_value = mock_issues
        issues_mixin.config.url = "https://example.atlassian.net"
        issues_mixin.config.projects_filter = "DEV"

        # Mock the API to raise an exception
        issues_mixin.jira.get_issue.side_effect = Exception("API error")

        # Call the method and verify it raises the expected exception
        with pytest.raises(
            Exception,
            match=(
                "Error retrieving issue TEST-123: "
                "Issue with project prefix 'TEST' are restricted by configuration"
            ),
        ):
            issues_mixin.get_issue("TEST-123")

    def test_get_issue_with_config_projects_filter_allowed(
        self, issues_mixin: IssuesMixin
    ):
        """Test get_issue with projects filter from config - allowed case."""
        # Setup mock response for a project that matches the filter
        mock_issue_data = {
            "id": "10001",
            "key": "DEV-123",
            "fields": {
                "summary": "Test issue",
                "description": "This is a test issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
            },
        }
        issues_mixin.jira.get_issue.return_value = mock_issue_data
        issues_mixin.config.url = "https://example.atlassian.net"
        issues_mixin.config.projects_filter = "DEV"

        # Call the method
        result = issues_mixin.get_issue("DEV-123")

        # Verify the API call was made correctly
        issues_mixin.jira.get_issue.assert_called_once_with(
            "DEV-123",
            expand=None,
            fields=ANY,
            properties=None,
            update_history=True,
        )

        # Verify the result
        assert isinstance(result, JiraIssue)
        assert result.key == "DEV-123"
        assert result.summary == "Test issue"

    def test_get_issue_with_multiple_projects_filter(self, issues_mixin: IssuesMixin):
        """Test get_issue with multiple projects in the filter."""
        # Setup mock response for a project that matches one of the multiple filters
        mock_issue_data = {
            "id": "10001",
            "key": "PROD-123",
            "fields": {
                "summary": "Production issue",
                "description": "This is a production issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
            },
        }
        issues_mixin.jira.get_issue.return_value = mock_issue_data
        issues_mixin.config.url = "https://example.atlassian.net"
        issues_mixin.config.projects_filter = "DEV,PROD"

        # Call the method
        result = issues_mixin.get_issue("PROD-123")

        # Verify the API call was made correctly
        issues_mixin.jira.get_issue.assert_called_once_with(
            "PROD-123",
            expand=None,
            fields=ANY,
            properties=None,
            update_history=True,
        )

        # Verify the result
        assert isinstance(result, JiraIssue)
        assert result.key == "PROD-123"
        assert result.summary == "Production issue"

    def test_get_issue_with_whitespace_in_projects_filter(
        self, issues_mixin: IssuesMixin
    ):
        """Test get_issue with extra whitespace in the projects filter."""
        # Setup mock response for a project that matches the filter with whitespace
        mock_issue_data = {
            "id": "10001",
            "key": "DEV-123",
            "fields": {
                "summary": "Development issue",
                "description": "This is a development issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
            },
        }
        issues_mixin.jira.get_issue.return_value = mock_issue_data
        issues_mixin.config.url = "https://example.atlassian.net"
        issues_mixin.config.projects_filter = " DEV , PROD "  # Extra whitespace

        # Call the method
        result = issues_mixin.get_issue("DEV-123")

        # Verify the API call was made correctly
        issues_mixin.jira.get_issue.assert_called_once_with(
            "DEV-123",
            expand=None,
            fields=ANY,
            properties=None,
            update_history=True,
        )

        # Verify the result
        assert isinstance(result, JiraIssue)
        assert result.key == "DEV-123"
        assert result.summary == "Development issue"
