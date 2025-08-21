#!/usr/bin/env python3
import asyncio
import os
import sys

sys.path.insert(0, '.')
from mcp_client_fixed import MCPClientFixed

async def main():
    confluence_space = os.getenv("CONFLUENCE_SPACE", "~911651470")
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    print(f"Testing error handling with invalid space...")
    
    try:
        client = MCPClientFixed(mcp_url)
        
        result = await client.create_confluence_page(
            space_id="INVALID",
            title="Should Fail",
            content="This should not work",
            content_format="markdown"
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        extracted = client.extract_json(result)
        print(f"Extracted: {extracted}")
        
    except Exception as e:
        print(f"Exception raised: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
