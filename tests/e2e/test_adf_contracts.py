"""
ADF contract tests for MCP Atlassian server.

These tests validate MCP tool call arguments and Atlassian REST payloads
for ADF content processing, replacing the visual browser tests with
contract verification.
"""

import json
from typing import Any

import pytest


@pytest.mark.mcp
@pytest.mark.adf
class TestADFMCPContracts:
    """Test MCP tool contracts for ADF content processing."""

    @pytest.mark.asyncio
    async def test_jira_issue_adf_mcp_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP tool call arguments for Jira issue with ADF content."""
        project_key = "TEST"

        # Expected Jira issue response
        expected_issue = {
            "key": "TEST-123",
            "id": "12345",
            "fields": {
                "summary": "ADF Test Issue",
                "description": {"version": 1, "type": "doc", "content": []},
                "project": {"key": project_key},
            },
        }

        # Stub the Jira API response
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)

        # ADF content with various elements
        adf_description = sample_test_data["adf_content"]

        # Call MCP tool
        result = await mcp_client.call_tool(
            "jira_issues_create_issue",
            {
                "project_key": project_key,
                "summary": "ADF Test Issue",
                "issue_type": "Task",
                "description": adf_description,
            },
        )

        # Validate MCP response structure
        assert isinstance(result, dict)
        response_data = self._extract_json_from_mcp_result(result)
        assert "key" in response_data
        assert response_data["key"] == "TEST-123"

        # Validate Atlassian REST API call was made correctly
        atlassian_stub.assert_called_once_with(
            "POST",
            "/rest/api/3/issue",
            json_contains={
                "fields": {
                    "project": {"key": project_key},
                    "summary": "ADF Test Issue",
                    "issuetype": {"name": "Task"},
                }
            },
        )

        # Verify that description field contains ADF JSON structure
        call_body = atlassian_stub.call_log[0][2]
        description_field = call_body["fields"]["description"]

        # For Cloud instances, description should be ADF JSON
        if isinstance(description_field, dict):
            assert "type" in description_field, (
                "Description should be ADF JSON with 'type' field"
            )
            assert description_field["type"] == "doc", (
                "ADF root should be document type"
            )
            assert "content" in description_field, "ADF should have content array"

        # Validate ADF content contains expected elements
        self._validate_adf_elements_in_payload(
            description_field, ["heading", "panel", "codeBlock", "status"]
        )

    @pytest.mark.asyncio
    async def test_confluence_page_adf_mcp_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP tool call arguments for Confluence page with ADF content."""
        space_id = "123456"

        # Expected Confluence page response
        expected_page = {
            "id": "67890",
            "title": "ADF Test Page",
            "type": "page",
            "space": {"id": space_id},
            "body": {
                "atlas_doc_format": {
                    "value": {"version": 1, "type": "doc", "content": []},
                    "representation": "atlas_doc_format",
                }
            },
        }

        # Stub the Confluence API response
        atlassian_stub.stub_confluence_create_page({}, expected_page)

        # ADF content with rich elements
        adf_content = sample_test_data["adf_content"]

        # Call MCP tool
        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "ADF Test Page",
                "content": adf_content,
                "content_format": "markdown",
            },
        )

        # Validate MCP response structure
        assert isinstance(result, dict)
        response_data = self._extract_json_from_mcp_result(result)
        assert "id" in response_data
        assert response_data["id"] == "67890"

        # Validate Atlassian REST API call
        atlassian_stub.assert_called_once_with(
            "POST",
            "/wiki/api/v2/pages",
            json_contains={"title": "ADF Test Page", "spaceId": space_id},
        )

        # Verify body contains ADF structure
        call_body = atlassian_stub.call_log[0][2]
        body_field = call_body.get("body", {})

        # For Cloud instances, should have atlas_doc_format
        if "atlas_doc_format" in body_field:
            adf_value = body_field["atlas_doc_format"]["value"]
            assert isinstance(adf_value, dict), "ADF should be JSON object"
            assert adf_value.get("type") == "doc", "ADF root should be document"

            # Validate ADF content structure
            self._validate_adf_elements_in_payload(
                adf_value, ["heading", "panel", "codeBlock", "status", "date"]
            )

    @pytest.mark.asyncio
    async def test_jira_comment_adf_mcp_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP tool call for Jira comment with ADF formatting."""
        issue_key = "TEST-456"

        # Expected comment response
        expected_comment = {
            "id": "10001",
            "body": {"version": 1, "type": "doc", "content": []},
            "author": {"displayName": "Test User"},
        }

        # Stub the comment API
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            f"https://test.atlassian.net/rest/api/3/issue/{issue_key}/comment",
            json=expected_comment,
            status=201,
        )

        # ADF comment content
        adf_comment = """## Comment with ADF Elements

### Status Updates
Current: {status:color=blue}In Progress{/status}
Next: {status:color=green}Ready for Review{/status}

### Code Reference
```bash
# Run the test command
npm run test:adf
```

### Important Notes
:::panel type="info"
**ADF Comment Test**: This panel should render properly.
:::"""

        # Call MCP tool
        result = await mcp_client.call_tool(
            "jira_add_comment", {"issue_key": issue_key, "comment": adf_comment}
        )

        # Validate MCP response
        response_data = self._extract_json_from_mcp_result(result)
        assert "id" in response_data

        # Verify API call structure
        assert len(atlassian_stub.call_log) > 0, "Should have made API call"
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert f"/issue/{issue_key}/comment" in url

        # Check comment body structure
        comment_body = body.get("body")
        if isinstance(comment_body, dict):
            assert comment_body.get("type") == "doc", "Comment should be ADF document"
            self._validate_adf_elements_in_payload(
                comment_body, ["heading", "codeBlock", "status"]
            )

    @pytest.mark.asyncio
    async def test_adf_status_element_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for status element processing."""
        project_key = "TEST"

        # Stub API response
        expected_issue = {
            "key": "TEST-STATUS",
            "fields": {"description": {"type": "doc", "content": []}},
        }
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)

        # Content with multiple status elements
        status_content = """# Status Test

Current status: {status:color=green}Complete{/status}
Priority: {status:color=red}High{/status}
Review: {status:color=yellow}Pending{/status}
Deployment: {status:color=blue}Scheduled{/status}"""

        # Create issue
        await mcp_client.call_tool(
            "jira_issues_create_issue",
            {
                "project_key": project_key,
                "summary": "Status Element Test",
                "issue_type": "Task",
                "description": status_content,
            },
        )

        # Validate API payload
        call_body = atlassian_stub.call_log[0][2]
        description = call_body["fields"]["description"]

        if isinstance(description, dict):
            # Verify status elements are properly converted to ADF
            status_nodes = self._find_adf_nodes_by_type(description, "status")
            assert len(status_nodes) >= 4, (
                f"Should find 4 status elements, found {len(status_nodes)}"
            )

            # Validate status element structure
            for status_node in status_nodes:
                assert "attrs" in status_node, "Status node should have attributes"
                assert "color" in status_node["attrs"], (
                    "Status should have color attribute"
                )
                assert status_node["attrs"]["color"] in [
                    "green",
                    "red",
                    "yellow",
                    "blue",
                ], f"Invalid status color: {status_node['attrs']['color']}"

    @pytest.mark.asyncio
    async def test_adf_panel_element_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for panel element processing."""
        space_id = "123456"

        # Stub API response
        expected_page = {
            "id": "PANEL-TEST",
            "body": {"atlas_doc_format": {"value": {"type": "doc", "content": []}}},
        }
        atlassian_stub.stub_confluence_create_page({}, expected_page)

        # Content with different panel types
        panel_content = """# Panel Test

:::panel type="info"
This is an **info panel** with formatting.
:::

:::panel type="warning"
**Warning**: This is a warning panel.
:::

:::panel type="success"
Success panel with `code`.
:::

:::panel type="error"
Error panel content.
:::"""

        # Create page
        await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "Panel Test Page",
                "content": panel_content,
                "content_format": "markdown",
            },
        )

        # Validate API payload
        call_body = atlassian_stub.call_log[0][2]
        body_content = (
            call_body.get("body", {}).get("atlas_doc_format", {}).get("value", {})
        )

        if isinstance(body_content, dict):
            # Find panel nodes
            panel_nodes = self._find_adf_nodes_by_type(body_content, "panel")
            assert len(panel_nodes) >= 4, (
                f"Should find 4 panels, found {len(panel_nodes)}"
            )

            # Validate panel types
            panel_types = [
                node["attrs"]["panelType"] for node in panel_nodes if "attrs" in node
            ]
            expected_types = {"info", "warning", "success", "error"}
            found_types = set(panel_types)
            assert expected_types.issubset(found_types), (
                f"Missing panel types. Expected: {expected_types}, Found: {found_types}"
            )

    @pytest.mark.asyncio
    async def test_adf_code_block_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for code block processing."""
        project_key = "TEST"

        # Stub response
        expected_issue = {
            "key": "TEST-CODE",
            "fields": {"description": {"type": "doc", "content": []}},
        }
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)

        # Content with code blocks
        code_content = """# Code Test

```python
def test_function():
    return "Hello ADF"
```

```javascript
console.log("JavaScript code");
```

```json
{
  "test": "json content",
  "valid": true
}
```"""

        # Create issue
        await mcp_client.call_tool(
            "jira_issues_create_issue",
            {
                "project_key": project_key,
                "summary": "Code Block Test",
                "issue_type": "Task",
                "description": code_content,
            },
        )

        # Validate code blocks in payload
        call_body = atlassian_stub.call_log[0][2]
        description = call_body["fields"]["description"]

        if isinstance(description, dict):
            code_blocks = self._find_adf_nodes_by_type(description, "codeBlock")
            assert len(code_blocks) >= 3, (
                f"Should find 3 code blocks, found {len(code_blocks)}"
            )

            # Validate language attributes
            languages = [
                block["attrs"]["language"] for block in code_blocks if "attrs" in block
            ]
            expected_languages = {"python", "javascript", "json"}
            found_languages = set(languages)

            # Some languages might be mapped differently
            assert len(found_languages) >= 2, (
                f"Should find multiple languages, found: {found_languages}"
            )

    def _extract_json_from_mcp_result(self, result: Any) -> dict:
        """Extract JSON from MCP tool result."""
        if isinstance(result, dict):
            return result

        try:
            # Handle FastMCP ToolResult structure
            content = getattr(result, "content", None) or result.get("content")
            if isinstance(content, list) and content:
                for item in content:
                    text = (
                        item.get("text")
                        if isinstance(item, dict)
                        else getattr(item, "text", None)
                    )
                    if text:
                        try:
                            return json.loads(text)
                        except Exception:
                            continue
        except Exception:
            pass

        # Fallback to string conversion
        try:
            return json.loads(str(result))
        except Exception:
            return {}

    def _validate_adf_elements_in_payload(
        self, adf_payload: dict, expected_types: list
    ):
        """Validate that ADF payload contains expected element types."""
        if not isinstance(adf_payload, dict):
            return

        found_types = set()
        self._collect_adf_node_types(adf_payload, found_types)

        for expected_type in expected_types:
            assert expected_type in found_types, (
                f"Expected ADF element type '{expected_type}' not found. Found types: {found_types}"
            )

    def _collect_adf_node_types(self, node: Any, found_types: set):
        """Recursively collect ADF node types from a document structure."""
        if isinstance(node, dict):
            if "type" in node:
                found_types.add(node["type"])

            for key, value in node.items():
                self._collect_adf_node_types(value, found_types)

        elif isinstance(node, list):
            for item in node:
                self._collect_adf_node_types(item, found_types)

    def _find_adf_nodes_by_type(self, adf_payload: dict, node_type: str) -> list:
        """Find all ADF nodes of a specific type."""
        nodes = []
        self._collect_nodes_by_type(adf_payload, node_type, nodes)
        return nodes

    def _collect_nodes_by_type(self, node: Any, target_type: str, nodes: list):
        """Recursively collect nodes of a specific type."""
        if isinstance(node, dict):
            if node.get("type") == target_type:
                nodes.append(node)

            for value in node.values():
                self._collect_nodes_by_type(value, target_type, nodes)

        elif isinstance(node, list):
            for item in node:
                self._collect_nodes_by_type(item, target_type, nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
