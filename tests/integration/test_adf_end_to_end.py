"""Integration tests for ADF implementation end-to-end verification."""

import json
from unittest.mock import Mock

import pytest

from mcp_atlassian.confluence.comments import CommentsMixin
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.confluence.pages import PagesMixin
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.jira.issues import IssuesMixin
from mcp_atlassian.preprocessing import (
    ConfluencePreprocessor,
    JiraPreprocessor,
)


@pytest.mark.integration
class TestConfluenceADFIntegration:
    """Test that Confluence properly uses ADF for Cloud instances."""

    @pytest.fixture
    def mock_cloud_config(self):
        """Create a mock Cloud configuration."""
        config = Mock(spec=ConfluenceConfig)
        config.url = "https://example.atlassian.net/wiki"
        config.auth_type = "oauth"
        config.is_cloud = True
        config.enable_adf = True
        return config

    @pytest.fixture
    def mock_server_config(self):
        """Create a mock Server configuration."""
        config = Mock(spec=ConfluenceConfig)
        config.url = "https://confluence.company.com"
        config.auth_type = "token"
        config.is_cloud = False
        config.enable_adf = False
        return config

    def test_create_page_cloud_uses_adf(self, mock_cloud_config):
        """Test that create_page uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = PagesMixin(mock_cloud_config)
        mixin.confluence = Mock()
        mixin.preprocessor = ConfluencePreprocessor(enable_adf=True)

        # Mock v2 adapter
        mock_v2 = Mock()
        mixin._v2_adapter = mock_v2

        # Mock successful page creation
        mock_v2.create_page.return_value = {"id": "123456"}
        mixin.get_page_content = Mock(return_value=Mock())

        # Create a page with markdown content
        markdown_content = """# Test Page

**Bold** text with *italic* and `code`.

## Features

- Bullet point 1
- Bullet point 2

[Link to docs](https://docs.example.com)"""

        # Call create_page
        result = mixin.create_page(
            space_key="TEST", title="Test Page", body=markdown_content, is_markdown=True
        )

        # Verify v2 adapter was called with ADF format
        assert mock_v2.create_page.called
        call_args = mock_v2.create_page.call_args[1]

        # Check that body is a dict (ADF) not a string
        assert isinstance(call_args["body"], dict)
        assert call_args["representation"] == "atlas_doc_format"

        # Verify ADF structure
        adf_body = call_args["body"]
        assert adf_body["type"] == "doc"
        assert adf_body["version"] == 1
        assert "content" in adf_body

    def test_create_page_server_uses_storage(self, mock_server_config):
        """Test that create_page uses storage format for Server instances."""
        # Create mixin with mocked client
        mixin = PagesMixin(mock_server_config)
        mixin.confluence = Mock()
        mixin.preprocessor = ConfluencePreprocessor(enable_adf=False)

        # No v2 adapter for server
        mixin._v2_adapter = None

        # Mock successful page creation
        mixin.confluence.create_page.return_value = {"id": "123456"}
        mixin.get_page_content = Mock(return_value=Mock())

        # Create a page with markdown content
        markdown_content = "# Test Page\n\n**Bold** text"

        # Call create_page
        result = mixin.create_page(
            space_key="TEST", title="Test Page", body=markdown_content, is_markdown=True
        )

        # Verify confluence.create_page was called with storage format
        assert mixin.confluence.create_page.called
        call_args = mixin.confluence.create_page.call_args[1]

        # Check that body is a string (storage) not a dict
        assert isinstance(call_args["body"], str)
        assert call_args["representation"] == "storage"
        assert "<h1>" in call_args["body"]  # HTML storage format

    def test_update_page_cloud_uses_adf(self, mock_cloud_config):
        """Test that update_page uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = PagesMixin(mock_cloud_config)
        mixin.confluence = Mock()
        mixin.preprocessor = ConfluencePreprocessor(enable_adf=True)

        # Mock v2 adapter
        mock_v2 = Mock()
        mixin._v2_adapter = mock_v2

        # Mock successful page update
        mock_v2.update_page.return_value = {"id": "123456"}
        mixin.get_page_content = Mock(return_value=Mock())

        # Update a page with markdown content
        markdown_content = "## Updated Content\n\n- New bullet point"

        # Call update_page
        result = mixin.update_page(
            page_id="123456",
            title="Updated Page",
            body=markdown_content,
            is_markdown=True,
        )

        # Verify v2 adapter was called with ADF format
        assert mock_v2.update_page.called
        call_args = mock_v2.update_page.call_args[1]

        # Check that body is a dict (ADF) not a string
        assert isinstance(call_args["body"], dict)
        assert call_args["representation"] == "atlas_doc_format"

    def test_add_comment_cloud_uses_adf(self, mock_cloud_config):
        """Test that add_comment uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = CommentsMixin(mock_cloud_config)
        mixin.confluence = Mock()
        mixin.preprocessor = ConfluencePreprocessor(enable_adf=True)

        # Mock successful comment addition
        mock_response = {
            "id": "789",
            "body": {"view": {"value": "<p>Test comment</p>"}},
        }
        mixin.confluence.add_comment.return_value = mock_response
        mixin.confluence.get_page_by_id.return_value = {"space": {"key": "TEST"}}

        # Add a comment with markdown content
        markdown_content = "**Important** comment with `code`"

        # Call add_comment
        result = mixin.add_comment(page_id="123456", content=markdown_content)

        # Verify confluence.add_comment was called
        assert mixin.confluence.add_comment.called
        call_args = mixin.confluence.add_comment.call_args

        # The content should be JSON-serialized ADF
        content_arg = call_args[0][1]  # Second positional argument

        # Parse the JSON to verify it's ADF
        adf_content = json.loads(content_arg)
        assert adf_content["type"] == "doc"
        assert adf_content["version"] == 1
        assert "content" in adf_content


@pytest.mark.integration
class TestJiraADFIntegration:
    """Test that Jira properly uses ADF for Cloud instances."""

    @pytest.fixture
    def mock_cloud_config(self):
        """Create a mock Cloud configuration."""
        config = Mock(spec=JiraConfig)
        config.url = "https://example.atlassian.net"
        config.is_cloud = True
        config.enable_adf = True
        return config

    @pytest.fixture
    def mock_server_config(self):
        """Create a mock Server configuration."""
        config = Mock(spec=JiraConfig)
        config.url = "https://jira.company.com"
        config.is_cloud = False
        config.enable_adf = False
        return config

    def test_create_issue_cloud_uses_adf(self, mock_cloud_config):
        """Test that create_issue uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = IssuesMixin(mock_cloud_config)
        mixin.jira = Mock()
        mixin.preprocessor = JiraPreprocessor(enable_adf=True)

        # Mock user and project lookups
        mixin._resolve_user_identifier = Mock(return_value={"accountId": "user123"})
        mixin._get_project_by_key = Mock(return_value={"id": "10000"})
        mixin._get_issue_type_id = Mock(return_value="10001")

        # Mock successful issue creation
        mock_issue = {
            "id": "10001",
            "key": "TEST-1",
            "fields": {"description": {"type": "doc", "version": 1, "content": []}},
        }
        mixin.jira.create_issue.return_value = mock_issue

        # Create an issue with markdown description
        markdown_description = """## Issue Description

This is a **critical** issue with the following problems:

1. First problem
2. Second problem

See [documentation](https://docs.example.com) for details."""

        # Call create_issue
        result = mixin.create_issue(
            project_key="TEST",
            summary="Test Issue",
            issue_type="Bug",
            description=markdown_description,
        )

        # Verify jira.create_issue was called
        assert mixin.jira.create_issue.called
        call_args = mixin.jira.create_issue.call_args[1]

        # Check that description is ADF format
        fields = call_args["fields"]
        assert "description" in fields
        assert isinstance(fields["description"], dict)
        assert fields["description"]["type"] == "doc"
        assert fields["description"]["version"] == 1

    def test_create_issue_server_uses_wiki(self, mock_server_config):
        """Test that create_issue uses wiki format for Server instances."""
        # Create mixin with mocked client
        mixin = IssuesMixin(mock_server_config)
        mixin.jira = Mock()
        mixin.preprocessor = JiraPreprocessor(enable_adf=False)

        # Mock user and project lookups
        mixin._resolve_user_identifier = Mock(return_value={"name": "testuser"})
        mixin._get_project_by_key = Mock(return_value={"id": "10000"})
        mixin._get_issue_type_id = Mock(return_value="10001")

        # Mock successful issue creation
        mock_issue = {
            "id": "10001",
            "key": "TEST-1",
            "fields": {"description": "h2. Issue Description"},
        }
        mixin.jira.create_issue.return_value = mock_issue

        # Create an issue with markdown description
        markdown_description = "## Issue Description\n\nThis is a **critical** issue"

        # Call create_issue
        result = mixin.create_issue(
            project_key="TEST",
            summary="Test Issue",
            issue_type="Bug",
            description=markdown_description,
        )

        # Verify jira.create_issue was called
        assert mixin.jira.create_issue.called
        call_args = mixin.jira.create_issue.call_args[1]

        # Check that description is wiki format string
        fields = call_args["fields"]
        assert "description" in fields
        assert isinstance(fields["description"], str)
        assert "h2. Issue Description" in fields["description"]

    def test_update_issue_cloud_uses_adf(self, mock_cloud_config):
        """Test that update_issue uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = IssuesMixin(mock_cloud_config)
        mixin.jira = Mock()
        mixin.preprocessor = JiraPreprocessor(enable_adf=True)

        # Mock successful issue update
        mixin.jira.update_issue.return_value = None
        mixin.get_issue = Mock(return_value=Mock())

        # Update an issue with markdown description
        markdown_description = "Updated description with **emphasis**"

        # Call update_issue
        fields = {"description": markdown_description}
        result = mixin.update_issue(issue_key="TEST-1", fields=fields)

        # Verify jira.update_issue was called
        assert mixin.jira.update_issue.called
        call_args = mixin.jira.update_issue.call_args[1]

        # Check that description is ADF format
        fields = call_args["fields"]
        assert "description" in fields
        assert isinstance(fields["description"], dict)
        assert fields["description"]["type"] == "doc"
        assert fields["description"]["version"] == 1

    def test_add_comment_cloud_uses_adf(self, mock_cloud_config):
        """Test that add_comment uses ADF format for Cloud instances."""
        # Create mixin with mocked client
        mixin = IssuesMixin(mock_cloud_config)
        mixin.jira = Mock()
        mixin.preprocessor = JiraPreprocessor(enable_adf=True)

        # Mock successful comment addition
        mock_comment = {
            "id": "10001",
            "body": {"type": "doc", "version": 1, "content": []},
        }
        mixin.jira.add_comment.return_value = mock_comment

        # Add a comment with markdown content
        markdown_comment = "This is a **test** comment with `code`"

        # Call add_comment
        result = mixin.add_comment(issue_key="TEST-1", comment=markdown_comment)

        # Verify jira.add_comment was called
        assert mixin.jira.add_comment.called
        call_args = mixin.jira.add_comment.call_args[1]

        # Check that body is ADF format
        body = call_args["body"]
        assert isinstance(body, dict)
        assert body["type"] == "doc"
        assert body["version"] == 1


@pytest.mark.integration
class TestV2AdapterADFHandling:
    """Test that v2_adapter properly handles ADF format."""

    def test_v2_adapter_create_page_adf_handling(self):
        """Test v2 adapter correctly handles ADF body format."""
        from mcp_atlassian.confluence.v2_adapter import ConfluenceV2Adapter

        # Create adapter with mocked session
        mock_session = Mock()
        mock_session.get.return_value = Mock(
            status_code=200, json=lambda: {"results": [{"id": "space123"}]}
        )
        mock_session.post.return_value = Mock(
            status_code=200, json=lambda: {"id": "page123", "title": "Test"}
        )

        adapter = ConfluenceV2Adapter(
            session=mock_session, base_url="https://example.atlassian.net/wiki"
        )

        # Create page with ADF body
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Test content"}],
                }
            ],
        }

        result = adapter.create_page(
            space_key="TEST",
            title="Test Page",
            body=adf_body,
            representation="atlas_doc_format",
        )

        # Verify POST request was made with correct data
        assert mock_session.post.called
        post_data = mock_session.post.call_args[1]["json"]

        # Check that ADF body is passed directly
        assert post_data["body"] == adf_body
        assert "representation" not in post_data["body"]

    def test_v2_adapter_update_page_adf_handling(self):
        """Test v2 adapter correctly handles ADF body format for updates."""
        from mcp_atlassian.confluence.v2_adapter import ConfluenceV2Adapter

        # Create adapter with mocked session
        mock_session = Mock()
        mock_session.get.return_value = Mock(
            status_code=200, json=lambda: {"version": {"number": 1}}
        )
        mock_session.put.return_value = Mock(
            status_code=200,
            json=lambda: {"id": "page123", "title": "Updated", "spaceId": "space123"},
        )

        adapter = ConfluenceV2Adapter(
            session=mock_session, base_url="https://example.atlassian.net/wiki"
        )

        # Update page with ADF body
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Updated Title"}],
                }
            ],
        }

        result = adapter.update_page(
            page_id="page123",
            title="Updated Page",
            body=adf_body,
            representation="atlas_doc_format",
        )

        # Verify PUT request was made with correct data
        assert mock_session.put.called
        put_data = mock_session.put.call_args[1]["json"]

        # Check that ADF body is passed directly
        assert put_data["body"] == adf_body
        assert "representation" not in put_data["body"]
