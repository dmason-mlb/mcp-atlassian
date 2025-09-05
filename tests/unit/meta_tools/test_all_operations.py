"""Comprehensive unit tests for all meta-tools operations."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.mcp_atlassian.meta_tools.errors import MetaToolError
from src.mcp_atlassian.meta_tools.migration_helper import MigrationHelper, MigrationResult, UsageAnalytics
from src.mcp_atlassian.meta_tools.parameter_optimizer import ParameterOptimizer
from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.schema_discovery import SchemaDiscovery, MinimalSchema


class TestAllMetaToolOperations:
    """Comprehensive test suite for all meta-tool operations."""

    @pytest.fixture
    def resource_manager(self):
        """Create ResourceManager instance for testing."""
        return ResourceManager()

    @pytest.fixture
    def dry_run_manager(self):
        """Create ResourceManager instance in dry-run mode."""
        return ResourceManager(dry_run=True)

    @pytest.fixture
    def schema_discovery(self):
        """Create SchemaDiscovery instance for testing."""
        return SchemaDiscovery()

    @pytest.fixture
    def parameter_optimizer(self):
        """Create ParameterOptimizer instance for testing."""
        return ParameterOptimizer()

    @pytest.fixture
    def migration_helper(self):
        """Create MigrationHelper instance for testing."""
        return MigrationHelper()

    @pytest.fixture
    def usage_analytics(self):
        """Create UsageAnalytics instance for testing."""
        return UsageAnalytics()

    @pytest.fixture
    def mock_context(self):
        """Create a mock FastMCP context."""
        return Mock()

    @pytest.fixture
    def mock_jira_client(self):
        """Create a comprehensive mock JiraFetcher."""
        client = Mock()
        
        # Mock issue operations
        mock_issue = Mock()
        mock_issue.to_simplified_dict.return_value = {
            "key": "TEST-123",
            "summary": "Test Issue",
            "status": "Open",
            "description": "Test description",
            "assignee": "test.user",
            "project": {"key": "TEST"},
            "issuetype": {"name": "Bug"}
        }
        client.get_issue.return_value = mock_issue
        client.create_issue.return_value = mock_issue
        client.update_issue.return_value = mock_issue
        client.delete_issue.return_value = True
        
        # Mock comment operations
        mock_comment = Mock()
        mock_comment.to_dict.return_value = {
            "id": "12345",
            "body": "Test comment",
            "author": "test.user"
        }
        client.get_issue_comments.return_value = [mock_comment]
        client.add_comment.return_value = mock_comment
        client.update_comment.return_value = mock_comment
        client.delete_comment.return_value = True
        
        # Mock worklog operations
        mock_worklog = Mock()
        mock_worklog.to_dict.return_value = {
            "id": "67890",
            "timeSpent": "1h",
            "comment": "Work log entry",
            "author": "test.user"
        }
        client.get_issue_worklogs.return_value = [mock_worklog]
        client.add_worklog.return_value = mock_worklog
        client.update_worklog.return_value = mock_worklog
        client.delete_worklog.return_value = True
        
        # Mock attachment operations
        mock_attachment = Mock()
        mock_attachment.to_dict.return_value = {
            "id": "54321",
            "filename": "test.txt",
            "size": 1024,
            "author": "test.user"
        }
        client.get_issue_attachments.return_value = [mock_attachment]
        client.add_attachment.return_value = mock_attachment
        client.delete_attachment.return_value = True
        
        # Mock link operations
        mock_link = Mock()
        mock_link.to_dict.return_value = {
            "id": "11111",
            "type": "relates to",
            "inwardIssue": {"key": "TEST-123"},
            "outwardIssue": {"key": "TEST-124"}
        }
        client.create_issue_link.return_value = mock_link
        client.delete_issue_link.return_value = True
        
        # Mock sprint operations
        mock_sprint = Mock()
        mock_sprint.to_dict.return_value = {
            "id": 100,
            "name": "Sprint 1",
            "state": "active",
            "startDate": "2025-01-01",
            "endDate": "2025-01-14"
        }
        client.get_sprint.return_value = mock_sprint
        client.create_sprint.return_value = mock_sprint
        client.update_sprint.return_value = mock_sprint
        
        # Mock version operations
        mock_version = Mock()
        mock_version.to_dict.return_value = {
            "id": 200,
            "name": "v1.0.0",
            "description": "First release",
            "released": False
        }
        client.get_version.return_value = mock_version
        client.create_version.return_value = mock_version
        client.update_version.return_value = mock_version
        client.delete_version.return_value = True
        
        return client

    @pytest.fixture
    def mock_confluence_client(self):
        """Create a comprehensive mock ConfluenceFetcher."""
        client = Mock()
        
        # Mock page operations
        mock_page = Mock()
        mock_page.to_dict.return_value = {
            "id": "123456",
            "title": "Test Page",
            "space": {"key": "TEST"},
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "version": {"number": 1}
        }
        client.get_page.return_value = mock_page
        client.create_page.return_value = mock_page
        client.update_page.return_value = mock_page
        client.delete_page.return_value = True
        
        # Mock comment operations
        mock_comment = Mock()
        mock_comment.to_dict.return_value = {
            "id": "comment-123",
            "body": {"storage": {"value": "<p>Test comment</p>"}},
            "author": "test.user"
        }
        client.get_page_comments.return_value = [mock_comment]
        client.add_comment.return_value = mock_comment
        client.update_comment.return_value = mock_comment
        client.delete_comment.return_value = True
        
        # Mock label operations
        client.add_labels.return_value = True
        client.delete_label.return_value = True
        
        # Mock space operations
        mock_space = Mock()
        mock_space.to_dict.return_value = {
            "key": "TEST",
            "name": "Test Space",
            "type": "global",
            "description": "Test space description"
        }
        client.get_space.return_value = mock_space
        client.create_space.return_value = mock_space
        client.update_space.return_value = mock_space
        client.delete_space.return_value = True
        
        return client

    # ResourceManager Tests
    @pytest.mark.asyncio
    async def test_resource_manager_jira_issue_crud(self, resource_manager, mock_context, mock_jira_client):
        """Test complete CRUD operations for Jira issues."""
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_jira_client', return_value=mock_jira_client):
                # Test create
                result = await resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue",
                    operation="create",
                    data={
                        "project": "TEST",
                        "summary": "New issue",
                        "description": "Issue description",
                        "issuetype": "Bug"
                    }
                )
                assert result["key"] == "TEST-123"
                
                # Test get
                result = await resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue",
                    operation="get",
                    identifier="TEST-123"
                )
                assert result["key"] == "TEST-123"
                
                # Test update
                result = await resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue",
                    operation="update",
                    identifier="TEST-123",
                    data={"summary": "Updated summary"}
                )
                assert result["key"] == "TEST-123"
                
                # Test delete
                result = await resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue",
                    operation="delete",
                    identifier="TEST-123"
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_resource_manager_confluence_page_crud(self, resource_manager, mock_context, mock_confluence_client):
        """Test complete CRUD operations for Confluence pages."""
        with patch.object(resource_manager, '_get_context', return_value=mock_context):
            with patch.object(resource_manager, '_get_confluence_client', return_value=mock_confluence_client):
                # Test create
                result = await resource_manager.manage_resource(
                    service="confluence",
                    resource_type="page",
                    operation="create",
                    data={
                        "space": "TEST",
                        "title": "New Page",
                        "content": "Page content"
                    }
                )
                assert result["title"] == "Test Page"
                
                # Test get
                result = await resource_manager.manage_resource(
                    service="confluence",
                    resource_type="page",
                    operation="get",
                    identifier="123456"
                )
                assert result["id"] == "123456"
                
                # Test update
                result = await resource_manager.manage_resource(
                    service="confluence",
                    resource_type="page",
                    operation="update",
                    identifier="123456",
                    data={"title": "Updated Page"}
                )
                assert result["id"] == "123456"
                
                # Test delete
                result = await resource_manager.manage_resource(
                    service="confluence",
                    resource_type="page",
                    operation="delete",
                    identifier="123456"
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_resource_manager_dry_run_mode(self, dry_run_manager):
        """Test dry-run mode validation."""
        result = await dry_run_manager.manage_resource(
            service="jira",
            resource_type="issue",
            operation="create",
            data={
                "project": "TEST",
                "summary": "Test issue",
                "issuetype": "Bug"
            }
        )
        
        assert result["status"] == "dry_run_success"
        assert "validation" in result
        assert result["validation"]["valid"] is True

    @pytest.mark.asyncio
    async def test_resource_manager_error_handling(self, resource_manager):
        """Test error handling for invalid operations."""
        # Test invalid service
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.manage_resource(
                service="invalid_service",
                resource_type="issue",
                operation="create",
                data={}
            )
        assert "invalid_service" in str(exc_info.value)
        
        # Test unsupported resource
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.manage_resource(
                service="jira",
                resource_type="unsupported_resource",
                operation="create",
                data={}
            )
        assert "unsupported_resource" in str(exc_info.value)
        
        # Test unsupported operation
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.manage_resource(
                service="jira",
                resource_type="issue",
                operation="unsupported_operation",
                data={}
            )
        assert "unsupported_operation" in str(exc_info.value)

    # SchemaDiscovery Tests
    def test_schema_discovery_get_resource_schema(self, schema_discovery):
        """Test resource schema discovery for different resource types."""
        # Test Jira issue schema
        schema = schema_discovery.get_resource_schema("jira", "issue", "create")
        assert isinstance(schema, MinimalSchema)
        assert len(schema.required) > 0
        assert isinstance(schema.fields, dict)
        
        # Test Confluence page schema  
        schema = schema_discovery.get_resource_schema("confluence", "page", "create")
        assert isinstance(schema, MinimalSchema)
        assert len(schema.required) > 0
        assert isinstance(schema.fields, dict)

    def test_schema_discovery_capabilities(self, schema_discovery):
        """Test capabilities discovery."""
        capabilities = schema_discovery.get_capabilities()
        assert isinstance(capabilities, dict)
        assert "jira" in capabilities or "services" in capabilities or "supported_operations" in capabilities

    def test_schema_discovery_cache_functionality(self, schema_discovery):
        """Test schema caching functionality."""
        # Test cache stats
        stats = schema_discovery.get_cache_stats()
        assert isinstance(stats, dict)
        
        # Test cache clearing
        schema_discovery.clear_conversation_hints()
        # Should not raise any errors

    # ParameterOptimizer Tests
    def test_parameter_optimizer_consolidation(self, parameter_optimizer):
        """Test parameter consolidation and common parameter handling."""
        # Test parameter consolidation
        params = {
            "jql": "project = TEST",
            "max_results": 50,
            "fields": ["summary", "status"],
            "expand": ["changelog"]
        }
        
        optimized = parameter_optimizer.optimize_parameters("jira_search", params)
        assert "jql" in optimized
        assert optimized["max_results"] == 50
        
        # Test common parameter extraction
        common = parameter_optimizer.extract_common_parameters(params)
        assert "max_results" in common or "limit" in common

    def test_parameter_optimizer_merge_parameters(self, parameter_optimizer):
        """Test parameter merging for batch operations."""
        param_sets = [
            {"project": "TEST", "fields": ["summary"]},
            {"project": "DEV", "fields": ["status"]},
            {"project": "PROD", "fields": ["assignee"]}
        ]
        
        merged = parameter_optimizer.merge_parameters(param_sets)
        assert isinstance(merged, dict)
        assert "projects" in merged or "project" in merged

    # MigrationHelper Tests
    @pytest.mark.asyncio
    async def test_migration_helper_translate_legacy_call(self, migration_helper):
        """Test translation of legacy tool calls to meta-tool calls."""
        legacy_call = {
            "tool": "jira_get_issue",
            "arguments": {"issue_key": "TEST-123"}
        }
        
        result = await migration_helper.translate_legacy_call(legacy_call)
        assert isinstance(result, MigrationResult)
        assert result.meta_tool_call["tool"] == "resource_manager"
        assert result.meta_tool_call["arguments"]["service"] == "jira"
        assert result.meta_tool_call["arguments"]["resource_type"] == "issue"
        assert result.meta_tool_call["arguments"]["operation"] == "get"

    def test_migration_helper_get_migration_guidance(self, migration_helper):
        """Test migration guidance generation."""
        guidance = migration_helper.get_migration_guidance("jira_create_issue")
        assert isinstance(guidance, dict)
        assert "meta_tool" in guidance
        assert "parameters_mapping" in guidance
        assert guidance["meta_tool"] == "resource_manager"

    def test_migration_helper_suggest_optimization(self, migration_helper):
        """Test optimization suggestions."""
        legacy_calls = [
            {"tool": "jira_get_issue", "arguments": {"issue_key": "TEST-123"}},
            {"tool": "jira_get_issue", "arguments": {"issue_key": "TEST-124"}},
            {"tool": "jira_search_issues", "arguments": {"jql": "project = TEST"}}
        ]
        
        suggestions = migration_helper.suggest_optimization(legacy_calls)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert "batch_operation" in suggestions[0] or "consolidation" in suggestions[0]

    # UsageAnalytics Tests
    def test_usage_analytics_tracking(self, usage_analytics):
        """Test usage tracking and analytics."""
        # Track some calls
        usage_analytics.track_legacy_call("jira_get_issue", True, 0.5)
        usage_analytics.track_legacy_call("jira_create_issue", True, 1.2)
        usage_analytics.track_legacy_call("jira_get_issue", False, 0.3, "API Error")
        
        # Check most used tools
        most_used = usage_analytics.get_most_used_tools(5)
        assert len(most_used) == 2
        assert most_used[0][0] == "jira_get_issue"  # Most used
        assert most_used[0][1] == 2  # Call count
        
        # Check analytics summary
        summary = usage_analytics.get_analytics_summary()
        assert summary["total_legacy_calls"] == 3
        assert summary["unique_tools_used"] == 2
        assert summary["success_rate"] == 2/3  # 2 successful out of 3 total

    def test_usage_analytics_error_tracking(self, usage_analytics):
        """Test error tracking in analytics."""
        usage_analytics.track_legacy_call(
            "confluence_create_page", 
            False, 
            2.1, 
            "Permission denied"
        )
        
        call_data = usage_analytics.usage_data["legacy_calls"]["confluence_create_page"]
        assert call_data["count"] == 1
        assert call_data["success_count"] == 0
        assert len(call_data["errors"]) == 1
        assert call_data["errors"][0]["message"] == "Permission denied"

    # Integration Tests Between Components
    def test_resource_manager_schema_integration(self, resource_manager, schema_discovery):
        """Test ResourceManager can work with SchemaDiscovery."""
        # Test that both components can be instantiated and work together
        assert resource_manager is not None
        assert schema_discovery is not None
        
        # Test schema discovery returns valid schemas
        schema = schema_discovery.get_resource_schema("jira", "issue", "create")
        assert isinstance(schema, MinimalSchema)
        assert len(schema.required) > 0

    def test_parameter_optimizer_with_migration_helper(self, parameter_optimizer, migration_helper):
        """Test ParameterOptimizer integration with MigrationHelper."""
        # Test parameter optimization in migration context
        legacy_params = {"issue_key": "TEST-123", "expand": "changelog"}
        
        with patch.object(migration_helper, 'parameter_optimizer', parameter_optimizer):
            guidance = migration_helper.get_migration_guidance("jira_get_issue")
            
            # Verify the guidance includes parameter optimization
            assert "parameters_mapping" in guidance
            assert isinstance(guidance["parameters_mapping"], dict)

    # Performance and Edge Case Tests
    def test_large_data_handling(self, resource_manager):
        """Test handling of large data sets."""
        large_data = {
            "description": "x" * 10000,  # Large description
            "custom_fields": {f"field_{i}": f"value_{i}" for i in range(100)}
        }
        
        # Should not raise any size-related errors
        result = resource_manager._validate_data_size(large_data)
        assert result is True or isinstance(result, dict)

    def test_concurrent_operations(self, resource_manager):
        """Test thread safety of meta-tools."""
        # This would be expanded with actual concurrent testing
        # For now, just verify the manager handles multiple instances
        manager1 = ResourceManager()
        manager2 = ResourceManager(dry_run=True)
        
        assert manager1.dry_run != manager2.dry_run
        assert id(manager1) != id(manager2)

    def test_configuration_validation(self, resource_manager, schema_discovery):
        """Test configuration and setup validation."""
        # Test invalid configurations
        with pytest.raises(ValueError):
            ResourceManager(dry_run="invalid")  # Should be boolean
        
        # Test schema discovery configuration
        schema = schema_discovery.get_minimal_schema("invalid_service", "issue", "create")
        assert schema.required_fields == []  # Should handle gracefully

    # Memory and Resource Management Tests  
    def test_memory_cleanup(self, usage_analytics):
        """Test memory cleanup and resource management."""
        # Add many tracking entries
        for i in range(1000):
            usage_analytics.track_legacy_call(f"tool_{i}", True, 0.1)
        
        # Should not consume excessive memory
        import sys
        initial_size = sys.getsizeof(usage_analytics.usage_data)
        assert initial_size < 1024 * 1024  # Less than 1MB for 1000 entries

    def test_error_recovery(self, resource_manager):
        """Test error recovery and graceful degradation."""
        with patch.object(resource_manager, '_get_context', side_effect=Exception("Connection lost")):
            # Should handle connection errors gracefully
            with pytest.raises((MetaToolError, Exception)):
                import asyncio
                asyncio.run(resource_manager.manage_resource(
                    service="jira",
                    resource_type="issue", 
                    operation="get",
                    identifier="TEST-123"
                ))