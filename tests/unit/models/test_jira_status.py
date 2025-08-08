"""Tests for the JiraStatus and JiraStatusCategory models."""


from src.mcp_atlassian.models.constants import JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import JiraStatus, JiraStatusCategory


class TestJiraStatusCategory:
    """Tests for the JiraStatusCategory model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraStatusCategory from valid API data."""
        category_data = {
            "id": 1,
            "key": "new",
            "name": "New",
            "colorName": "blue-gray",
        }

        category = JiraStatusCategory.from_api_response(category_data)

        assert category.id == 1
        assert category.key == "new"
        assert category.name == "New"
        assert category.color_name == "blue-gray"


class TestJiraStatus:
    """Tests for the JiraStatus model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraStatus from valid API data."""
        status_data = {
            "id": "10001",
            "name": "In Progress",
            "description": "This issue is being actively worked on at the moment by the assignee.",
            "iconUrl": "https://example.com/icons/statuses/inprogress.png",
            "statusCategory": {
                "id": 4,
                "key": "indeterminate",
                "name": "In Progress",
                "colorName": "yellow",
            },
        }

        status = JiraStatus.from_api_response(status_data)

        assert status.id == "10001"
        assert status.name == "In Progress"
        assert (
            status.description
            == "This issue is being actively worked on at the moment by the assignee."
        )
        assert status.icon_url == "https://example.com/icons/statuses/inprogress.png"
        assert status.status_category.name == "In Progress"
        assert status.status_category.key == "indeterminate"

    def test_from_api_response_with_missing_category(self):
        """Test creating a JiraStatus without status category."""
        status_data = {
            "id": "10001",
            "name": "In Progress",
            "description": "Status description",
        }

        status = JiraStatus.from_api_response(status_data)

        assert status.id == "10001"
        assert status.name == "In Progress"
        assert status.status_category.id == JIRA_DEFAULT_ID
        assert status.status_category.name == UNKNOWN
