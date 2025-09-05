"""Test suite for parameter optimization system."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from mcp_atlassian.meta_tools.parameter_optimizer import (
    ParameterOptimizer,
    OptimizedParameter,
    get_parameter_optimizer,
    optimize_tool_parameters,
)


class TestParameterOptimizer:
    """Test cases for ParameterOptimizer class."""

    @pytest.fixture
    def sample_registry_data(self):
        """Sample registry data for testing."""
        return {
            "common_parameters": {
                "issue_key": {
                    "type": "string",
                    "pattern": "^[A-Z]+-\\d+$",
                    "description": "Jira issue key",
                    "example": "PROJ-123",
                    "usage_count": 15
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "Maximum results",
                    "usage_count": 18
                },
                "dry_run": {
                    "type": "boolean",
                    "default": False,
                    "description": "Validate without executing",
                    "usage_count": 8
                }
            },
            "context_defaults": {
                "search_operations": {
                    "limit": 25,
                    "start_at": 0,
                    "fields": "summary,status,assignee"
                },
                "create_operations": {
                    "fields": {},
                    "dry_run": False
                },
                "get_operations": {
                    "expand": "changelog,comments",
                    "comment_limit": 10
                }
            },
            "parameter_combinations": {
                "jira_issue_operations": ["issue_key", "fields", "expand", "comment_limit"],
                "jira_search_operations": ["jql", "fields", "limit", "start_at"],
                "confluence_page_operations": ["page_id", "title", "space_key", "parent_id"]
            }
        }

    @pytest.fixture
    def optimizer(self, sample_registry_data):
        """Create optimizer instance with mocked registry data."""
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_registry_data))):
            return ParameterOptimizer()

    def test_registry_loading(self, optimizer, sample_registry_data):
        """Test that registry data loads correctly."""
        assert len(optimizer.registry) == 3
        assert "issue_key" in optimizer.registry
        assert "limit" in optimizer.registry
        assert "dry_run" in optimizer.registry

        assert len(optimizer.context_defaults) == 3
        assert "search_operations" in optimizer.context_defaults
        
        assert len(optimizer.combinations) == 3
        assert "jira_issue_operations" in optimizer.combinations

    def test_registry_loading_failure(self):
        """Test fallback when registry file cannot be loaded."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            optimizer = ParameterOptimizer()
            
        # Should fallback to empty registries
        assert optimizer.registry == {}
        assert optimizer.context_defaults == {}
        assert optimizer.combinations == {}

    def test_get_parameter_definition(self, optimizer):
        """Test retrieving parameter definitions."""
        # Test existing parameter
        issue_key_def = optimizer.get_parameter_definition("issue_key")
        assert issue_key_def is not None
        assert issue_key_def["description"] == "Jira issue key"
        assert issue_key_def["pattern"] == "^[A-Z]+-\\d+$"
        
        # Test non-existent parameter
        unknown_def = optimizer.get_parameter_definition("unknown_param")
        assert unknown_def is None

    def test_optimize_parameter_from_registry(self, optimizer):
        """Test parameter optimization using registry definitions."""
        optimized = optimizer.optimize_parameter(
            param_name="issue_key",
            required=True
        )
        
        assert isinstance(optimized, OptimizedParameter)
        assert optimized.name == "issue_key"
        assert optimized.type_info == "string"
        assert optimized.description == "Jira issue key"
        assert optimized.required is True
        assert optimized.validation is not None
        assert optimized.validation["pattern"] == "^[A-Z]+-\\d+$"

    def test_optimize_parameter_with_defaults(self, optimizer):
        """Test parameter optimization with defaults."""
        optimized = optimizer.optimize_parameter(
            param_name="limit"
        )
        
        assert optimized.name == "limit"
        assert optimized.type_info == "integer"
        assert optimized.default == 10
        assert optimized.validation["minimum"] == 1
        assert optimized.validation["maximum"] == 50

    def test_optimize_parameter_fallback(self, optimizer):
        """Test parameter optimization fallback for unknown parameters."""
        optimized = optimizer.optimize_parameter(
            param_name="custom_field",
            original_description="(Optional) Custom field value for the issue",
            param_type="string"
        )
        
        assert optimized.name == "custom_field"
        assert optimized.type_info == "string"
        assert optimized.description == "Custom field value for the issue"  # Minimized
        assert optimized.validation is None

    def test_apply_context_defaults(self, optimizer):
        """Test context-aware defaults application."""
        # Test search operation defaults
        params = {}
        result = optimizer.apply_context_defaults(
            service="jira",
            resource="issue",
            operation="search",
            parameters=params
        )
        
        assert result["limit"] == 25
        assert result["start_at"] == 0
        assert result["fields"] == "summary,status,assignee"

    def test_apply_context_defaults_existing_values(self, optimizer):
        """Test that existing parameter values are preserved."""
        params = {"limit": 100, "fields": "custom,fields"}
        result = optimizer.apply_context_defaults(
            service="jira",
            resource="issue", 
            operation="search",
            parameters=params
        )
        
        # Should preserve existing values
        assert result["limit"] == 100
        assert result["fields"] == "custom,fields"
        # Should add missing defaults
        assert result["start_at"] == 0

    def test_apply_context_defaults_get_operation(self, optimizer):
        """Test defaults for get operations."""
        params = {}
        result = optimizer.apply_context_defaults(
            service="jira",
            resource="issue",
            operation="get", 
            parameters=params
        )
        
        assert result["expand"] == "changelog,comments"
        assert result["comment_limit"] == 10

    def test_apply_context_defaults_create_operation(self, optimizer):
        """Test defaults for create operations."""
        params = {}
        result = optimizer.apply_context_defaults(
            service="jira",
            resource="issue",
            operation="create",
            parameters=params
        )
        
        assert result["dry_run"] is False

    def test_get_recommended_parameters(self, optimizer):
        """Test getting recommended parameters for operations."""
        # Test Jira issue operations
        recommendations = optimizer.get_recommended_parameters(
            service="jira",
            resource="issue",
            operation="get"
        )
        
        expected = ["issue_key", "fields", "expand", "comment_limit"]
        assert all(param in recommendations for param in expected)

    def test_get_recommended_parameters_search(self, optimizer):
        """Test recommendations for search operations."""
        recommendations = optimizer.get_recommended_parameters(
            service="jira",
            resource="issue", 
            operation="search"
        )
        
        assert "jql" in recommendations
        assert "limit" in recommendations
        assert "start_at" in recommendations

    def test_get_parameter_schema_ref(self, optimizer):
        """Test JSON Schema reference generation."""
        # Test common parameter
        ref = optimizer.get_parameter_schema_ref("issue_key")
        assert ref == {"$ref": "#/$defs/common_parameters/issue_key"}
        
        # Test non-common parameter
        ref = optimizer.get_parameter_schema_ref("unknown_param")
        assert ref is None

    def test_calculate_token_savings(self, optimizer):
        """Test token savings calculation."""
        params = ["issue_key", "limit", "custom_field", "description"]
        savings = optimizer.calculate_token_savings(params)
        
        assert "original_tokens" in savings
        assert "optimized_tokens" in savings
        assert "token_savings" in savings
        assert "savings_percentage" in savings
        assert "common_parameters" in savings
        assert "total_parameters" in savings
        
        assert savings["total_parameters"] == 4
        assert savings["common_parameters"] == 2  # issue_key and limit
        assert savings["token_savings"] > 0
        assert 0 <= savings["savings_percentage"] <= 100

    def test_format_type(self):
        """Test type formatting utility."""
        # String type
        assert ParameterOptimizer._format_type("string") == "string"
        
        # Union type
        assert ParameterOptimizer._format_type(["string", "null"]) == "string | null"

    def test_extract_validation(self):
        """Test validation extraction from registry definition."""
        registry_def = {
            "type": "string",
            "pattern": "^[A-Z]+$",
            "minimum": 1,
            "maximum": 100,
            "description": "Test param"
        }
        
        validation = ParameterOptimizer._extract_validation(registry_def)
        assert validation["pattern"] == "^[A-Z]+$"
        assert validation["minimum"] == 1
        assert validation["maximum"] == 100

    def test_extract_validation_empty(self):
        """Test validation extraction with no validation rules."""
        registry_def = {
            "type": "string",
            "description": "Test param"
        }
        
        validation = ParameterOptimizer._extract_validation(registry_def)
        assert validation is None

    def test_minimize_description(self):
        """Test description minimization."""
        # Test with example removal
        original = "Jira issue key (e.g., 'PROJ-123')"
        minimized = ParameterOptimizer._minimize_description(original)
        assert minimized == "Jira issue key"
        
        # Test with optional prefix removal
        original = "(Optional) The title of the page"
        minimized = ParameterOptimizer._minimize_description(original)
        assert minimized == "Title of the page"
        
        # Test with capitalization
        original = "maximum number of results"
        minimized = ParameterOptimizer._minimize_description(original)
        assert minimized == "Maximum number of results"


class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_parameter_optimizer_singleton(self):
        """Test that get_parameter_optimizer returns same instance."""
        optimizer1 = get_parameter_optimizer()
        optimizer2 = get_parameter_optimizer()
        
        assert optimizer1 is optimizer2

    @patch('mcp_atlassian.meta_tools.parameter_optimizer.get_parameter_optimizer')
    def test_optimize_tool_parameters_caching(self, mock_get_optimizer):
        """Test that optimize_tool_parameters uses caching."""
        mock_optimizer = mock_get_optimizer.return_value
        mock_optimizer.optimize_parameter.return_value = OptimizedParameter(
            name="test",
            type_info="string",
            description="Test param"
        )
        
        # Call twice with same parameters
        params = ("issue_key", "limit")
        result1 = optimize_tool_parameters("jira", "issue", "get", params)
        result2 = optimize_tool_parameters("jira", "issue", "get", params)
        
        # Should return same cached result
        assert result1 is result2
        # Optimizer should only be called once due to caching
        assert mock_get_optimizer.call_count == 1


class TestIntegration:
    """Integration tests with real registry file."""

    def test_real_registry_loading(self):
        """Test loading the actual common_params.json file."""
        optimizer = ParameterOptimizer()
        
        # Should load without errors
        assert isinstance(optimizer.registry, dict)
        assert isinstance(optimizer.context_defaults, dict)
        assert isinstance(optimizer.combinations, dict)
        
        # Check for expected parameters
        expected_params = ["issue_key", "project_key", "limit", "start_at", "fields"]
        for param in expected_params:
            assert param in optimizer.registry

    def test_end_to_end_optimization(self):
        """Test complete parameter optimization workflow."""
        optimizer = get_parameter_optimizer()
        
        # Test optimizing parameters for a Jira issue operation
        original_params = [
            "issue_key", "fields", "expand", "comment_limit", "custom_field"
        ]
        
        optimized = []
        for param in original_params:
            opt_param = optimizer.optimize_parameter(param, required=(param == "issue_key"))
            optimized.append(opt_param)
        
        # Apply context defaults
        params_with_defaults = optimizer.apply_context_defaults(
            service="jira",
            resource="issue",
            operation="get",
            parameters={}
        )
        
        # Calculate savings
        savings = optimizer.calculate_token_savings(original_params)
        
        # Verify results
        assert len(optimized) == 5
        assert all(isinstance(p, OptimizedParameter) for p in optimized)
        assert "expand" in params_with_defaults
        assert savings["token_savings"] > 0


@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks for parameter optimization."""

    def test_parameter_optimization_performance(self, benchmark):
        """Benchmark parameter optimization speed."""
        optimizer = get_parameter_optimizer()
        
        def optimize_many_params():
            params = ["issue_key", "fields", "limit", "start_at", "expand"] * 20
            for param in params:
                optimizer.optimize_parameter(param)
        
        result = benchmark(optimize_many_params)
        # Should complete quickly even with many parameters

    def test_context_defaults_performance(self, benchmark):
        """Benchmark context defaults application speed."""
        optimizer = get_parameter_optimizer()
        
        def apply_many_defaults():
            for i in range(100):
                optimizer.apply_context_defaults(
                    service="jira",
                    resource="issue",
                    operation="search",
                    parameters={}
                )
        
        result = benchmark(apply_many_defaults)
        # Should handle many operations efficiently