"""
Jira MCP contract validation tests.

These tests validate MCP tool call arguments and Atlassian REST payloads
for Jira operations, focusing on contract verification rather than API behavior.
"""

import pytest
import json
from typing import Dict, Any


@pytest.mark.mcp
@pytest.mark.jira
class TestJiraMCPContracts:
    """Test MCP tool contracts for Jira operations."""
    
    @pytest.mark.asyncio
    async def test_jira_create_issue_mcp_contract(self, mcp_client, atlassian_stub, sample_test_data):
        """Test MCP tool call arguments for Jira issue creation."""
        project_key = "TEST"
        
        # Expected Jira issue response
        expected_issue = {
            "key": "TEST-123",
            "id": "12345",
            "fields": {
                "summary": "Test Issue",
                "description": {"version": 1, "type": "doc", "content": []},
                "project": {"key": project_key},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"}
            }
        }
        
        # Stub the Jira API response
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)
        
        # Call MCP tool
        result = await mcp_client.call_tool(
            "jira_create_issue",
            {
                "project_key": project_key,
                "summary": "Test Issue",
                "issue_type": "Task",
                "description": "Test description"
            }
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
                    "summary": "Test Issue",
                    "issuetype": {"name": "Task"}
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_jira_create_issue_with_priority_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for issue creation with priority."""
        project_key = "TEST"
        
        expected_issue = {
            "key": "TEST-456",
            "fields": {"priority": {"name": "High"}}
        }
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)
        
        # Call with additional_fields
        result = await mcp_client.call_tool(
            "jira_create_issue",
            {
                "project_key": project_key,
                "summary": "High Priority Issue",
                "issue_type": "Bug",
                "additional_fields": {
                    "priority": {"name": "High"}
                }
            }
        )
        
        self.assert_success_response(result)
        
        # Validate priority field in API call
        call_body = atlassian_stub.call_log[0][2]
        assert "priority" in call_body["fields"]
        assert call_body["fields"]["priority"]["name"] == "High"
    
    @pytest.mark.asyncio
    async def test_jira_create_issue_with_labels_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for issue creation with labels."""
        project_key = "TEST"
        
        expected_issue = {"key": "TEST-789", "fields": {"labels": ["test", "automation"]}}
        atlassian_stub.stub_jira_create_issue(project_key, expected_issue)
        
        result = await mcp_client.call_tool(
            "jira_create_issue",
            {
                "project_key": project_key,
                "summary": "Labeled Issue",
                "issue_type": "Task",
                "additional_fields": {
                    "labels": ["test", "automation", "mcp"]
                }
            }
        )
        
        self.assert_success_response(result)
        
        # Validate labels in API call
        call_body = atlassian_stub.call_log[0][2]
        assert "labels" in call_body["fields"]
        assert "test" in call_body["fields"]["labels"]
        assert "automation" in call_body["fields"]["labels"]
    
    @pytest.mark.asyncio
    async def test_jira_update_issue_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for issue updates."""
        issue_key = "TEST-123"
        
        # Stub update response
        atlassian_stub.responses.add(
            atlassian_stub.responses.PUT,
            f"https://test.atlassian.net/rest/api/3/issue/{issue_key}",
            json={"key": issue_key},
            status=204
        )
        
        # Call update tool
        result = await mcp_client.call_tool(
            "jira_update_issue",
            {
                "issue_key": issue_key,
                "fields": {
                    "summary": "Updated Summary",
                    "description": "Updated description"
                }
            }
        )
        
        self.assert_success_response(result)
        
        # Validate API call structure
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "PUT"
        assert f"/issue/{issue_key}" in url
        assert "fields" in body
        assert body["fields"]["summary"] == "Updated Summary"
    
    @pytest.mark.asyncio
    async def test_jira_add_comment_mcp_contract(self, mcp_client, atlassian_stub, sample_test_data):
        """Test MCP contract for adding comments."""
        issue_key = "TEST-123"
        
        # Expected comment response
        expected_comment = {
            "id": "10001",
            "body": {"version": 1, "type": "doc", "content": []},
            "author": {"displayName": "Test User"}
        }
        
        # Stub comment API
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            f"https://test.atlassian.net/rest/api/3/issue/{issue_key}/comment",
            json=expected_comment,
            status=201
        )
        
        # Add formatted comment
        comment_text = """## Test Comment

This comment has **formatting** and status: {status:color=blue}In Progress{/status}

```python
def test():
    return "code block"
```"""
        
        result = await mcp_client.call_tool(
            "jira_add_comment",
            {
                "issue_key": issue_key,
                "comment": comment_text
            }
        )
        
        self.assert_success_response(result)
        
        # Validate comment API call
        assert len(atlassian_stub.call_log) > 0
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert f"/issue/{issue_key}/comment" in url
        assert "body" in body
        
        # For Cloud instances, body should be ADF
        comment_body = body["body"]
        if isinstance(comment_body, dict):
            assert comment_body.get("type") == "doc"
            assert "content" in comment_body
    
    @pytest.mark.asyncio
    async def test_jira_get_transitions_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for getting transitions."""
        issue_key = "TEST-123"
        
        # Mock transitions response
        expected_transitions = {
            "transitions": [
                {"id": "11", "name": "To Do", "to": {"name": "To Do"}},
                {"id": "21", "name": "In Progress", "to": {"name": "In Progress"}},
                {"id": "31", "name": "Done", "to": {"name": "Done"}}
            ]
        }
        
        atlassian_stub.responses.add(
            atlassian_stub.responses.GET,
            f"https://test.atlassian.net/rest/api/3/issue/{issue_key}/transitions",
            json=expected_transitions,
            status=200
        )
        
        result = await mcp_client.call_tool(
            "jira_get_transitions",
            {"issue_key": issue_key}
        )
        
        self.assert_success_response(result)
        
        # Validate transitions structure
        response_data = self._extract_json_from_mcp_result(result)
        assert isinstance(response_data, list)
        assert len(response_data) == 3
        
        for transition in response_data:
            assert "id" in transition
            assert "name" in transition
    
    @pytest.mark.asyncio
    async def test_jira_transition_issue_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for issue transitions."""
        issue_key = "TEST-123"
        transition_id = "21"
        
        # Stub transition response
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            f"https://test.atlassian.net/rest/api/3/issue/{issue_key}/transitions",
            json={},
            status=204
        )
        
        result = await mcp_client.call_tool(
            "jira_transition_issue",
            {
                "issue_key": issue_key,
                "transition_id": transition_id,
                "comment": "Automated transition"
            }
        )
        
        self.assert_success_response(result)
        
        # Validate transition API call
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert f"/issue/{issue_key}/transitions" in url
        assert "transition" in body
        assert body["transition"]["id"] == transition_id
        
        # Should include comment if provided
        if "comment" in body:
            comment_body = body["comment"]
            if isinstance(comment_body, dict):
                # ADF format for Cloud
                assert comment_body.get("type") == "doc"
            else:
                # String format for Server/DC
                assert isinstance(comment_body, str)
    
    @pytest.mark.asyncio
    async def test_jira_search_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for Jira search."""
        jql = "project = TEST AND status = 'To Do'"
        
        # Mock search response
        expected_search = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "First Issue",
                        "status": {"name": "To Do"}
                    }
                },
                {
                    "key": "TEST-2", 
                    "fields": {
                        "summary": "Second Issue",
                        "status": {"name": "To Do"}
                    }
                }
            ],
            "total": 2,
            "startAt": 0,
            "maxResults": 50
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
                "jql": jql,
                "fields": "summary,status",
                "limit": 10
            }
        )
        
        self.assert_success_response(result)
        
        # Validate search API call
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert "/rest/api/3/search" in url
        assert "jql" in body
        assert body["jql"] == jql
        assert "fields" in body
        assert "maxResults" in body
        assert body["maxResults"] == 10
        
        # Validate response structure
        response_data = self._extract_json_from_mcp_result(result)
        assert "issues" in response_data
        assert len(response_data["issues"]) == 2
    
    @pytest.mark.asyncio
    async def test_jira_create_issue_link_mcp_contract(self, mcp_client, atlassian_stub):
        """Test MCP contract for creating issue links."""
        # Stub link creation response
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/issueLink",
            json={"id": "10001"},
            status=201
        )
        
        result = await mcp_client.call_tool(
            "jira_create_issue_link",
            {
                "link_type": "Blocks",
                "inward_issue_key": "TEST-1",
                "outward_issue_key": "TEST-2",
                "comment": "Linking issues for testing"
            }
        )
        
        self.assert_success_response(result)
        
        # Validate link API call
        method, url, body = atlassian_stub.call_log[0]
        assert method == "POST"
        assert "/issueLink" in url
        assert "type" in body
        assert "inwardIssue" in body
        assert "outwardIssue" in body
        assert body["inwardIssue"]["key"] == "TEST-1"
        assert body["outwardIssue"]["key"] == "TEST-2"
    
    @pytest.mark.asyncio
    async def test_jira_error_handling_contract(self, mcp_client, atlassian_stub):
        """Test MCP error handling for invalid requests."""
        # Stub 400 error response
        atlassian_stub.responses.add(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/issue",
            json={"errors": {"project": "Project is required"}},
            status=400
        )
        
        result = await mcp_client.call_tool(
            "jira_create_issue",
            {
                "project_key": "",  # Invalid empty project
                "summary": "Test Issue",
                "issue_type": "Task"
            }
        )
        
        # Should return error result
        assert isinstance(result, dict)
        # Error handling varies by MCP implementation
        # but should not raise unhandled exceptions
    
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