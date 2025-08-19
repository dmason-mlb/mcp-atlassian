#!/usr/bin/env python3

import os
import sys
import asyncio
import json
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def test_page_creation():
    """Test page creation to see exact error."""
    mcp_url = "http://localhost:9000/mcp"
    
    async with streamablehttp_client(mcp_url) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            print("Testing Confluence page creation...")
            
            try:
                result = await session.call_tool(
                    "confluence_pages_create_page",
                    {
                        "space_id": "~911651470",  # Your personal space
                        "title": f"Debug Test Page V2 - {os.getpid()}",
                        "content": "# Simple Test\n\nJust testing **bold** text.",
                        "content_format": "markdown",
                    },
                )
                print(f"SUCCESS: {result}")
            except Exception as e:
                print(f"ERROR: {e}")
                print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_page_creation())