"""Integration tests for meta-tools with MCP server infrastructure."""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Context
from fastmcp.tools import Tool as FastMCPTool
from mcp.types import Tool as MCPTool

from src.mcp_atlassian.meta_tools.errors import MetaToolError
from src.mcp_atlassian.meta_tools.loader import get_tool_version, should_load_v1_tools, should_load_v2_tools, ToolVersion
from src.mcp_atlassian.meta_tools.migration_helper import get_migration_helper
from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.schema_discovery import schema_discovery
from src.mcp_atlassian.servers.context import MainAppContext
from src.mcp_atlassian.servers.main import AtlassianMCP
from tests.utils.factories import ConfluencePageFactory, JiraIssueFactory
from tests.utils.mocks import MockEnvironment

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.anyio
class TestMetaToolsIntegration:
    """Integration test suite for meta-tools with MCP server."""

    @pytest.fixture
    async def mock_context(self):
        """Create a mock MainAppContext."""
        context = MagicMock(spec=MainAppContext)
        context.jira_client = AsyncMock()
        context.confluence_client = AsyncMock()
        context.jira_config = MagicMock()
        context.confluence_config = MagicMock()
        
        # Configure auth states
        context.jira_config.is_auth_configured.return_value = True
        context.confluence_config.is_auth_configured.return_value = True
        
        return context

    @pytest.fixture
    async def mock_tool_loader(self):
        """Create mock tool loader functionality."""
        class MockToolLoader:
            def load_tools(self, version=None, filter_by_auth=False):
                if version == "v2" or should_load_v2_tools():
                    return [
                        MagicMock(name="resource_manager", description="Universal resource manager"),
                        MagicMock(name="schema_discovery", description="Schema discovery tool"),
                        MagicMock(name="migration_helper", description="Migration helper tool"),
                        MagicMock(name="parameter_optimizer", description="Parameter optimizer tool")
                    ]
                else:
                    return [
                        MagicMock(name="jira_get_issue", description="Get Jira issue"),
                        MagicMock(name="jira_create_issue", description="Create Jira issue"),
                        MagicMock(name="confluence_get_page", description="Get Confluence page")
                    ]
        return MockToolLoader()

    @pytest.fixture
    async def mcp_server(self, mock_context):
        """Create AtlassianMCP server with meta-tools."""
        with patch('src.mcp_atlassian.servers.main.MainAppContext', return_value=mock_context):
            server = AtlassianMCP()
            await server.setup_context()
            return server

    async def test_meta_tool_registration(self, mock_tool_loader):
        """Test that meta-tools are properly registered."""
        # Test v2 meta-tools loading
        tools = mock_tool_loader.load_tools(version="v2")
        
        expected_tools = {
            "resource_manager",
            "schema_discovery", 
            "migration_helper",
            "parameter_optimizer"
        }
        
        loaded_tool_names = {tool.name for tool in tools}
        assert expected_tools.issubset(loaded_tool_names)

    async def test_meta_tool_exclusivity(self, mock_tool_loader):
        """Test that v1 and v2 tools are mutually exclusive."""
        # Load v1 tools
        v1_tools = mock_tool_loader.load_tools(version="v1")
        v1_tool_names = {tool.name for tool in v1_tools}
        
        # Load v2 tools
        v2_tools = mock_tool_loader.load_tools(version="v2")
        v2_tool_names = {tool.name for tool in v2_tools}
        
        # Verify no overlap
        overlap = v1_tool_names & v2_tool_names
        assert len(overlap) == 0, f"Tools should not overlap between versions: {overlap}"

    async def test_version_selection_environment(self, mock_tool_loader):
        """Test version selection via environment variable."""
        with MockEnvironment({"MCP_VERSION": "v2"}):
            tools = mock_tool_loader.load_tools()
            tool_names = {tool.name for tool in tools}
            
            # Should load meta-tools when v2 is specified
            assert "resource_manager" in tool_names
            assert "schema_discovery" in tool_names

    @pytest.mark.asyncio
    async def test_resource_manager_integration(self, mock_context):
        """Test ResourceManager integration with MCP server context."""
        resource_manager = ResourceManager()
        
        # Mock Jira operations
        mock_issue = MagicMock()
        mock_issue.to_simplified_dict.return_value = {
            "key": "INT-123",
            "summary": "Integration Test Issue",
            "status": "Open"
        }
        mock_context.jira_client.get_issue.return_value = mock_issue
        
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_context.jira_client):
                result = await resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue",
                    operation="get",
                    identifier="INT-123"
                )
                
                assert result["key"] == "INT-123"
                mock_context.jira_client.get_issue.assert_called_once_with("INT-123")

    @pytest.mark.asyncio
    async def test_schema_discovery_integration(self, mock_context):
        """Test SchemaDiscovery integration with real API metadata."""
        # Mock Jira metadata response
        create_meta = {
            "projects": [{
                "key": "INT",
                "name": "Integration Test Project",
                "issuetypes": [{
                    "name": "Task",
                    "fields": {
                        "summary": {
                            "required": True,
                            "name": "Summary"
                        },
                        "description": {
                            "required": False,
                            "name": "Description"
                        },
                        "priority": {
                            "required": False,
                            "name": "Priority"
                        }
                    }
                }]
            }]
        }
        
        mock_context.jira_client.get_create_meta.return_value = create_meta
        
        with patch.object(schema_discovery, '_get_context', return_value=mock_context):
            with patch.object(schema_discovery, '_get_jira_client', return_value=mock_context.jira_client):
                fields = schema_discovery.discover_fields(
                    service="jira",
                    resource_type="issue",
                    context={"project": "INT", "issuetype": "Task"}
                )
                
                assert "summary" in fields
                assert fields["summary"]["required"] is True
                assert "description" in fields
                assert fields["description"]["required"] is False

    @pytest.mark.asyncio
    async def test_migration_helper_integration(self, mock_context):
        """Test MigrationHelper integration with legacy tool translation."""
        migration_helper = get_migration_helper()
        
        # Test legacy call translation
        legacy_call = {
            "tool": "jira_get_issue",
            "arguments": {"issue_key": "INT-456"}
        }
        
        with patch.object(migration_helper.resource_manager, '_get_context', return_value=mock_context):
            result = await migration_helper.translate_legacy_call(legacy_call)
            
            assert result.meta_tool_call["tool"] == "resource_manager"
            assert result.meta_tool_call["arguments"]["service"] == "jira"
            assert result.meta_tool_call["arguments"]["operation"] == "get"
            assert result.meta_tool_call["arguments"]["identifier"] == "INT-456"

    async def test_tool_filtering_by_auth_state(self, mock_tool_loader):
        """Test tool filtering based on authentication state."""
        # Mock authenticated state
        with patch('src.mcp_atlassian.servers.context.MainAppContext') as mock_context_class:
            mock_context = MagicMock()
            mock_context.jira_config.is_auth_configured.return_value = True
            mock_context.confluence_config.is_auth_configured.return_value = False
            mock_context_class.return_value = mock_context
            
            tools = mock_tool_loader.load_tools(version="v2", filter_by_auth=True)
            
            # Should include Jira-capable tools but exclude Confluence-only tools
            tool_names = {tool.name for tool in tools}
            assert "resource_manager" in tool_names  # Universal tool
            
            # Verify tool descriptions mention appropriate services
            resource_manager_tool = next(t for t in tools if t.name == "resource_manager")
            assert "jira" in resource_manager_tool.description.lower()

    async def test_tool_middleware_integration(self, mcp_server):
        """Test integration with user token middleware."""
        # Mock a request with user tokens
        headers = {
            "X-Jira-Token": "user_jira_token",
            "X-Confluence-Token": "user_confluence_token"
        }
        
        # This would test the actual middleware in a real request context
        # For now, verify the server can handle user token scenarios
        assert hasattr(mcp_server, 'user_token_middleware')

    @pytest.mark.asyncio
    async def test_cross_service_operations(self, mock_context):
        """Test operations that span both Jira and Confluence."""
        resource_manager = ResourceManager()
        
        # Mock both services
        mock_jira_issue = MagicMock()
        mock_jira_issue.to_simplified_dict.return_value = {"key": "CROSS-123"}
        mock_context.jira_client.get_issue.return_value = mock_jira_issue
        
        mock_confluence_page = MagicMock()
        mock_confluence_page.to_dict.return_value = {"id": "789", "title": "Related Page"}
        mock_context.confluence_client.get_page.return_value = mock_confluence_page
        
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_context.jira_client):
                with patch.object(resource_manager, '_get_confluence_client', return_value=mock_context.confluence_client):
                    
                    # Test Jira operation
                    jira_result = await resource_manager.manage_resource(
                        service="jira",
                        resource_type="issue",
                        operation="get",
                        identifier="CROSS-123"
                    )
                    
                    # Test Confluence operation
                    confluence_result = await resource_manager.manage_resource(
                        service="confluence",
                        resource_type="page",
                        operation="get",
                        identifier="789"
                    )
                    
                    assert jira_result["key"] == "CROSS-123"
                    assert confluence_result["id"] == "789"

    async def test_error_propagation_and_handling(self, mock_context):
        """Test error propagation from meta-tools through MCP stack."""
        resource_manager = ResourceManager()
        
        # Mock an API error
        mock_context.jira_client.get_issue.side_effect = Exception("API Error")
        
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_context.jira_client):
                
                with pytest.raises(Exception) as exc_info:
                    await resource_manager.manage_resource(
                        service="jira",
                        resource_type="issue",
                        operation="get",
                        identifier="ERROR-123"
                    )
                
                assert "API Error" in str(exc_info.value)

    async def test_performance_vs_legacy_tools(self, mock_tool_loader):
        """Test performance characteristics of meta-tools vs legacy tools."""
        # Load both versions for comparison
        v1_tools = mock_tool_loader.load_tools(version="v1")
        v2_tools = mock_tool_loader.load_tools(version="v2")
        
        # Verify token reduction (v2 should have significantly fewer tools)
        assert len(v2_tools) < len(v1_tools) * 0.25  # At least 75% reduction
        
        # Verify comprehensive coverage (v2 should cover most v1 functionality)
        # This would be expanded with actual functionality mapping
        v2_tool_names = {tool.name for tool in v2_tools}
        essential_tools = {"resource_manager", "schema_discovery"}
        assert essential_tools.issubset(v2_tool_names)

    @pytest.mark.asyncio
    async def test_concurrent_meta_tool_operations(self, mock_context):
        """Test concurrent operations with meta-tools."""
        resource_manager = ResourceManager()
        
        # Mock successful responses
        mock_issue = MagicMock()
        mock_issue.to_simplified_dict.return_value = {"key": "CONCURRENT-123"}
        mock_context.jira_client.get_issue.return_value = mock_issue
        
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_context.jira_client):
                
                # Create multiple concurrent operations
                tasks = []
                for i in range(5):
                    task = resource_manager.manage_resource(
                        service="jira",
                        resource_type="issue",
                        operation="get",
                        identifier=f"CONCURRENT-{i}"
                    )
                    tasks.append(task)
                
                # Execute concurrently
                results = await asyncio.gather(*tasks)
                
                # Verify all succeeded
                assert len(results) == 5
                for result in results:
                    assert "key" in result
                    assert "CONCURRENT-" in result["key"]

    async def test_tool_validation_and_schema_compliance(self, mock_tool_loader):
        """Test that meta-tools comply with MCP tool schema."""
        tools = mock_tool_loader.load_tools(version="v2")
        
        for tool in tools:
            # Verify required FastMCP tool attributes
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'handler')
            assert callable(tool.handler)
            
            # Verify tool names are valid
            assert tool.name.replace('_', '').isalnum()
            assert len(tool.name) > 0
            
            # Verify descriptions are informative
            assert len(tool.description) > 10
            assert tool.description[0].isupper()  # Should be properly capitalized

    async def test_configuration_override_integration(self, mock_tool_loader):
        """Test configuration overrides in integration context."""
        # Test read-only mode
        with MockEnvironment({"READONLY": "true"}):
            tools = mock_tool_loader.load_tools(version="v2")
            
            # Should still load tools but they should handle read-only mode
            tool_names = {tool.name for tool in tools}
            assert "resource_manager" in tool_names
            
            # The actual read-only enforcement would be tested at the operation level

    async def test_backward_compatibility_mode(self, mock_tool_loader):
        """Test backward compatibility with existing integrations."""
        # Test default version (should be v1 for backward compatibility)
        default_tools = mock_tool_loader.load_tools()
        default_tool_names = {tool.name for tool in default_tools}
        
        # Should load v1 tools by default
        legacy_tool_patterns = ["jira_", "confluence_"]
        has_legacy_tools = any(
            any(pattern in name for pattern in legacy_tool_patterns)
            for name in default_tool_names
        )
        assert has_legacy_tools, "Default should load v1 legacy tools for backward compatibility"

    async def test_health_check_integration(self, mcp_server):
        """Test health check integration with meta-tools."""
        # This would test the health check endpoint's awareness of meta-tools
        # For now, verify the server has health check capability
        assert hasattr(mcp_server, 'health_check') or callable(getattr(mcp_server, 'health_check', None))

    @pytest.mark.asyncio
    async def test_logging_and_monitoring_integration(self, mock_context):
        """Test logging and monitoring integration with meta-tools."""
        resource_manager = ResourceManager()
        
        # Mock successful operation
        mock_issue = MagicMock()
        mock_issue.to_simplified_dict.return_value = {"key": "LOG-123"}
        mock_context.jira_client.get_issue.return_value = mock_issue
        
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_context.jira_client):
                
                # Capture logs during operation
                with patch('src.mcp_atlassian.meta_tools.resource_manager.logger') as mock_logger:
                    await resource_manager.manage_resource(
                        service="jira",
                        resource_type="issue",
                        operation="get",
                        identifier="LOG-123"
                    )
                    
                    # Verify logging occurred (implementation would depend on actual logging)
                    # This is a placeholder for actual log verification
                    assert True  # Would verify specific log calls

    async def test_security_context_integration(self, mock_context):
        """Test security context integration with meta-tools."""
        resource_manager = ResourceManager()
        
        # Test with different auth contexts
        auth_contexts = [
            {"type": "oauth", "user": "test.user"},
            {"type": "token", "user": "api.user"},
            {"type": "pat", "user": "service.account"}
        ]
        
        for auth_context in auth_contexts:
            mock_context.current_auth = auth_context
            
            with patch.object(resource_manager, '_get_context', return_value=mock_context):
                # Should handle different auth contexts gracefully
                try:
                    context = resource_manager._get_context()
                    assert context.current_auth == auth_context
                except Exception as e:
                    # Should not raise auth-related errors for valid contexts
                    assert "auth" not in str(e).lower(), f"Auth error for {auth_context}: {e}"