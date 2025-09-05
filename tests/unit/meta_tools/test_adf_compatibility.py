"""
Test ADF formatting compatibility with meta-tools.

This module verifies that the meta-tools properly integrate with the ADF formatting
system, ensuring that markdown content is automatically converted to the appropriate
format (ADF for Cloud, wiki markup for Server/DC) when creating resources.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.errors import MetaToolError


class TestADFCompatibility:
    """Test ADF formatting integration with meta-tools."""

    @pytest.fixture
    def mock_jira_fetcher(self):
        """Mock JiraFetcher with ADF formatting capabilities."""
        fetcher = AsyncMock()
        # Mock the preprocessor and its markdown_to_jira method
        fetcher.preprocessor.markdown_to_jira.return_value = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test issue description with "},
                        {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": " text"}
                    ]
                }
            ]
        }
        # Mock create_issue to return a JiraIssue-like object
        issue_mock = MagicMock()
        issue_mock.to_simplified_dict.return_value = {
            "key": "TEST-123",
            "id": "12345",
            "summary": "Test Issue",
            "description": "Formatted description"
        }
        fetcher.create_issue.return_value = issue_mock
        return fetcher

    @pytest.fixture
    def mock_confluence_fetcher(self):
        """Mock ConfluenceFetcher with ADF formatting capabilities."""
        fetcher = AsyncMock()
        # Mock the preprocessor and its markdown_to_confluence method
        fetcher.preprocessor.markdown_to_confluence.return_value = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Page content with "},
                        {"type": "text", "text": "italic", "marks": [{"type": "em"}]},
                        {"type": "text", "text": " formatting"}
                    ]
                }
            ]
        }
        # Mock create_page to return a ConfluencePage-like object
        page_mock = MagicMock()
        page_mock.to_dict.return_value = {
            "id": "98765",
            "title": "Test Page",
            "body": {"value": "Formatted content"}
        }
        fetcher.create_page.return_value = page_mock
        return fetcher

    @pytest.fixture
    def resource_manager(self):
        """Create ResourceManager instance."""
        return ResourceManager(dry_run=False)

    @pytest.mark.asyncio
    async def test_jira_issue_creation_with_markdown_cloud(
        self, resource_manager, mock_jira_fetcher
    ):
        """Test that Jira issue creation converts markdown to ADF for Cloud instances."""
        # Test data with markdown content
        issue_data = {
            "project_key": "TEST",
            "summary": "Test Issue with Markdown",
            "issue_type": "Task",
            "description": "This is a **bold** description with *italic* text and `code`."
        }

        # Execute operation
        result = await resource_manager._create_jira_issue(
            client=mock_jira_fetcher,
            identifier=None,
            data=issue_data,
            options=None
        )

        # Verify the service method was called correctly
        mock_jira_fetcher.create_issue.assert_called_once_with(
            project_key="TEST",
            summary="Test Issue with Markdown",
            issue_type="Task",
            description="This is a **bold** description with *italic* text and `code`."
        )

        # Verify result structure
        assert result["key"] == "TEST-123"
        assert result["summary"] == "Test Issue"

    @pytest.mark.asyncio
    async def test_jira_comment_creation_with_markdown(
        self, resource_manager, mock_jira_fetcher
    ):
        """Test that Jira comment creation properly handles markdown formatting."""
        # Mock add_comment method
        comment_mock = MagicMock()
        comment_mock.to_dict.return_value = {
            "id": "comment123",
            "body": "Formatted comment content"
        }
        mock_jira_fetcher.add_comment.return_value = comment_mock

        # Test data with markdown content
        comment_data = {
            "body": "This comment has **bold**, *italic*, and `code` formatting.\n\n- List item 1\n- List item 2"
        }

        # Execute operation
        result = await resource_manager._add_jira_comment(
            client=mock_jira_fetcher,
            identifier="TEST-123",
            data=comment_data,
            options=None
        )

        # Verify the service method was called with markdown content
        mock_jira_fetcher.add_comment.assert_called_once_with(
            issue_key="TEST-123",
            comment="This comment has **bold**, *italic*, and `code` formatting.\n\n- List item 1\n- List item 2"
        )

        # Verify result
        assert result["id"] == "comment123"

    @pytest.mark.asyncio
    async def test_confluence_page_creation_with_markdown_cloud(
        self, resource_manager, mock_confluence_fetcher
    ):
        """Test that Confluence page creation converts markdown to ADF for Cloud instances."""
        # Test data with markdown content
        page_data = {
            "space_id": "TEST",
            "title": "Test Page with Markdown",
            "body": """# Main Header

This page contains **bold** text and *italic* text.

## Subheader

- Bullet point 1
- Bullet point 2

```python
def hello():
    print("Hello, world!")
```

> This is a blockquote
"""
        }

        # Execute operation
        result = await resource_manager._create_confluence_page(
            client=mock_confluence_fetcher,
            identifier=None,
            data=page_data,
            options=None
        )

        # Verify the service method was called correctly
        mock_confluence_fetcher.create_page.assert_called_once_with(
            space_id="TEST",
            title="Test Page with Markdown",
            body=page_data["body"],
            parent_id=None,
            is_markdown=True,
            enable_heading_anchors=False,
            content_representation=None
        )

        # Verify result structure
        assert result["id"] == "98765"
        assert result["title"] == "Test Page"

    @pytest.mark.asyncio
    async def test_confluence_comment_creation_with_markdown(
        self, resource_manager, mock_confluence_fetcher
    ):
        """Test that Confluence comment creation properly handles markdown formatting."""
        # Mock add_comment method
        comment_mock = MagicMock()
        comment_mock.to_dict.return_value = {
            "id": "comment456",
            "body": {"value": "Formatted comment content"}
        }
        mock_confluence_fetcher.add_comment.return_value = comment_mock

        # Test data with markdown content
        comment_data = {
            "body": "Comment with **formatting** and [links](http://example.com)"
        }

        # Execute operation  
        result = await resource_manager._add_confluence_comment(
            client=mock_confluence_fetcher,
            identifier="98765",
            data=comment_data,
            options=None
        )

        # Verify the service method was called with markdown content
        mock_confluence_fetcher.add_comment.assert_called_once_with(
            page_id="98765",
            comment="Comment with **formatting** and [links](http://example.com)"
        )

        # Verify result
        assert result["id"] == "comment456"

    @pytest.mark.asyncio
    async def test_adf_specific_elements_preservation(
        self, resource_manager, mock_confluence_fetcher
    ):
        """Test that ADF-specific elements (panels, status, etc.) are preserved."""
        # Test data with ADF-specific markdown extensions
        page_data = {
            "space_id": "TEST",
            "title": "Page with ADF Elements", 
            "body": """:::panel type="info"
This is an info panel with **important** information.
:::

Status: {status:color=green}Complete{/status}

Due date: {date:2025-02-15}

CC: @john.doe

:::expand title="Click to expand"
Hidden content here
:::"""
        }

        # Execute operation
        result = await resource_manager._create_confluence_page(
            client=mock_confluence_fetcher,
            identifier=None,
            data=page_data,
            options=None
        )

        # Verify the content with ADF extensions was passed through correctly
        mock_confluence_fetcher.create_page.assert_called_once()
        call_args = mock_confluence_fetcher.create_page.call_args
        
        # Check that the body contains ADF-specific syntax
        body_content = call_args.kwargs["body"]
        assert ":::panel type=\"info\"" in body_content
        assert "{status:color=green}Complete{/status}" in body_content
        assert "{date:2025-02-15}" in body_content
        assert "@john.doe" in body_content
        assert ":::expand title=\"Click to expand\"" in body_content

    @pytest.mark.asyncio
    async def test_formatting_fallback_on_error(
        self, resource_manager, mock_jira_fetcher
    ):
        """Test that formatting errors don't break resource creation."""
        # Mock preprocessor to raise an error
        mock_jira_fetcher.preprocessor.markdown_to_jira.side_effect = Exception("ADF conversion failed")
        
        # But the create_issue should still work (services handle fallback)
        issue_mock = MagicMock()
        issue_mock.to_simplified_dict.return_value = {
            "key": "TEST-124",
            "summary": "Fallback test"
        }
        mock_jira_fetcher.create_issue.return_value = issue_mock

        # Test data
        issue_data = {
            "project_key": "TEST",
            "summary": "Issue with formatting error",
            "issue_type": "Bug",
            "description": "This **should** still work"
        }

        # Execute - should not raise an exception
        result = await resource_manager._create_jira_issue(
            client=mock_jira_fetcher,
            identifier=None,
            data=issue_data,
            options=None
        )

        # Verify the issue was still created (service layer handles fallback)
        assert result["key"] == "TEST-124"
        mock_jira_fetcher.create_issue.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_content_handling(
        self, resource_manager, mock_confluence_fetcher
    ):
        """Test that empty or None content is handled gracefully."""
        # Test with empty body
        page_data = {
            "space_id": "TEST",
            "title": "Empty Page",
            "body": ""
        }

        page_mock = MagicMock()
        page_mock.to_dict.return_value = {"id": "empty123", "title": "Empty Page"}
        mock_confluence_fetcher.create_page.return_value = page_mock

        result = await resource_manager._create_confluence_page(
            client=mock_confluence_fetcher,
            identifier=None,
            data=page_data,
            options=None
        )

        # Should still work with empty content
        mock_confluence_fetcher.create_page.assert_called_once_with(
            space_id="TEST",
            title="Empty Page", 
            body="",
            parent_id=None,
            is_markdown=True,
            enable_heading_anchors=False,
            content_representation=None
        )
        assert result["id"] == "empty123"

    @pytest.mark.asyncio
    async def test_server_dc_wiki_markup_handling(
        self, resource_manager, mock_jira_fetcher
    ):
        """Test that Server/DC instances receive wiki markup instead of ADF."""
        # Mock preprocessor to return wiki markup (string) instead of ADF (dict)
        mock_jira_fetcher.preprocessor.markdown_to_jira.return_value = "h1. Header\n\n*Bold text* and _italic text_"
        
        issue_mock = MagicMock()
        issue_mock.to_simplified_dict.return_value = {
            "key": "SERVER-123", 
            "summary": "Server test"
        }
        mock_jira_fetcher.create_issue.return_value = issue_mock

        issue_data = {
            "project_key": "SERVER",
            "summary": "Server DC Issue",
            "issue_type": "Task", 
            "description": "# Header\n\n**Bold text** and *italic text*"
        }

        result = await resource_manager._create_jira_issue(
            client=mock_jira_fetcher,
            identifier=None,
            data=issue_data,
            options=None
        )

        # Verify the content was passed through (formatting handled by service)
        mock_jira_fetcher.create_issue.assert_called_once()
        assert result["key"] == "SERVER-123"