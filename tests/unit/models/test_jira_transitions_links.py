"""Tests for Jira transition and link models."""

import pytest

from src.mcp_atlassian.models.constants import EMPTY_STRING, JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import (
    JiraIssueLink,
    JiraIssueLinkType,
    JiraLinkedIssue,
    JiraLinkedIssueFields,
    JiraTransition,
)


class TestJiraTransition:
    """Tests for the JiraTransition model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraTransition from valid API data."""
        transition_data = {
            "id": "11",
            "name": "To Do",
            "to": {
                "id": "10001",
                "name": "To Do",
                "description": "The issue is open and ready for work",
                "statusCategory": {
                    "id": 2,
                    "key": "new",
                    "name": "To Do",
                    "colorName": "blue-gray",
                },
            },
            "hasScreen": True,
            "isGlobal": False,
            "isInitial": False,
            "isAvailable": True,
            "isConditional": False,
            "fields": {
                "summary": {
                    "required": False,
                    "schema": {"type": "string", "system": "summary"},
                    "name": "Summary",
                    "key": "summary",
                    "hasDefaultValue": False,
                    "operations": ["set", "edit"],
                    "allowedValues": [],
                    "autoCompleteUrl": "",
                }
            },
            "expand": "transitions.fields",
        }

        transition = JiraTransition.from_api_response(transition_data)

        assert transition.id == "11"
        assert transition.name == "To Do"
        assert transition.to.name == "To Do"
        assert transition.to.description == "The issue is open and ready for work"
        assert transition.has_screen is True
        assert transition.is_global is False
        assert transition.is_initial is False
        assert transition.is_available is True
        assert transition.is_conditional is False
        assert "summary" in transition.fields
        assert transition.expand == "transitions.fields"

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraTransition with minimal data."""
        transition_data = {
            "id": "11",
            "name": "To Do",
        }

        transition = JiraTransition.from_api_response(transition_data)

        assert transition.id == "11"
        assert transition.name == "To Do"
        assert transition.to.id == JIRA_DEFAULT_ID
        assert transition.to.name == UNKNOWN
        assert transition.has_screen is False  # Default value
        assert transition.is_global is False  # Default value
        assert transition.fields == {}
        assert transition.expand == EMPTY_STRING


class TestJiraIssueLinkType:
    """Tests for the JiraIssueLinkType model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraIssueLinkType from valid API data."""
        link_type_data = {
            "id": "10000",
            "name": "Blocks",
            "inward": "is blocked by",
            "outward": "blocks",
            "self": "https://example.atlassian.net/rest/api/3/issueLinkType/10000",
        }

        link_type = JiraIssueLinkType.from_api_response(link_type_data)

        assert link_type.id == "10000"
        assert link_type.name == "Blocks"
        assert link_type.inward == "is blocked by"
        assert link_type.outward == "blocks"
        assert link_type.self_url == "https://example.atlassian.net/rest/api/3/issueLinkType/10000"

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraIssueLinkType with minimal data."""
        link_type_data = {
            "id": "10000",
            "name": "Blocks",
        }

        link_type = JiraIssueLinkType.from_api_response(link_type_data)

        assert link_type.id == "10000"
        assert link_type.name == "Blocks"
        assert link_type.inward == EMPTY_STRING
        assert link_type.outward == EMPTY_STRING
        assert link_type.self_url == EMPTY_STRING


class TestJiraLinkedIssueFields:
    """Tests for the JiraLinkedIssueFields model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraLinkedIssueFields from valid API data."""
        fields_data = {
            "summary": "Linked Issue Summary",
            "status": {
                "id": "10001",
                "name": "Done",
                "description": "The issue is complete",
                "statusCategory": {
                    "id": 3,
                    "key": "done",
                    "name": "Done",
                    "colorName": "green",
                },
            },
            "priority": {
                "id": "2",
                "name": "High",
                "description": "High priority issue",
            },
            "issuetype": {
                "id": "10001",
                "name": "Story",
                "description": "User story",
                "subtask": False,
            },
        }

        fields = JiraLinkedIssueFields.from_api_response(fields_data)

        assert fields.summary == "Linked Issue Summary"
        assert fields.status.name == "Done"
        assert fields.priority.name == "High"
        assert fields.issue_type.name == "Story"


class TestJiraLinkedIssue:
    """Tests for the JiraLinkedIssue model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraLinkedIssue from valid API data."""
        linked_issue_data = {
            "id": "10002",
            "key": "LINKED-456",
            "self": "https://example.atlassian.net/rest/api/3/issue/10002",
            "fields": {
                "summary": "Linked Issue Summary",
                "status": {
                    "id": "10001",
                    "name": "Done",
                    "statusCategory": {
                        "id": 3,
                        "key": "done",
                        "name": "Done",
                        "colorName": "green",
                    },
                },
                "priority": {"id": "2", "name": "High"},
                "issuetype": {
                    "id": "10001",
                    "name": "Story",
                    "subtask": False,
                },
            },
        }

        linked_issue = JiraLinkedIssue.from_api_response(linked_issue_data)

        assert linked_issue.id == "10002"
        assert linked_issue.key == "LINKED-456"
        assert linked_issue.self_url == "https://example.atlassian.net/rest/api/3/issue/10002"
        assert linked_issue.fields.summary == "Linked Issue Summary"
        assert linked_issue.fields.status.name == "Done"


class TestJiraIssueLink:
    """Tests for the JiraIssueLink model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraIssueLink from valid API data."""
        link_data = {
            "id": "10001",
            "self": "https://example.atlassian.net/rest/api/3/issueLink/10001",
            "type": {
                "id": "10000",
                "name": "Blocks",
                "inward": "is blocked by",
                "outward": "blocks",
            },
            "inwardIssue": {
                "id": "10003",
                "key": "INWARD-789",
                "fields": {
                    "summary": "Inward Issue",
                    "status": {"id": "10001", "name": "Open"},
                    "priority": {"id": "3", "name": "Medium"},
                    "issuetype": {"id": "10001", "name": "Bug", "subtask": False},
                },
            },
            "outwardIssue": {
                "id": "10004",
                "key": "OUTWARD-101",
                "fields": {
                    "summary": "Outward Issue",
                    "status": {"id": "10002", "name": "In Progress"},
                    "priority": {"id": "1", "name": "Highest"},
                    "issuetype": {"id": "10002", "name": "Task", "subtask": False},
                },
            },
        }

        link = JiraIssueLink.from_api_response(link_data)

        assert link.id == "10001"
        assert link.self_url == "https://example.atlassian.net/rest/api/3/issueLink/10001"
        assert link.type.name == "Blocks"
        assert link.type.inward == "is blocked by"
        assert link.type.outward == "blocks"
        assert link.inward_issue.key == "INWARD-789"
        assert link.inward_issue.fields.summary == "Inward Issue"
        assert link.outward_issue.key == "OUTWARD-101"
        assert link.outward_issue.fields.summary == "Outward Issue"

    def test_from_api_response_with_only_inward_issue(self):
        """Test creating a JiraIssueLink with only inward issue."""
        link_data = {
            "id": "10001",
            "type": {
                "id": "10000",
                "name": "Blocks",
            },
            "inwardIssue": {
                "id": "10003",
                "key": "INWARD-789",
                "fields": {"summary": "Inward Issue Only"},
            },
        }

        link = JiraIssueLink.from_api_response(link_data)

        assert link.id == "10001"
        assert link.type.name == "Blocks"
        assert link.inward_issue.key == "INWARD-789"
        # Outward issue should have default values
        assert link.outward_issue.id == JIRA_DEFAULT_ID
        assert link.outward_issue.key == EMPTY_STRING
