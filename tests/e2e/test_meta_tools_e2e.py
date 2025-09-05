"""End-to-end tests for meta-tools functionality."""

import asyncio
import json
import time
from typing import Any, Dict, List

import pytest


@pytest.mark.e2e
@pytest.mark.meta_tools
class TestMetaToolsEndToEnd:
    """End-to-end test suite for meta-tools with real MCP client interactions."""

    @pytest.mark.asyncio
    async def test_resource_manager_jira_issue_lifecycle(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test complete Jira issue lifecycle using ResourceManager meta-tool."""
        project_key = "E2E"
        
        # Expected responses for different lifecycle stages
        created_issue = {
            "key": f"{project_key}-456",
            "id": "67890",
            "fields": {
                "summary": "E2E Test Issue",
                "description": {"version": 1, "type": "doc", "content": []},
                "project": {"key": project_key},
                "issuetype": {"name": "Task"},
                "status": {"name": "To Do"},
            },
        }
        
        updated_issue = {**created_issue}
        updated_issue["fields"]["summary"] = "Updated E2E Test Issue"
        updated_issue["fields"]["status"] = {"name": "In Progress"}
        
        # Stub API responses
        atlassian_stub.stub_jira_create_issue(project_key, created_issue)
        atlassian_stub.stub_jira_get_issue(f"{project_key}-456", created_issue)
        atlassian_stub.stub_jira_update_issue(f"{project_key}-456", updated_issue)
        atlassian_stub.stub_jira_delete_issue(f"{project_key}-456", True)
        
        # Test CREATE operation
        create_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "create",
                "data": {
                    "project": project_key,
                    "summary": "E2E Test Issue",
                    "issuetype": "Task",
                    "description": "This is an end-to-end test issue"
                }
            }
        )
        
        assert create_result["key"] == f"{project_key}-456"
        assert create_result["fields"]["summary"] == "E2E Test Issue"
        
        # Test GET operation
        get_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "get",
                "identifier": f"{project_key}-456"
            }
        )
        
        assert get_result["key"] == f"{project_key}-456"
        assert get_result["fields"]["project"]["key"] == project_key
        
        # Test UPDATE operation
        update_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "update",
                "identifier": f"{project_key}-456",
                "data": {
                    "summary": "Updated E2E Test Issue",
                    "status": "In Progress"
                }
            }
        )
        
        assert update_result["fields"]["summary"] == "Updated E2E Test Issue"
        
        # Test DELETE operation
        delete_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "delete",
                "identifier": f"{project_key}-456"
            }
        )
        
        assert delete_result is True

    @pytest.mark.asyncio
    async def test_resource_manager_confluence_page_lifecycle(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test complete Confluence page lifecycle using ResourceManager meta-tool."""
        space_key = "E2E"
        
        # Expected responses
        created_page = {
            "id": "789012",
            "title": "E2E Test Page",
            "space": {"key": space_key, "name": "End-to-End Test Space"},
            "body": {"storage": {"value": "<p>This is an E2E test page</p>"}},
            "version": {"number": 1},
        }
        
        updated_page = {**created_page}
        updated_page["title"] = "Updated E2E Test Page"
        updated_page["body"]["storage"]["value"] = "<p>Updated content</p>"
        updated_page["version"]["number"] = 2
        
        # Stub API responses
        atlassian_stub.stub_confluence_create_page(space_key, created_page)
        atlassian_stub.stub_confluence_get_page("789012", created_page)
        atlassian_stub.stub_confluence_update_page("789012", updated_page)
        atlassian_stub.stub_confluence_delete_page("789012", True)
        
        # Test CREATE operation
        create_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "confluence",
                "resource_type": "page",
                "operation": "create",
                "data": {
                    "space": space_key,
                    "title": "E2E Test Page",
                    "content": "This is an E2E test page"
                }
            }
        )
        
        assert create_result["id"] == "789012"
        assert create_result["title"] == "E2E Test Page"
        assert create_result["space"]["key"] == space_key
        
        # Test GET operation
        get_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "confluence",
                "resource_type": "page",
                "operation": "get",
                "identifier": "789012"
            }
        )
        
        assert get_result["id"] == "789012"
        assert get_result["title"] == "E2E Test Page"
        
        # Test UPDATE operation
        update_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "confluence",
                "resource_type": "page",
                "operation": "update",
                "identifier": "789012",
                "data": {
                    "title": "Updated E2E Test Page",
                    "content": "Updated content"
                }
            }
        )
        
        assert update_result["title"] == "Updated E2E Test Page"
        
        # Test DELETE operation
        delete_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "confluence",
                "resource_type": "page",
                "operation": "delete",
                "identifier": "789012"
            }
        )
        
        assert delete_result is True

    @pytest.mark.asyncio
    async def test_schema_discovery_field_exploration(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test schema discovery for exploring available fields."""
        project_key = "SCHEMA"
        
        # Mock Jira create metadata
        create_meta = {
            "projects": [{
                "key": project_key,
                "name": "Schema Test Project",
                "issuetypes": [{
                    "name": "Bug",
                    "fields": {
                        "summary": {
                            "required": True,
                            "name": "Summary",
                            "hasDefaultValue": False
                        },
                        "description": {
                            "required": False,
                            "name": "Description",
                            "hasDefaultValue": False
                        },
                        "priority": {
                            "required": False,
                            "name": "Priority",
                            "hasDefaultValue": True,
                            "allowedValues": [
                                {"name": "High"},
                                {"name": "Medium"},
                                {"name": "Low"}
                            ]
                        },
                        "assignee": {
                            "required": False,
                            "name": "Assignee",
                            "hasDefaultValue": False
                        }
                    }
                }]
            }]
        }
        
        atlassian_stub.stub_jira_create_meta(project_key, create_meta)
        
        # Test field discovery
        discovery_result = await mcp_client.call_tool(
            "schema_discovery",
            {
                "service": "jira",
                "resource_type": "issue",
                "context": {
                    "project": project_key,
                    "issuetype": "Bug"
                }
            }
        )
        
        assert "fields" in discovery_result
        fields = discovery_result["fields"]
        
        # Verify required fields
        assert "summary" in fields
        assert fields["summary"]["required"] is True
        
        # Verify optional fields
        assert "description" in fields
        assert fields["description"]["required"] is False
        
        # Verify field with allowed values
        assert "priority" in fields
        assert "allowedValues" in fields["priority"]
        assert len(fields["priority"]["allowedValues"]) == 3

    @pytest.mark.asyncio
    async def test_migration_helper_legacy_translation(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test migration helper for translating legacy tool calls."""
        # Test translation of a legacy Jira tool call
        translation_result = await mcp_client.call_tool(
            "migration_helper",
            {
                "operation": "translate",
                "legacy_call": {
                    "tool": "jira_get_issue",
                    "arguments": {
                        "issue_key": "MIG-789"
                    }
                }
            }
        )
        
        assert "meta_tool_call" in translation_result
        meta_call = translation_result["meta_tool_call"]
        
        assert meta_call["tool"] == "resource_manager"
        assert meta_call["arguments"]["service"] == "jira"
        assert meta_call["arguments"]["resource_type"] == "issue"
        assert meta_call["arguments"]["operation"] == "get"
        assert meta_call["arguments"]["identifier"] == "MIG-789"
        
        # Test guidance generation
        guidance_result = await mcp_client.call_tool(
            "migration_helper",
            {
                "operation": "guidance",
                "legacy_tool": "confluence_create_page"
            }
        )
        
        assert "meta_tool" in guidance_result
        assert "parameters_mapping" in guidance_result
        assert guidance_result["meta_tool"] == "resource_manager"

    @pytest.mark.asyncio
    async def test_parameter_optimizer_consolidation(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test parameter optimizer for consolidating common parameters."""
        # Test parameter optimization for search operations
        optimization_result = await mcp_client.call_tool(
            "parameter_optimizer",
            {
                "operation": "optimize",
                "tool_name": "jira_search_issues",
                "parameters": {
                    "jql": "project = OPT AND status = Open",
                    "fields": ["summary", "status", "assignee"],
                    "expand": ["changelog"],
                    "max_results": 100,
                    "start_at": 0
                }
            }
        )
        
        assert "optimized_parameters" in optimization_result
        optimized = optimization_result["optimized_parameters"]
        
        # Should maintain essential parameters
        assert "jql" in optimized
        assert optimized["jql"] == "project = OPT AND status = Open"
        
        # Test batch parameter consolidation
        batch_result = await mcp_client.call_tool(
            "parameter_optimizer",
            {
                "operation": "merge",
                "parameter_sets": [
                    {"project": "BATCH1", "fields": ["summary"]},
                    {"project": "BATCH2", "fields": ["status"]},
                    {"project": "BATCH3", "fields": ["assignee"]}
                ]
            }
        )
        
        assert "merged_parameters" in batch_result
        merged = batch_result["merged_parameters"]
        
        # Should consolidate projects and fields
        assert "projects" in merged or "jql" in merged

    @pytest.mark.asyncio
    async def test_dry_run_validation(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test dry-run mode for validation without execution."""
        # Test dry-run for issue creation
        dry_run_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "create",
                "data": {
                    "project": "DRYRUN",
                    "summary": "Dry Run Test",
                    "issuetype": "Task"
                },
                "options": {
                    "dry_run": True
                }
            }
        )
        
        assert dry_run_result["status"] == "dry_run_success"
        assert "validation" in dry_run_result
        assert dry_run_result["validation"]["valid"] is True
        
        # Test dry-run with validation errors
        invalid_dry_run_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "create",
                "data": {
                    "project": "DRYRUN"
                    # Missing required fields: summary, issuetype
                },
                "options": {
                    "dry_run": True
                }
            }
        )
        
        assert invalid_dry_run_result["status"] == "dry_run_validation_failed"
        assert "validation" in invalid_dry_run_result
        assert invalid_dry_run_result["validation"]["valid"] is False
        assert "missing_required" in invalid_dry_run_result["validation"]

    @pytest.mark.asyncio
    async def test_cross_service_workflow(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test workflow spanning both Jira and Confluence."""
        project_key = "CROSS"
        space_key = "CROSS"
        
        # Create Jira issue
        issue_data = {
            "key": f"{project_key}-001",
            "id": "cross001",
            "fields": {
                "summary": "Cross-Service Test Issue",
                "project": {"key": project_key},
                "issuetype": {"name": "Task"}
            }
        }
        
        atlassian_stub.stub_jira_create_issue(project_key, issue_data)
        
        issue_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "create",
                "data": {
                    "project": project_key,
                    "summary": "Cross-Service Test Issue",
                    "issuetype": "Task"
                }
            }
        )
        
        # Create related Confluence page
        page_data = {
            "id": "cross001",
            "title": f"Documentation for {issue_result['key']}",
            "space": {"key": space_key},
            "body": {"storage": {"value": f"<p>Documentation for issue {issue_result['key']}</p>"}}
        }
        
        atlassian_stub.stub_confluence_create_page(space_key, page_data)
        
        page_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "confluence",
                "resource_type": "page",
                "operation": "create",
                "data": {
                    "space": space_key,
                    "title": f"Documentation for {issue_result['key']}",
                    "content": f"Documentation for issue {issue_result['key']}"
                }
            }
        )
        
        # Verify both resources were created
        assert issue_result["key"] == f"{project_key}-001"
        assert page_result["title"] == f"Documentation for {project_key}-001"

    @pytest.mark.asyncio
    async def test_performance_comparison_v1_vs_v2(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test performance comparison between v1 and v2 tools."""
        # This test would compare performance characteristics
        # For now, we'll test that v2 tools work correctly
        
        start_time = time.time()
        
        # Perform multiple operations with v2 meta-tools
        operations = []
        for i in range(5):
            issue_key = f"PERF-{i:03d}"
            issue_data = {
                "key": issue_key,
                "id": f"perf{i:03d}",
                "fields": {
                    "summary": f"Performance Test Issue {i}",
                    "project": {"key": "PERF"},
                    "issuetype": {"name": "Task"}
                }
            }
            
            atlassian_stub.stub_jira_get_issue(issue_key, issue_data)
            
            operation = mcp_client.call_tool(
                "resource_manager",
                {
                    "service": "jira",
                    "resource_type": "issue",
                    "operation": "get",
                    "identifier": issue_key
                }
            )
            operations.append(operation)
        
        # Execute all operations concurrently
        results = await asyncio.gather(*operations)
        
        execution_time = time.time() - start_time
        
        # Verify all operations succeeded
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["key"] == f"PERF-{i:03d}"
        
        # Performance should be reasonable (< 5 seconds for 5 operations)
        assert execution_time < 5.0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test error handling and recovery scenarios."""
        # Test handling of API errors
        atlassian_stub.stub_error_response(
            "jira",
            "GET",
            "/rest/api/2/issue/ERROR-001",
            status_code=404,
            error_data={"error": "Issue not found"}
        )
        
        # Should handle the error gracefully
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool(
                "resource_manager",
                {
                    "service": "jira",
                    "resource_type": "issue",
                    "operation": "get",
                    "identifier": "ERROR-001"
                }
            )
        
        # Verify appropriate error information is provided
        error_message = str(exc_info.value)
        assert "404" in error_message or "not found" in error_message.lower()

    @pytest.mark.asyncio
    async def test_authentication_context_handling(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test authentication context handling in E2E scenarios."""
        # This test would verify that meta-tools properly handle
        # different authentication contexts in real scenarios
        
        # Test with OAuth context (simulated)
        oauth_result = await mcp_client.call_tool(
            "resource_manager",
            {
                "service": "jira",
                "resource_type": "issue",
                "operation": "get",
                "identifier": "AUTH-001",
                "options": {
                    "auth_context": "oauth"
                }
            }
        )
        
        # Should execute without authentication errors
        # (Actual implementation would depend on how auth context is passed)
        assert oauth_result is not None

    @pytest.mark.asyncio
    async def test_large_scale_operations(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test meta-tools with large-scale operations."""
        # Test batch operations with many items
        project_key = "BATCH"
        
        # Create many issues for batch testing
        issues = []
        for i in range(20):
            issue_key = f"{project_key}-{i:03d}"
            issue_data = {
                "key": issue_key,
                "id": f"batch{i:03d}",
                "fields": {
                    "summary": f"Batch Test Issue {i}",
                    "project": {"key": project_key},
                    "issuetype": {"name": "Task"}
                }
            }
            issues.append(issue_data)
            atlassian_stub.stub_jira_get_issue(issue_key, issue_data)
        
        # Test batch retrieval (simulated through multiple calls)
        batch_operations = []
        for issue in issues:
            operation = mcp_client.call_tool(
                "resource_manager",
                {
                    "service": "jira",
                    "resource_type": "issue",
                    "operation": "get",
                    "identifier": issue["key"]
                }
            )
            batch_operations.append(operation)
        
        # Execute batch operations
        batch_results = await asyncio.gather(*batch_operations)
        
        # Verify all operations succeeded
        assert len(batch_results) == 20
        for i, result in enumerate(batch_results):
            assert result["key"] == f"{project_key}-{i:03d}"

    @pytest.mark.asyncio
    async def test_migration_workflow_end_to_end(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test complete migration workflow from v1 to v2."""
        # Step 1: Get migration guidance
        guidance = await mcp_client.call_tool(
            "migration_helper",
            {
                "operation": "guidance",
                "legacy_tool": "jira_update_issue"
            }
        )
        
        assert guidance["meta_tool"] == "resource_manager"
        
        # Step 2: Translate legacy call
        legacy_call = {
            "tool": "jira_update_issue",
            "arguments": {
                "issue_key": "MIG-123",
                "summary": "Updated via migration",
                "description": "Updated description"
            }
        }
        
        translation = await mcp_client.call_tool(
            "migration_helper",
            {
                "operation": "translate",
                "legacy_call": legacy_call
            }
        )
        
        # Step 3: Execute the translated call
        updated_issue = {
            "key": "MIG-123",
            "id": "mig123",
            "fields": {
                "summary": "Updated via migration",
                "description": {"version": 1, "type": "doc", "content": []},
                "project": {"key": "MIG"},
                "issuetype": {"name": "Task"}
            }
        }
        
        atlassian_stub.stub_jira_update_issue("MIG-123", updated_issue)
        
        meta_call = translation["meta_tool_call"]
        result = await mcp_client.call_tool(
            meta_call["tool"],
            meta_call["arguments"]
        )
        
        assert result["key"] == "MIG-123"
        assert result["fields"]["summary"] == "Updated via migration"