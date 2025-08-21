#!/usr/bin/env python3
"""
Test the fixed MCP Client.
"""
import pytest
import asyncio
from mcp_client_fixed import MCPClientFixed, MCPClientSession


@pytest.mark.asyncio
async def test_fixed_mcpclient_list_tools():
    """Test the fixed MCPClient list_tools method."""
    client = MCPClientFixed("http://localhost:9001/mcp")
    
    try:
        async with asyncio.timeout(10):
            tools = await client.list_tools()
            assert len(tools) > 0, "Should have tools available"
            print(f"✓ Found {len(tools)} tools")
    except asyncio.TimeoutError:
        pytest.fail("Fixed MCPClient list_tools timed out")
    except Exception as e:
        pytest.fail(f"Fixed MCPClient list_tools failed: {e}")


@pytest.mark.asyncio
async def test_fixed_mcpclient_context_manager():
    """Test the fixed MCPClient using context manager."""
    try:
        async with asyncio.timeout(10):
            async with MCPClientSession("http://localhost:9001/mcp") as client:
                tools = await client.list_tools()
                assert len(tools) > 0, "Should have tools available"
                print(f"✓ Context manager worked with {len(tools)} tools")
    except asyncio.TimeoutError:
        pytest.fail("Fixed MCPClientSession context manager timed out")
    except Exception as e:
        pytest.fail(f"Fixed MCPClientSession context manager failed: {e}")