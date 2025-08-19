"""Unit tests for JIRA server using real API response fixtures.

These tests use actual API responses captured from the FTEST project
to ensure our mock tests accurately reflect real JIRA API behavior.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.context import MainAppContext
from tests.fixtures.jira_real_responses import (
    REAL_ISSUE_COMMENT_RESPONSE,
    REAL_ISSUE_CREATE_RESPONSE,
    REAL_ISSUE_GET_RESPONSE,
    REAL_ISSUE_TRANSITIONS,
    REAL_ISSUE_UPDATE_RESPONSE,
    REAL_SEARCH_RESPONSE,
    REAL_USER_PROFILE,
)


class TestJiraIssueOperationsWithRealFixtures:
    """Test JIRA issue operations using real API response fixtures."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_jira_config = MagicMock()
        mock_jira_config.is_auth_configured.return_value = True

        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=None,
            read_only=False,
            enabled_tools=None,
        )

        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
        mock_fastmcp._mcp_server.request_context = mock_request_context

        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_jira_fetcher(self):
        """Create a mock JiraFetcher with properly configured methods."""
        # Create a mock that doesn't inherit any real behavior
        mock_fetcher = Mock()

        # Configure create_issue to return a Mock issue instead of trying to make real calls
        mock_issue = Mock()
        mock_issue.to_simplified_dict = Mock(return_value=REAL_ISSUE_CREATE_RESPONSE)
        mock_issue.key = "FTEST-120"
        mock_issue.custom_fields = {}  # Empty dict for 'in' operator checks
        mock_fetcher.create_issue = Mock(return_value=mock_issue)

        # Configure other methods similarly
        mock_get_issue = Mock()
        mock_get_issue.to_simplified_dict = Mock(return_value=REAL_ISSUE_GET_RESPONSE)
        mock_get_issue.key = "FTEST-120"
        mock_get_issue.custom_fields = {}
        mock_fetcher.get_issue = Mock(return_value=mock_get_issue)

        # For update_issue, return a different mock issue with update response
        mock_updated_issue = Mock()
        mock_updated_issue.to_simplified_dict = Mock(
            return_value=REAL_ISSUE_UPDATE_RESPONSE
        )
        mock_updated_issue.key = "FTEST-120"
        mock_updated_issue.custom_fields = {}
        mock_fetcher.update_issue = Mock(return_value=mock_updated_issue)

        mock_fetcher.add_comment = Mock(return_value=REAL_ISSUE_COMMENT_RESPONSE)
        mock_fetcher.get_issue_transitions = Mock(return_value=REAL_ISSUE_TRANSITIONS)

        # Configure search to return a mock search result
        mock_search_result = Mock()
        mock_search_result.to_simplified_dict = Mock(return_value=REAL_SEARCH_RESPONSE)
        mock_fetcher.search_issues = Mock(return_value=mock_search_result)

        # Configure user profile - needs to be a JiraUser-like object
        from mcp_atlassian.models.jira.common import JiraUser

        mock_user = Mock(spec=JiraUser)
        mock_user.to_simplified_dict = Mock(return_value=REAL_USER_PROFILE)
        mock_fetcher.get_user_profile = Mock(return_value=mock_user)

        return mock_fetcher

    @staticmethod
    def create_async_mock_fetcher(mock_fetcher):
        """Create an async function that returns the mock fetcher."""

        async def async_return_fetcher(*args, **kwargs):
            return mock_fetcher

        return async_return_fetcher

    @pytest.mark.anyio
    async def test_create_issue_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test issue creation returns real API response structure."""
        from mcp_atlassian.servers.jira.issues import create_issue

        # Patch where get_jira_fetcher is imported and used
        with patch(
            "mcp_atlassian.servers.jira.mixins.creation.get_jira_fetcher"
        ) as mock_get_fetcher:
            # get_jira_fetcher is async, so we need to return a coroutine
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await create_issue(
                mock_context,
                project_key="FTEST",
                summary="Test Issue",
                issue_type="Task",
                description="Test description",
            )
            parsed = json.loads(result)

            # Assert - The create_issue function wraps the response in a message
            assert "message" in parsed
            assert parsed["message"] == "Issue created successfully"
            assert "issue" in parsed

            issue_data = parsed["issue"]

            # Verify real response structure
            assert "id" in issue_data
            assert "key" in issue_data
            assert issue_data["key"].startswith("FTEST-")
            assert "url" in issue_data
            assert issue_data["url"].startswith(
                "https://baseball.atlassian.net/rest/api/3/issue/"
            )

            # Verify ADF format for description
            assert "description" in issue_data
            assert issue_data["description"]["type"] == "doc"
            assert issue_data["description"]["version"] == 1
            assert "content" in issue_data["description"]

            # Verify status structure
            assert "status" in issue_data
            assert "name" in issue_data["status"]
            assert "category" in issue_data["status"]
            assert "color" in issue_data["status"]

            # Verify user structures
            assert "assignee" in issue_data
            assert "display_name" in issue_data["assignee"]
            assert "email" in issue_data["assignee"]
            assert "avatar_url" in issue_data["assignee"]

            assert "reporter" in issue_data
            assert "display_name" in issue_data["reporter"]

            # Verify timestamps
            assert "created" in issue_data
            assert "updated" in issue_data

    @pytest.mark.anyio
    async def test_get_issue_with_real_response(self, mock_context, mock_jira_fetcher):
        """Test issue retrieval returns real API response structure."""
        from mcp_atlassian.servers.jira.issues import get_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await get_issue(mock_context, "FTEST-120")
            parsed = json.loads(result)

            # Assert - Verify matches real response
            assert parsed["id"] == REAL_ISSUE_GET_RESPONSE["id"]
            assert parsed["key"] == REAL_ISSUE_GET_RESPONSE["key"]
            assert parsed["summary"] == REAL_ISSUE_GET_RESPONSE["summary"]

            # Verify ADF description structure
            assert parsed["description"]["type"] == "doc"
            assert len(parsed["description"]["content"]) > 0

            # Verify status details
            assert parsed["status"]["name"] == "To Do"
            assert parsed["status"]["category"] == "To Do"
            assert parsed["status"]["color"] == "blue-gray"

    @pytest.mark.anyio
    async def test_update_issue_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test issue update returns real API response structure."""
        from mcp_atlassian.servers.jira.issues import update_issue

        with patch(
            "mcp_atlassian.servers.jira.mixins.update.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await update_issue(
                mock_context,
                issue_key="FTEST-120",
                fields={"summary": "UPDATED - Test Issue"},
            )
            parsed = json.loads(result)

            # Assert - Verify response has message and issue structure
            assert "message" in parsed
            assert parsed["message"] == "Issue updated successfully"
            assert "issue" in parsed

            issue_data = parsed["issue"]

            # Verify real response structure
            assert issue_data["summary"].startswith("UPDATED - ")
            assert (
                issue_data["updated"] > issue_data["created"]
            )  # Updated timestamp is newer

            # Verify other fields remain intact
            assert "worklog" in issue_data
            assert issue_data["worklog"]["total"] == 0
            assert issue_data["worklog"]["worklogs"] == []

    @pytest.mark.anyio
    async def test_add_comment_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test adding comment returns real API response structure."""
        from mcp_atlassian.servers.jira.issues import add_comment

        with patch(
            "mcp_atlassian.servers.jira.mixins.update.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await add_comment(
                mock_context, issue_key="FTEST-120", comment="Test comment"
            )
            parsed = json.loads(result)

            # Assert - Verify real response structure
            assert "id" in parsed
            assert "body" in parsed
            # The body contains ADF format as a string
            assert "'type': 'doc'" in parsed["body"]
            assert "'version': 1" in parsed["body"]
            assert "created" in parsed
            assert "author" in parsed

    @pytest.mark.anyio
    async def test_get_transitions_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test getting transitions returns real API response structure."""
        from mcp_atlassian.servers.jira.management import get_transitions

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await get_transitions(mock_context, "FTEST-120")
            parsed = json.loads(result)

            # Assert - Verify real response structure
            assert isinstance(parsed, list)
            assert len(parsed) == 3  # To Do, Done, Start Work

            # Verify transition structure
            for transition in parsed:
                assert "id" in transition
                assert "name" in transition
                assert "to" in transition
                assert "statusCategory" in transition["to"]
                assert "isAvailable" in transition
                assert transition["isAvailable"] is True

            # Verify specific transitions
            transition_names = [t["name"] for t in parsed]
            assert "To Do" in transition_names
            assert "Done" in transition_names
            assert "Start Work" in transition_names

    @pytest.mark.anyio
    async def test_search_issues_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test searching issues returns real API response structure."""
        from mcp_atlassian.servers.jira.search import search

        with patch(
            "mcp_atlassian.servers.jira.search.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await search(mock_context, jql="project = FTEST", limit=3)
            parsed = json.loads(result)

            # Assert - Verify real response structure
            assert "total" in parsed
            assert parsed["total"] > 0
            assert "issues" in parsed
            assert len(parsed["issues"]) <= 3

            # Verify issue structure in search results
            for issue in parsed["issues"]:
                assert "id" in issue
                assert "key" in issue
                assert issue["key"].startswith("FTEST-")
                assert "summary" in issue
                assert "description" in issue
                assert issue["description"]["type"] == "doc"  # ADF format
                assert "status" in issue
                assert "assignee" in issue
                assert "reporter" in issue
                assert "created" in issue
                assert "updated" in issue

    @pytest.mark.anyio
    async def test_get_user_profile_with_real_response(
        self, mock_context, mock_jira_fetcher
    ):
        """Test getting user profile returns real API response structure."""
        from mcp_atlassian.servers.jira.management import get_user_profile

        with patch(
            "mcp_atlassian.servers.jira.management.get_jira_fetcher"
        ) as mock_get_fetcher:
            mock_get_fetcher.side_effect = self.create_async_mock_fetcher(
                mock_jira_fetcher
            )

            # Act
            result = await get_user_profile(mock_context, "douglas.mason@mlb.com")
            parsed = json.loads(result)

            # Assert - Verify real response structure matches our simplified format
            assert "display_name" in parsed
            assert "name" in parsed
            assert "email" in parsed
            assert "avatar_url" in parsed

            # Verify the values match the real response
            assert parsed["display_name"] == REAL_USER_PROFILE["display_name"]
            assert parsed["name"] == REAL_USER_PROFILE["name"]
            assert parsed["email"] == REAL_USER_PROFILE["email"]
            assert parsed["avatar_url"] == REAL_USER_PROFILE["avatar_url"]


class TestJiraResponseValidation:
    """Test that our mocks properly validate against real response structures."""

    def test_adf_format_in_descriptions(self):
        """Verify that descriptions use ADF format, not plain text."""
        # Real responses use Atlassian Document Format (ADF)
        assert REAL_ISSUE_CREATE_RESPONSE["description"]["type"] == "doc"
        assert REAL_ISSUE_CREATE_RESPONSE["description"]["version"] == 1
        assert "content" in REAL_ISSUE_CREATE_RESPONSE["description"]

        # Each content block has specific structure
        content = REAL_ISSUE_CREATE_RESPONSE["description"]["content"][0]
        assert content["type"] == "paragraph"
        assert "content" in content
        assert content["content"][0]["type"] == "text"
        assert "text" in content["content"][0]

    def test_status_structure(self):
        """Verify status objects have the correct structure."""
        status = REAL_ISSUE_GET_RESPONSE["status"]
        assert "name" in status
        assert "category" in status
        assert "color" in status

        # Status transitions have more detailed structure
        transition = REAL_ISSUE_TRANSITIONS[0]
        assert "to" in transition
        assert "statusCategory" in transition["to"]
        assert "id" in transition["to"]["statusCategory"]
        assert "key" in transition["to"]["statusCategory"]
        assert "colorName" in transition["to"]["statusCategory"]

    def test_user_object_structure(self):
        """Verify user objects have consistent structure."""
        assignee = REAL_ISSUE_CREATE_RESPONSE["assignee"]
        assert "display_name" in assignee
        assert "name" in assignee
        assert "email" in assignee
        assert "avatar_url" in assignee

        # User profile matches the simplified format we return
        assert "display_name" in REAL_USER_PROFILE
        assert "name" in REAL_USER_PROFILE
        assert "email" in REAL_USER_PROFILE
        assert "avatar_url" in REAL_USER_PROFILE

    def test_search_response_pagination(self):
        """Verify search responses include pagination info."""
        assert "total" in REAL_SEARCH_RESPONSE
        assert "start_at" in REAL_SEARCH_RESPONSE
        assert "max_results" in REAL_SEARCH_RESPONSE
        assert "issues" in REAL_SEARCH_RESPONSE
        assert isinstance(REAL_SEARCH_RESPONSE["issues"], list)

    def test_timestamp_format(self):
        """Verify timestamp formats in responses."""
        # Timestamps use ISO format with timezone
        created = REAL_ISSUE_CREATE_RESPONSE["created"]
        assert "T" in created  # ISO format separator
        assert "-" in created  # Timezone offset

        # Updated should be after or equal to created
        updated = REAL_ISSUE_CREATE_RESPONSE["updated"]
        assert updated >= created
