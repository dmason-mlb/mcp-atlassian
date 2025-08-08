"""Tests for the JiraIssueType and JiraPriority models."""


from src.mcp_atlassian.models.constants import EMPTY_STRING
from src.mcp_atlassian.models.jira import JiraIssueType, JiraPriority


class TestJiraIssueType:
    """Tests for the JiraIssueType model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraIssueType from valid API data."""
        issue_type_data = {
            "id": "10001",
            "name": "Bug",
            "description": "A problem which impairs or prevents the functions of the product.",
            "iconUrl": "https://example.com/icons/issuetypes/bug.png",
            "subtask": False,
        }

        issue_type = JiraIssueType.from_api_response(issue_type_data)

        assert issue_type.id == "10001"
        assert issue_type.name == "Bug"
        assert (
            issue_type.description
            == "A problem which impairs or prevents the functions of the product."
        )
        assert issue_type.icon_url == "https://example.com/icons/issuetypes/bug.png"
        assert issue_type.subtask is False

    def test_from_api_response_subtask_type(self):
        """Test creating a JiraIssueType for subtask."""
        issue_type_data = {
            "id": "10003",
            "name": "Sub-task",
            "description": "The sub-task of the issue",
            "iconUrl": "https://example.com/icons/issuetypes/subtask.png",
            "subtask": True,
        }

        issue_type = JiraIssueType.from_api_response(issue_type_data)

        assert issue_type.id == "10003"
        assert issue_type.name == "Sub-task"
        assert issue_type.subtask is True


class TestJiraPriority:
    """Tests for the JiraPriority model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraPriority from valid API data."""
        priority_data = {
            "id": "1",
            "name": "Highest",
            "description": "This problem will block progress.",
            "iconUrl": "https://example.com/icons/priorities/highest.svg",
        }

        priority = JiraPriority.from_api_response(priority_data)

        assert priority.id == "1"
        assert priority.name == "Highest"
        assert priority.description == "This problem will block progress."
        assert priority.icon_url == "https://example.com/icons/priorities/highest.svg"

    def test_from_api_response_with_missing_fields(self):
        """Test creating a JiraPriority with missing fields."""
        priority_data = {
            "id": "3",
            "name": "Medium",
        }

        priority = JiraPriority.from_api_response(priority_data)

        assert priority.id == "3"
        assert priority.name == "Medium"
        assert priority.description == EMPTY_STRING
        assert priority.icon_url == EMPTY_STRING
