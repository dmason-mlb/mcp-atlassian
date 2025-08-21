#!/usr/bin/env python3
"""
Test to isolate MCP connection issues.
"""
import pytest
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


@pytest.mark.asyncio
async def test_mcp_streamable_http_only():
    """Test just the streamablehttp_client connection."""
    mcp_url = "http://localhost:9001/mcp"
    
    try:
        # Test the timeout behavior
        async with asyncio.timeout(5):  # 5 second timeout
            async with streamablehttp_client(mcp_url) as (r, w, _):
                # Just test connection establishment
                assert r is not None
                assert w is not None
                print("✓ streamablehttp_client connection established")
    except asyncio.TimeoutError:
        pytest.fail("streamablehttp_client connection timed out")
    except Exception as e:
        pytest.fail(f"streamablehttp_client connection failed: {e}")


@pytest.mark.asyncio 
async def test_mcp_client_session_only():
    """Test MCP ClientSession with manual timeout."""
    mcp_url = "http://localhost:9001/mcp"
    
    try:
        # Test with explicit timeout
        async with asyncio.timeout(10):  # 10 second timeout
            async with streamablehttp_client(mcp_url) as (r, w, _):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    print("✓ MCP ClientSession initialized")
    except asyncio.TimeoutError:
        pytest.fail("MCP ClientSession initialization timed out")
    except Exception as e:
        pytest.fail(f"MCP ClientSession failed: {e}")