"""Tests for the core JiraIssue model functionality."""

import pytest

from src.mcp_atlassian.models.constants import EMPTY_STRING, JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import (
    JiraComment,
    JiraIssue,
    JiraIssueType,
    JiraPriority,
    JiraStatus,
    JiraStatusCategory,
    JiraTimetracking,
    JiraUser,
)


class TestJiraIssue:
    """Tests for the JiraIssue model - core functionality."""

    def test_from_api_response_with_comprehensive_data(self):
        """Test creating a JiraIssue from comprehensive API data."""
        issue_data = {
            "id": "10001",
            "key": "TEST-123",
            "self": "https://example.atlassian.net/rest/api/3/issue/10001",
            "fields": {
                "summary": "Test Issue Summary",
                "description": "Detailed description of the test issue",
                "status": {
                    "id": "10001",
                    "name": "In Progress",
                    "description": "This issue is being actively worked on",
                    "statusCategory": {
                        "id": 4,
                        "key": "indeterminate",
                        "name": "In Progress",
                        "colorName": "yellow",
                    },
                },
                "issuetype": {
                    "id": "10002",
                    "name": "Bug",
                    "description": "A problem in the system",
                    "subtask": False,
                },
                "priority": {
                    "id": "3",
                    "name": "Medium",
                    "description": "Standard priority",
                },
                "reporter": {
                    "accountId": "reporter123",
                    "displayName": "Reporter User",
                    "emailAddress": "reporter@example.com",
                    "active": True,
                },
                "assignee": {
                    "accountId": "assignee456",
                    "displayName": "Assignee User",
                    "emailAddress": "assignee@example.com",
                    "active": True,
                },
                "created": "2023-01-01T00:00:00.000+0000",
                "updated": "2023-01-02T00:00:00.000+0000",
                "duedate": "2023-12-31",
                "labels": ["urgent", "backend"],
                "components": [
                    {"id": "10000", "name": "Backend"},
                    {"id": "10001", "name": "API"},
                ],
                "fixVersions": [
                    {"id": "10020", "name": "v2.0.0", "released": False}
                ],
                "timetracking": {
                    "originalEstimate": "1w",
                    "remainingEstimate": "3d",
                    "timeSpent": "2d",
                    "originalEstimateSeconds": 604800,
                    "remainingEstimateSeconds": 259200,
                    "timeSpentSeconds": 172800,
                },
            },
        }

        issue = JiraIssue.from_api_response(
            issue_data, base_url="https://example.atlassian.net"
        )

        # Test basic fields
        assert issue.id == "10001"
        assert issue.key == "TEST-123"
        assert issue.self_url == "https://example.atlassian.net/rest/api/3/issue/10001"
        assert issue.summary == "Test Issue Summary"
        assert issue.description == "Detailed description of the test issue"
        assert issue.created == "2023-01-01T00:00:00.000+0000"
        assert issue.updated == "2023-01-02T00:00:00.000+0000"
        assert issue.due_date == "2023-12-31"
        assert issue.labels == ["urgent", "backend"]
        assert issue.url == "https://example.atlassian.net/browse/TEST-123"

        # Test complex objects
        assert isinstance(issue.status, JiraStatus)
        assert issue.status.name == "In Progress"
        assert issue.status.status_category.name == "In Progress"

        assert isinstance(issue.issue_type, JiraIssueType)
        assert issue.issue_type.name == "Bug"
        assert issue.issue_type.subtask is False

        assert isinstance(issue.priority, JiraPriority)
        assert issue.priority.name == "Medium"

        assert isinstance(issue.reporter, JiraUser)
        assert issue.reporter.display_name == "Reporter User"

        assert isinstance(issue.assignee, JiraUser)
        assert issue.assignee.display_name == "Assignee User"

        assert isinstance(issue.timetracking, JiraTimetracking)
        assert issue.timetracking.original_estimate == "1w"
        assert issue.timetracking.time_spent == "2d"

        # Test components and fix versions
        assert len(issue.components) == 2
        assert issue.components[0]["name"] == "Backend"
        assert issue.components[1]["name"] == "API"

        assert len(issue.fix_versions) == 1
        assert issue.fix_versions[0]["name"] == "v2.0.0"
        assert issue.fix_versions[0]["released"] is False

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraIssue with minimal required data."""
        issue_data = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {
                "summary": "Minimal Test Issue",
            },
        }

        issue = JiraIssue.from_api_response(issue_data)

        # Test basic fields with defaults
        assert issue.id == "10001"
        assert issue.key == "TEST-123"
        assert issue.summary == "Minimal Test Issue"
        assert issue.description == EMPTY_STRING
        assert issue.created == EMPTY_STRING
        assert issue.updated == EMPTY_STRING
        assert issue.due_date == EMPTY_STRING
        assert issue.labels == []
        assert issue.components == []
        assert issue.fix_versions == []

        # Test default objects
        assert issue.status.id == JIRA_DEFAULT_ID
        assert issue.status.name == UNKNOWN
        assert issue.issue_type.id == JIRA_DEFAULT_ID
        assert issue.issue_type.name == UNKNOWN
        assert issue.priority.id == JIRA_DEFAULT_ID
        assert issue.priority.name == UNKNOWN
        assert issue.reporter.account_id == JIRA_DEFAULT_ID
        assert issue.assignee.account_id == JIRA_DEFAULT_ID

    def test_from_api_response_with_none_values(self):
        """Test JiraIssue handles None values gracefully."""
        issue_data = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue",
                "description": None,
                "status": None,
                "assignee": None,
                "reporter": None,
                "labels": None,
                "components": None,
                "fixVersions": None,
                "duedate": None,
            },
        }

        issue = JiraIssue.from_api_response(issue_data)

        assert issue.description == EMPTY_STRING
        assert issue.due_date == EMPTY_STRING
        assert issue.labels == []
        assert issue.components == []
        assert issue.fix_versions == []
        assert issue.status.name == UNKNOWN
        assert issue.assignee.account_id == JIRA_DEFAULT_ID
        assert issue.reporter.account_id == JIRA_DEFAULT_ID
