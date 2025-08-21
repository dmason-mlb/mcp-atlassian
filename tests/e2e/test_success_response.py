#!/usr/bin/env python3
import asyncio
import os
import sys
import json

sys.path.insert(0, '.')
from mcp_client_fixed import MCPClientFixed

async def main():
    confluence_space = os.getenv("CONFLUENCE_SPACE", "~911651470")
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    print(f"Testing successful page creation...")
    
    try:
        client = MCPClientFixed(mcp_url)
        
        result = await client.create_confluence_page(
            space_id=confluence_space,
            title="Success Test Page",
            content="This should work",
            content_format="markdown"
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        extracted = client.extract_json(result)
        print(f"Extracted: {json.dumps(extracted, indent=2)}")
        
    except Exception as e:
        print(f"Exception raised: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
