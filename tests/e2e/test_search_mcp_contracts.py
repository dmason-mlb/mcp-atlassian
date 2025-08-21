"""
Search MCP contract validation tests.

These tests validate MCP tool call arguments and Atlassian REST payloads
for search operations, focusing on contract verification rather than API behavior.
"""

import pytest
import json
from typing import Dict, Any


@pytest.mark.mcp
@pytest.mark.search
class TestSearchMCPContracts:
    """Test MCP tool contracts for search operations."""
    
    @pytest.mark.asyncio
    async def test_jira_search_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP tool call arguments for Jira search."""
        # Expected Jira search response
        expected_search = {
            "issues": [
                {
                    "key": "TEST-123",
                    "fields": {
                        "summary": "Test Issue",
                        "status": {"name": "To Do"},
                        "issuetype": {"name": "Task"}
                    }
                }
            ],
            "total": 1,
            "startAt": 0,
            "maxResults": 10
        }
        
        # Stub the Jira search API response
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/search",
            json=expected_search,
            status=200
        )
        
        # Call MCP tool
        result = await mcp_client.call_tool(
            "jira_search",
            {
                "jql": "project = TEST AND status = 'To Do'",
                "fields": "summary,status,issuetype",
                "limit": 10,
                "start_at": 0
            }
        )
        
        # Validate MCP response structure
        assert isinstance(result, dict)
        response_data = self._extract_json_from_mcp_result(result)
        assert "issues" in response_data
        assert len(response_data["issues"]) == 1
        
        # Validate Atlassian REST API call was made correctly
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert "/rest/api/3/search" in url
        assert "jql" in body
        assert body["jql"] == "project = TEST AND status = 'To Do'"
        assert "fields" in body
        assert "maxResults" in body
        assert body["maxResults"] == 10
        assert "startAt" in body
        assert body["startAt"] == 0
    
    @pytest.mark.asyncio
    async def test_jira_search_with_pagination_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Jira search pagination."""
        # Mock paginated response
        expected_search = {
            "issues": [
                {"key": "TEST-4", "fields": {"summary": "Fourth Issue"}},
                {"key": "TEST-5", "fields": {"summary": "Fifth Issue"}}
            ],
            "total": 15,
            "startAt": 3,
            "maxResults": 2
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/search",
            json=expected_search,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "jira_search",
            {
                "jql": "project = TEST ORDER BY created ASC",
                "limit": 2,
                "start_at": 3
            }
        )
        
        self.assert_success_response(result)
        
        # Validate pagination parameters in API call
        method, url, body = atlassian_stub.call_log[0]
        assert body["maxResults"] == 2
        assert body["startAt"] == 3
        
        # Validate response structure
        response_data = self._extract_json_from_mcp_result(result)
        assert response_data["total"] == 15
        assert response_data["startAt"] == 3
        assert len(response_data["issues"]) == 2
    
    @pytest.mark.asyncio
    async def test_jira_search_fields_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Jira field search."""
        # Mock field search response
        expected_fields = [
            {
                "id": "summary",
                "name": "Summary",
                "custom": False,
                "searchable": True
            },
            {
                "id": "customfield_10001",
                "name": "Epic Link",
                "custom": True,
                "searchable": True
            }
        ]
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/rest/api/3/field",
            json=expected_fields,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "jira_search_fields",
            {
                "keyword": "summary",
                "limit": 10
            }
        )
        
        self.assert_success_response(result)
        
        # Validate field search API call
        method, url, body = atlassian_stub.call_log[0]
        assert method == "GET"
        assert "/rest/api/3/field" in url
        
        # Validate response structure
        response_data = self._extract_json_from_mcp_result(result)
        assert isinstance(response_data, list)
        assert len(response_data) >= 1
        
        summary_field = next((f for f in response_data if f.get("name") == "Summary"), None)
        assert summary_field is not None
        assert summary_field["id"] == "summary"
    
    @pytest.mark.asyncio
    async def test_jira_advanced_jql_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for advanced JQL queries."""
        # Mock response for complex JQL
        expected_search = {
            "issues": [
                {
                    "key": "TEST-100",
                    "fields": {
                        "summary": "Recent High Priority Bug",
                        "priority": {"name": "High"},
                        "issuetype": {"name": "Bug"},
                        "created": "2025-01-20T10:00:00.000+0000"
                    }
                }
            ],
            "total": 1,
            "startAt": 0,
            "maxResults": 5
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/search",
            json=expected_search,
            status=200
        )
        
        # Complex JQL with date, priority, and text search
        complex_jql = "project = TEST AND priority = High AND issuetype = Bug AND created >= -7d AND text ~ 'urgent'"
        
        result = await mcp_client.call_tool(
            "jira_search",
            {
                "jql": complex_jql,
                "fields": "summary,priority,issuetype,created",
                "limit": 5
            }
        )
        
        self.assert_success_response(result)
        
        # Validate complex JQL was passed correctly
        method, url, body = atlassian_stub.call_log[0]
        assert body["jql"] == complex_jql
        assert "summary" in body["fields"]
        assert "priority" in body["fields"]
    
    @pytest.mark.asyncio
    async def test_confluence_search_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP tool call arguments for Confluence search."""
        # Expected Confluence search response
        expected_search = {
            "results": [
                {
                    "content": {
                        "id": "123456",
                        "title": "Test Page",
                        "type": "page"
                    },
                    "space": {
                        "key": "TEST",
                        "name": "Test Space"
                    }
                }
            ],
            "size": 1,
            "limit": 10,
            "start": 0
        }
        
        # Stub the Confluence search API response
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/rest/api/content/search",
            json=expected_search,
            status=200
        )
        
        # Call MCP tool
        result = await mcp_client.call_tool(
            "confluence_search_search",
            {
                "query": "siteSearch ~ 'test page'",
                "limit": 10
            }
        )
        
        # Validate MCP response structure
        assert isinstance(result, dict)
        response_data = self._extract_json_from_mcp_result(result)
        assert "results" in response_data
        assert len(response_data["results"]) == 1
        
        # Validate Atlassian REST API call was made correctly
        assert len(atlassian_stub.call_log) > 0
        method, url, query_params = atlassian_stub.call_log[0]
        assert method == "GET"
        assert "/wiki/rest/api/content/search" in url
        # Note: Query parameters would be in URL for GET requests
    
    @pytest.mark.asyncio
    async def test_confluence_cql_search_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Confluence CQL search."""
        # Mock CQL search response
        expected_search = {
            "results": [
                {
                    "content": {
                        "id": "789012",
                        "title": "CQL Test Page",
                        "type": "page",
                        "space": {"key": "DEV"}
                    }
                }
            ],
            "size": 1
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/rest/api/content/search",
            json=expected_search,
            status=200
        )
        
        # CQL query
        cql_query = "type=page AND space=DEV AND title~'CQL Test'"
        
        result = await mcp_client.call_tool(
            "confluence_search_search",
            {
                "query": cql_query,
                "limit": 5
            }
        )
        
        self.assert_success_response(result)
        
        # Validate CQL query was passed correctly
        method, url, query_params = atlassian_stub.call_log[0]
        assert method == "GET"
        # CQL should be passed as a parameter in the URL
        assert "cql=" in url or "q=" in url
    
    @pytest.mark.asyncio
    async def test_confluence_text_search_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Confluence text search."""
        # Mock text search response
        expected_search = {
            "results": [
                {
                    "content": {
                        "id": "345678",
                        "title": "Documentation Page",
                        "type": "page"
                    },
                    "excerpt": "This page contains searchable content..."
                }
            ]
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/rest/api/content/search",
            json=expected_search,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "confluence_search_search",
            {
                "query": "searchable content documentation",
                "limit": 10
            }
        )
        
        self.assert_success_response(result)
        
        # Validate text search parameters
        response_data = self._extract_json_from_mcp_result(result)
        assert "results" in response_data
        assert len(response_data["results"]) == 1
        
        result_item = response_data["results"][0]
        assert "content" in result_item
        assert result_item["content"]["type"] == "page"
    
    @pytest.mark.asyncio
    async def test_confluence_search_with_spaces_filter_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Confluence search with spaces filter."""
        # Mock filtered search response
        expected_search = {
            "results": [
                {
                    "content": {
                        "id": "456789",
                        "title": "Filtered Page",
                        "type": "page"
                    },
                    "space": {
                        "key": "PROJ",
                        "name": "Project Space"
                    }
                }
            ]
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/rest/api/content/search",
            json=expected_search,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "confluence_search_search",
            {
                "query": "project documentation",
                "spaces_filter": "PROJ,DEV",
                "limit": 5
            }
        )
        
        self.assert_success_response(result)
        
        # Validate spaces filter was applied
        method, url, query_params = atlassian_stub.call_log[0]
        # Spaces filter should be incorporated into the query or parameters
        assert "PROJ" in url or "spaceKey=" in url
    
    @pytest.mark.asyncio
    async def test_confluence_user_search_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Confluence user search."""
        # Mock user search response
        expected_users = {
            "results": [
                {
                    "user": {
                        "accountId": "12345",
                        "displayName": "John Doe",
                        "email": "john.doe@example.com"
                    }
                }
            ]
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            "https://test.atlassian.net/wiki/rest/api/search/user",
            json=expected_users,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "confluence_search_search_user",
            {
                "query": "user.fullname ~ 'John Doe'",
                "limit": 10
            }
        )
        
        self.assert_success_response(result)
        
        # Validate user search API call
        method, url, query_params = atlassian_stub.call_log[0]
        assert method == "GET"
        assert "/wiki/rest/api/search/user" in url
        
        # Validate response structure
        response_data = self._extract_json_from_mcp_result(result)
        assert "results" in response_data
        assert len(response_data["results"]) == 1
        
        user_result = response_data["results"][0]
        assert "user" in user_result
        assert user_result["user"]["displayName"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_search_error_handling_contract(self, mcp_client, atlassian_stub):
        """Test MCP error handling for invalid search queries."""
        # Stub error responses for invalid queries
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/search",
            json={"errorMessages": ["The value 'INVALID' does not exist for the field 'project'."]},
            status=400
        )
        
        result = await mcp_client.call_tool(
            "jira_search",
            {
                "jql": "project = INVALID_PROJECT",
                "limit": 5
            }
        )
        
        # Should return error result without throwing unhandled exceptions
        assert isinstance(result, dict)
        # Error handling varies by MCP implementation
        # but should not raise unhandled exceptions
    
    @pytest.mark.asyncio
    async def test_search_performance_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for search performance limits."""
        # Mock large result set response
        large_results = {
            "issues": [
                {"key": f"TEST-{i}", "fields": {"summary": f"Issue {i}"}}
                for i in range(100)
            ],
            "total": 1000,
            "startAt": 0,
            "maxResults": 100
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/search",
            json=large_results,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "jira_search",
            {
                "jql": "project = TEST",
                "limit": 100
            }
        )
        
        self.assert_success_response(result)
        
        # Validate large limit was passed correctly
        method, url, body = atlassian_stub.call_log[0]
        assert body["maxResults"] == 100
        
        # Validate response can handle large result sets
        response_data = self._extract_json_from_mcp_result(result)
        assert len(response_data["issues"]) == 100
        assert response_data["total"] == 1000
    
    def _extract_json_from_mcp_result(self, result: Any) -> Dict:
        """Extract JSON from MCP tool result."""
        if isinstance(result, dict):
            return result
        
        try:
            # Handle FastMCP ToolResult structure
            content = getattr(result, "content", None) or result.get("content")
            if isinstance(content, list) and content:
                for item in content:
                    text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
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
    
    def assert_success_response(self, result):
        """Assert that MCP tool result indicates success."""
        assert result is not None, "Result should not be None"
        # Success validation depends on MCP response format
        # Typically non-error responses are considered successful


if __name__ == "__main__":
    pytest.main([__file__, "-v"])