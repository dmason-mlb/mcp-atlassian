"""Comprehensive tests for the Confluence MCP server implementation."""

import json
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError, MCPAtlassianError
from mcp_atlassian.models.confluence.page import ConfluencePage
from mcp_atlassian.servers.confluence import confluence_mcp


class TestConfluencePageOperations:
    """Test Confluence page operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_fastmcp = MagicMock()
        mock_fastmcp.context = MagicMock()
        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_confluence_fetcher(self):
        """Create a mock ConfluenceFetcher."""
        return AsyncMock(spec=ConfluenceFetcher)

    @pytest.mark.anyio
    async def test_get_page_by_id_success(self, mock_context, mock_confluence_fetcher):
        """Test successful page retrieval by ID."""
        # Arrange
        mock_page = Mock(spec=ConfluencePage)
        mock_page.to_dict.return_value = {
            "id": "123456",
            "title": "Test Page",
            "content": "# Test Content\n\nThis is a test page.",
            "version": {"number": 1},
            "space": {"key": "TEST"}
        }
        mock_confluence_fetcher.get_page.return_value = mock_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.pages import get_page
            result = await get_page(mock_context, page_id="123456")
            parsed = json.loads(result)

            # Assert
            assert parsed["page"]["id"] == "123456"
            assert parsed["page"]["title"] == "Test Page"
            assert parsed["format"] == "markdown"
            mock_confluence_fetcher.get_page.assert_called_once()

    @pytest.mark.anyio
    async def test_get_page_by_title_and_space(self, mock_context, mock_confluence_fetcher):
        """Test page retrieval by title and space key."""
        # Arrange
        mock_page = Mock(spec=ConfluencePage)
        mock_page.to_dict.return_value = {
            "id": "789012",
            "title": "My Page",
            "space": {"key": "PERSONAL"}
        }
        mock_confluence_fetcher.get_page_by_title.return_value = mock_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.pages import get_page
            result = await get_page(
                mock_context,
                title="My Page",
                space_key="PERSONAL"
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["page"]["title"] == "My Page"
            mock_confluence_fetcher.get_page_by_title.assert_called_once_with(
                "My Page", "PERSONAL"
            )

    @pytest.mark.anyio
    async def test_get_page_not_found(self, mock_context, mock_confluence_fetcher):
        """Test page retrieval when page doesn't exist."""
        # Arrange
        mock_confluence_fetcher.get_page.side_effect = MCPAtlassianError("Page not found")

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.pages import get_page
            result = await get_page(mock_context, page_id="nonexistent")
            parsed = json.loads(result)

            # Assert
            assert parsed["error"] == "Page not found"

    @pytest.mark.anyio
    async def test_get_page_without_markdown_conversion(self, mock_context, mock_confluence_fetcher):
        """Test page retrieval without markdown conversion."""
        # Arrange
        mock_page = Mock(spec=ConfluencePage)
        mock_page.to_dict.return_value = {
            "id": "345678",
            "content": "<p>HTML content</p>"
        }
        mock_confluence_fetcher.get_page.return_value = mock_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.pages import get_page
            result = await get_page(
                mock_context,
                page_id="345678",
                convert_to_markdown=False
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["format"] == "storage"
            assert "<p>" in str(parsed["page"]["content"])

    @pytest.mark.anyio
    async def test_create_page_success(self, mock_context, mock_confluence_fetcher):
        """Test successful page creation."""
        # Arrange
        mock_created_page = Mock(spec=ConfluencePage)
        mock_created_page.to_dict.return_value = {
            "id": "new123",
            "title": "New Page",
            "version": {"number": 1}
        }
        mock_confluence_fetcher.create_page.return_value = mock_created_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.pages.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None  # Pass write check

            # Act
            from mcp_atlassian.servers.confluence.pages import create_page
            result = await create_page(
                mock_context,
                space_id="12345",
                title="New Page",
                content="# New Content"
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["id"] == "new123"
            assert parsed["title"] == "New Page"

    @pytest.mark.anyio
    async def test_create_page_read_only_mode(self, mock_context, mock_confluence_fetcher):
        """Test that page creation is blocked in read-only mode."""
        # Arrange
        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.pages.check_write_access") as mock_check_write:
            mock_check_write.side_effect = ValueError("Read-only mode enabled")

            # Act & Assert
            from mcp_atlassian.servers.confluence.pages import create_page
            with pytest.raises(ValueError, match="Read-only mode"):
                await create_page(
                    mock_context,
                    space_id="12345",
                    title="Blocked Page",
                    content="Content"
                )

    @pytest.mark.anyio
    async def test_update_page_success(self, mock_context, mock_confluence_fetcher):
        """Test successful page update."""
        # Arrange
        mock_updated_page = Mock(spec=ConfluencePage)
        mock_updated_page.to_dict.return_value = {
            "id": "123456",
            "title": "Updated Title",
            "version": {"number": 2}
        }
        mock_confluence_fetcher.update_page.return_value = mock_updated_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.pages.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None

            # Act
            from mcp_atlassian.servers.confluence.pages import update_page
            result = await update_page(
                mock_context,
                page_id="123456",
                title="Updated Title",
                content="Updated content"
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["title"] == "Updated Title"
            assert parsed["version"]["number"] == 2

    @pytest.mark.anyio
    async def test_delete_page_success(self, mock_context, mock_confluence_fetcher):
        """Test successful page deletion."""
        # Arrange
        mock_confluence_fetcher.delete_page.return_value = None

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.pages.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None

            # Act
            from mcp_atlassian.servers.confluence.pages import delete_page
            result = await delete_page(mock_context, page_id="123456")
            parsed = json.loads(result)

            # Assert
            assert parsed["success"] is True
            assert parsed["message"] == "Page deleted successfully"
            mock_confluence_fetcher.delete_page.assert_called_once_with("123456")


class TestConfluenceSearch:
    """Test Confluence search functionality."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_fastmcp = MagicMock()
        mock_fastmcp.context = MagicMock()
        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_confluence_fetcher(self):
        """Create a mock ConfluenceFetcher."""
        return AsyncMock(spec=ConfluenceFetcher)

    @pytest.mark.anyio
    async def test_search_with_simple_query(self, mock_context, mock_confluence_fetcher):
        """Test search with a simple text query."""
        # Arrange
        mock_results = [
            {"id": "1", "title": "Result 1", "type": "page"},
            {"id": "2", "title": "Result 2", "type": "page"}
        ]
        mock_confluence_fetcher.search.return_value = mock_results

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.search import search
            result = await search(mock_context, query="test documentation")
            parsed = json.loads(result)

            # Assert
            assert len(parsed["results"]) == 2
            assert parsed["results"][0]["title"] == "Result 1"

    @pytest.mark.anyio
    async def test_search_with_cql_query(self, mock_context, mock_confluence_fetcher):
        """Test search with a CQL query."""
        # Arrange
        mock_results = [{"id": "3", "title": "CQL Result", "space": {"key": "DEV"}}]
        mock_confluence_fetcher.search.return_value = mock_results

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.search import search
            result = await search(
                mock_context,
                query='type=page AND space=DEV AND title~"API*"'
            )
            parsed = json.loads(result)

            # Assert
            assert len(parsed["results"]) == 1
            assert parsed["results"][0]["space"]["key"] == "DEV"

    @pytest.mark.anyio
    async def test_search_with_limit(self, mock_context, mock_confluence_fetcher):
        """Test search with result limit."""
        # Arrange
        mock_results = [{"id": str(i), "title": f"Result {i}"} for i in range(10)]
        mock_confluence_fetcher.search.return_value = mock_results[:5]

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.search import search
            result = await search(mock_context, query="test", limit=5)
            parsed = json.loads(result)

            # Assert
            assert len(parsed["results"]) <= 5

    @pytest.mark.anyio
    async def test_search_user(self, mock_context, mock_confluence_fetcher):
        """Test user search functionality."""
        # Arrange
        mock_users = [
            {"accountId": "123", "displayName": "John Doe", "email": "john@example.com"},
            {"accountId": "456", "displayName": "Jane Smith", "email": "jane@example.com"}
        ]
        mock_confluence_fetcher.search_user.return_value = mock_users

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.search import search_user
            result = await search_user(mock_context, query='user.fullname ~ "John"')
            parsed = json.loads(result)

            # Assert
            assert len(parsed["results"]) == 2
            assert parsed["results"][0]["displayName"] == "John Doe"


class TestConfluenceContent:
    """Test Confluence content operations (comments, labels)."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_fastmcp = MagicMock()
        mock_fastmcp.context = MagicMock()
        return Context(fastmcp=mock_fastmcp)

    @pytest.fixture
    def mock_confluence_fetcher(self):
        """Create a mock ConfluenceFetcher."""
        return AsyncMock(spec=ConfluenceFetcher)

    @pytest.mark.anyio
    async def test_get_comments(self, mock_context, mock_confluence_fetcher):
        """Test retrieving comments for a page."""
        # Arrange
        mock_comments = [
            {"id": "1", "body": "First comment", "author": {"displayName": "User1"}},
            {"id": "2", "body": "Second comment", "author": {"displayName": "User2"}}
        ]
        mock_confluence_fetcher.get_comments.return_value = mock_comments

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.content import get_comments
            result = await get_comments(mock_context, page_id="123456")
            parsed = json.loads(result)

            # Assert
            assert len(parsed) == 2
            assert parsed[0]["body"] == "First comment"

    @pytest.mark.anyio
    async def test_add_comment(self, mock_context, mock_confluence_fetcher):
        """Test adding a comment to a page."""
        # Arrange
        mock_comment = {"id": "3", "body": "New comment"}
        mock_confluence_fetcher.add_comment.return_value = mock_comment

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.content.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None

            # Act
            from mcp_atlassian.servers.confluence.content import add_comment
            result = await add_comment(
                mock_context,
                page_id="123456",
                content="New comment"
            )
            parsed = json.loads(result)

            # Assert
            assert parsed["body"] == "New comment"

    @pytest.mark.anyio
    async def test_get_labels(self, mock_context, mock_confluence_fetcher):
        """Test retrieving labels for a page."""
        # Arrange
        mock_labels = [
            {"name": "important", "id": "1"},
            {"name": "documentation", "id": "2"}
        ]
        mock_confluence_fetcher.get_labels.return_value = mock_labels

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.content import get_labels
            result = await get_labels(mock_context, page_id="123456")
            parsed = json.loads(result)

            # Assert
            assert len(parsed) == 2
            assert parsed[0]["name"] == "important"

    @pytest.mark.anyio
    async def test_add_label(self, mock_context, mock_confluence_fetcher):
        """Test adding a label to a page."""
        # Arrange
        mock_labels = [
            {"name": "existing", "id": "1"},
            {"name": "new-label", "id": "2"}
        ]
        mock_confluence_fetcher.add_label.return_value = mock_labels

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.content.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None

            # Act
            from mcp_atlassian.servers.confluence.content import add_label
            result = await add_label(
                mock_context,
                page_id="123456",
                name="new-label"
            )
            parsed = json.loads(result)

            # Assert
            assert any(label["name"] == "new-label" for label in parsed)


class TestConfluenceErrorHandling:
    """Test error handling in Confluence operations."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_fastmcp = MagicMock()
        mock_fastmcp.context = MagicMock()
        return Context(fastmcp=mock_fastmcp)

    @pytest.mark.anyio
    async def test_auth_error_handling(self, mock_context):
        """Test handling of authentication errors."""
        # Arrange
        mock_confluence_fetcher = AsyncMock(spec=ConfluenceFetcher)
        mock_confluence_fetcher.get_page.side_effect = MCPAtlassianAuthenticationError("Invalid token")

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.pages import get_page
            result = await get_page(mock_context, page_id="123")
            parsed = json.loads(result)

            # Assert
            assert "Invalid token" in parsed["error"]

    @pytest.mark.anyio
    async def test_network_error_handling(self, mock_context):
        """Test handling of network errors."""
        # Arrange
        mock_confluence_fetcher = AsyncMock(spec=ConfluenceFetcher)
        mock_confluence_fetcher.search.side_effect = ConnectionError("Network unreachable")

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act & Assert
            from mcp_atlassian.servers.confluence.search import search
            with pytest.raises(ConnectionError):
                await search(mock_context, query="test")


class TestConfluenceToolRegistration:
    """Test that Confluence tools are properly registered."""

    def test_confluence_mcp_has_required_tools(self):
        """Test that confluence_mcp has all required tools registered."""
        # Act
        tools = confluence_mcp.get_tool_names()

        # Assert core tools are registered
        assert "search" in tools
        assert "get_page" in tools
        assert "create_page" in tools
        assert "update_page" in tools
        assert "delete_page" in tools
        assert "get_comments" in tools
        assert "add_comment" in tools

    def test_confluence_tools_have_correct_tags(self):
        """Test that Confluence tools have correct tags."""
        # Act
        all_tools = confluence_mcp._tools

        # Assert
        for tool_name, tool in all_tools.items():
            assert "confluence" in tool.tags
            if any(action in tool_name for action in ["create", "update", "delete", "add"]):
                assert "write" in tool.tags
            else:
                assert "read" in tool.tags


class TestConfluenceEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        mock_fastmcp = MagicMock()
        mock_fastmcp.context = MagicMock()
        return Context(fastmcp=mock_fastmcp)

    @pytest.mark.anyio
    async def test_search_with_max_limit(self, mock_context):
        """Test search with maximum allowed limit."""
        # Arrange
        mock_confluence_fetcher = AsyncMock(spec=ConfluenceFetcher)
        mock_confluence_fetcher.search.return_value = []

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher:
            mock_get_fetcher.return_value = mock_confluence_fetcher

            # Act
            from mcp_atlassian.servers.confluence.search import search
            await search(mock_context, query="test", limit=50)

            # Assert
            call_args = mock_confluence_fetcher.search.call_args
            assert call_args[1]["limit"] == 50

    @pytest.mark.anyio
    async def test_create_page_with_markdown_format(self, mock_context):
        """Test page creation with markdown content format."""
        # Arrange
        mock_confluence_fetcher = AsyncMock(spec=ConfluenceFetcher)
        mock_page = Mock(spec=ConfluencePage)
        mock_page.to_dict.return_value = {"id": "123"}
        mock_confluence_fetcher.create_page.return_value = mock_page

        with patch("mcp_atlassian.servers.dependencies.get_confluence_fetcher") as mock_get_fetcher, \
             patch("mcp_atlassian.servers.confluence.pages.check_write_access") as mock_check_write:
            mock_get_fetcher.return_value = mock_confluence_fetcher
            mock_check_write.return_value = None

            # Act
            from mcp_atlassian.servers.confluence.pages import create_page
            await create_page(
                mock_context,
                space_id="123",
                title="Test",
                content="# Markdown\n\n**Bold** text",
                content_format="markdown"
            )

            # Assert
            call_args = mock_confluence_fetcher.create_page.call_args
            assert call_args[1]["content_format"] == "markdown"
