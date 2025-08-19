#!/usr/bin/env python3

import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def list_tools():
    """List available MCP tools."""
    mcp_url = "http://localhost:9001/mcp"
    
    async with streamablehttp_client(mcp_url) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            # List all available tools
            result = await session.list_tools()
            tools = result.tools
            
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Look for create-related tools
            create_tools = [t for t in tools if 'create' in t.name.lower()]
            print(f"\nCreate-related tools ({len(create_tools)}):")
            for tool in create_tools:
                print(f"  - {tool.name}")

if __name__ == "__main__":
    asyncio.run(list_tools())