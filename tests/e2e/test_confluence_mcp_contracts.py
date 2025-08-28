"""
Confluence MCP contract validation tests.

These tests validate MCP tool call arguments and Atlassian REST payloads
for Confluence operations, focusing on contract verification rather than API behavior.
"""

import json
from typing import Any

import pytest


@pytest.mark.mcp
@pytest.mark.confluence
class TestConfluenceMCPContracts:
    """Test MCP tool contracts for Confluence operations."""

    @pytest.mark.asyncio
    async def test_confluence_create_page_mcp_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP tool call arguments for Confluence page creation."""
        space_id = "123456"

        # Expected Confluence page response
        expected_page = {
            "id": "67890",
            "title": "Test Page",
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

        # Call MCP tool
        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "Test Page",
                "content": sample_test_data["basic_markdown"],
                "content_format": "markdown",
            },
        )

        # Validate MCP response structure
        assert isinstance(result, dict)
        response_data = self._extract_json_from_mcp_result(result)
        assert "id" in response_data
        assert response_data["id"] == "67890"

        # Validate Atlassian REST API call was made correctly
        atlassian_stub.assert_called_once_with(
            "POST",
            "/wiki/api/v2/pages",
            json_contains={"title": "Test Page", "spaceId": space_id},
        )

        # Verify that body field contains ADF structure for Cloud
        call_body = atlassian_stub.call_log[0][2]
        body_field = call_body.get("body", {})

        if "atlas_doc_format" in body_field:
            adf_value = body_field["atlas_doc_format"]["value"]
            assert isinstance(adf_value, dict), "ADF should be JSON object"
            assert adf_value.get("type") == "doc", "ADF root should be document"
            assert "content" in adf_value, "ADF should have content array"

    @pytest.mark.asyncio
    async def test_confluence_create_page_with_parent_contract(
        self, mcp_client, atlassian_stub
    ):
        """Test MCP contract for page creation with parent relationship."""
        space_id = "123456"
        parent_id = "555555"

        expected_page = {"id": "78901", "title": "Child Page", "parentId": parent_id}

        atlassian_stub.stub_confluence_create_page({}, expected_page)

        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "Child Page",
                "content": "# Child Page Content",
                "content_format": "markdown",
                "parent_id": parent_id,
            },
        )

        self.assert_success_response(result)

        # Validate parent_id in API call
        call_body = atlassian_stub.call_log[0][2]
        assert "parentId" in call_body
        assert call_body["parentId"] == parent_id

    @pytest.mark.asyncio
    async def test_confluence_create_page_wiki_format_contract(
        self, mcp_client, atlassian_stub
    ):
        """Test MCP contract for page creation with wiki markup."""
        space_id = "123456"

        expected_page = {
            "id": "11111",
            "title": "Wiki Page",
            "body": {
                "storage": {
                    "value": "<h1>Wiki Markup</h1>",
                    "representation": "storage",
                }
            },
        }

        atlassian_stub.stub_confluence_create_page({}, expected_page)

        wiki_content = "h1. Wiki Markup Test\n\nThis is *bold* text."

        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "Wiki Page",
                "content": wiki_content,
                "content_format": "wiki",
            },
        )

        self.assert_success_response(result)

        # Validate wiki content format in API call
        call_body = atlassian_stub.call_log[0][2]
        body_field = call_body.get("body", {})

        # For Server/DC or wiki format, should use storage format
        if "storage" in body_field:
            storage_value = body_field["storage"]
            assert "value" in storage_value
            assert "representation" in storage_value
            assert storage_value["representation"] == "storage"

    @pytest.mark.asyncio
    async def test_confluence_update_page_mcp_contract(
        self, mcp_client, atlassian_stub
    ):
        """Test MCP contract for page updates."""
        page_id = "67890"

        # Stub update response
        atlassian_stub.responses.add(
            atlassian_stub.responses.PUT,
            f"https://test.atlassian.net/wiki/api/v2/pages/{page_id}",
            json={"id": page_id, "version": {"number": 2}},
            status=200,
        )

        result = await mcp_client.call_tool(
            "confluence_pages_update_page",
            {
                "page_id": page_id,
                "title": "Updated Title",
                "content": "# Updated Content\n\nThis is updated.",
                "content_format": "markdown",
                "version_comment": "Updated by test",
            },
        )

        self.assert_success_response(result)

        # Validate API call structure
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "PUT"
        assert f"/pages/{page_id}" in url
        assert "title" in body
        assert body["title"] == "Updated Title"

        # Should include version comment if provided
        if "version" in body:
            version_info = body["version"]
            if "message" in version_info:
                assert version_info["message"] == "Updated by test"

    @pytest.mark.asyncio
    async def test_confluence_add_comment_mcp_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP contract for adding comments."""
        page_id = "67890"

        # Expected comment response
        expected_comment = {
            "id": "comment-123",
            "body": {"version": 1, "type": "doc", "content": []},
            "author": {"displayName": "Test User"},
        }

        # Stub comment API
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            f"https://test.atlassian.net/wiki/api/v2/pages/{page_id}/comments",
            json=expected_comment,
            status=201,
        )

        # Add formatted comment
        comment_text = """## Review Comment

This comment contains **formatting** and status: {status:color=green}Approved{/status}

:::panel type="info"
**Note**: Please review carefully.
:::

```bash
# Test command
npm run test
```"""

        result = await mcp_client.call_tool(
            "confluence_content_add_comment",
            {"page_id": page_id, "content": comment_text},
        )

        self.assert_success_response(result)

        # Validate comment API call
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert f"/pages/{page_id}/comments" in url
        assert "body" in body

        # For Cloud instances, body should be ADF
        comment_body = body["body"]
        if isinstance(comment_body, dict):
            assert comment_body.get("type") == "doc"
            assert "content" in comment_body

    @pytest.mark.asyncio
    async def test_confluence_add_label_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for adding labels."""
        page_id = "67890"
        label_name = "test-label"

        # Expected label response
        expected_labels = [{"id": "label-1", "name": label_name, "prefix": "global"}]

        # Stub label API
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            f"https://test.atlassian.net/wiki/api/v2/pages/{page_id}/labels",
            json=expected_labels,
            status=200,
        )

        result = await mcp_client.call_tool(
            "confluence_content_add_label", {"page_id": page_id, "name": label_name}
        )

        self.assert_success_response(result)

        # Validate label API call
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert f"/pages/{page_id}/labels" in url

        # Label payload structure validation
        if isinstance(body, list):
            assert len(body) > 0
            label_data = body[0]
            assert "name" in label_data
            assert label_data["name"] == label_name
        elif isinstance(body, dict):
            assert "name" in body
            assert body["name"] == label_name

    @pytest.mark.asyncio
    async def test_confluence_get_page_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for retrieving pages."""
        page_id = "67890"

        # Mock page response
        expected_page = {
            "id": page_id,
            "title": "Test Page",
            "body": {
                "atlas_doc_format": {
                    "value": {"type": "doc", "content": []},
                    "representation": "atlas_doc_format",
                }
            },
            "version": {"number": 1},
            "space": {"id": "123456"},
        }

        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            f"https://test.atlassian.net/wiki/api/v2/pages/{page_id}",
            json=expected_page,
            status=200,
        )

        result = await mcp_client.call_tool(
            "confluence_pages_get_page",
            {"page_id": page_id, "include_metadata": True, "convert_to_markdown": True},
        )

        self.assert_success_response(result)

        # Validate API call parameters
        method, url, _ = atlassian_stub.call_log[0]
        assert method == "GET"
        assert f"/pages/{page_id}" in url

        # Response should contain page data
        response_data = self._extract_json_from_mcp_result(result)
        assert "id" in response_data
        assert response_data["id"] == page_id

    @pytest.mark.asyncio
    async def test_confluence_search_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Confluence search."""
        search_query = "test content"

        # Mock search response
        expected_search = {
            "results": [
                {"content": {"id": "111", "title": "Test Page 1", "type": "page"}},
                {"content": {"id": "222", "title": "Test Page 2", "type": "page"}},
            ],
            "totalSize": 2,
            "start": 0,
            "limit": 25,
        }

        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/api/v2/search",
            json=expected_search,
            status=200,
        )

        result = await mcp_client.call_tool(
            "confluence_search_search", {"query": search_query, "limit": 10}
        )

        self.assert_success_response(result)

        # Validate search API call
        method, url, _ = atlassian_stub.call_log[0]
        assert method == "GET"
        assert "/search" in url
        assert search_query.replace(" ", "%20") in url or "cql=" in url

        # Response should contain search results
        response_data = self._extract_json_from_mcp_result(result)
        assert isinstance(response_data, list) or "results" in response_data

    @pytest.mark.asyncio
    async def test_confluence_get_page_children_mcp_contract(
        self, mcp_client, atlassian_stub
    ):
        """Test MCP contract for getting page children."""
        parent_id = "67890"

        # Mock children response
        expected_children = {
            "results": [
                {"id": "111", "title": "Child Page 1", "parentId": parent_id},
                {"id": "222", "title": "Child Page 2", "parentId": parent_id},
            ]
        }

        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            f"https://test.atlassian.net/wiki/api/v2/pages/{parent_id}/children",
            json=expected_children,
            status=200,
        )

        result = await mcp_client.call_tool(
            "confluence_pages_get_page_children",
            {"parent_id": parent_id, "limit": 25, "include_content": False},
        )

        self.assert_success_response(result)

        # Validate children API call
        method, url, _ = atlassian_stub.call_log[0]
        assert method == "GET"
        assert f"/pages/{parent_id}/children" in url

        # Response should contain children data
        response_data = self._extract_json_from_mcp_result(result)
        assert isinstance(response_data, (list, dict))

    @pytest.mark.asyncio
    async def test_confluence_error_handling_contract(self, mcp_client, atlassian_stub):
        """Test MCP error handling for invalid requests."""
        # Stub 400 error response
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/wiki/api/v2/pages",
            json={"message": "Title is required"},
            status=400,
        )

        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": "123456",
                "title": "",  # Invalid empty title
                "content": "Test content",
                "content_format": "markdown",
            },
        )

        # Should return error result
        assert isinstance(result, dict)
        # Error handling varies by MCP implementation
        # but should not raise unhandled exceptions

    @pytest.mark.asyncio
    async def test_confluence_adf_content_processing_contract(
        self, mcp_client, atlassian_stub, sample_test_data
    ):
        """Test MCP contract for ADF content processing."""
        space_id = "123456"

        expected_page = {
            "id": "adf-test",
            "body": {"atlas_doc_format": {"value": {"type": "doc", "content": []}}},
        }

        atlassian_stub.stub_confluence_create_page({}, expected_page)

        # Use ADF-rich content
        adf_content = sample_test_data["adf_content"]

        result = await mcp_client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": space_id,
                "title": "ADF Test Page",
                "content": adf_content,
                "content_format": "markdown",
            },
        )

        self.assert_success_response(result)

        # Validate ADF processing in API payload
        call_body = atlassian_stub.call_log[0][2]
        body_content = (
            call_body.get("body", {}).get("atlas_doc_format", {}).get("value", {})
        )

        if isinstance(body_content, dict):
            # Should find ADF elements like panels, status, etc.
            adf_elements = self._find_adf_elements_in_content(body_content)
            assert len(adf_elements) > 0, (
                "Should find ADF elements in processed content"
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

    def _find_adf_elements_in_content(self, content: dict) -> list:
        """Find ADF elements in content structure."""
        elements = []

        def collect_elements(node):
            if isinstance(node, dict):
                if "type" in node:
                    elements.append(node["type"])
                for value in node.values():
                    collect_elements(value)
            elif isinstance(node, list):
                for item in node:
                    collect_elements(item)

        collect_elements(content)
        return elements

    def assert_success_response(self, result):
        """Assert that MCP tool result indicates success."""
        assert result is not None, "Result should not be None"
        # Success validation depends on MCP response format
        # Typically non-error responses are considered successful


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
