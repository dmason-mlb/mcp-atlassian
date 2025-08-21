#!/usr/bin/env python3
"""
Direct MCP connection test to bypass fixtures.
"""
import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_direct_connection():
    """Test direct MCP connection without pytest fixtures."""
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    print(f"Testing connection to: {mcp_url}")
    
    try:
        async with streamablehttp_client(mcp_url) as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()
                print("✓ Connected to MCP server successfully")
                
                # Test tool listing
                tools = await session.list_tools()
                print(f"✓ Found {len(tools.tools)} tools")
                
                return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_connection())
    exit(0 if success else 1)