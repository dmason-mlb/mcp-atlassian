"""Tests for the main MCP server implementation."""

from unittest.mock import AsyncMock, MagicMock, patch
import json

import httpx
import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_atlassian.servers.main import UserTokenMiddleware, main_mcp


@pytest.mark.anyio
async def test_run_server_stdio():
    """Test that main_mcp.run_async is called with stdio transport."""
    with patch.object(main_mcp, "run_async") as mock_run_async:
        mock_run_async.return_value = None
        await main_mcp.run_async(transport="stdio")
        mock_run_async.assert_called_once_with(transport="stdio")


@pytest.mark.anyio
async def test_run_server_sse():
    """Test that main_mcp.run_async is called with sse transport and correct port."""
    with patch.object(main_mcp, "run_async") as mock_run_async:
        mock_run_async.return_value = None
        test_port = 9000
        await main_mcp.run_async(transport="sse", port=test_port)
        mock_run_async.assert_called_once_with(transport="sse", port=test_port)


@pytest.mark.anyio
async def test_run_server_streamable_http():
    """Test that main_mcp.run_async is called with streamable-http transport and correct parameters."""
    with patch.object(main_mcp, "run_async") as mock_run_async:
        mock_run_async.return_value = None
        test_port = 9001
        test_host = "127.0.0.1"
        test_path = "/custom_mcp"
        await main_mcp.run_async(
            transport="streamable-http", port=test_port, host=test_host, path=test_path
        )
        mock_run_async.assert_called_once_with(
            transport="streamable-http", port=test_port, host=test_host, path=test_path
        )


@pytest.mark.anyio
async def test_run_server_invalid_transport():
    """Test that run_server raises ValueError for invalid transport."""
    # We don't need to patch run_async here as the error occurs before it's called
    with pytest.raises(ValueError) as excinfo:
        await main_mcp.run_async(transport="invalid")  # type: ignore

    assert "Unknown transport" in str(excinfo.value)
    assert "invalid" in str(excinfo.value)


@pytest.mark.anyio
async def test_health_check_endpoint():
    """Test the health check endpoint returns 200 and correct JSON response."""
    app = main_mcp.sse_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_sse_app_health_check_endpoint():
    """Test the /healthz endpoint on the SSE app returns 200 and correct JSON response."""
    app = main_mcp.sse_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_streamable_http_app_health_check_endpoint():
    """Test the /healthz endpoint on the Streamable HTTP app returns 200 and correct JSON response."""
    app = main_mcp.streamable_http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestUserTokenMiddleware:
    """Tests for the UserTokenMiddleware class."""

    @pytest.fixture
    def middleware(self):
        """Create a UserTokenMiddleware instance for testing."""
        mock_app = AsyncMock()
        # Create a mock MCP server to avoid warnings
        mock_mcp_server = MagicMock()
        mock_mcp_server.settings.streamable_http_path = "/mcp"
        return UserTokenMiddleware(mock_app, mcp_server_ref=mock_mcp_server)

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = MagicMock(spec=Request)
        request.url.path = "/mcp"
        request.method = "POST"
        request.headers = {}
        # Create a real state object that can be modified
        from types import SimpleNamespace

        request.state = SimpleNamespace()
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create a mock call_next function."""
        mock_response = JSONResponse({"test": "response"})
        call_next = AsyncMock(return_value=mock_response)
        return call_next

    @pytest.mark.anyio
    async def test_cloud_id_header_extraction_success(
        self, middleware, mock_request, mock_call_next
    ):
        """Test successful cloud ID header extraction."""
        # Setup request with cloud ID header
        mock_request.headers = {
            "Authorization": "Bearer test-token",
            "X-Atlassian-Cloud-Id": "test-cloud-id-123",
        }

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Verify cloud ID was extracted and stored in request state
        assert hasattr(mock_request.state, "user_atlassian_cloud_id")
        assert mock_request.state.user_atlassian_cloud_id == "test-cloud-id-123"

        # Verify the request was processed normally
        mock_call_next.assert_called_once_with(mock_request)
        assert result is not None


class TestV2ToolHandlers:
    """Test suite for v2 tool handlers in main.py."""

    @pytest.fixture
    def mock_server(self):
        """Create mock AtlassianMCP server with proper structure."""
        server = MagicMock()

        # Create the proper _mcp_server structure that dependencies.py expects
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_app_context = MagicMock()

        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        return server

    @pytest.mark.anyio
    async def test_batch_processor_tool_handler(self, mock_server):
        """Test that batch_processor_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import batch_processor_tool

        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBatchProcessor:
            mock_batch_instance = MockBatchProcessor.return_value
            mock_batch_instance.execute_batch_operation = AsyncMock(
                return_value='{"success": true, "service": "jira", "operation": "create"}'
            )

            # Call the tool handler
            result = await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",
                items=[{"summary": "Test Issue"}],
                dry_run=True
            )

            # Verify BatchProcessor instantiation
            MockBatchProcessor.assert_called_once_with(dry_run=True)

            # Verify the execute_batch_operation call
            call_args = mock_batch_instance.execute_batch_operation.call_args

            # Check that resource is converted to resource_type
            assert 'resource_type' in call_args.kwargs
            assert call_args.kwargs['resource_type'] == 'issue'
            assert 'resource' not in call_args.kwargs

            # Verify other parameters
            assert call_args.kwargs['service'] == 'jira'
            assert call_args.kwargs['operation'] == 'create'
            assert call_args.kwargs['items'] == [{"summary": "Test Issue"}]

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict['success'] is True

    @pytest.mark.anyio
    async def test_resource_manager_tool_handler(self, mock_server):
        """Test that resource_manager_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import resource_manager_tool

        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockResourceManager:
            mock_rm_instance = MockResourceManager.return_value
            mock_rm_instance.execute_operation = AsyncMock(
                return_value='{"success": true, "resource": "issue"}'
            )

            # Call the tool handler
            result = await resource_manager_tool(
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
                dry_run=False
            )

            # Verify ResourceManager instantiation
            MockResourceManager.assert_called_once_with(dry_run=False)

            # Verify the execute_operation call
            call_args = mock_rm_instance.execute_operation.call_args

            # Verify parameters
            assert call_args.kwargs['service'] == 'jira'
            assert call_args.kwargs['resource'] == 'issue'
            assert call_args.kwargs['operation'] == 'get'
            assert call_args.kwargs['identifier'] == 'TEST-123'

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict['success'] is True

    @pytest.mark.anyio
    async def test_search_engine_tool_handler(self, mock_server):
        """Test that search_engine_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import search_engine_tool

        with patch('src.mcp_atlassian.meta_tools.search_engine.SearchEngine') as MockSearchEngine:
            mock_se_instance = MockSearchEngine.return_value
            mock_se_instance.execute_search = AsyncMock(
                return_value='{"results": [], "total": 0}'
            )

            # Call the tool handler
            result = await search_engine_tool(
                service="jira",
                query_type="jql",
                query="project = TEST",
                dry_run=True
            )

            # Verify SearchEngine instantiation
            MockSearchEngine.assert_called_once_with(dry_run=True)

            # Verify the execute_search call
            call_args = mock_se_instance.execute_search.call_args

            # Verify parameters
            assert call_args.kwargs['service'] == 'jira'
            assert call_args.kwargs['query_type'] == 'jql'
            assert call_args.kwargs['query'] == 'project = TEST'

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert 'results' in result_dict

    @pytest.mark.anyio
    async def test_workflow_engine_tool_handler(self, mock_server):
        """Test that workflow_engine_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import workflow_engine_tool

        with patch('src.mcp_atlassian.meta_tools.workflow_engine.WorkflowEngine') as MockWorkflowEngine:
            mock_we_instance = MockWorkflowEngine.return_value
            mock_we_instance.execute_workflow_operation = AsyncMock(
                return_value='{"success": true, "operation": "transition"}'
            )

            # Call the tool handler
            result = await workflow_engine_tool(
                operation="transition",
                issue_key="TEST-123",
                transition_name="In Progress",
                dry_run=False
            )

            # Verify WorkflowEngine instantiation
            MockWorkflowEngine.assert_called_once_with(dry_run=False)

            # Verify the execute_workflow_operation call
            call_args = mock_we_instance.execute_workflow_operation.call_args

            # Verify parameters
            assert call_args.kwargs['operation'] == 'transition'
            assert call_args.kwargs['issue_key'] == 'TEST-123'
            assert call_args.kwargs['transition_name'] == 'In Progress'

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict['success'] is True

    @pytest.mark.anyio
    async def test_relationship_manager_tool_handler(self, mock_server):
        """Test that relationship_manager_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import relationship_manager_tool

        with patch('src.mcp_atlassian.meta_tools.relationship_manager.RelationshipManager') as MockRelationshipManager:
            mock_rm_instance = MockRelationshipManager.return_value
            mock_rm_instance.execute_relationship_operation = AsyncMock(
                return_value='{"success": true, "operation": "link"}'
            )

            # Call the tool handler
            result = await relationship_manager_tool(
                operation="link",
                issue_key="TEST-123",
                target_issue_key="TEST-456",
                link_type="Blocks",
                dry_run=True
            )

            # Verify RelationshipManager instantiation
            MockRelationshipManager.assert_called_once_with(dry_run=True)

            # Verify the execute_relationship_operation call
            call_args = mock_rm_instance.execute_relationship_operation.call_args

            # Verify parameters
            assert call_args.kwargs['operation'] == 'link'
            assert call_args.kwargs['issue_key'] == 'TEST-123'
            assert call_args.kwargs['target_issue_key'] == 'TEST-456'
            assert call_args.kwargs['link_type'] == 'Blocks'

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict['success'] is True

    @pytest.mark.anyio
    async def test_attachment_handler_tool_handler(self, mock_server):
        """Test that attachment_handler_tool handler works correctly."""
        from src.mcp_atlassian.servers.main import attachment_handler_tool

        with patch('src.mcp_atlassian.meta_tools.attachment_handler.AttachmentHandler') as MockAttachmentHandler:
            mock_ah_instance = MockAttachmentHandler.return_value
            mock_ah_instance.execute_attachment_operation = AsyncMock(
                return_value='{"success": true, "operation": "upload"}'
            )

            # Call the tool handler
            result = await attachment_handler_tool(
                service="jira",
                operation="upload",
                issue_key="TEST-123",
                file_path="/test/file.txt",
                dry_run=False
            )

            # Verify AttachmentHandler instantiation
            MockAttachmentHandler.assert_called_once_with(dry_run=False)

            # Verify the execute_attachment_operation call
            call_args = mock_ah_instance.execute_attachment_operation.call_args

            # Verify parameters
            assert call_args.kwargs['service'] == 'jira'
            assert call_args.kwargs['operation'] == 'upload'
            assert call_args.kwargs['issue_key'] == 'TEST-123'
            assert call_args.kwargs['file_path'] == '/test/file.txt'

            # Verify result is JSON string
            result_dict = json.loads(result)
            assert result_dict['success'] is True

    @pytest.mark.anyio
    async def test_all_v2_tools_accept_dry_run(self):
        """Test that all v2 tool constructors accept dry_run parameter."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
        from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

        # All these should work without TypeError about unexpected dry_run argument
        tools = [
            ResourceManager(dry_run=True),
            BatchProcessor(dry_run=True),
            SearchEngine(dry_run=True),
            WorkflowEngine(dry_run=True),
            RelationshipManager(dry_run=True),
            AttachmentHandler(dry_run=True)
        ]

        for tool in tools:
            assert tool.dry_run is True

    @pytest.mark.anyio
    async def test_context_access_pattern_regression_prevention(self):
        """Test that the RequestContext access pattern prevents P0 regression."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher

        # Create mock context with the correct structure
        mock_server_ctx = MagicMock()
        mock_request_context = MagicMock()
        mock_app_context = MagicMock()

        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_server_ctx.request_context = mock_request_context

        with patch('src.mcp_atlassian.jira.client.JiraClient'):
            # This should work - passing server._mcp_server (not server._mcp_server.request_context)
            fetcher = get_jira_fetcher(mock_server_ctx)  # ctx = server._mcp_server
            assert fetcher is not None

            # This would fail with the old pattern that caused P0 error:
            # get_jira_fetcher(mock_server_ctx.request_context)  # This would cause AttributeError
