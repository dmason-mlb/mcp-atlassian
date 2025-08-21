"""
MCP Client for Atlassian E2E Testing.

This module provides a reusable MCP client for testing Atlassian tools,
adapted from the existing seed.py implementation with enhanced error handling
and testing-specific utilities.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPConnectionError(MCPClientError):
    """Raised when MCP connection fails."""
    pass


class MCPToolError(MCPClientError):
    """Raised when MCP tool execution fails."""
    pass


class MCPClient:
    """
    MCP Client for Atlassian testing.
    
    Provides a clean interface for calling MCP tools with proper error handling,
    response validation, and testing utilities.
    """
    
    def __init__(self, mcp_url: str = "http://localhost:9001/mcp"):
        """
        Initialize MCP client.
        
        Args:
            mcp_url: URL of the MCP server endpoint
        """
        self.mcp_url = mcp_url
        self.session: Optional[ClientSession] = None
        self._client_cm = None
        self._session_cm = None
        
        # Optional auth passthrough for multi-tenant server
        self.headers: Dict[str, str] = {}
        if os.getenv("USER_OAUTH_TOKEN"):
            self.headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
        if os.getenv("USER_CLOUD_ID"):
            self.headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")
    
    async def connect(self) -> None:
        """
        Establish connection to MCP server.
        
        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            # Use proper async context management like the working seed script
            self._client_cm = streamablehttp_client(self.mcp_url, headers=self.headers)
            read_stream, write_stream, _ = await self._client_cm.__aenter__()
            
            self._session_cm = ClientSession(read_stream, write_stream)
            self.session = await self._session_cm.__aenter__()
            
        except Exception as e:
            # Cleanup on failure
            await self._cleanup()
            raise MCPConnectionError(f"Failed to connect to MCP server at {self.mcp_url}: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        await self._cleanup()
    
    async def _cleanup(self) -> None:
        """Internal cleanup method."""
        if self._session_cm and self.session:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
            self.session = None
        
        if self._client_cm:
            try:
                await self._client_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._client_cm = None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available MCP tools.
        
        Returns:
            List of tool definitions
            
        Raises:
            MCPClientError: If not connected or tool listing fails
        """
        if not self.session:
            raise MCPClientError("Not connected to MCP server")
        
        try:
            tools = await self.session.list_tools()
            return tools.tools if hasattr(tools, 'tools') else []
        except Exception as e:
            raise MCPClientError(f"Failed to list tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            MCPToolError: If tool execution fails
            MCPClientError: If not connected
        """
        if not self.session:
            raise MCPClientError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            raise MCPToolError(f"Tool '{tool_name}' failed: {e}")
    
    def extract_json(self, result: Any) -> Dict[str, Any]:
        """
        Extract JSON object from MCP tool result.
        
        Args:
            result: MCP tool result
            
        Returns:
            Extracted JSON data
        """
        if isinstance(result, dict):
            return result
        
        try:
            # FastMCP ToolResult shape
            content = getattr(result, "content", None) or result.get("content")
            if isinstance(content, list) and content:
                # Prefer text blocks that contain JSON
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
        
        # Fallback: try json.loads on str(result)
        try:
            return json.loads(str(result))
        except Exception:
            return {}
    
    def extract_value(self, result: Any, *keys: str, default: Any = None) -> Any:
        """
        Extract a specific value from MCP tool result using key path.
        
        Args:
            result: MCP tool result
            *keys: Key path to extract (e.g., "issue", "key")
            default: Default value if extraction fails
            
        Returns:
            Extracted value or default
        """
        data = self.extract_json(result)
        
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        
        return data
    
    async def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Jira issue using MCP tools.
        
        Args:
            project_key: Jira project key
            summary: Issue summary
            issue_type: Issue type (Task, Bug, Story, etc.)
            description: Issue description
            additional_fields: Additional fields to set
            assignee: Assignee identifier
            
        Returns:
            Created issue data
        """
        arguments = {
            "project_key": project_key,
            "summary": summary,
            "issue_type": issue_type,
        }
        
        if description:
            arguments["description"] = description
        if assignee:
            arguments["assignee"] = assignee
        if additional_fields:
            arguments["additional_fields"] = additional_fields
        
        result = await self.call_tool("jira_issues_create_issue", arguments)
        return self.extract_json(result)
    
    async def update_jira_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any],
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update a Jira issue using MCP tools.
        
        Args:
            issue_key: Jira issue key
            fields: Fields to update
            additional_fields: Additional fields to update
            
        Returns:
            Updated issue data
        """
        arguments = {
            "issue_key": issue_key,
            "fields": fields,
        }
        
        if additional_fields:
            arguments["additional_fields"] = additional_fields
        
        result = await self.call_tool("jira_issues_update_issue", arguments)
        return self.extract_json(result)
    
    async def add_jira_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: Jira issue key
            comment: Comment text
            
        Returns:
            Comment data
        """
        result = await self.call_tool("jira_add_comment", {
            "issue_key": issue_key,
            "comment": comment,
        })
        return self.extract_json(result)
    
    async def get_jira_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for a Jira issue.
        
        Args:
            issue_key: Jira issue key
            
        Returns:
            List of available transitions
        """
        result = await self.call_tool("jira_management_get_transitions", {
            "issue_key": issue_key,
        })
        data = self.extract_json(result)
        return data.get("transitions", [])
    
    async def transition_jira_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transition a Jira issue.
        
        Args:
            issue_key: Jira issue key
            transition_id: Transition ID
            comment: Optional comment
            fields: Optional fields to update
            
        Returns:
            Transition result
        """
        arguments = {
            "issue_key": issue_key,
            "transition_id": transition_id,
        }
        
        if comment:
            arguments["comment"] = comment
        if fields:
            arguments["fields"] = fields
        
        result = await self.call_tool("jira_issues_transition_issue", arguments)
        return self.extract_json(result)
    
    async def create_confluence_page(
        self,
        space_id: str,
        title: str,
        content: str,
        content_format: str = "markdown",
        parent_id: Optional[str] = None,
        enable_heading_anchors: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Confluence page using MCP tools.
        
        Args:
            space_id: Confluence space ID
            title: Page title
            content: Page content
            content_format: Content format (markdown, wiki, storage)
            parent_id: Parent page ID
            enable_heading_anchors: Enable heading anchors
            
        Returns:
            Created page data
        """
        arguments = {
            "space_id": space_id,
            "title": title,
            "content": content,
            "content_format": content_format,
            "enable_heading_anchors": enable_heading_anchors,
        }
        
        if parent_id:
            arguments["parent_id"] = parent_id
        
        result = await self.call_tool("confluence_pages_create_page", arguments)
        return self.extract_json(result)
    
    async def update_confluence_page(
        self,
        page_id: str,
        title: str,
        content: str,
        content_format: str = "markdown",
        version_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a Confluence page using MCP tools.
        
        Args:
            page_id: Page ID
            title: Page title
            content: Page content
            content_format: Content format
            version_comment: Version comment
            
        Returns:
            Updated page data
        """
        arguments = {
            "page_id": page_id,
            "title": title,
            "content": content,
            "content_format": content_format,
        }
        
        if version_comment:
            arguments["version_comment"] = version_comment
        
        result = await self.call_tool("confluence_pages_update_page", arguments)
        return self.extract_json(result)
    
    async def add_confluence_comment(self, page_id: str, content: str) -> Dict[str, Any]:
        """
        Add a comment to a Confluence page.
        
        Args:
            page_id: Page ID
            content: Comment content
            
        Returns:
            Comment data
        """
        result = await self.call_tool("confluence_content_add_comment", {
            "page_id": page_id,
            "content": content,
        })
        return self.extract_json(result)
    
    async def add_confluence_label(self, page_id: str, name: str) -> Dict[str, Any]:
        """
        Add a label to a Confluence page.
        
        Args:
            page_id: Page ID
            name: Label name
            
        Returns:
            Label data
        """
        result = await self.call_tool("confluence_content_add_label", {
            "page_id": page_id,
            "name": name,
        })
        return self.extract_json(result)
    
    async def search_jira(
        self,
        jql: str,
        fields: str = "summary,status,assignee,labels,created",
        limit: int = 10,
        expand: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search Jira issues using JQL.
        
        Args:
            jql: JQL query
            fields: Fields to return
            limit: Maximum results
            expand: Fields to expand
            
        Returns:
            Search results
        """
        arguments = {
            "jql": jql,
            "fields": fields,
            "limit": limit,
        }
        
        if expand:
            arguments["expand"] = expand
        
        result = await self.call_tool("jira_search_search", arguments)
        return self.extract_json(result)
    
    async def search_confluence(
        self,
        query: str,
        limit: int = 10,
        spaces_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search Confluence content.
        
        Args:
            query: Search query
            limit: Maximum results
            spaces_filter: Space filter
            
        Returns:
            Search results
        """
        arguments = {
            "query": query,
            "limit": limit,
        }
        
        if spaces_filter:
            arguments["spaces_filter"] = spaces_filter
        
        result = await self.call_tool("confluence_search_search", arguments)
        return self.extract_json(result)


# Context manager for convenient usage
class MCPClientSession:
    """Context manager for MCP client sessions."""
    
    def __init__(self, mcp_url: str = "http://localhost:9001/mcp"):
        self.client = MCPClient(mcp_url)
    
    async def __aenter__(self) -> MCPClient:
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()


# Utility functions
async def with_mcp_client(mcp_url: str = "http://localhost:9001/mcp"):
    """
    Context manager for MCP client sessions.
    
    Args:
        mcp_url: MCP server URL
        
    Yields:
        MCPClient: Connected MCP client
    """
    async with MCPClientSession(mcp_url) as client:
        yield client