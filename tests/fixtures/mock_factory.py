"""
Mock factory for creating realistic client mocks for testing.

This module provides factories for creating mock objects that behave like
real Jira and Confluence clients, using actual response data structures
to ensure tests validate the real behavior patterns.
"""

import json
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from .jira_mocks import MOCK_JIRA_ISSUE_RESPONSE
from .confluence_mocks import MOCK_CONFLUENCE_PAGE_RESPONSE


class MockJiraClient:
    """Mock Jira client that returns realistic responses."""

    def __init__(self):
        self.base_url = "https://test.atlassian.net"
        self.session = MagicMock()

    def create_issue(self,
                    project_key: str,
                    summary: str,
                    issue_type: str,
                    description: str = "",
                    assignee: Optional[str] = None,
                    components: Optional[List[str]] = None,
                    **kwargs) -> MagicMock:
        """Mock issue creation with realistic response matching actual interface."""
        mock_issue = MagicMock()

        # Create a realistic response based on input
        response_data = MOCK_JIRA_ISSUE_RESPONSE.copy()
        response_data["fields"]["summary"] = summary
        response_data["key"] = f"{project_key}-123"

        mock_issue.key = response_data["key"]
        mock_issue.to_simplified_dict.return_value = {
            "key": response_data["key"],
            "id": response_data["id"],
            "summary": summary,
            "status": response_data["fields"]["status"],
            "issuetype": response_data["fields"]["issuetype"]
        }

        return mock_issue

    def get_issue(self, issue_key: str, fields: Optional[str] = None, **kwargs):
        """Mock issue retrieval with realistic response."""
        response_data = MOCK_JIRA_ISSUE_RESPONSE.copy()
        response_data["key"] = issue_key

        # Handle issuelinks field specifically for RelationshipManager
        if fields and "issuelinks" in fields:
            # Return a simple object with issuelinks data
            class MockIssueWithLinks:
                def __init__(self, issue_key):
                    self.key = issue_key
                    self.issuelinks = [
                        {
                            "id": "12345",
                            "type": {"name": "Relates", "inward": "relates to", "outward": "relates to"},
                            "inwardIssue": {"key": "FTEST-1492", "fields": {"summary": "First Issue"}},
                            "outwardIssue": {"key": "FTEST-1493", "fields": {"summary": "Second Issue"}}
                        }
                    ]

                def to_simplified_dict(self):
                    return {
                        "key": self.key,
                        "id": response_data["id"],
                        "summary": response_data["fields"]["summary"],
                        "status": response_data["fields"]["status"],
                        "issuetype": response_data["fields"]["issuetype"]
                    }

            return MockIssueWithLinks(issue_key)
        else:
            # Return normal MagicMock for other cases
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {
                "key": issue_key,
                "id": response_data["id"],
                "summary": response_data["fields"]["summary"],
                "status": response_data["fields"]["status"],
                "issuetype": response_data["fields"]["issuetype"]
            }
            return mock_issue

    def update_issue(self, issue_key: str, update_data: Dict[str, Any]) -> MagicMock:
        """Mock issue update with realistic response."""
        mock_issue = MagicMock()
        response_data = MOCK_JIRA_ISSUE_RESPONSE.copy()
        response_data["key"] = issue_key

        # Update fields based on input
        if "summary" in update_data:
            response_data["fields"]["summary"] = update_data["summary"]

        mock_issue.to_simplified_dict.return_value = {
            "key": issue_key,
            "id": response_data["id"],
            "summary": response_data["fields"]["summary"],
            "status": response_data["fields"]["status"],
            "issuetype": response_data["fields"]["issuetype"]
        }

        return mock_issue

    def search_issues(self, jql: str, fields: Optional[List[str]] = None, limit: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Mock issue search with realistic response."""
        return {
            "issues": [
                {
                    "key": "TEST-123",
                    "fields": {
                        "summary": "Mock Search Result",
                        "status": {"name": "To Do"}
                    }
                }
            ],
            "total": 1,
            "startAt": 0,
            "maxResults": 50
        }

    def get_current_user_account_id(self) -> str:
        """Mock current user retrieval."""
        return "mock-user-account-id-123"

    def transition_issue(self, issue_key: str, transition: Dict[str, Any] = None, transition_id: str = None, **kwargs) -> bool:
        """Mock issue transition with support for transition_id."""
        return True

    def get_issue_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """Mock getting available transitions."""
        return [
            {
                "id": "21",
                "name": "In Progress",
                "to": {"name": "In Progress", "id": "3"}
            },
            {
                "id": "31",
                "name": "Done",
                "to": {"name": "Done", "id": "6"}
            }
        ]

    def create_issue_link(self, link_data: Dict[str, Any] = None, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Mock issue link creation."""
        # Accept both link_data and data parameters for compatibility
        link_info = link_data or data or {}
        return {"id": "mock-link-id-12345"}

    def get_all_projects(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """Mock getting all projects."""
        projects = [
            {
                "key": "FTEST",
                "name": "Test Project",
                "id": "10000",
                "projectTypeKey": "software"
            },
            {
                "key": "DEMO",
                "name": "Demo Project",
                "id": "10001",
                "projectTypeKey": "business"
            }
        ]

        if include_archived:
            projects.append({
                "key": "ARCH",
                "name": "Archived Project",
                "id": "10002",
                "projectTypeKey": "software",
                "archived": True
            })

        return projects

    def get_available_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """Mock getting available transitions for an issue."""
        return [
            {
                "id": "21",
                "name": "To Do",
                "to": {"name": "To Do", "id": "1"}
            },
            {
                "id": "41",
                "name": "Done",
                "to": {"name": "Done", "id": "6"}
            },
            {
                "id": "2",
                "name": "Start Work",
                "to": {"name": "In Progress", "id": "3"}
            }
        ]

    def get_project_statuses(self, project_key: str) -> List[Dict[str, Any]]:
        """Mock getting statuses for a project."""
        return [
            {"id": "1", "name": "To Do", "statusCategory": {"name": "To Do"}},
            {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
            {"id": "6", "name": "Done", "statusCategory": {"name": "Done"}}
        ]

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Mock getting all statuses in the instance."""
        return [
            {"id": "1", "name": "To Do", "statusCategory": {"name": "To Do"}},
            {"id": "2", "name": "Open", "statusCategory": {"name": "To Do"}},
            {"id": "3", "name": "In Progress", "statusCategory": {"name": "In Progress"}},
            {"id": "4", "name": "Reopened", "statusCategory": {"name": "To Do"}},
            {"id": "5", "name": "Resolved", "statusCategory": {"name": "Done"}},
            {"id": "6", "name": "Done", "statusCategory": {"name": "Done"}}
        ]

    def search_users(self, query: str, start_at: int = 0, max_results: int = 50) -> List[Dict[str, Any]]:
        """Mock user search."""
        return [
            {
                "accountId": "mock-user-123",
                "displayName": "Test User",
                "emailAddress": "test@example.com"
            },
            {
                "accountId": "mock-user-456",
                "displayName": "Another User",
                "emailAddress": "another@example.com"
            }
        ]

    def get_issue_links(self, issue_key: str) -> List[Dict[str, Any]]:
        """Mock getting issue links."""
        # Return proper dict structure that's JSON serializable
        return [
            {
                "id": "12345",
                "type": {"name": "Relates", "inward": "relates to", "outward": "relates to"},
                "inwardIssue": {"key": "FTEST-1492", "fields": {"summary": "First Issue"}},
                "outwardIssue": {"key": "FTEST-1493", "fields": {"summary": "Second Issue"}}
            }
        ]


class MockConfluenceClient:
    """Mock Confluence client that returns realistic responses."""

    def __init__(self):
        self.base_url = "https://test.atlassian.net"
        self.session = MagicMock()

    def create_page(self, page_data: Dict[str, Any]) -> MagicMock:
        """Mock page creation with realistic response."""
        mock_page = MagicMock()

        # Create realistic response based on input
        response_data = MOCK_CONFLUENCE_PAGE_RESPONSE.copy()
        if "title" in page_data:
            response_data["title"] = page_data["title"]
        if "space_key" in page_data:
            response_data["space"]["key"] = page_data["space_key"]

        mock_page.to_dict.return_value = {
            "id": response_data["id"],
            "title": response_data["title"],
            "space": response_data["space"],
            "version": response_data["version"]
        }

        return mock_page

    def get_page(self, page_id: str) -> MagicMock:
        """Mock page retrieval with realistic response."""
        mock_page = MagicMock()
        response_data = MOCK_CONFLUENCE_PAGE_RESPONSE.copy()
        response_data["id"] = page_id

        mock_page.to_dict.return_value = {
            "id": page_id,
            "title": response_data["title"],
            "space": response_data["space"],
            "version": response_data["version"]
        }

        return mock_page

    def update_page(self, page_id: str, page_data: Dict[str, Any]) -> MagicMock:
        """Mock page update with realistic response."""
        mock_page = MagicMock()
        response_data = MOCK_CONFLUENCE_PAGE_RESPONSE.copy()
        response_data["id"] = page_id

        # Update fields based on input
        if "title" in page_data:
            response_data["title"] = page_data["title"]

        mock_page.to_dict.return_value = {
            "id": page_id,
            "title": response_data["title"],
            "space": response_data["space"],
            "version": response_data["version"]
        }

        return mock_page

    def get_current_user(self) -> Dict[str, Any]:
        """Mock current user retrieval."""
        return {
            "accountId": "mock-user-account-id-456",
            "email": "test@example.com",
            "displayName": "Test User"
        }

    def search_content(self, cql: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Mock content search with realistic response."""
        return {
            "results": [
                {
                    "id": "123456",
                    "title": "Mock Search Result",
                    "type": "page",
                    "space": {"key": "TEST"}
                }
            ],
            "start": 0,
            "limit": limit or 25,
            "size": 1
        }

    def get_all_spaces(self, start: int = 0, limit: int = 500, **kwargs) -> Dict[str, Any]:
        """Mock getting all spaces."""
        return {
            "results": [
                {
                    "id": "1234567",
                    "key": "~911651470",
                    "name": "Personal Space",
                    "type": "personal",
                    "status": "current"
                },
                {
                    "id": "7654321",
                    "key": "TEAMSPACE",
                    "name": "Team Space",
                    "type": "global",
                    "status": "current"
                }
            ],
            "start": start,
            "limit": limit,
            "size": 2
        }


class MockClientFactory:
    """Factory for creating mock clients with proper dependency injection."""

    @staticmethod
    def create_jira_client(config: Any = None) -> MockJiraClient:
        """Create a mock Jira client with realistic behavior."""
        return MockJiraClient()

    @staticmethod
    def create_confluence_client(config: Any = None) -> MockConfluenceClient:
        """Create a mock Confluence client with realistic behavior."""
        return MockConfluenceClient()

    @staticmethod
    async def create_async_jira_client(config: Any = None) -> MockJiraClient:
        """Create an async mock Jira client."""
        client = MockJiraClient()

        # Make async methods actually async
        async def async_create_issue(issue_data):
            return client.create_issue(issue_data)

        async def async_get_current_user_account_id():
            return client.get_current_user_account_id()

        async def async_search_issues(jql, fields=None):
            return client.search_issues(jql, fields)

        # Replace sync methods with async versions
        client.create_issue = async_create_issue
        client.get_current_user_account_id = async_get_current_user_account_id
        client.search_issues = async_search_issues

        return client

    @staticmethod
    async def create_async_confluence_client(config: Any = None) -> MockConfluenceClient:
        """Create an async mock Confluence client."""
        client = MockConfluenceClient()

        # Make async methods actually async
        async def async_create_page(page_data):
            return client.create_page(page_data)

        async def async_get_current_user():
            return client.get_current_user()

        async def async_search_content(cql, limit=None):
            return client.search_content(cql, limit)

        # Replace sync methods with async versions
        client.create_page = async_create_page
        client.get_current_user = async_get_current_user
        client.search_content = async_search_content

        return client


def create_realistic_app_context() -> MagicMock:
    """Create a realistic mock app context for testing."""
    app_context = MagicMock()

    # Mock Jira configuration
    app_context.full_jira_config = MagicMock()
    app_context.full_jira_config.url = "https://test.atlassian.net"
    app_context.full_jira_config.auth_type = "oauth"
    app_context.full_jira_config.is_auth_configured.return_value = True
    app_context.full_jira_config.username = "test@example.com"
    app_context.full_jira_config.api_token = "mock-api-token"

    # Mock Confluence configuration
    app_context.full_confluence_config = MagicMock()
    app_context.full_confluence_config.url = "https://test.atlassian.net"
    app_context.full_confluence_config.auth_type = "oauth"
    app_context.full_confluence_config.is_auth_configured.return_value = True
    app_context.full_confluence_config.username = "test@example.com"
    app_context.full_confluence_config.api_token = "mock-api-token"

    return app_context


def create_realistic_server_context(app_context: Optional[MagicMock] = None) -> MagicMock:
    """Create a realistic mock server context for testing."""
    if app_context is None:
        app_context = create_realistic_app_context()

    server = MagicMock()
    mock_mcp_server = MagicMock()
    mock_request_context = MagicMock()
    mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
    mock_mcp_server.request_context = mock_request_context
    server._mcp_server = mock_mcp_server

    return server