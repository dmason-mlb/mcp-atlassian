#!/usr/bin/env python3
"""
Debug Confluence page creation issue.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, '.')

# Import our MCP client
from mcp_client_fixed import MCPClientFixed

async def main():
    # Set up environment
    confluence_space = os.getenv("CONFLUENCE_SPACE", "~911651470")
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    print(f"Using MCP URL: {mcp_url}")
    print(f"Using Confluence space: {repr(confluence_space)}")
    print()
    
    try:
        client = MCPClientFixed(mcp_url)
        
        # Test basic connectivity
        print("1. Testing tool availability...")
        tools = await client.list_tools()
        confluence_tools = [t['name'] for t in tools if 'confluence' in t['name']]
        print(f"   Found {len(confluence_tools)} Confluence tools: {confluence_tools[:5]}...")
        print()
        
        # Test page creation
        print("2. Testing page creation...")
        title = "Debug Test Page"
        content = "This is a debug test page."
        
        print(f"   Creating page: {title}")
        print(f"   In space: {confluence_space}")
        print(f"   Content: {content}")
        print()
        
        result = await client.create_confluence_page(
            space_id=confluence_space,
            title=title,
            content=content,
            content_format="markdown"
        )
        
        print("3. Raw result:")
        print(f"   Type: {type(result)}")
        print(f"   Value: {result}")
        print()
        
        # Extract JSON
        extracted = client.extract_json(result)
        print("4. Extracted JSON:")
        print(f"   Type: {type(extracted)}")
        print(f"   Value: {json.dumps(extracted, indent=2)}")
        print()
        
        # Test direct tool call
        print("5. Testing direct tool call...")
        direct_result = await client.call_tool("confluence_pages_create_page", {
            "space_id": confluence_space,
            "title": f"{title} Direct",
            "content": content,
            "content_format": "markdown"
        })
        
        print(f"   Direct result type: {type(direct_result)}")
        print(f"   Direct result: {direct_result}")
        print()
        
        direct_extracted = client.extract_json(direct_result)
        print("6. Direct extracted JSON:")
        print(f"   Type: {type(direct_extracted)}")
        print(f"   Value: {json.dumps(direct_extracted, indent=2)}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())