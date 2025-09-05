"""Unit tests for ResourceManager meta-tool."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_atlassian.meta_tools.errors import MetaToolError
from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager


class TestResourceManager:
    """Test suite for ResourceManager."""

    @pytest.fixture
    def resource_manager(self):
        """Create ResourceManager instance for testing."""
        return ResourceManager()

    @pytest.fixture
    def dry_run_manager(self):
        """Create ResourceManager instance in dry-run mode."""
        return ResourceManager(dry_run=True)

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        return Mock()

    @pytest.fixture
    def mock_jira_client(self):
        """Create a mock JiraFetcher."""
        client = Mock()
        
        # Mock issue operations
        mock_issue = Mock()
        mock_issue.to_simplified_dict.return_value = {
            "key": "TEST-123",
            "summary": "Test Issue",
            "status": "Open",
        }
        client.get_issue.return_value = mock_issue
        client.create_issue.return_value = mock_issue
        client.update_issue.return_value = mock_issue
        client.delete_issue.return_value = True
        
        return client

    @pytest.fixture
    def mock_confluence_client(self):
        """Create a mock ConfluenceFetcher."""
        client = Mock()
        
        # Mock page operations
        mock_page = Mock()
        mock_page.to_dict.return_value = {
            "id": "123456",
            "title": "Test Page",
            "status": "current",
        }
        client.get_page_content.return_value = mock_page
        client.create_page.return_value = mock_page
        client.update_page.return_value = mock_page
        client.delete_page.return_value = True
        
        return client

    # Test initialization
    def test_init_default(self):
        """Test ResourceManager initialization with defaults."""
        manager = ResourceManager()
        assert manager.dry_run is False

    def test_init_dry_run(self):
        """Test ResourceManager initialization in dry-run mode."""
        manager = ResourceManager(dry_run=True)
        assert manager.dry_run is True

    # Test input validation
    @pytest.mark.asyncio
    async def test_invalid_service(self, resource_manager, mock_context):
        """Test error handling for invalid service."""
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                ctx=mock_context,
                service="invalid",
                resource="issue",
                operation="get",
                identifier="TEST-123",
            )
        
        error = exc_info.value
        assert error.error_code == "INVALID_SERVICE"
        assert "invalid" in error.user_message

    @pytest.mark.asyncio
    async def test_missing_identifier_for_get(self, resource_manager, mock_context):
        """Test error handling for missing identifier on get operation."""
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="get",
            )
        
        error = exc_info.value
        assert error.error_code == "MISSING_IDENTIFIER"
        assert "identifier" in error.user_message

    @pytest.mark.asyncio
    async def test_missing_data_for_create(self, resource_manager, mock_context):
        """Test error handling for missing data on create operation."""
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="create",
            )
        
        error = exc_info.value
        assert error.error_code == "MISSING_DATA"
        assert "data payload" in error.user_message

    @pytest.mark.asyncio
    async def test_unsupported_resource(self, resource_manager, mock_context):
        """Test error handling for unsupported resource type."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = Mock()
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="jira",
                    resource="invalid_resource",
                    operation="get",
                    identifier="TEST-123",
                )
            
            error = exc_info.value
            assert error.error_code == "JIRA_RESOURCE_NOT_SUPPORTED"
            assert "invalid_resource" in error.user_message

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, resource_manager, mock_context):
        """Test error handling for unsupported operation."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = Mock()
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="jira",
                    resource="issue",
                    operation="invalid_op",
                    identifier="TEST-123",
                )
            
            error = exc_info.value
            assert error.error_code == "JIRA_OPERATION_NOT_SUPPORTED"
            assert "invalid_op" in error.user_message

    # Test dry run functionality
    @pytest.mark.asyncio
    async def test_dry_run_validation_success(self, dry_run_manager, mock_context):
        """Test successful dry run validation."""
        result = await dry_run_manager.execute_operation(
            ctx=mock_context,
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "TEST",
                "summary": "Test Issue",
                "issue_type": "Task",
            },
        )
        
        result_data = json.loads(result)
        assert result_data["dry_run"] is True
        assert result_data["validation"] == "PASSED"
        assert result_data["service"] == "jira"
        assert result_data["resource"] == "issue"
        assert result_data["operation"] == "create"

    @pytest.mark.asyncio
    async def test_dry_run_validation_missing_fields(self, dry_run_manager, mock_context):
        """Test dry run validation with missing required fields."""
        result = await dry_run_manager.execute_operation(
            ctx=mock_context,
            service="jira",
            resource="issue",
            operation="create",
            data={
                "summary": "Test Issue",
                # Missing project_key and issue_type
            },
        )
        
        result_data = json.loads(result)
        assert result_data["dry_run"] is True
        assert result_data["validation"] == "FAILED"
        assert "missing_fields" in result_data
        assert "project_key" in result_data["missing_fields"]
        assert "issue_type" in result_data["missing_fields"]

    # Test Jira operations
    @pytest.mark.asyncio
    async def test_jira_get_issue_success(self, resource_manager, mock_context, mock_jira_client):
        """Test successful Jira issue get operation."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = mock_jira_client
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "jira_issue_get"
            assert result_data["result"]["key"] == "TEST-123"
            
            mock_jira_client.get_issue.assert_called_once_with("TEST-123", expand=None)

    @pytest.mark.asyncio
    async def test_jira_create_issue_success(self, resource_manager, mock_context, mock_jira_client):
        """Test successful Jira issue creation."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = mock_jira_client
            
            issue_data = {
                "project_key": "TEST",
                "summary": "New Test Issue",
                "issue_type": "Task",
                "description": "Test description",
            }
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="create",
                data=issue_data,
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "jira_issue_create"
            
            mock_jira_client.create_issue.assert_called_once_with(
                project_key="TEST",
                summary="New Test Issue",
                issue_type="Task",
                description="Test description",
                assignee=None,
                components=None,
            )

    @pytest.mark.asyncio
    async def test_jira_create_issue_missing_required_fields(self, resource_manager, mock_context):
        """Test Jira issue creation with missing required fields."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = Mock()
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="jira",
                    resource="issue",
                    operation="create",
                    data={"summary": "Incomplete issue"},  # Missing project_key and issue_type
                )
            
            error = exc_info.value
            assert error.error_code == "JIRA_CREATE_ISSUE_FAILED"
            assert "Missing required fields" in str(error.original_error)

    @pytest.mark.asyncio
    async def test_jira_update_issue_success(self, resource_manager, mock_context, mock_jira_client):
        """Test successful Jira issue update."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = mock_jira_client
            
            update_data = {"summary": "Updated summary"}
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="update",
                identifier="TEST-123",
                data=update_data,
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "jira_issue_update"
            
            mock_jira_client.update_issue.assert_called_once_with("TEST-123", fields=update_data)

    @pytest.mark.asyncio
    async def test_jira_delete_issue_success(self, resource_manager, mock_context, mock_jira_client):
        """Test successful Jira issue deletion."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = mock_jira_client
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="delete",
                identifier="TEST-123",
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "jira_issue_delete"
            assert result_data["result"]["deleted"] is True
            assert result_data["result"]["issue_key"] == "TEST-123"
            
            mock_jira_client.delete_issue.assert_called_once_with("TEST-123")

    # Test Confluence operations
    @pytest.mark.asyncio
    async def test_confluence_get_page_success(self, resource_manager, mock_context, mock_confluence_client):
        """Test successful Confluence page get operation."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher") as mock_get_confluence:
            mock_get_confluence.return_value = mock_confluence_client
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="get",
                identifier="123456",
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "confluence_page_get"
            assert result_data["result"]["id"] == "123456"
            
            mock_confluence_client.get_page_content.assert_called_once_with("123456", expand=None)

    @pytest.mark.asyncio
    async def test_confluence_create_page_success(self, resource_manager, mock_context, mock_confluence_client):
        """Test successful Confluence page creation."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher") as mock_get_confluence:
            mock_get_confluence.return_value = mock_confluence_client
            
            page_data = {
                "space_id": "SPACE123",
                "title": "New Test Page",
                "body": "Test content",
            }
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="create",
                data=page_data,
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "confluence_page_create"
            
            mock_confluence_client.create_page.assert_called_once_with(
                space_id="SPACE123",
                title="New Test Page",
                body="Test content",
                parent_id=None,
                is_markdown=True,
                enable_heading_anchors=False,
                content_representation=None,
            )

    @pytest.mark.asyncio
    async def test_confluence_update_page_success(self, resource_manager, mock_context, mock_confluence_client):
        """Test successful Confluence page update."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher") as mock_get_confluence:
            mock_get_confluence.return_value = mock_confluence_client
            
            update_data = {
                "title": "Updated Page Title",
                "body": "Updated content",
            }
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="update",
                identifier="123456",
                data=update_data,
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "confluence_page_update"
            
            mock_confluence_client.update_page.assert_called_once_with(
                page_id="123456",
                title="Updated Page Title",
                body="Updated content",
                is_markdown=True,
                enable_heading_anchors=False,
                content_representation=None,
            )

    @pytest.mark.asyncio
    async def test_confluence_delete_page_success(self, resource_manager, mock_context, mock_confluence_client):
        """Test successful Confluence page deletion."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher") as mock_get_confluence:
            mock_get_confluence.return_value = mock_confluence_client
            
            result = await resource_manager.execute_operation(
                ctx=mock_context,
                service="confluence",
                resource="page",
                operation="delete",
                identifier="123456",
            )
            
            result_data = json.loads(result)
            assert result_data["success"] is True
            assert result_data["operation"] == "confluence_page_delete"
            assert result_data["result"]["deleted"] is True
            assert result_data["result"]["page_id"] == "123456"
            
            mock_confluence_client.delete_page.assert_called_once_with("123456")

    # Test error handling for unimplemented operations
    @pytest.mark.asyncio
    async def test_jira_comment_not_implemented(self, resource_manager, mock_context):
        """Test that unimplemented Jira comment operations raise appropriate errors."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = Mock()
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="jira",
                    resource="comment",
                    operation="get",
                    identifier="comment-123",
                )
            
            error = exc_info.value
            assert error.error_code == "JIRA_COMMENT_GET_NOT_IMPLEMENTED"

    @pytest.mark.asyncio
    async def test_confluence_comment_not_implemented(self, resource_manager, mock_context):
        """Test that unimplemented Confluence comment operations raise appropriate errors."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher") as mock_get_confluence:
            mock_get_confluence.return_value = Mock()
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="confluence",
                    resource="comment",
                    operation="add",
                    data={"body": "Test comment"},
                )
            
            error = exc_info.value
            assert error.error_code == "CONFLUENCE_COMMENT_ADD_NOT_IMPLEMENTED"

    # Test error wrapping for unexpected exceptions
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, resource_manager, mock_context):
        """Test handling of unexpected exceptions."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_jira_client = Mock()
            mock_jira_client.get_issue.side_effect = RuntimeError("Unexpected error")
            mock_get_jira.return_value = mock_jira_client
            
            with pytest.raises(MetaToolError) as exc_info:
                await resource_manager.execute_operation(
                    ctx=mock_context,
                    service="jira",
                    resource="issue",
                    operation="get",
                    identifier="TEST-123",
                )
            
            error = exc_info.value
            assert error.error_code == "RESOURCE_MANAGER_ERROR"
            assert "Failed to get jira issue" in error.user_message
            assert isinstance(error.original_error, RuntimeError)

    # Test get_required_fields method
    def test_get_required_fields_jira_issue_create(self, resource_manager):
        """Test get_required_fields for Jira issue creation."""
        fields = resource_manager._get_required_fields("jira", "issue", "create")
        assert fields == ["project_key", "summary", "issue_type"]

    def test_get_required_fields_confluence_page_create(self, resource_manager):
        """Test get_required_fields for Confluence page creation."""
        fields = resource_manager._get_required_fields("confluence", "page", "create")
        assert fields == ["space_id", "title", "body"]

    def test_get_required_fields_unknown(self, resource_manager):
        """Test get_required_fields for unknown resource/operation."""
        fields = resource_manager._get_required_fields("unknown", "resource", "operation")
        assert fields == []

    # Test options parameter handling
    @pytest.mark.asyncio
    async def test_options_parameter_handling(self, resource_manager, mock_context, mock_jira_client):
        """Test that options parameter is passed correctly."""
        with patch("src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher") as mock_get_jira:
            mock_get_jira.return_value = mock_jira_client
            
            options = {"expand": "changelog,transitions"}
            
            await resource_manager.execute_operation(
                ctx=mock_context,
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
                options=options,
            )
            
            mock_jira_client.get_issue.assert_called_once_with("TEST-123", expand="changelog,transitions")


class TestMetaToolErrorIntegration:
    """Test MetaToolError integration with ResourceManager."""

    def test_meta_tool_error_creation(self):
        """Test MetaToolError creation and serialization."""
        error = MetaToolError(
            error_code="TEST_ERROR",
            user_message="Test error message",
            api_endpoint="/test/endpoint",
            suggestions=["Try again", "Check configuration"],
            context={"test_key": "test_value"},
        )
        
        assert error.error_code == "TEST_ERROR"
        assert error.user_message == "Test error message"
        assert error.api_endpoint == "/test/endpoint"
        assert error.suggestions == ["Try again", "Check configuration"]
        assert error.context == {"test_key": "test_value"}
        
        error_dict = error.to_dict()
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["user_message"] == "Test error message"

    def test_meta_tool_error_from_exception(self):
        """Test creating MetaToolError from existing exception."""
        original_error = ValueError("Original error message")
        
        meta_error = MetaToolError.from_exception(
            error=original_error,
            error_code="WRAPPED_ERROR",
            user_message="Custom user message",
            suggestions=["Fix the issue"],
        )
        
        assert meta_error.error_code == "WRAPPED_ERROR"
        assert meta_error.user_message == "Custom user message"
        assert meta_error.original_error == original_error
        assert meta_error.suggestions == ["Fix the issue"]