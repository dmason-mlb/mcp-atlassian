"""Tests for Jira Issues mixin - Issue Creation functionality."""

from unittest.mock import ANY, MagicMock, patch

import pytest

from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.issues import IssuesMixin, logger
from mcp_atlassian.models.jira import JiraIssue


class TestIssuesCreationMixin:
    """Tests for the IssuesMixin class - Issue Creation functionality."""

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

    def test_create_issue_basic(self, issues_mixin: IssuesMixin):
        """Test creating a basic issue."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock the issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue",
                "description": "This is a test issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data

        # Mock empty comments
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Call create_issue
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue",
            issue_type="Bug",
            description="This is a test issue",
        )

        # Verify API calls
        # For Cloud instances, the description is converted to ADF format
        expected_fields = {
            "project": {"key": "TEST"},
            "summary": "Test Issue",
            "issuetype": {"name": "Bug"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "This is a test issue"}]}]}',
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)
        issues_mixin.jira.get_issue.assert_called_once_with("TEST-123")

        # Verify issue
        assert issue.key == "TEST-123"
        assert issue.summary == "Test Issue"

    def test_create_issue_with_assignee_cloud(self, issues_mixin: IssuesMixin):
        """Test creating an issue with an assignee for cloud."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue",
                "description": "Test issue with assignee",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "assignee": {"displayName": "Test User", "accountId": "test-user"},
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Set up for cloud instance
        issues_mixin.config.cloud = True

        # Call create_issue with assignee
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue",
            issue_type="Bug",
            description="Test issue with assignee",
            assignee="test-user",
        )

        # Verify API calls - assignee field should use accountId
        expected_fields = {
            "project": {"key": "TEST"},
            "summary": "Test Issue",
            "issuetype": {"name": "Bug"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test issue with assignee"}]}]}',
            "assignee": {"accountId": "test-user"},
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)

        # Verify issue
        assert issue.key == "TEST-123"
        assert issue.assignee.account_id == "test-user"

    def test_create_epic(self, issues_mixin: IssuesMixin):
        """Test creating an epic issue."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "EPIC-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock the issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "EPIC-123",
            "fields": {
                "summary": "Test Epic",
                "description": "This is a test epic",
                "status": {"name": "Open"},
                "issuetype": {"name": "Epic"},
                "customfield_10011": "Test Epic Name",  # Epic Name field
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Mock field mapping for epic fields
        issues_mixin.get_field_ids_to_epic = MagicMock(
            return_value={"epic_name": "customfield_10011"}
        )

        # Call create_issue for epic
        issue = issues_mixin.create_issue(
            project_key="EPIC",
            summary="Test Epic",
            issue_type="Epic",
            description="This is a test epic",
            additional_fields={"epic_name": "Test Epic Name"},
        )

        # Verify API calls
        expected_fields = {
            "project": {"key": "EPIC"},
            "summary": "Test Epic",
            "issuetype": {"name": "Epic"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "This is a test epic"}]}]}',
            "customfield_10011": "Test Epic Name",  # Epic name field
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)

        # Verify issue
        assert issue.key == "EPIC-123"
        assert issue.summary == "Test Epic"

    def test_create_issue_with_components(self, issues_mixin: IssuesMixin):
        """Test creating an issue with components."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock the issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue with Components",
                "description": "Issue with components",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "components": [{"name": "Frontend"}, {"name": "Backend"}],
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Call create_issue with components
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue with Components",
            issue_type="Bug",
            description="Issue with components",
            components="Frontend,Backend",
        )

        # Verify API calls - components should be array of objects
        expected_fields = {
            "project": {"key": "TEST"},
            "summary": "Test Issue with Components",
            "issuetype": {"name": "Bug"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Issue with components"}]}]}',
            "components": [{"name": "Frontend"}, {"name": "Backend"}],
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)

        # Verify issue
        assert issue.key == "TEST-123"
        assert len(issue.components) == 2

    def test_create_issue_with_labels(self, issues_mixin: IssuesMixin):
        """Test creating an issue with labels."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock the issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue with Labels",
                "description": "Issue with labels",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "labels": ["bug", "frontend"],
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Call create_issue with labels
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue with Labels",
            issue_type="Bug",
            description="Issue with labels",
            additional_fields={"labels": ["bug", "frontend"]},
        )

        # Verify API calls
        expected_fields = {
            "project": {"key": "TEST"},
            "summary": "Test Issue with Labels",
            "issuetype": {"name": "Bug"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Issue with labels"}]}]}',
            "labels": ["bug", "frontend"],
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)

        # Verify issue
        assert issue.key == "TEST-123"
        assert issue.labels == ["bug", "frontend"]

    def test_create_issue_with_fixversions(self, issues_mixin: IssuesMixin):
        """Test creating an issue with fix versions."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock the issue data for get_issue
        issue_data = {
            "id": "12345", 
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue with Fix Version",
                "description": "Issue with fix version",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "fixVersions": [{"name": "v1.0.0", "id": "10020"}],
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Call create_issue with fix versions
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue with Fix Version", 
            issue_type="Bug",
            description="Issue with fix version",
            additional_fields={"fixVersions": [{"name": "v1.0.0"}]},
        )

        # Verify API calls
        expected_fields = {
            "project": {"key": "TEST"},
            "summary": "Test Issue with Fix Version",
            "issuetype": {"name": "Bug"},
            "description": '{"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Issue with fix version"}]}]}',
            "fixVersions": [{"name": "v1.0.0"}],
        }
        issues_mixin.jira.create_issue.assert_called_once_with(fields=expected_fields)

        # Verify issue
        assert issue.key == "TEST-123"
        assert len(issue.fix_versions) == 1
        assert issue.fix_versions[0]["name"] == "v1.0.0"

    def test_process_additional_fields_with_fixversions(self, issues_mixin: IssuesMixin):
        """Test processing additional fields with fix versions."""
        # Mock create_issue response
        create_response = {"id": "12345", "key": "TEST-123"}
        issues_mixin.jira.create_issue.return_value = create_response

        # Mock issue data for get_issue
        issue_data = {
            "id": "12345",
            "key": "TEST-123",
            "fields": {
                "summary": "Test Issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "fixVersions": [{"name": "v2.0.0"}],
            },
        }
        issues_mixin.jira.get_issue.return_value = issue_data
        issues_mixin.jira.issue_get_comments.return_value = {"comments": []}

        # Test with fixVersions in additional_fields
        issue = issues_mixin.create_issue(
            project_key="TEST",
            summary="Test Issue",
            issue_type="Bug",
            additional_fields={"fixVersions": [{"name": "v2.0.0"}]},
        )

        # Verify field processing
        call_args = issues_mixin.jira.create_issue.call_args
        fields = call_args[1]["fields"]
        assert "fixVersions" in fields
        assert fields["fixVersions"] == [{"name": "v2.0.0"}]

        assert issue.key == "TEST-123"