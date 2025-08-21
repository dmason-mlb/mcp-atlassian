"""Tests for the JiraWorklog model and real API validation."""

import os
import re

import pytest

from src.mcp_atlassian.models.constants import EMPTY_STRING, JIRA_DEFAULT_ID, UNKNOWN
from src.mcp_atlassian.models.jira import JiraWorklog

# Optional: Import real API client for optional real-data testing
try:
    from mcp_atlassian.jira import JiraConfig, JiraFetcher
    from mcp_atlassian.jira.issues import IssuesMixin
    from mcp_atlassian.jira.projects import ProjectsMixin
    from mcp_atlassian.jira.transitions import TransitionsMixin
    from mcp_atlassian.jira.worklog import WorklogMixin
    from mcp_atlassian.rest.adapters import JiraAdapter

    real_api_available = True
except ImportError:
    real_api_available = False

    # Create a module-level namespace for dummy classes
    class _DummyClasses:
        """Namespace for dummy classes when real imports fail."""

        class JiraFetcher:
            pass

        class JiraConfig:
            @staticmethod
            def from_env():
                return None

        class IssuesMixin:
            pass

        class ProjectsMixin:
            pass

        class TransitionsMixin:
            pass

        class WorklogMixin:
            pass

        class JiraAdapter:
            pass

    # Assign dummy classes to module namespace
    JiraFetcher = _DummyClasses.JiraFetcher
    JiraConfig = _DummyClasses.JiraConfig
    IssuesMixin = _DummyClasses.IssuesMixin
    ProjectsMixin = _DummyClasses.ProjectsMixin
    TransitionsMixin = _DummyClasses.TransitionsMixin
    WorklogMixin = _DummyClasses.WorklogMixin
    JiraAdapter = _DummyClasses.JiraAdapter


class TestJiraWorklog:
    """Tests for the JiraWorklog model."""

    def test_from_api_response_with_valid_data(self):
        """Test creating a JiraWorklog from valid API data."""
        worklog_data = {
            "id": "10000",
            "issueId": "10001",
            "author": {
                "accountId": "author123",
                "displayName": "Worklog Author",
                "emailAddress": "author@example.com",
                "active": True,
            },
            "updateAuthor": {
                "accountId": "updater456",
                "displayName": "Worklog Updater",
                "emailAddress": "updater@example.com",
                "active": True,
            },
            "comment": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Worked on bug fix"}],
                    }
                ],
            },
            "created": "2023-01-01T09:00:00.000+0000",
            "updated": "2023-01-01T09:15:00.000+0000",
            "started": "2023-01-01T09:00:00.000+0000",
            "timeSpent": "2h 30m",
            "timeSpentSeconds": 9000,
        }

        worklog = JiraWorklog.from_api_response(worklog_data)

        assert worklog.id == "10000"
        assert worklog.issue_id == "10001"
        assert worklog.author.account_id == "author123"
        assert worklog.author.display_name == "Worklog Author"
        assert worklog.update_author.account_id == "updater456"
        assert worklog.update_author.display_name == "Worklog Updater"
        assert isinstance(worklog.comment, dict)
        assert worklog.created == "2023-01-01T09:00:00.000+0000"
        assert worklog.updated == "2023-01-01T09:15:00.000+0000"
        assert worklog.started == "2023-01-01T09:00:00.000+0000"
        assert worklog.time_spent == "2h 30m"
        assert worklog.time_spent_seconds == 9000

    def test_from_api_response_minimal_data(self):
        """Test creating a JiraWorklog with minimal data."""
        worklog_data = {
            "id": "10000",
            "timeSpent": "1h",
            "timeSpentSeconds": 3600,
        }

        worklog = JiraWorklog.from_api_response(worklog_data)

        assert worklog.id == "10000"
        assert worklog.issue_id == EMPTY_STRING
        assert worklog.author.account_id == JIRA_DEFAULT_ID
        assert worklog.author.display_name == UNKNOWN
        assert worklog.update_author.account_id == JIRA_DEFAULT_ID
        assert worklog.update_author.display_name == UNKNOWN
        assert worklog.comment == {}
        assert worklog.created == EMPTY_STRING
        assert worklog.updated == EMPTY_STRING
        assert worklog.started == EMPTY_STRING
        assert worklog.time_spent == "1h"
        assert worklog.time_spent_seconds == 3600

    def test_from_api_response_with_none_values(self):
        """Test JiraWorklog handles None values gracefully."""
        worklog_data = {
            "id": "10000",
            "issueId": None,
            "author": None,
            "updateAuthor": None,
            "comment": None,
            "created": None,
            "updated": None,
            "started": None,
            "timeSpent": "30m",
            "timeSpentSeconds": 1800,
        }

        worklog = JiraWorklog.from_api_response(worklog_data)

        assert worklog.id == "10000"
        assert worklog.issue_id == EMPTY_STRING
        assert worklog.author.account_id == JIRA_DEFAULT_ID
        assert worklog.update_author.account_id == JIRA_DEFAULT_ID
        assert worklog.comment == {}
        assert worklog.created == EMPTY_STRING
        assert worklog.updated == EMPTY_STRING
        assert worklog.started == EMPTY_STRING
        assert worklog.time_spent == "30m"
        assert worklog.time_spent_seconds == 1800


@pytest.mark.skipif(
    not real_api_available or os.getenv("SKIP_REAL_API_TESTS", "true") == "true",
    reason="Real API tests disabled or dependencies not available",
)
class TestRealJiraData:
    """Tests against real Jira data for model validation."""

    @pytest.fixture(scope="class")
    def jira_config(self):
        """Create Jira configuration from environment."""
        config = JiraConfig.from_env()
        if not config or not config.url:
            pytest.skip("Jira configuration not available in environment")
        return config

    @pytest.fixture(scope="class")
    def jira_client(self, jira_config):
        """Create Jira client for real API tests."""
        try:
            # Create adapter with config
            adapter = JiraAdapter(
                url=jira_config.url,
                username=jira_config.username,
                password=jira_config.password,
                token=jira_config.token,
                cloud=jira_config.cloud,
                verify_ssl=jira_config.verify_ssl,
            )
            return adapter
        except Exception as e:
            pytest.skip(f"Could not create Jira client: {e}")

    def test_real_issue_model_compatibility(self, jira_client):
        """Test that real API responses work with models."""
        try:
            # Get a few recent issues to test with
            search_result = jira_client.jql(
                "order by created DESC", start_at=0, limit=3
            )

            if not search_result.get("issues"):
                pytest.skip("No issues found in Jira instance")

            issues = search_result["issues"]

            for issue_data in issues:
                # Test that the model can be created
                issue_model = JiraIssue.from_api_response(
                    issue_data, base_url=jira_client.url
                )

                # Validate basic fields
                assert issue_model.key
                assert issue_model.id
                assert issue_model.summary
                assert re.match(r"^[A-Z]+-\d+$", issue_model.key)

                # Validate URLs
                if issue_model.url:
                    assert issue_model.url.startswith(jira_client.url)

                print(f"✓ Successfully validated model for issue {issue_model.key}")

        except Exception as e:
            pytest.fail(f"Model compatibility test failed: {e}")

    def test_real_search_result_model_compatibility(self, jira_client):
        """Test that real search API responses work with models."""
        try:
            # Perform a simple search
            search_data = jira_client.jql("order by created DESC", start_at=0, limit=5)

            # Test that the model can be created
            search_result = JiraSearchResult.from_api_response(search_data)

            # Validate basic fields
            assert search_result.total >= 0
            assert search_result.start_at == 0
            assert search_result.max_results > 0
            assert len(search_result.issues) >= 0

            print(
                f"✓ Successfully validated search result with {len(search_result.issues)} issues"
            )

        except Exception as e:
            pytest.fail(f"Search result model compatibility test failed: {e}")

    def test_real_project_model_compatibility(self, jira_client):
        """Test that real project API responses work with models."""
        try:
            # Get available projects
            projects_data = jira_client.projects()

            if not projects_data:
                pytest.skip("No projects found in Jira instance")

            # Test first few projects
            for project_data in projects_data[:3]:
                # Test that the model can be created
                project_model = JiraProject.from_api_response(project_data)

                # Validate basic fields
                assert project_model.key
                assert project_model.id
                assert project_model.name
                assert re.match(r"^[A-Z][A-Z0-9]*$", project_model.key)

                print(f"✓ Successfully validated model for project {project_model.key}")

        except Exception as e:
            pytest.fail(f"Project model compatibility test failed: {e}")
