#!/usr/bin/env python3
"""
Test the MCPClient wrapper class to find the hanging issue.
"""

import asyncio

import pytest
from mcp_client import MCPClient


@pytest.mark.asyncio
async def test_mcpclient_connect():
    """Test MCPClient.connect() with timeout."""
    client = MCPClient("http://localhost:9001/mcp")

    try:
        async with asyncio.timeout(10):  # 10 second timeout
            await client.connect()
            print("✓ MCPClient.connect() succeeded")

        # Test basic operations
        async with asyncio.timeout(5):
            tools = await client.list_tools()
            assert len(tools) > 0
            print(f"✓ Found {len(tools)} tools")

        await client.disconnect()
        print("✓ MCPClient.disconnect() succeeded")

    except asyncio.TimeoutError as e:
        await client.disconnect()  # cleanup
        pytest.fail("MCPClient operations timed out")
    except Exception as e:
        await client.disconnect()  # cleanup
        pytest.fail(f"MCPClient failed: {e}")


@pytest.mark.asyncio
async def test_mcpclient_context_manager():
    """Test MCPClient using context manager."""
    from mcp_client import MCPClientSession

    try:
        async with asyncio.timeout(10):
            async with MCPClientSession("http://localhost:9001/mcp") as client:
                tools = await client.list_tools()
                assert len(tools) > 0
                print(f"✓ Context manager worked with {len(tools)} tools")
    except asyncio.TimeoutError:
        pytest.fail("MCPClientSession context manager timed out")
    except Exception as e:
        pytest.fail(f"MCPClientSession context manager failed: {e}")
