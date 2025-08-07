"""Tests for the JiraComment and JiraTimetracking models."""

import pytest

from src.mcp_atlassian.models.constants import EMPTY_STRING, JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import JiraComment, JiraTimetracking, JiraUser


class TestJiraComment:
    """Tests for the JiraComment model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraComment from valid API data."""
        comment_data = {
            "id": "10000",
            "body": "This is a comment body",
            "author": {
                "accountId": "author123",
                "displayName": "Comment Author",
                "emailAddress": "author@example.com",
                "active": True,
            },
            "updateAuthor": {
                "accountId": "updater123",
                "displayName": "Comment Updater",
                "emailAddress": "updater@example.com",
                "active": True,
            },
            "created": "2023-01-01T00:00:00.000+0000",
            "updated": "2023-01-02T00:00:00.000+0000",
            "visibility": {
                "type": "group",
                "value": "jira-users",
            },
        }

        comment = JiraComment.from_api_response(comment_data)

        assert comment.id == "10000"
        assert comment.body == "This is a comment body"
        assert comment.author.account_id == "author123"
        assert comment.author.display_name == "Comment Author"
        assert comment.update_author.account_id == "updater123"
        assert comment.created == "2023-01-01T00:00:00.000+0000"
        assert comment.updated == "2023-01-02T00:00:00.000+0000"
        assert comment.visibility == {"type": "group", "value": "jira-users"}

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraComment with minimal data."""
        comment_data = {
            "id": "10000",
            "body": "Minimal comment",
        }

        comment = JiraComment.from_api_response(comment_data)

        assert comment.id == "10000"
        assert comment.body == "Minimal comment"
        assert comment.author.account_id == JIRA_DEFAULT_ID
        assert comment.author.display_name == UNKNOWN
        assert comment.update_author.account_id == JIRA_DEFAULT_ID
        assert comment.created == EMPTY_STRING
        assert comment.updated == EMPTY_STRING
        assert comment.visibility == {}


class TestJiraTimetracking:
    """Tests for the JiraTimetracking model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraTimetracking from valid API data."""
        timetracking_data = {
            "originalEstimate": "1w 2d",
            "remainingEstimate": "3d 4h",
            "timeSpent": "2d 1h",
            "originalEstimateSeconds": 604800,  # 1 week
            "remainingEstimateSeconds": 28800,  # 8 hours
            "timeSpentSeconds": 32400,  # 9 hours
        }

        timetracking = JiraTimetracking.from_api_response(timetracking_data)

        assert timetracking.original_estimate == "1w 2d"
        assert timetracking.remaining_estimate == "3d 4h"
        assert timetracking.time_spent == "2d 1h"
        assert timetracking.original_estimate_seconds == 604800
        assert timetracking.remaining_estimate_seconds == 28800
        assert timetracking.time_spent_seconds == 32400

    def test_from_api_response_with_none_values(self):
        """Test creating a JiraTimetracking with None values."""
        timetracking_data = {
            "originalEstimate": None,
            "remainingEstimate": None,
            "timeSpent": None,
            "originalEstimateSeconds": None,
            "remainingEstimateSeconds": None,
            "timeSpentSeconds": None,
        }

        timetracking = JiraTimetracking.from_api_response(timetracking_data)

        assert timetracking.original_estimate == EMPTY_STRING
        assert timetracking.remaining_estimate == EMPTY_STRING
        assert timetracking.time_spent == EMPTY_STRING
        assert timetracking.original_estimate_seconds == 0
        assert timetracking.remaining_estimate_seconds == 0
        assert timetracking.time_spent_seconds == 0

    def test_from_api_response_empty_dict(self):
        """Test creating a JiraTimetracking from empty dict."""
        timetracking_data = {}

        timetracking = JiraTimetracking.from_api_response(timetracking_data)

        assert timetracking.original_estimate == EMPTY_STRING
        assert timetracking.remaining_estimate == EMPTY_STRING
        assert timetracking.time_spent == EMPTY_STRING
        assert timetracking.original_estimate_seconds == 0
        assert timetracking.remaining_estimate_seconds == 0
        assert timetracking.time_spent_seconds == 0
