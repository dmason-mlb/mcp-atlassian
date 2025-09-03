#!/usr/bin/env python3
import asyncio
import json
import os
import sys

sys.path.insert(0, ".")
from mcp_client_fixed import MCPClientFixed


async def main():
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")

    print("Testing direct tool call with invalid space...")

    try:
        client = MCPClientFixed(mcp_url)

        # Direct tool call to see raw response
        result = await client.call_tool(
            "confluence_pages_create_page",
            {
                "space_id": "INVALID",
                "title": "Should Fail",
                "content": "This should not work",
                "content_format": "markdown",
            },
        )

        print(f"Direct result type: {type(result)}")
        print(f"Direct result: {result}")

        # Check if it has content
        if hasattr(result, "content"):
            print(f"Result content: {result.content}")

        # Try to extract JSON
        extracted = client.extract_json(result)
        print(f"Extracted JSON: {json.dumps(extracted, indent=2)}")

    except Exception as e:
        print(f"Exception raised: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
