"""Tests for JiraSearchResult and JiraProject models."""

import pytest

from src.mcp_atlassian.models.constants import EMPTY_STRING, JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import JiraIssue, JiraProject, JiraSearchResult


class TestJiraSearchResult:
    """Tests for the JiraSearchResult model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraSearchResult from valid API data."""
        # Create mock issues for the search result
        mock_issue_1 = {
            "id": "10001",
            "key": "TEST-123",
            "fields": {"summary": "First test issue"},
        }
        mock_issue_2 = {
            "id": "10002",
            "key": "TEST-124",
            "fields": {"summary": "Second test issue"},
        }

        search_data = {
            "expand": "names,schema",
            "startAt": 0,
            "maxResults": 50,
            "total": 2,
            "issues": [mock_issue_1, mock_issue_2],
            "warningMessages": ["Some warning message"],
            "names": {"priority": "Priority", "status": "Status"},
            "schema": {
                "priority": {
                    "type": "priority",
                    "system": "priority",
                },
                "status": {
                    "type": "status",
                    "system": "status",
                },
            },
        }

        result = JiraSearchResult.from_api_response(search_data)

        assert result.start_at == 0
        assert result.max_results == 50
        assert result.total == 2
        assert len(result.issues) == 2
        assert result.issues[0].key == "TEST-123"
        assert result.issues[1].key == "TEST-124"
        assert result.warning_messages == ["Some warning message"]
        assert result.names == {"priority": "Priority", "status": "Status"}
        assert "priority" in result.schema
        assert "status" in result.schema

    def test_from_api_response_empty_results(self):
        """Test creating a JiraSearchResult with no issues."""
        search_data = {
            "startAt": 0,
            "maxResults": 50,
            "total": 0,
            "issues": [],
        }

        result = JiraSearchResult.from_api_response(search_data)

        assert result.start_at == 0
        assert result.max_results == 50
        assert result.total == 0
        assert len(result.issues) == 0
        assert result.warning_messages == []
        assert result.names == {}
        assert result.schema == {}


class TestJiraProject:
    """Tests for the JiraProject model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraProject from valid API data."""
        project_data = {
            "id": "10000",
            "key": "TEST",
            "name": "Test Project",
            "description": "A test project for unit testing",
            "lead": {
                "accountId": "lead123",
                "displayName": "Project Lead",
                "emailAddress": "lead@example.com",
                "active": True,
            },
            "projectTypeKey": "software",
            "simplified": False,
            "style": "classic",
            "isPrivate": False,
            "properties": {},
            "entityId": "project-entity-123",
            "uuid": "project-uuid-456",
        }

        project = JiraProject.from_api_response(project_data)

        assert project.id == "10000"
        assert project.key == "TEST"
        assert project.name == "Test Project"
        assert project.description == "A test project for unit testing"
        assert project.lead.display_name == "Project Lead"
        assert project.lead.account_id == "lead123"
        assert project.project_type_key == "software"
        assert project.simplified is False
        assert project.style == "classic"
        assert project.is_private is False
        assert project.properties == {}
        assert project.entity_id == "project-entity-123"
        assert project.uuid == "project-uuid-456"

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraProject with minimal data."""
        project_data = {
            "id": "10000",
            "key": "TEST",
            "name": "Test Project",
        }

        project = JiraProject.from_api_response(project_data)

        assert project.id == "10000"
        assert project.key == "TEST"
        assert project.name == "Test Project"
        assert project.description == EMPTY_STRING
        assert project.lead.account_id == JIRA_DEFAULT_ID
        assert project.lead.display_name == UNKNOWN
        assert project.project_type_key == EMPTY_STRING
        assert project.simplified is False  # Default value
        assert project.style == EMPTY_STRING
        assert project.is_private is False  # Default value
        assert project.properties == {}
        assert project.entity_id == EMPTY_STRING
        assert project.uuid == EMPTY_STRING

    def test_from_api_response_with_none_values(self):
        """Test JiraProject handles None values gracefully."""
        project_data = {
            "id": "10000",
            "key": "TEST",
            "name": "Test Project",
            "description": None,
            "lead": None,
            "projectTypeKey": None,
            "simplified": None,
            "style": None,
            "isPrivate": None,
            "properties": None,
            "entityId": None,
            "uuid": None,
        }

        project = JiraProject.from_api_response(project_data)

        assert project.description == EMPTY_STRING
        assert project.lead.account_id == JIRA_DEFAULT_ID
        assert project.project_type_key == EMPTY_STRING
        assert project.simplified is False
        assert project.style == EMPTY_STRING
        assert project.is_private is False
        assert project.properties == {}
        assert project.entity_id == EMPTY_STRING
        assert project.uuid == EMPTY_STRING
