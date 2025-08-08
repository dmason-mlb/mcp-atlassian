"""Tests for the JiraUser model."""


from src.mcp_atlassian.models.constants import EMPTY_STRING
from src.mcp_atlassian.models.jira import JiraUser


class TestJiraUser:
    """Tests for the JiraUser model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraUser from valid API data."""
        user_data = {
            "accountId": "user123",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True,
            "avatarUrls": {
                "48x48": "https://example.com/avatar.png",
                "24x24": "https://example.com/avatar-small.png",
            },
        }

        user = JiraUser.from_api_response(user_data)

        assert user.account_id == "user123"
        assert user.display_name == "Test User"
        assert user.email_address == "test@example.com"
        assert user.active is True
        assert user.avatar_urls == {
            "48x48": "https://example.com/avatar.png",
            "24x24": "https://example.com/avatar-small.png",
        }

    def test_from_api_response_with_missing_data(self):
        """Test creating a JiraUser with missing optional fields."""
        user_data = {
            "accountId": "user123",
            "displayName": "Test User",
        }

        user = JiraUser.from_api_response(user_data)

        assert user.account_id == "user123"
        assert user.display_name == "Test User"
        assert user.email_address == EMPTY_STRING
        assert user.active is True  # Default value
        assert user.avatar_urls == {}

    def test_from_api_response_with_none_values(self):
        """Test JiraUser handles None values gracefully."""
        user_data = {
            "accountId": "user123",
            "displayName": "Test User",
            "emailAddress": None,
            "active": None,
            "avatarUrls": None,
        }

        user = JiraUser.from_api_response(user_data)

        assert user.account_id == "user123"
        assert user.display_name == "Test User"
        assert user.email_address == EMPTY_STRING
        assert user.active is True  # Default for None
        assert user.avatar_urls == {}
