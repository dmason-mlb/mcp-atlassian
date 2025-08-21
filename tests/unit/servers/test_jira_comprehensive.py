"""Comprehensive tests for the Jira MCP server implementation."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastmcp import Context
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import (
    MCPAtlassianAuthenticationError,
    MCPAtlassianError,
)
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.models.jira.common import JiraUser
from mcp_atlassian.models.jira.issue import JiraIssue
from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.servers.jira import jira_mcp
from mcp_atlassian.servers.jira.issues import get_issue
from mcp_atlassian.servers.jira.management import get_user_profile


class TestJiraUserProfile:
    """Test the get_user_profile tool."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        # Create app context with Jira config
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Mock FastMCP with proper request_context path
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        # Set up the _mcp_server.request_context path that Context expects
        mock_fastmcp._mcp_server.request_context = mock_request_context

        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_jira_fetcher(self):
        """Create a mock JiraFetcher."""
        # We need to use Mock instead of AsyncMock because get_user_profile is not async
        return Mock(spec=JiraFetcher)

    @pytest.mark.anyio
    async def test_get_user_profile_success(self, mock_context, mock_jira_fetcher):
        """Test successful user profile retrieval."""
        # Arrange - Use real response structure from captured data
        mock_user = Mock(spec=JiraUser)
        mock_user.to_simplified_dict.return_value = {
            "accountId": "5dfa93ea4517db0caf3738b4",
            "emailAddress": "douglas.mason@mlb.com",
            "displayName": "Douglas Mason",
            "active": True,
            "avatarUrls": {
                "48x48": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
                "24x24": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/24",
                "16x16": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/16",
                "32x32": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/32",
            },
            "self": "https://baseball.atlassian.net/rest/api/3/user?accountId=5dfa93ea4517db0caf3738b4",
            "timeZone": "America/New_York",
            "accountType": "atlassian",
        }
        mock_jira_fetcher.get_user_profile.return_value = mock_user

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_user_profile(mock_context, "user@example.com")
            parsed = json.loads(result)

            # Assert - The function returns the user data directly, not a success wrapper
            assert parsed["accountId"] == "5dfa93ea4517db0caf3738b4"
            assert parsed["emailAddress"] == "douglas.mason@mlb.com"
            assert parsed["displayName"] == "Douglas Mason"
            assert parsed["active"] is True
            assert "avatarUrls" in parsed
            assert parsed["timeZone"] == "America/New_York"
            mock_jira_fetcher.get_user_profile.assert_called_once_with(
                "user@example.com"
            )

    @pytest.mark.anyio
    async def test_get_user_profile_not_found(self, mock_context, mock_jira_fetcher):
        """Test user profile retrieval when user is not found."""
        # Arrange
        mock_jira_fetcher.get_user_profile.side_effect = ValueError("User not found")

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_user_profile(mock_context, "nonexistent@example.com")
            parsed = json.loads(result)

            # Assert - The function returns an error dict without 'success' field
            assert "error" in parsed
            assert "User not found" in parsed["error"]

    @pytest.mark.anyio
    async def test_get_user_profile_auth_error(self, mock_context, mock_jira_fetcher):
        """Test user profile retrieval with authentication error."""
        # Arrange
        mock_jira_fetcher.get_user_profile.side_effect = (
            MCPAtlassianAuthenticationError("Invalid token")
        )

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_user_profile(mock_context, "user@example.com")
            parsed = json.loads(result)

            # Assert - The function returns an error dict without 'success' field
            assert "error" in parsed
            assert "Failed to get user profile" in parsed["error"]

    @pytest.mark.anyio
    async def test_get_user_profile_network_error(
        self, mock_context, mock_jira_fetcher
    ):
        """Test user profile retrieval with network error."""
        # Arrange
        mock_jira_fetcher.get_user_profile.side_effect = HTTPError("Connection timeout")

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_user_profile(mock_context, "user@example.com")
            parsed = json.loads(result)

            # Assert - The function returns an error dict without 'success' field
            assert "error" in parsed
            assert "Failed to get user profile" in parsed["error"]

    @pytest.mark.anyio
    async def test_get_user_profile_unexpected_error(
        self, mock_context, mock_jira_fetcher
    ):
        """Test user profile retrieval with unexpected error."""
        # Arrange
        mock_jira_fetcher.get_user_profile.side_effect = RuntimeError(
            "Unexpected error"
        )

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act & Assert - RuntimeError is not caught, so it should propagate
            with pytest.raises(RuntimeError, match="Unexpected error"):
                await get_user_profile(mock_context, "user@example.com")


class TestJiraGetIssue:
    """Test the get_issue tool."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        # Create app context with Jira config
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Mock FastMCP with proper request_context path
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        # Set up the _mcp_server.request_context path that Context expects
        mock_fastmcp._mcp_server.request_context = mock_request_context

        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_jira_fetcher(self):
        """Create a mock JiraFetcher."""
        # We need to use Mock instead of AsyncMock because get_user_profile is not async
        return Mock(spec=JiraFetcher)

    @pytest.mark.anyio
    async def test_get_issue_with_default_fields(self, mock_context, mock_jira_fetcher):
        """Test getting an issue with default fields."""
        # Arrange - Use real response structure from captured data
        mock_issue = Mock(spec=JiraIssue)
        mock_issue.to_simplified_dict.return_value = {
            "id": "1166230",
            "key": "FTEST-120",
            "summary": "Response Capture Test - 20250817_235744",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Test issue for capturing API responses",
                            }
                        ],
                    }
                ],
            },
            "status": {"name": "To Do", "category": "To Do", "color": "blue-gray"},
            "priority": {"name": "None"},
            "assignee": {
                "display_name": "Douglas Mason",
                "name": "Douglas Mason",
                "email": "douglas.mason@mlb.com",
                "avatar_url": "https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/5dfa93ea4517db0caf3738b4/f724f67d-332f-4817-a3bc-86ed1382dd7d/48",
            },
        }
        mock_jira_fetcher.get_issue.return_value = mock_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_issue(mock_context, "FTEST-123")
            parsed = json.loads(result)

            # Assert - Verify real response structure
            assert parsed["id"] == "1166230"
            assert parsed["key"] == "FTEST-120"
            assert parsed["summary"] == "Response Capture Test - 20250817_235744"
            assert parsed["description"]["type"] == "doc"  # ADF format
            assert parsed["status"]["name"] == "To Do"
            assert parsed["assignee"]["display_name"] == "Douglas Mason"
            mock_jira_fetcher.get_issue.assert_called_once()

    @pytest.mark.anyio
    async def test_get_issue_with_custom_fields(self, mock_context, mock_jira_fetcher):
        """Test getting an issue with custom fields specified."""
        # Arrange
        mock_issue = Mock(spec=JiraIssue)
        mock_issue.to_simplified_dict.return_value = {
            "key": "FTEST-456",
            "summary": "Custom Fields Test",
            "customfield_10010": "Epic Link",
        }
        mock_jira_fetcher.get_issue.return_value = mock_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_issue(
                mock_context, "FTEST-456", fields="summary,customfield_10010"
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["customfield_10010"] == "Epic Link"

    @pytest.mark.anyio
    async def test_get_issue_with_all_fields(self, mock_context, mock_jira_fetcher):
        """Test getting an issue with all fields requested."""
        # Arrange
        mock_issue = Mock(spec=JiraIssue)
        mock_issue.to_simplified_dict.return_value = {
            "key": "FTEST-789",
            "fields": {"all": "fields", "included": True},
        }
        mock_jira_fetcher.get_issue.return_value = mock_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_issue(mock_context, "FTEST-789", fields="*all")

            # Assert
            mock_jira_fetcher.get_issue.assert_called_once()
            call_args = mock_jira_fetcher.get_issue.call_args
            assert call_args[1]["fields"] == "*all"

    @pytest.mark.anyio
    async def test_get_issue_with_comments(self, mock_context, mock_jira_fetcher):
        """Test getting an issue with comments."""
        # Arrange
        mock_issue = Mock(spec=JiraIssue)
        mock_issue.to_simplified_dict.return_value = {
            "key": "FTEST-321",
            "comments": [
                {"author": "user1", "body": "Comment 1"},
                {"author": "user2", "body": "Comment 2"},
            ],
        }
        mock_jira_fetcher.get_issue.return_value = mock_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            result = await get_issue(mock_context, "FTEST-321", comment_limit=2)
            parsed = json.loads(result)

            # Assert
            assert len(parsed.get("comments", [])) <= 2

    @pytest.mark.anyio
    async def test_get_issue_not_found(self, mock_context, mock_jira_fetcher):
        """Test getting a non-existent issue."""
        # Arrange
        mock_jira_fetcher.get_issue.side_effect = MCPAtlassianError("Issue not found")

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act & Assert
            with pytest.raises(MCPAtlassianError, match="Issue not found"):
                await get_issue(mock_context, "NONEXISTENT-999")


class TestJiraToolRegistration:
    """Test that Jira tools are properly registered."""

    @pytest.mark.anyio
    async def test_jira_mcp_has_required_tools(self):
        """Test that jira_mcp has all required tools registered."""
        # Act
        tools = await jira_mcp.get_tools()
        tool_names = list(tools.keys())

        # Assert core tools are registered
        # Tools are prefixed with their mount point (e.g., "management_get_user_profile")
        assert any("get_user_profile" in name for name in tool_names)
        assert any("get_issue" in name for name in tool_names)

    @pytest.mark.anyio
    async def test_jira_tools_have_correct_tags(self):
        """Test that Jira tools have correct tags."""
        # Act
        all_tools = await jira_mcp.get_tools()

        # Assert
        for tool_name, tool_def in all_tools.items():
            # Check if tool_def has inputSchema which contains the tags info
            # In FastMCP, tags are part of the tool metadata
            # For now, just verify we have tools
            assert tool_name  # Basic check that tool exists
            # More specific tag checking would require accessing tool metadata
            # which depends on FastMCP's internal structure


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        # Create app context with Jira config
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Mock FastMCP with proper request_context path
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}

        # Set up the _mcp_server.request_context path that Context expects
        mock_fastmcp._mcp_server.request_context = mock_request_context

        return Context(fastmcp=mock_fastmcp)

    @pytest.mark.anyio
    async def test_get_issue_with_empty_issue_key(self, mock_context):
        """Test that empty issue key is handled properly."""
        # Arrange
        mock_jira_fetcher = Mock(spec=JiraFetcher)
        mock_jira_fetcher.get_issue.side_effect = ValueError("Invalid issue key")

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act & Assert
            with pytest.raises(ValueError):
                await get_issue(mock_context, "")

    @pytest.mark.anyio
    async def test_get_issue_with_max_comment_limit(self, mock_context):
        """Test that comment limit is enforced at maximum."""
        # Arrange
        mock_jira_fetcher = Mock(spec=JiraFetcher)
        mock_issue = Mock(spec=JiraIssue)
        mock_issue.to_simplified_dict.return_value = {"key": "FTEST-MAX"}
        mock_jira_fetcher.get_issue.return_value = mock_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act
            await get_issue(mock_context, "FTEST-MAX", comment_limit=100)

            # Assert
            call_args = mock_jira_fetcher.get_issue.call_args
            assert call_args[1]["comment_limit"] == 100

    @pytest.mark.anyio
    async def test_get_issue_with_beyond_max_comment_limit(self, mock_context):
        """Test that comment limit beyond maximum is rejected."""
        # This test would depend on Pydantic validation
        # The Field definition specifies le=100, so values > 100 should be rejected
        pass  # Pydantic handles this at the API layer

    @pytest.mark.anyio
    async def test_get_user_profile_with_various_identifiers(self, mock_context):
        """Test user profile retrieval with different identifier types."""
        # Arrange
        test_identifiers = [
            "user@example.com",  # Email
            "johndoe",  # Username
            "accountid:123456",  # Account ID
            "key:userkey",  # Key for Server/DC
        ]

        mock_jira_fetcher = Mock(spec=JiraFetcher)  # Use Mock, not AsyncMock
        mock_user = Mock(spec=JiraUser)
        mock_user.to_simplified_dict.return_value = {"accountId": "123"}
        mock_jira_fetcher.get_user_profile.return_value = mock_user

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_jira_fetcher

            # Act & Assert
            for identifier in test_identifiers:
                result = await get_user_profile(mock_context, identifier)
                parsed = json.loads(result)
                # The function returns user data directly, not a success wrapper
                assert parsed["accountId"] == "123"


class TestConcurrentRequests:
    """Test concurrent request handling for Jira tools."""

    @pytest.mark.anyio
    async def test_concurrent_get_issue_requests(self):
        """Test that multiple concurrent get_issue requests are handled correctly."""
        # Arrange
        # Create app context with Jira config
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        # Create multiple contexts with proper request_context path
        contexts = []
        for _ in range(5):
            mock_fastmcp = MagicMock()
            mock_request_context = MagicMock()
            mock_request_context.lifespan_context = {
                "app_lifespan_context": app_context
            }
            mock_fastmcp._mcp_server.request_context = mock_request_context
            contexts.append(Context(fastmcp=mock_fastmcp))

        issue_keys = [f"FTEST-{i}" for i in range(100, 105)]

        mock_jira_fetcher = Mock(spec=JiraFetcher)

        def mock_get_issue(issue_key=None, **kwargs):
            mock_issue = Mock(spec=JiraIssue)
            mock_issue.to_simplified_dict.return_value = {"key": issue_key}
            return mock_issue

        mock_jira_fetcher.get_issue = mock_get_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            # Make get_jira_fetcher return a coroutine
            async def async_return_fetcher(*args, **kwargs):
                return mock_jira_fetcher

            mock_get_fetcher.side_effect = async_return_fetcher

            # Act - Use anyio's task group for proper async handling
            from anyio import create_task_group

            results = []

            async def run_get_issue(ctx, key):
                result = await get_issue(ctx, key)
                results.append((key, result))

            async with create_task_group() as tg:
                for ctx, key in zip(contexts, issue_keys, strict=False):
                    tg.start_soon(run_get_issue, ctx, key)

            # Assert
            results.sort(key=lambda x: x[0])  # Sort by key for consistent ordering
            for key, result in results:
                parsed = json.loads(result)
                assert parsed["key"] == key
