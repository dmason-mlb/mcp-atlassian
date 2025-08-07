"""Tests for Jira Issues mixin - Batch Operations functionality."""

from unittest.mock import MagicMock

import pytest

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.issues import IssuesMixin
from mcp_atlassian.models.jira import JiraIssue


class TestIssuesBatchMixin:
    """Tests for the IssuesMixin class - Batch Operations functionality."""

    @pytest.fixture
    def issues_mixin(self, jira_fetcher: JiraFetcher) -> IssuesMixin:
        """Create an IssuesMixin instance with mocked dependencies."""
        mixin = jira_fetcher

        # Add mock methods that would be provided by other mixins
        mixin._get_account_id = MagicMock(return_value="test-account-id")
        mixin.get_available_transitions = MagicMock(
            return_value=[{"id": "10", "name": "In Progress"}]
        )
        mixin.transition_issue = MagicMock(
            return_value=JiraIssue(id="123", key="TEST-123", summary="Test Issue")
        )

        return mixin

    def test_batch_create_issues_basic(self, issues_mixin: IssuesMixin):
        """Test basic functionality of batch_create_issues."""
        # Setup test data
        issues = [
            {
                "project_key": "TEST",
                "summary": "Test Issue 1",
                "issue_type": "Task",
                "description": "Description 1",
            },
            {
                "project_key": "TEST",
                "summary": "Test Issue 2",
                "issue_type": "Bug",
                "description": "Description 2",
                "assignee": "john.doe",
                "components": ["Frontend"],
            },
        ]

        # Mock bulk create response
        bulk_response = {
            "issues": [
                {"id": "1", "key": "TEST-1", "self": "http://example.com/TEST-1"},
                {"id": "2", "key": "TEST-2", "self": "http://example.com/TEST-2"},
            ],
            "errors": [],
        }
        issues_mixin.jira.create_issues.return_value = bulk_response

        # Mock get_issue responses
        def get_issue_side_effect(key):
            if key == "TEST-1":
                return {
                    "id": "1",
                    "key": "TEST-1",
                    "fields": {"summary": "Test Issue 1"},
                }
            return {"id": "2", "key": "TEST-2", "fields": {"summary": "Test Issue 2"}}

        issues_mixin.jira.get_issue.side_effect = get_issue_side_effect
        issues_mixin._get_account_id.return_value = "user123"

        # Call the method
        result = issues_mixin.batch_create_issues(issues)

        # Verify results
        assert len(result) == 2
        assert result[0].key == "TEST-1"
        assert result[1].key == "TEST-2"

        # Verify bulk create was called correctly
        issues_mixin.jira.create_issues.assert_called_once()
        call_args = issues_mixin.jira.create_issues.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["fields"]["summary"] == "Test Issue 1"
        assert call_args[1]["fields"]["summary"] == "Test Issue 2"

    def test_batch_create_issues_validate_only(self, issues_mixin: IssuesMixin):
        """Test batch_create_issues with validate_only=True."""
        # Setup test data
        issues = [
            {
                "project_key": "TEST",
                "summary": "Test Issue 1",
                "issue_type": "Task",
            },
            {
                "project_key": "TEST",
                "summary": "Test Issue 2",
                "issue_type": "Bug",
            },
        ]

        # Call the method with validate_only=True
        result = issues_mixin.batch_create_issues(issues, validate_only=True)

        # Verify no issues were created
        assert len(result) == 0
        assert not issues_mixin.jira.create_issues.called

    def test_batch_create_issues_missing_required_fields(
        self, issues_mixin: IssuesMixin
    ):
        """Test batch_create_issues with missing required fields."""
        # Setup test data with missing fields
        issues = [
            {
                "project_key": "TEST",
                "summary": "Test Issue 1",
                # Missing issue_type
            },
            {
                "project_key": "TEST",
                "summary": "Test Issue 2",
                "issue_type": "Bug",
            },
        ]

        # Verify it raises ValueError
        with pytest.raises(ValueError) as exc_info:
            issues_mixin.batch_create_issues(issues)

        assert "Missing required fields" in str(exc_info.value)
        assert not issues_mixin.jira.create_issues.called

    def test_batch_create_issues_partial_failure(self, issues_mixin: IssuesMixin):
        """Test batch_create_issues when some issues fail to create."""
        # Setup test data
        issues = [
            {
                "project_key": "TEST",
                "summary": "Test Issue 1",
                "issue_type": "Task",
            },
            {
                "project_key": "TEST",
                "summary": "Test Issue 2",
                "issue_type": "Bug",
            },
        ]

        # Mock bulk create response with an error
        bulk_response = {
            "issues": [
                {"id": "1", "key": "TEST-1", "self": "http://example.com/TEST-1"},
            ],
            "errors": [{"issue": {"key": None}, "error": "Invalid issue type"}],
        }
        issues_mixin.jira.create_issues.return_value = bulk_response

        # Mock get_issue response for successful creation
        issues_mixin.jira.get_issue.return_value = {
            "id": "1",
            "key": "TEST-1",
            "fields": {"summary": "Test Issue 1"},
        }

        # Call the method
        result = issues_mixin.batch_create_issues(issues)

        # Verify results - should have only the first issue
        assert len(result) == 1
        assert result[0].key == "TEST-1"

        # Verify error was logged
        issues_mixin.jira.create_issues.assert_called_once()
        assert len(issues_mixin.jira.get_issue.mock_calls) == 1

    def test_batch_create_issues_empty_list(self, issues_mixin: IssuesMixin):
        """Test batch_create_issues with an empty list."""
        result = issues_mixin.batch_create_issues([])
        assert result == []
        assert not issues_mixin.jira.create_issues.called

    def test_batch_create_issues_with_components(self, issues_mixin: IssuesMixin):
        """Test batch_create_issues with component handling."""
        # Setup test data with various component formats
        issues = [
            {
                "project_key": "TEST",
                "summary": "Test Issue 1",
                "issue_type": "Task",
                "components": ["Frontend", "", None, "  Backend  "],
            }
        ]

        # Mock responses
        bulk_response = {
            "issues": [
                {"id": "1", "key": "TEST-1", "self": "http://example.com/TEST-1"},
            ],
            "errors": [],
        }
        issues_mixin.jira.create_issues.return_value = bulk_response
        issues_mixin.jira.get_issue.return_value = {
            "id": "1",
            "key": "TEST-1",
            "fields": {"summary": "Test Issue 1"},
        }

        # Call the method
        result = issues_mixin.batch_create_issues(issues)

        # Verify results
        assert len(result) == 1

        # Verify components were properly formatted
        call_args = issues_mixin.jira.create_issues.call_args[0][0]
        assert len(call_args) == 1
        components = call_args[0]["fields"]["components"]
        assert len(components) == 2
        assert components[0]["name"] == "Frontend"
        assert components[1]["name"] == "Backend"

    def test_add_assignee_to_fields_cloud(self, issues_mixin: IssuesMixin):
        """Test _add_assignee_to_fields for Cloud instance."""
        # Set up cloud config
        issues_mixin.config = MagicMock()
        issues_mixin.config.is_cloud = True

        # Test fields dict
        fields = {}

        # Call the method
        issues_mixin._add_assignee_to_fields(fields, "account-123")

        # Verify result
        assert fields["assignee"] == {"accountId": "account-123"}

    def test_add_assignee_to_fields_server_dc(self, issues_mixin: IssuesMixin):
        """Test _add_assignee_to_fields for Server/Data Center instance."""
        # Set up Server/DC config
        issues_mixin.config = MagicMock()
        issues_mixin.config.is_cloud = False

        # Test fields dict
        fields = {}

        # Call the method
        issues_mixin._add_assignee_to_fields(fields, "jdoe")

        # Verify result
        assert fields["assignee"] == {"name": "jdoe"}

    def test_batch_get_changelogs_not_cloud(self, issues_mixin: IssuesMixin):
        """Test batch_get_changelogs method on non-cloud instance."""
        issues_mixin.config = MagicMock()
        issues_mixin.config.is_cloud = False

        with pytest.raises(NotImplementedError):
            issues_mixin.batch_get_changelogs(
                issue_ids_or_keys=["TEST-123"],
                fields=["summary", "description"],
            )

    def test_batch_get_changelogs_cloud(self, issues_mixin: IssuesMixin):
        """Test batch_get_changelogs method on cloud instance."""
        issues_mixin.config = MagicMock()
        issues_mixin.config.is_cloud = True

        # Mock get_paged result
        mock_get_paged_result = [
            {
                "issueChangeLogs": [
                    {
                        "issueId": "TEST-1",
                        "changeHistories": [
                            {
                                "id": "10001",
                                "author": {
                                    "accountId": "user123",
                                    "displayName": "Test User 1",
                                    "active": True,
                                    "timeZone": "UTC",
                                    "accountType": "atlassian",
                                },
                                "created": "2024-01-05T10:06:03.548+0800",
                                "items": [
                                    {
                                        "field": "IssueParentAssociation",
                                        "fieldtype": "jira",
                                        "from": None,
                                        "fromString": None,
                                        "to": "1001",
                                        "toString": "TEST-100",
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "issueId": "TEST-2",
                        "changeHistories": [
                            {
                                "id": "10002",
                                "author": {
                                    "accountId": "user456",
                                    "displayName": "Test User 2",
                                    "active": True,
                                    "timeZone": "UTC",
                                    "accountType": "atlassian",
                                },
                                "created": "1704106800000",  # 2024-01-01
                                "items": [
                                    {
                                        "field": "Parent",
                                        "fieldtype": "jira",
                                        "from": None,
                                        "fromString": None,
                                        "to": "1002",
                                        "toString": "TEST-200",
                                    }
                                ],
                            },
                            {
                                "id": "10003",
                                "author": {
                                    "accountId": "user789",
                                    "displayName": "Test User 3",
                                    "active": True,
                                    "timeZone": "UTC",
                                    "accountType": "atlassian",
                                },
                                "created": "2024-01-06T10:06:03.548+0800",
                                "items": [
                                    {
                                        "field": "Parent",
                                        "fieldtype": "jira",
                                        "from": "1002",
                                        "fromString": "TEST-200",
                                        "to": "1003",
                                        "toString": "TEST-300",
                                    }
                                ],
                            },
                        ],
                    },
                ],
                "nextPageToken": "token1",
            },
            {
                "issueChangeLogs": [
                    {
                        "issueId": "TEST-2",
                        "changeHistories": [
                            {
                                "id": "10004",
                                "author": {
                                    "accountId": "user123",
                                    "displayName": "Test User 1",
                                    "active": True,
                                    "timeZone": "UTC",
                                    "accountType": "atlassian",
                                },
                                "created": "2024-01-10T10:06:03.548+0800",
                                "items": [
                                    {
                                        "field": "Parent",
                                        "fieldtype": "jira",
                                        "from": "1003",
                                        "fromString": "TEST-300",
                                        "to": "1004",
                                        "toString": "TEST-400",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        ]

        # Expected result
        expected_result = [
            {
                "assignee": {"display_name": "Unassigned"},
                "changelogs": [
                    {
                        "author": {
                            "avatar_url": None,
                            "display_name": "Test User 1",
                            "email": None,
                            "name": "Test User 1",
                        },
                        "created": "2024-01-05 10:06:03.548000+08:00",
                        "items": [
                            {
                                "field": "IssueParentAssociation",
                                "fieldtype": "jira",
                                "to_id": "1001",
                                "to_string": "TEST-100",
                            },
                        ],
                    },
                ],
                "id": "TEST-1",
                "key": "UNKNOWN-0",
                "summary": "",
            },
            {
                "assignee": {"display_name": "Unassigned"},
                "changelogs": [
                    {
                        "author": {
                            "avatar_url": None,
                            "display_name": "Test User 2",
                            "email": None,
                            "name": "Test User 2",
                        },
                        "created": "2024-01-01 11:00:00+00:00",
                        "items": [
                            {
                                "field": "Parent",
                                "fieldtype": "jira",
                                "to_id": "1002",
                                "to_string": "TEST-200",
                            },
                        ],
                    },
                    {
                        "author": {
                            "avatar_url": None,
                            "display_name": "Test User 3",
                            "email": None,
                            "name": "Test User 3",
                        },
                        "created": "2024-01-06 10:06:03.548000+08:00",
                        "items": [
                            {
                                "field": "Parent",
                                "fieldtype": "jira",
                                "from_id": "1002",
                                "from_string": "TEST-200",
                                "to_id": "1003",
                                "to_string": "TEST-300",
                            },
                        ],
                    },
                    {
                        "author": {
                            "avatar_url": None,
                            "display_name": "Test User 1",
                            "email": None,
                            "name": "Test User 1",
                        },
                        "created": "2024-01-10 10:06:03.548000+08:00",
                        "items": [
                            {
                                "field": "Parent",
                                "fieldtype": "jira",
                                "from_id": "1003",
                                "from_string": "TEST-300",
                                "to_id": "1004",
                                "to_string": "TEST-400",
                            },
                        ],
                    },
                ],
                "id": "TEST-2",
                "key": "UNKNOWN-0",
                "summary": "",
            },
        ]

        # Mock the get_paged method
        issues_mixin.get_paged = MagicMock(return_value=mock_get_paged_result)

        # Call the method
        result = issues_mixin.batch_get_changelogs(
            issue_ids_or_keys=["TEST-1", "TEST-2"],
            fields=["Parent"],
        )

        # Verify the result
        simplified_result = [issue.to_simplified_dict() for issue in result]
        assert simplified_result == expected_result

        # Verify the method was called with the correct arguments
        issues_mixin.get_paged.assert_called_once_with(
            method="post",
            url=issues_mixin.jira.resource_url("changelog/bulkfetch"),
            params_or_json={
                "fieldIds": ["Parent"],
                "issueIdsOrKeys": ["TEST-1", "TEST-2"],
            },
        )