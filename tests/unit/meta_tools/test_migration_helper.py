"""Tests for migration helper functionality.

Tests cover:
- Legacy tool translation accuracy  
- Parameter transformation
- Analytics tracking
- Error handling
- Integration scenarios
"""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from typing import Any, Dict

from src.mcp_atlassian.meta_tools.migration_helper import (
    MigrationHelper,
    MigrationResult, 
    UsageAnalytics,
    get_migration_helper
)
from src.mcp_atlassian.meta_tools.errors import MetaToolError


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    context = Mock()
    context.get_jira_fetcher = AsyncMock()
    context.get_confluence_fetcher = AsyncMock()
    return context


@pytest.fixture
def sample_mappings():
    """Sample mappings for testing."""
    return {
        "jira": {
            "get_issue": {
                "meta_tool": "resource_manager",
                "resource": "issue",
                "operation": "get",
                "parameter_mapping": {
                    "issue_key": "identifier",
                    "fields": {"target": "options", "field": "fields"}
                }
            },
            "create_issue": {
                "meta_tool": "resource_manager",
                "resource": "issue", 
                "operation": "create",
                "parameter_mapping": {
                    "project_key": {"target": "data", "field": "project"},
                    "summary": {"target": "data", "field": "summary"},
                    "issue_type": {"target": "data", "field": "issuetype"}
                }
            }
        },
        "confluence": {
            "get_page": {
                "meta_tool": "resource_manager",
                "resource": "page",
                "operation": "get", 
                "parameter_mapping": {
                    "page_id": "identifier",
                    "expand": {"target": "options", "field": "expand"}
                }
            }
        }
    }


@pytest.fixture  
def migration_helper():
    """Create a migration helper instance."""
    helper = MigrationHelper()
    return helper


class TestUsageAnalytics:
    """Test usage analytics functionality."""
    
    def test_track_legacy_call_success(self):
        """Test tracking successful legacy call."""
        analytics = UsageAnalytics()
        
        analytics.track_legacy_call("get_issue", True, 0.123)
        
        assert "get_issue" in analytics.usage_data["legacy_calls"]
        call_data = analytics.usage_data["legacy_calls"]["get_issue"]
        assert call_data["count"] == 1
        assert call_data["success_count"] == 1
        assert call_data["total_time"] == 0.123
        assert analytics.usage_data["migration_success_rate"] == 1.0
    
    def test_track_legacy_call_failure(self):
        """Test tracking failed legacy call."""
        analytics = UsageAnalytics()
        
        analytics.track_legacy_call("create_issue", False, 0.456, "Test error")
        
        call_data = analytics.usage_data["legacy_calls"]["create_issue"]
        assert call_data["count"] == 1
        assert call_data["success_count"] == 0
        assert len(call_data["errors"]) == 1
        assert call_data["errors"][0]["message"] == "Test error"
        assert analytics.usage_data["migration_success_rate"] == 0.0
    
    def test_get_most_used_tools(self):
        """Test getting most used tools."""
        analytics = UsageAnalytics()
        
        # Track multiple calls
        analytics.track_legacy_call("get_issue", True, 0.1)
        analytics.track_legacy_call("get_issue", True, 0.1)
        analytics.track_legacy_call("create_issue", True, 0.2)
        analytics.track_legacy_call("update_issue", True, 0.3)
        
        most_used = analytics.get_most_used_tools(2)
        assert len(most_used) == 2
        assert most_used[0] == ("get_issue", 2)
        assert most_used[1][1] == 1  # Either create_issue or update_issue
    
    def test_get_analytics_summary(self):
        """Test analytics summary generation."""
        analytics = UsageAnalytics()
        
        analytics.track_legacy_call("get_issue", True, 0.1)
        analytics.track_legacy_call("create_issue", False, 0.2, "Error")
        
        summary = analytics.get_analytics_summary()
        assert summary["total_legacy_calls"] == 2
        assert summary["unique_tools_used"] == 2
        assert summary["success_rate"] == 0.5
        assert summary["avg_execution_time"] == 0.15
        assert len(summary["most_used_tools"]) == 2


class TestMigrationHelper:
    """Test migration helper core functionality."""
    
    def test_init(self):
        """Test migration helper initialization."""
        helper = MigrationHelper()
        
        assert helper.resource_manager is not None
        assert helper.schema_discovery is not None
        assert helper.analytics is not None
        assert helper._mappings is None
        assert not helper._mappings_loaded
    
    @patch('src.mcp_atlassian.meta_tools.migration_helper.Path')
    @patch('builtins.open')
    def test_load_mappings_success(self, mock_open, mock_path, sample_mappings):
        """Test successful mappings loading."""
        helper = MigrationHelper()
        
        # Mock file operations
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        # Mock json.load
        with patch('json.load', return_value=sample_mappings):
            mappings = helper._load_mappings()
        
        assert mappings == sample_mappings
        assert helper._mappings_loaded
    
    @patch('src.mcp_atlassian.meta_tools.migration_helper.Path')
    def test_load_mappings_file_not_found(self, mock_path):
        """Test mappings loading when file doesn't exist."""
        helper = MigrationHelper()
        
        mock_path_instance = MagicMock() 
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance
        
        mappings = helper._load_mappings()
        
        assert mappings == {"jira": {}, "confluence": {}}
        assert helper._mappings_loaded
    
    def test_get_service_from_tool_name_jira(self):
        """Test service detection for Jira tools."""
        helper = MigrationHelper()
        
        jira_tools = [
            "get_issue", "create_issue", "update_issue", 
            "create_sprint", "get_project", "add_comment"
        ]
        
        for tool in jira_tools:
            assert helper._get_service_from_tool_name(tool) == "jira"
    
    def test_get_service_from_tool_name_confluence(self):
        """Test service detection for Confluence tools."""
        helper = MigrationHelper()
        
        confluence_tools = [
            "get_page", "create_page", "update_page",
            "add_label", "search_confluence"
        ]
        
        for tool in confluence_tools:
            assert helper._get_service_from_tool_name(tool) == "confluence"
    
    def test_get_service_from_tool_name_unknown(self):
        """Test service detection for unknown tools defaults to jira."""
        helper = MigrationHelper()
        
        assert helper._get_service_from_tool_name("unknown_tool") == "jira"
    
    def test_transform_parameters_simple_mapping(self):
        """Test simple parameter transformation."""
        helper = MigrationHelper()
        
        legacy_params = {"issue_key": "PROJ-123", "fields": "summary,status"}
        mapping_config = {
            "parameter_mapping": {
                "issue_key": "identifier",
                "fields": {"target": "options", "field": "fields"}
            }
        }
        
        resource_params, options = helper._transform_parameters(legacy_params, mapping_config)
        
        assert resource_params["identifier"] == "PROJ-123"
        assert options["fields"] == "summary,status"
    
    def test_transform_parameters_data_mapping(self):
        """Test parameter transformation to data field."""
        helper = MigrationHelper()
        
        legacy_params = {
            "project_key": "PROJ",
            "summary": "Test issue",
            "issue_type": "Bug"
        }
        mapping_config = {
            "parameter_mapping": {
                "project_key": {"target": "data", "field": "project"},
                "summary": {"target": "data", "field": "summary"},
                "issue_type": {"target": "data", "field": "issuetype"}
            }
        }
        
        resource_params, options = helper._transform_parameters(legacy_params, mapping_config)
        
        assert resource_params["data"]["project"] == "PROJ"
        assert resource_params["data"]["summary"] == "Test issue"
        assert resource_params["data"]["issuetype"] == "Bug"
        assert len(options) == 0
    
    def test_handle_common_parameter_patterns_additional_fields_dict(self):
        """Test handling additional_fields as dictionary."""
        helper = MigrationHelper()
        
        legacy_params = {
            "additional_fields": {"priority": {"name": "High"}, "labels": ["urgent"]}
        }
        resource_params = {}
        options = {}
        mapping_config = {}
        
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        assert resource_params["data"]["priority"]["name"] == "High"
        assert resource_params["data"]["labels"] == ["urgent"]
    
    def test_handle_common_parameter_patterns_additional_fields_json(self):
        """Test handling additional_fields as JSON string."""
        helper = MigrationHelper()
        
        legacy_params = {
            "additional_fields": '{"priority": {"name": "Medium"}}'
        }
        resource_params = {}
        options = {}
        mapping_config = {}
        
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        assert resource_params["data"]["priority"]["name"] == "Medium"
    
    def test_handle_common_parameter_patterns_components_string(self):
        """Test handling components as comma-separated string."""
        helper = MigrationHelper()
        
        legacy_params = {"components": "Frontend, API, Database"}
        resource_params = {}
        options = {}
        mapping_config = {}
        
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        expected_components = [
            {"name": "Frontend"},
            {"name": "API"}, 
            {"name": "Database"}
        ]
        assert resource_params["data"]["components"] == expected_components
    
    def test_handle_common_parameter_patterns_pagination(self):
        """Test handling pagination parameters."""
        helper = MigrationHelper()
        
        legacy_params = {
            "start_at": 10,
            "max_results": 50,
            "fields": "summary,status",
            "expand": "changelog"
        }
        resource_params = {}
        options = {}
        mapping_config = {}
        
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        assert options["start_at"] == 10
        assert options["max_results"] == 50
        assert options["fields"] == "summary,status"
        assert options["expand"] == "changelog"
    
    @patch.object(MigrationHelper, '_load_mappings')
    def test_translate_legacy_call_success(self, mock_load_mappings, sample_mappings):
        """Test successful legacy call translation."""
        helper = MigrationHelper()
        mock_load_mappings.return_value = sample_mappings
        
        legacy_params = {"issue_key": "PROJ-123", "fields": "summary,status"}
        
        result = helper.translate_legacy_call("get_issue", legacy_params)
        
        expected = {
            "tool": "resource_manager",
            "parameters": {
                "service": "jira",
                "resource": "issue",
                "operation": "get",
                "identifier": "PROJ-123",
                "options": {"fields": "summary,status"}
            }
        }
        assert result == expected
    
    @patch.object(MigrationHelper, '_load_mappings')
    def test_translate_legacy_call_not_found(self, mock_load_mappings):
        """Test translation with unmapped legacy tool."""
        helper = MigrationHelper()
        mock_load_mappings.return_value = {"jira": {}, "confluence": {}}
        
        with pytest.raises(MetaToolError) as exc_info:
            helper.translate_legacy_call("unknown_tool", {})
        
        error = exc_info.value
        assert error.error_code == "JIRA_MIGRATION_MAPPING_NOT_FOUND"
        assert "No migration mapping found" in error.message
    
    def test_generate_migration_guidance(self):
        """Test migration guidance generation."""
        helper = MigrationHelper()
        
        meta_tool_call = {
            "tool": "resource_manager", 
            "parameters": {"service": "jira", "resource": "issue"}
        }
        
        guidance = helper._generate_migration_guidance(
            "get_issue", meta_tool_call, 0.123
        )
        
        assert guidance["legacy_tool"] == "get_issue"
        assert guidance["meta_tool_equivalent"] == meta_tool_call
        assert "learning_note" in guidance
        assert "benefits" in guidance
        assert guidance["execution_time"] == "0.123s"
        assert "next_steps" in guidance
    
    @pytest.mark.asyncio
    @patch.object(MigrationHelper, 'translate_legacy_call')
    async def test_migrate_legacy_call_success(self, mock_translate, mock_context):
        """Test successful migration execution."""
        helper = MigrationHelper()
        
        # Mock translation
        mock_translate.return_value = {
            "tool": "resource_manager",
            "parameters": {
                "service": "jira",
                "resource": "issue", 
                "operation": "get",
                "identifier": "PROJ-123"
            }
        }
        
        # Mock resource manager execution
        helper.resource_manager.execute_operation = AsyncMock(
            return_value='{"key": "PROJ-123", "summary": "Test issue"}'
        )
        
        result = await helper.migrate_legacy_call(
            mock_context, "get_issue", {"issue_key": "PROJ-123"}
        )
        
        assert isinstance(result, MigrationResult)
        assert result.legacy_tool_name == "get_issue"
        assert "PROJ-123" in result.result
        assert result.meta_tool_call["tool"] == "resource_manager"
        assert "learning_note" in result.migration_guidance
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    @patch.object(MigrationHelper, 'translate_legacy_call')
    async def test_migrate_legacy_call_failure(self, mock_translate, mock_context):
        """Test migration execution with failure."""
        helper = MigrationHelper()
        
        # Mock translation failure
        mock_translate.side_effect = MetaToolError(
            error_code="TEST_ERROR", 
            message="Test error"
        )
        
        with pytest.raises(MetaToolError):
            await helper.migrate_legacy_call(
                mock_context, "unknown_tool", {}
            )
        
        # Verify analytics tracked the failure
        assert "unknown_tool" in helper.analytics.usage_data["legacy_calls"]
        call_data = helper.analytics.usage_data["legacy_calls"]["unknown_tool"]
        assert call_data["success_count"] == 0
        assert len(call_data["errors"]) == 1
    
    @patch.object(MigrationHelper, '_load_mappings')
    def test_get_migration_guidance(self, mock_load_mappings, sample_mappings):
        """Test getting migration guidance without execution."""
        helper = MigrationHelper()
        mock_load_mappings.return_value = sample_mappings
        
        guidance = helper.get_migration_guidance("get_issue")
        
        assert guidance["legacy_tool"] == "get_issue"
        assert guidance["meta_tool"] == "resource_manager"
        assert guidance["resource"] == "issue"
        assert guidance["operation"] == "get"
        assert guidance["service"] == "jira"
        assert "parameter_mapping" in guidance
    
    @patch.object(MigrationHelper, '_load_mappings')
    def test_get_migration_guidance_not_found(self, mock_load_mappings):
        """Test getting guidance for unmapped tool."""
        helper = MigrationHelper()
        mock_load_mappings.return_value = {"jira": {"known_tool": {}}, "confluence": {}}
        
        guidance = helper.get_migration_guidance("unknown_tool")
        
        assert "error" in guidance
        assert "available_tools" in guidance
        assert "suggestion" in guidance
        assert "known_tool" in guidance["available_tools"]
    
    def test_get_usage_analytics(self):
        """Test getting usage analytics."""
        helper = MigrationHelper()
        
        # Add some usage data
        helper.analytics.track_legacy_call("get_issue", True, 0.1)
        helper.analytics.track_legacy_call("create_issue", True, 0.2)
        
        analytics = helper.get_usage_analytics()
        
        assert analytics["total_legacy_calls"] == 2
        assert analytics["unique_tools_used"] == 2
        assert analytics["success_rate"] == 1.0
        assert analytics["avg_execution_time"] == 0.15
    
    @patch.object(MigrationHelper, '_load_mappings')
    def test_list_available_migrations(self, mock_load_mappings, sample_mappings):
        """Test listing available migrations."""
        helper = MigrationHelper()
        mock_load_mappings.return_value = sample_mappings
        
        # Test all services
        all_migrations = helper.list_available_migrations()
        assert "jira" in all_migrations
        assert "confluence" in all_migrations
        assert "get_issue" in all_migrations["jira"]
        assert "get_page" in all_migrations["confluence"]
        
        # Test specific service
        jira_migrations = helper.list_available_migrations("jira")
        assert len(jira_migrations) == 1
        assert "jira" in jira_migrations
        assert "get_issue" in jira_migrations["jira"]


class TestGlobalMigrationHelper:
    """Test global migration helper singleton."""
    
    def test_get_migration_helper_singleton(self):
        """Test that get_migration_helper returns singleton."""
        helper1 = get_migration_helper()
        helper2 = get_migration_helper()
        
        assert helper1 is helper2
        assert isinstance(helper1, MigrationHelper)


class TestIntegrationScenarios:
    """Test complete migration scenarios."""
    
    @pytest.mark.asyncio
    @patch('src.mcp_atlassian.meta_tools.migration_helper.Path')
    @patch('builtins.open')
    async def test_complete_jira_issue_creation_migration(
        self, mock_open, mock_path, mock_context, sample_mappings
    ):
        """Test complete Jira issue creation migration."""
        helper = MigrationHelper()
        
        # Mock mappings file loading
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        with patch('json.load', return_value=sample_mappings):
            # Mock successful resource manager execution  
            helper.resource_manager.execute_operation = AsyncMock(
                return_value='{"key": "PROJ-124", "summary": "New test issue"}'
            )
            
            legacy_params = {
                "project_key": "PROJ",
                "summary": "New test issue",
                "issue_type": "Bug",
                "additional_fields": '{"priority": {"name": "High"}}'
            }
            
            result = await helper.migrate_legacy_call(
                mock_context, "create_issue", legacy_params
            )
            
            # Verify result
            assert isinstance(result, MigrationResult)
            assert result.legacy_tool_name == "create_issue"
            assert "PROJ-124" in result.result
            
            # Verify meta-tool call structure
            meta_call = result.meta_tool_call
            assert meta_call["tool"] == "resource_manager"
            assert meta_call["parameters"]["service"] == "jira"
            assert meta_call["parameters"]["resource"] == "issue"
            assert meta_call["parameters"]["operation"] == "create"
            
            # Verify transformed data
            data = meta_call["parameters"]["data"]
            assert data["project"] == "PROJ"
            assert data["summary"] == "New test issue"
            assert data["issuetype"] == "Bug"
            assert data["priority"]["name"] == "High"
            
            # Verify analytics
            analytics = helper.get_usage_analytics()
            assert analytics["total_legacy_calls"] == 1
            assert analytics["success_rate"] == 1.0
            
            # Verify guidance
            guidance = result.migration_guidance
            assert guidance["legacy_tool"] == "create_issue"
            assert "learning_note" in guidance
            assert "benefits" in guidance
    
    @pytest.mark.asyncio 
    @patch('src.mcp_atlassian.meta_tools.migration_helper.Path')
    @patch('builtins.open')
    async def test_complete_confluence_page_retrieval_migration(
        self, mock_open, mock_path, mock_context, sample_mappings
    ):
        """Test complete Confluence page retrieval migration."""
        helper = MigrationHelper()
        
        # Mock mappings file loading
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance
        
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file
        
        with patch('json.load', return_value=sample_mappings):
            # Mock successful resource manager execution
            helper.resource_manager.execute_operation = AsyncMock(
                return_value='{"id": "123456", "title": "Test Page"}'
            )
            
            legacy_params = {
                "page_id": "123456",
                "expand": "body.storage,version"
            }
            
            result = await helper.migrate_legacy_call(
                mock_context, "get_page", legacy_params
            )
            
            # Verify result
            assert isinstance(result, MigrationResult) 
            assert result.legacy_tool_name == "get_page"
            assert "123456" in result.result
            
            # Verify meta-tool call
            meta_call = result.meta_tool_call
            assert meta_call["tool"] == "resource_manager"
            assert meta_call["parameters"]["service"] == "confluence"
            assert meta_call["parameters"]["resource"] == "page"
            assert meta_call["parameters"]["operation"] == "get"
            assert meta_call["parameters"]["identifier"] == "123456"
            assert meta_call["parameters"]["options"]["expand"] == "body.storage,version"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_transform_parameters_missing_mapping(self):
        """Test parameter transformation with missing mapping."""
        helper = MigrationHelper()
        
        legacy_params = {"unknown_param": "value"}
        mapping_config = {"parameter_mapping": {}}
        
        resource_params, options = helper._transform_parameters(legacy_params, mapping_config)
        
        # Unknown parameters should not be included
        assert "unknown_param" not in resource_params
        assert "unknown_param" not in options
    
    def test_handle_common_parameter_patterns_invalid_json(self):
        """Test handling invalid JSON in additional_fields."""
        helper = MigrationHelper()
        
        legacy_params = {"additional_fields": "invalid json"}
        resource_params = {}
        options = {}
        mapping_config = {}
        
        # Should not raise exception, just log warning
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        # Should not create data field for invalid JSON
        assert "data" not in resource_params
    
    def test_components_empty_string(self):
        """Test handling empty components string."""
        helper = MigrationHelper()
        
        legacy_params = {"components": ""}
        resource_params = {}
        options = {}
        mapping_config = {}
        
        helper._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )
        
        # Should create empty components array
        assert resource_params["data"]["components"] == []
    
    def test_dry_run_parameter_passthrough(self):
        """Test that dry_run parameter is passed through correctly."""
        helper = MigrationHelper()
        
        with patch.object(helper, '_load_mappings') as mock_load:
            mock_load.return_value = {
                "jira": {
                    "test_tool": {
                        "meta_tool": "resource_manager",
                        "resource": "test",
                        "operation": "get",
                        "parameter_mapping": {}
                    }
                }
            }
            
            result = helper.translate_legacy_call("test_tool", {"dry_run": True})
            
            assert result["parameters"]["dry_run"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])