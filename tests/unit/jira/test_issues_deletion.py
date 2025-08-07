"""Tests for Jira Issues mixin - Issue Deletion functionality."""

from unittest.mock import MagicMock

import pytest

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.issues import IssuesMixin
from mcp_atlassian.models.jira import JiraIssue


class TestIssuesDeletionMixin:
    """Tests for the IssuesMixin class - Issue Deletion functionality."""

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

    def test_delete_issue(self, issues_mixin: IssuesMixin):
        """Test deleting an issue."""
        # Call the method
        result = issues_mixin.delete_issue("TEST-123")

        # Verify the API call
        issues_mixin.jira.delete_issue.assert_called_once_with("TEST-123")
        assert result is True

    def test_delete_issue_error(self, issues_mixin: IssuesMixin):
        """Test error handling when deleting an issue."""
        # Setup mock to throw exception
        issues_mixin.jira.delete_issue.side_effect = Exception("Delete failed")

        # Call the method and verify exception is raised correctly
        with pytest.raises(
            Exception, match="Error deleting issue TEST-123: Delete failed"
        ):
            issues_mixin.delete_issue("TEST-123")