#!/usr/bin/env python3
"""
Test using the exact same pattern as the working seed.py
"""
import asyncio
import os
import pytest
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Load env like seed.py does
def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        try:
            from dotenv import load_dotenv as _dz
            _dz(env_path, override=False)
            return
        except Exception:
            pass
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.strip().startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                # Drop inline comments
                if " #" in val:
                    val = val.split(" #", 1)[0]
                if " ;" in val:
                    val = val.split(" ;", 1)[0]
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parents[3]
_load_env_file(ROOT_DIR / ".env")


@pytest.mark.asyncio
async def test_seed_pattern_connection():
    """Test using the exact same connection pattern as seed.py"""
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    # Same headers pattern as seed.py
    headers: dict[str, str] = {}
    if os.getenv("USER_OAUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
    if os.getenv("USER_CLOUD_ID"):
        headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")
    
    print(f"Connecting to: {mcp_url}")
    print(f"Headers: {headers}")
    
    try:
        async with asyncio.timeout(10):
            async with streamablehttp_client(mcp_url, headers=headers) as (r, w, _):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    print(f"✓ Success! Found {len(tools.tools)} tools")
                    assert len(tools.tools) > 0, "Should have tools available"
    except asyncio.TimeoutError:
        pytest.fail("Seed pattern connection timed out")
    except Exception as e:
        pytest.fail(f"Seed pattern connection failed: {e}")


@pytest.mark.asyncio  
async def test_list_tools_call():
    """Test calling list_tools using the exact pattern from seed.py"""
    mcp_url = os.getenv("MCP_URL", "http://localhost:9001/mcp")
    
    headers: dict[str, str] = {}
    if os.getenv("USER_OAUTH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.getenv('USER_OAUTH_TOKEN')}"
    if os.getenv("USER_CLOUD_ID"):
        headers["X-Atlassian-Cloud-Id"] = os.getenv("USER_CLOUD_ID", "")
    
    try:
        async with asyncio.timeout(10):
            async with streamablehttp_client(mcp_url, headers=headers) as (r, w, _):
                async with ClientSession(r, w) as session:
                    await session.initialize()
                    # Call list_tools just like in conftest.py logic would
                    tools = await session.list_tools()
                    tool_list = tools.tools if hasattr(tools, 'tools') else []
                    print(f"✓ list_tools worked! Found {len(tool_list)} tools")
                    assert len(tool_list) > 0, "Should have tools available"
    except asyncio.TimeoutError:
        pytest.fail("list_tools call timed out")
    except Exception as e:
        pytest.fail(f"list_tools call failed: {e}")