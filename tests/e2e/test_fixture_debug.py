#!/usr/bin/env python3
"""
Debug pytest fixtures to isolate the connection hanging issue.
"""
import pytest
import asyncio
from mcp_client import MCPClient


@pytest.mark.asyncio
async def test_mcp_client_direct():
    """Test MCP client directly without fixtures."""
    client = MCPClient("http://localhost:9001/mcp")
    await client.connect()
    
    tools = await client.list_tools()
    assert len(tools) > 0, "Should have tools available"
    
    await client.disconnect()


@pytest.mark.asyncio
async def test_mcp_client_fixture_usage(mcp_client):
    """Test using the mcp_client fixture."""
    tools = await mcp_client.list_tools()
    assert len(tools) > 0, "Should have tools available"