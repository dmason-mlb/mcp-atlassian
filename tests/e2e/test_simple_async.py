#!/usr/bin/env python3
"""
Test basic async functionality without any MCP dependencies.
"""

import asyncio

import pytest


@pytest.mark.asyncio
async def test_basic_async():
    """Test basic async functionality."""
    await asyncio.sleep(0.1)
    assert True


@pytest.mark.asyncio
async def test_async_http():
    """Test async HTTP without MCP."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Test if basic HTTP works
        try:
            async with session.get(
                "http://localhost:9001/healthz", timeout=2
            ) as response:
                assert response.status == 200
                text = await response.text()
                assert text == "OK"
        except Exception as e:
            pytest.fail(f"HTTP request failed: {e}")
