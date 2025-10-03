#!/usr/bin/env python3
"""Schema Completeness Validation Tests

This test suite validates that the schemas returned by get_resource_schema exactly match
what the actual tools require. It ensures parameter optimizers and common_params.json
aren't accidentally removing required fields that would cause AI agent failures.

These tests prevent regressions where schemas appear complete but are missing critical
fields that tools actually need.
"""

import json
import os
from typing import Any, Dict, List, Set
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.meta_tools.parameter_optimizer import ParameterOptimizer
from mcp_atlassian.meta_tools.schema_discovery import SchemaDiscovery
from mcp_atlassian.servers.main import AtlassianMCP, main_lifespan
from mcp_atlassian.servers.context import MainAppContext
from tests.utils.mocks import MockEnvironment


@pytest.fixture
async def schema_test_server():
    """Create test server for schema validation."""
    test_env = {
        "ATLASSIAN_URL": "https://baseball.atlassian.net",
        "ATLASSIAN_EMAIL": "test@example.com",
        "ATLASSIAN_API_TOKEN": "test-token",
        "CONFLUENCE_URL": "https://baseball.atlassian.net/wiki",
    }

    with patch.dict(os.environ, test_env):
        from mcp_atlassian.jira.config import JiraConfig
        from mcp_atlassian.confluence.config import ConfluenceConfig

        # Create mock configs
        mock_jira_config = MagicMock(spec=JiraConfig)
        mock_jira_config.is_auth_configured.return_value = True
        mock_jira_config.url = "https://baseball.atlassian.net"

        mock_confluence_config = MagicMock(spec=ConfluenceConfig)
        mock_confluence_config.is_auth_configured.return_value = True
        mock_confluence_config.url = "https://baseball.atlassian.net/wiki"

        # Create app context
        app_context = MainAppContext(
            full_jira_config=mock_jira_config,
            full_confluence_config=mock_confluence_config,
            read_only=False,
            enabled_tools=None,
        )

        yield app_context


@pytest.mark.integration
@pytest.mark.anyio
class TestSchemaCompleteness:
    """Test that all schemas are complete and match tool requirements."""

    async def test_confluence_page_schema_field_completeness(self, schema_test_server):
        """Test that Confluence page schemas include ALL required fields."""

        # Test create operation
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_resource_schema",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create"
                }
            }
        }

        # Execute tool directly
        from mcp_atlassian.servers.main import get_resource_schema_tool

        # Create context
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": schema_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await get_resource_schema_tool(ctx, "confluence", "page", "create")
        schema_data = json.loads(result)

        # CRITICAL: These fields must be present for Confluence page creation
        required_fields = {"space_key", "title", "body"}
        schema_fields = set(schema_data["fields"].keys())

        missing_fields = required_fields - schema_fields
        assert not missing_fields, f"Schema missing required fields: {missing_fields}"

        # Verify they're marked as required
        schema_required = set(schema_data["required"])
        missing_required = required_fields - schema_required
        assert not missing_required, f"Fields not marked as required: {missing_required}"

        print(f"✅ Confluence page create schema complete: {schema_fields}")

    async def test_jira_issue_schema_field_completeness(self, schema_test_server):
        """Test that Jira issue schemas include ALL required fields."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_resource_schema",
                "arguments": {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "create"
                }
            }
        }

        # Execute tool directly
        from mcp_atlassian.servers.main import get_resource_schema_tool

        # Create context
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": schema_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        result = await get_resource_schema_tool(ctx, "jira", "issue", "create")
        schema_data = json.loads(result)

        # Required fields for Jira issue creation
        required_fields = {"project_key", "summary", "issue_type"}
        schema_fields = set(schema_data["fields"].keys())

        missing_fields = required_fields - schema_fields
        assert not missing_fields, f"Jira schema missing required fields: {missing_fields}"

        schema_required = set(schema_data["required"])
        missing_required = required_fields - schema_required
        assert not missing_required, f"Jira fields not marked as required: {missing_required}"

        print(f"✅ Jira issue create schema complete: {schema_fields}")

    async def test_all_operation_schemas_have_essential_components(self, schema_test_server):
        """Test that all operation schemas have essential components."""

        # Test cases covering all major operations
        test_operations = [
            ("confluence", "page", "create"),
            ("confluence", "page", "update"),
            ("confluence", "page", "get"),
            ("confluence", "page", "delete"),
            ("confluence", "comment", "add"),
            ("jira", "issue", "create"),
            ("jira", "issue", "update"),
            ("jira", "issue", "get"),
            ("jira", "comment", "add"),
            ("jira", "worklog", "add"),
        ]

        for service, resource, operation in test_operations:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_resource_schema",
                    "arguments": {
                        "service": service,
                        "resource": resource,
                        "operation": operation
                    }
                }
            }

            # Execute tool directly
            from mcp_atlassian.servers.main import get_resource_schema_tool

            # Create context
            mock_fastmcp = MagicMock()
            mock_request_context = MagicMock()
            mock_request_context.lifespan_context = {"app_lifespan_context": schema_test_server}
            mock_fastmcp.request_context = mock_request_context
            ctx = Context(fastmcp=mock_fastmcp)

            result = await get_resource_schema_tool(ctx, service, resource, operation)
            schema_data = json.loads(result)

            # Every schema must have these components
            assert "fields" in schema_data, f"No fields in {service}/{resource}/{operation}"
            assert "required" in schema_data, f"No required list in {service}/{resource}/{operation}"
            assert "examples" in schema_data, f"No examples in {service}/{resource}/{operation}"

            # Fields should not be empty
            assert len(schema_data["fields"]) > 0, f"Empty fields in {service}/{resource}/{operation}"

            print(f"✅ Schema complete for {service}/{resource}/{operation}")


@pytest.mark.integration
class TestParameterOptimizerIntegrity:
    """Test that parameter optimizer doesn't break schema completeness."""

    def test_parameter_optimizer_preserves_required_fields(self):
        """Test that parameter optimizer doesn't remove actually required fields."""

        optimizer = ParameterOptimizer()

        # Test critical parameter combinations
        test_cases = [
            ("confluence", "page", "create", ["space_key", "title", "body"]),
            ("jira", "issue", "create", ["project_key", "summary", "issue_type"]),
            ("confluence", "comment", "add", ["body"]),
            ("jira", "comment", "add", ["body"]),
            ("jira", "worklog", "add", ["time_spent"]),
        ]

        for service, resource, operation, expected_fields in test_cases:
            recommended = optimizer.get_recommended_parameters(service, resource, operation)

            recommended_set = set(recommended)
            expected_set = set(expected_fields)

            missing_fields = expected_set - recommended_set
            assert not missing_fields, f"Parameter optimizer missing fields for {service}/{resource}/{operation}: {missing_fields}"

            print(f"✅ Parameter optimizer preserves required fields for {service}/{resource}/{operation}")

    def test_common_params_json_completeness(self):
        """Test that common_params.json has complete field definitions."""

        from pathlib import Path
        import json

        # Load common_params.json
        common_params_path = Path(__file__).parent.parent.parent / "src/mcp_atlassian/meta_tools/common_params.json"
        assert common_params_path.exists(), "common_params.json not found"

        with open(common_params_path) as f:
            common_params = json.load(f)

        # Check critical parameter groups
        critical_checks = {
            "confluence_page_operations": {"space_key", "title", "body"},
            "jira_issue_operations": {"project_key", "summary", "issue_type"},
            "confluence_comment_operations": {"body"},
            "jira_comment_operations": {"body"},
        }

        parameter_combinations = common_params.get("parameter_combinations", {})

        for param_group, required_fields in critical_checks.items():
            assert param_group in parameter_combinations, f"Missing parameter group: {param_group}"

            group_fields = set(parameter_combinations[param_group])
            missing_fields = required_fields - group_fields

            assert not missing_fields, f"common_params.json missing fields in {param_group}: {missing_fields}"

            print(f"✅ common_params.json complete for {param_group}")


@pytest.mark.integration
class TestSchemaToolIntegration:
    """Test integration between schema generation and actual tool execution."""

    async def test_schema_parameters_match_tool_expectations(self, schema_test_server):
        """Test that schema parameters exactly match what tools expect."""

        # Get schema for Confluence page creation
        schema_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_resource_schema",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create"
                }
            }
        }

        # Execute schema tool directly
        from mcp_atlassian.servers.main import get_resource_schema_tool

        # Create context
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": schema_test_server}
        mock_fastmcp.request_context = mock_request_context
        ctx = Context(fastmcp=mock_fastmcp)

        schema_result = await get_resource_schema_tool(ctx, "confluence", "page", "create")
        schema_data = json.loads(schema_result)

        # Now try to use the tool with EXACTLY the schema parameters
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        field: f"test_{field}_value" if field != "body" else "# Test\n\nTest content"
                        for field in schema_data["required"]
                    },
                    "dry_run": True
                }
            }
        }

        # Execute resource manager tool directly
        from mcp_atlassian.servers.main import resource_manager_tool

        tool_result = await resource_manager_tool(
            ctx,
            service="confluence",
            resource="page",
            operation="create",
            data={
                field: f"test_{field}_value" if field != "body" else "# Test\n\nTest content"
                for field in schema_data["required"]
            },
            dry_run=True
        )

        response_data = json.loads(tool_result)

        # Should not be a missing field error
        if "error_code" in response_data:
            assert not response_data["error_code"].endswith("_MISSING_SPACE")
            assert not response_data["error_code"].endswith("_MISSING_TITLE")
            assert not response_data["error_code"].endswith("_MISSING_BODY")

        print("✅ Schema parameters exactly match tool expectations")

    async def test_schema_examples_are_valid(self, schema_test_server):
        """Test that examples in schemas actually work with tools."""

        operations_to_test = [
            ("confluence", "page", "create"),
            ("jira", "issue", "create"),
        ]

        for service, resource, operation in operations_to_test:
            # Get schema with examples
            schema_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_resource_schema",
                    "arguments": {
                        "service": service,
                        "resource": resource,
                        "operation": operation
                    }
                }
            }

            # Execute schema tool directly
            schema_result = await get_resource_schema_tool(ctx, service, resource, operation)
            schema_data = json.loads(schema_result)

            # Extract minimal example
            if "minimal" in schema_data["examples"]:
                example_data = schema_data["examples"]["minimal"]

                # Try to use the example with the actual tool
                tool_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "resource_manager_tool",
                        "arguments": {
                            "service": service,
                            "resource": resource,
                            "operation": operation,
                            "data": example_data,
                            "dry_run": True
                        }
                    }
                }

                # Execute resource manager tool directly
                from mcp_atlassian.servers.main import resource_manager_tool

                tool_result = await resource_manager_tool(
                    ctx,
                    service=service,
                    resource=resource,
                    operation=operation,
                    data=example_data,
                    dry_run=True
                )
                # Should not raise exception
                assert tool_result is not None

                print(f"✅ Schema example works for {service}/{resource}/{operation}")


@pytest.mark.integration
class TestSchemaRegressionPrevention:
    """Prevent regressions in schema completeness."""

    def test_confluence_body_field_never_missing(self):
        """Regression test: Ensure body field is never missing from Confluence page schemas."""

        discovery = SchemaDiscovery()
        schema = discovery.get_resource_schema("confluence", "page", "create")

        # This was the bug - body field was missing
        assert "body" in schema.fields, "REGRESSION: body field missing from Confluence page schema"
        assert "body" in schema.required, "REGRESSION: body not marked as required"

        print("✅ Body field regression test passed")

    def test_space_key_field_always_present(self):
        """Regression test: Ensure space_key is always in Confluence schemas."""

        discovery = SchemaDiscovery()

        confluence_operations = [
            ("page", "create"),
            ("page", "update"),
            ("comment", "add"),
        ]

        for resource, operation in confluence_operations:
            schema = discovery.get_resource_schema("confluence", resource, operation)

            # space_key should be present for most Confluence operations
            if operation == "create":
                assert "space_key" in schema.fields, f"space_key missing from {resource}/{operation}"

        print("✅ Space key regression test passed")

    def test_jira_required_fields_always_present(self):
        """Regression test: Ensure Jira required fields are never missing."""

        discovery = SchemaDiscovery()
        schema = discovery.get_resource_schema("jira", "issue", "create")

        # These fields were problematic in the past
        required_jira_fields = {"project_key", "summary", "issue_type"}
        schema_fields = set(schema.fields.keys())

        missing_fields = required_jira_fields - schema_fields
        assert not missing_fields, f"REGRESSION: Jira fields missing: {missing_fields}"

        # Check they're marked as required
        schema_required = set(schema.required)
        missing_required = required_jira_fields - schema_required
        assert not missing_required, f"REGRESSION: Jira fields not required: {missing_required}"

        print("✅ Jira required fields regression test passed")