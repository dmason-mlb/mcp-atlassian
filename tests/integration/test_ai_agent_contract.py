#!/usr/bin/env python3
"""AI Agent Contract Validation Tests

This test suite defines and validates the exact "contract" that AI agents expect
from the MCP Atlassian server. It ensures backward compatibility and prevents
regressions that would break AI agent integrations.

These tests act as a specification for what AI agents can depend on.
"""

import json
import os
from typing import Any, Dict, List, Set
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.main import AtlassianMCP, main_lifespan
from mcp_atlassian.servers.context import MainAppContext
from tests.utils.mocks import MockEnvironment


@pytest.fixture
async def contract_test_server():
    """Create test server for contract validation."""
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
class TestAIAgentContract:
    """Test the contract that AI agents can depend on."""

    async def test_essential_tools_are_always_available(self, contract_test_server):
        """Contract: Essential tools must always be discoverable."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await contract_test_server.request(request)
        assert "result" in response

        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]

        # CONTRACT: These tools must always be available
        essential_tools = {
            "resource_manager_tool",
            "search_engine_tool",
            "get_resource_schema",
            "get_tool_examples"
        }

        missing_tools = essential_tools - set(tool_names)
        assert not missing_tools, f"CONTRACT VIOLATION: Missing essential tools: {missing_tools}"

        print(f"✅ Contract: All essential tools available ({len(essential_tools)} tools)")

    async def test_tool_descriptions_meet_minimum_requirements(self, contract_test_server):
        """Contract: Tool descriptions must provide sufficient information for AI agents."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await contract_test_server.request(request)
        tools = response["result"]["tools"]

        for tool in tools:
            if tool["name"] == "resource_manager_tool":
                description = tool["description"]

                # CONTRACT: Description must include key information
                required_info = {
                    "parameters": "Parameters:" in description,
                    "examples": "Examples:" in description or "Usage:" in description,
                    "services": "confluence" in description.lower() and "jira" in description.lower(),
                    "operations": "create" in description and "update" in description,
                    "sufficient_length": len(description) > 1000  # Must be detailed enough
                }

                failed_requirements = [req for req, met in required_info.items() if not met]
                assert not failed_requirements, f"CONTRACT VIOLATION: Tool description missing: {failed_requirements}"

        print("✅ Contract: Tool descriptions meet minimum requirements")

    async def test_schema_structure_contract(self, contract_test_server):
        """Contract: Schemas must have consistent structure."""

        # Test multiple schema requests
        schema_requests = [
            ("confluence", "page", "create"),
            ("confluence", "page", "update"),
            ("jira", "issue", "create"),
            ("jira", "issue", "update"),
        ]

        for service, resource, operation in schema_requests:
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

            response = await contract_test_server.request(request)
            assert "result" in response

            result_content = response["result"]["content"]
            if isinstance(result_content, list):
                schema_text = result_content[0]["text"]
            else:
                schema_text = result_content

            schema_data = json.loads(schema_text)

            # CONTRACT: Every schema must have these fields
            required_schema_fields = {
                "fields",
                "required",
                "examples",
                "cache_key",
                "cache_hint"
            }

            missing_fields = required_schema_fields - set(schema_data.keys())
            assert not missing_fields, f"CONTRACT VIOLATION: Schema missing fields for {service}/{resource}/{operation}: {missing_fields}"

            # CONTRACT: Fields and required must be consistent
            schema_fields = set(schema_data["fields"].keys())
            required_fields = set(schema_data["required"])

            orphaned_required = required_fields - schema_fields
            assert not orphaned_required, f"CONTRACT VIOLATION: Required fields not in fields: {orphaned_required}"

        print("✅ Contract: Schema structure is consistent")

    async def test_error_response_contract(self, contract_test_server):
        """Contract: Error responses must have consistent structure."""

        # Trigger an error by missing required fields
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {"title": "Test"}  # Missing space_key and body
                }
            }
        }

        response = await contract_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # CONTRACT: Error responses must have these fields
        required_error_fields = {
            "error",  # or error_code
            "message",  # or user_message
            "suggestions",
            "working_example"
        }

        # Check that we have either error or error_code, and either message or user_message
        has_error = "error" in error_data or "error_code" in error_data
        has_message = "message" in error_data or "user_message" in error_data

        assert has_error, "CONTRACT VIOLATION: Error response missing error/error_code"
        assert has_message, "CONTRACT VIOLATION: Error response missing message/user_message"
        assert "suggestions" in error_data, "CONTRACT VIOLATION: Error response missing suggestions"
        assert "working_example" in error_data, "CONTRACT VIOLATION: Error response missing working_example"

        # CONTRACT: Suggestions must be actionable (not empty)
        suggestions = error_data["suggestions"]
        assert isinstance(suggestions, list), "CONTRACT VIOLATION: Suggestions must be a list"
        assert len(suggestions) > 0, "CONTRACT VIOLATION: Suggestions cannot be empty"

        print("✅ Contract: Error responses have consistent structure")

    async def test_confluence_page_creation_contract(self, contract_test_server):
        """Contract: Confluence page creation must accept these exact parameters."""

        # CONTRACT: This exact call must work
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "space_key": "~911651470",
                        "title": "Contract Test Page",
                        "body": "# Test Content\n\nThis validates the contract."
                    },
                    "dry_run": True
                }
            }
        }

        response = await contract_test_server.request(request)
        assert "result" in response

        # Should not return a missing field error
        result_content = response["result"]["content"]
        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        response_data = json.loads(response_text)

        # Should not be missing field errors
        if "error_code" in response_data:
            forbidden_errors = {
                "CONFLUENCE_MISSING_SPACE",
                "CONFLUENCE_MISSING_TITLE",
                "CONFLUENCE_MISSING_BODY"
            }
            assert response_data["error_code"] not in forbidden_errors

        print("✅ Contract: Confluence page creation accepts standard parameters")

    async def test_field_name_compatibility_contract(self, contract_test_server):
        """Contract: Both space_key and space_id must be accepted."""

        test_cases = [
            {"space_key": "~911651470"},  # Standard
            {"space_id": "~911651470"},   # Legacy compatibility
        ]

        for space_field in test_cases:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "resource_manager_tool",
                    "arguments": {
                        "service": "confluence",
                        "resource": "page",
                        "operation": "create",
                        "data": {
                            **space_field,
                            "title": "Test Page",
                            "body": "Test content"
                        },
                        "dry_run": True
                    }
                }
            }

            response = await contract_test_server.request(request)
            result_content = response["result"]["content"]

            if isinstance(result_content, list):
                response_text = result_content[0]["text"]
            else:
                response_text = result_content

            response_data = json.loads(response_text)

            # Must not be a missing space error
            if "error_code" in response_data:
                assert response_data["error_code"] != "CONFLUENCE_MISSING_SPACE"

        print("✅ Contract: Both space_key and space_id are accepted")

    async def test_jira_issue_creation_contract(self, contract_test_server):
        """Contract: Jira issue creation must accept these exact parameters."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "jira",
                    "resource": "issue",
                    "operation": "create",
                    "data": {
                        "project_key": "FTEST",
                        "summary": "Contract Test Issue",
                        "issue_type": "Task",
                        "description": "This validates the Jira contract."
                    },
                    "dry_run": True
                }
            }
        }

        response = await contract_test_server.request(request)
        assert "result" in response

        # Should not return missing field errors for the provided fields
        result_content = response["result"]["content"]
        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        response_data = json.loads(response_text)

        # Should not be missing field errors for required Jira fields
        if "error_code" in response_data:
            forbidden_errors = {
                "JIRA_MISSING_PROJECT",
                "JIRA_MISSING_SUMMARY",
                "JIRA_MISSING_ISSUE_TYPE"
            }
            assert not any(forbidden in response_data["error_code"] for forbidden in forbidden_errors)

        print("✅ Contract: Jira issue creation accepts standard parameters")

    async def test_backward_compatibility_guarantee(self, contract_test_server):
        """Contract: Changes must not break existing AI agent integrations."""

        # This test represents calls that worked in previous versions
        legacy_working_calls = [
            {
                "name": "resource_manager_tool",
                "args": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "space_key": "~911651470",
                        "title": "Legacy Test",
                        "body": "Legacy body content"
                    },
                    "dry_run": True
                }
            },
            {
                "name": "get_resource_schema",
                "args": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create"
                }
            },
        ]

        for call in legacy_working_calls:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": call["name"],
                    "arguments": call["args"]
                }
            }

            response = await contract_test_server.request(request)

            # Must return a result (not error at MCP level)
            assert "result" in response, f"BACKWARD COMPATIBILITY BROKEN: {call['name']} failed"

            # Content must be parseable JSON
            result_content = response["result"]["content"]
            if isinstance(result_content, list):
                content_text = result_content[0]["text"]
            else:
                content_text = result_content

            # Must be valid JSON
            json.loads(content_text)

        print("✅ Contract: Backward compatibility maintained")


@pytest.mark.integration
@pytest.mark.anyio
class TestAIAgentUsabilityContract:
    """Test usability requirements that AI agents depend on."""

    async def test_schema_examples_are_copy_pasteable(self, contract_test_server):
        """Contract: Schema examples must be directly usable by AI agents."""

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

        response = await contract_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            schema_text = result_content[0]["text"]
        else:
            schema_text = result_content

        schema_data = json.loads(schema_text)

        # Get the minimal example
        examples = schema_data.get("examples", {})
        assert "minimal" in examples, "CONTRACT VIOLATION: Schema must include minimal example"

        minimal_example = examples["minimal"]

        # Example must be directly usable
        test_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": minimal_example,
                    "dry_run": True
                }
            }
        }

        test_response = await contract_test_server.request(test_request)
        assert "result" in test_response, "CONTRACT VIOLATION: Schema example must be directly usable"

        print("✅ Contract: Schema examples are copy-pasteable")

    async def test_error_guidance_prevents_common_mistakes(self, contract_test_server):
        """Contract: Error messages must prevent AI agents from making common mistakes."""

        # Common mistake: Wrong field names
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "resource_manager_tool",
                "arguments": {
                    "service": "confluence",
                    "resource": "page",
                    "operation": "create",
                    "data": {
                        "space": "~911651470",  # Wrong: should be space_key
                        "name": "Test Page",    # Wrong: should be title
                        "content": "Test"       # Wrong: should be body
                    }
                }
            }
        }

        response = await contract_test_server.request(request)
        result_content = response["result"]["content"]

        if isinstance(result_content, list):
            response_text = result_content[0]["text"]
        else:
            response_text = result_content

        error_data = json.loads(response_text)

        # Error message should guide toward correct field names
        full_text = str(error_data).lower()
        assert "space_key" in full_text, "CONTRACT VIOLATION: Error should mention correct field name 'space_key'"
        assert "title" in full_text, "CONTRACT VIOLATION: Error should mention correct field name 'title'"
        assert "body" in full_text, "CONTRACT VIOLATION: Error should mention correct field name 'body'"

        print("✅ Contract: Errors prevent common field name mistakes")

    async def test_tool_discovery_is_consistent(self, contract_test_server):
        """Contract: Tool discovery must return consistent results."""

        # Make multiple discovery requests
        responses = []
        for i in range(3):
            request = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/list",
                "params": {}
            }
            response = await contract_test_server.request(request)
            responses.append(response)

        # All responses should be identical
        first_tools = responses[0]["result"]["tools"]
        first_tool_names = sorted([tool["name"] for tool in first_tools])

        for response in responses[1:]:
            tools = response["result"]["tools"]
            tool_names = sorted([tool["name"] for tool in tools])
            assert tool_names == first_tool_names, "CONTRACT VIOLATION: Tool discovery must be consistent"

        print("✅ Contract: Tool discovery is consistent across calls")


@pytest.mark.integration
@pytest.mark.anyio
class TestContractRegressionPrevention:
    """Prevent regressions that would break the AI agent contract."""

    async def test_critical_field_presence_regression_prevention(self, contract_test_server):
        """Prevent regressions where critical fields disappear from schemas."""

        # These field presence requirements must never regress
        critical_field_requirements = [
            ("confluence", "page", "create", {"space_key", "title", "body"}),
            ("confluence", "page", "update", {"title", "body"}),
            ("jira", "issue", "create", {"project_key", "summary", "issue_type"}),
            ("jira", "issue", "update", {"summary"}),
            ("jira", "comment", "add", {"body"}),
        ]

        for service, resource, operation, required_fields in critical_field_requirements:
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

            response = await contract_test_server.request(request)
            result_content = response["result"]["content"]

            if isinstance(result_content, list):
                schema_text = result_content[0]["text"]
            else:
                schema_text = result_content

            schema_data = json.loads(schema_text)

            schema_fields = set(schema_data["fields"].keys())
            missing_critical = required_fields - schema_fields

            assert not missing_critical, f"REGRESSION: Critical fields missing from {service}/{resource}/{operation}: {missing_critical}"

        print("✅ Contract: No regression in critical field presence")

    async def test_essential_tool_availability_regression_prevention(self, contract_test_server):
        """Prevent regressions where essential tools become unavailable."""

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        response = await contract_test_server.request(request)
        tools = response["result"]["tools"]
        available_tools = {tool["name"] for tool in tools}

        # These tools must never disappear
        essential_tools = {
            "resource_manager_tool",
            "search_engine_tool",
            "get_resource_schema",
            "get_tool_examples"
        }

        missing_essential = essential_tools - available_tools
        assert not missing_essential, f"REGRESSION: Essential tools missing: {missing_essential}"

        print("✅ Contract: No regression in essential tool availability")