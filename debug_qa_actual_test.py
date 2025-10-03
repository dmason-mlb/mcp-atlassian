#!/usr/bin/env python3
"""
Direct test to verify actual tool behavior outside of pytest mocking.

This script will call the MCP tools directly to see what actually happens
when authentication and operations fail, versus what the QA tests claim.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.servers.main import AtlassianMCP, register_v2_tools
from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.confluence.config import ConfluenceConfig


async def test_actual_tool_behavior():
    """Test actual tool behavior with real (but invalid) configuration."""
    print("🔍 Testing actual tool behavior with invalid authentication...")

    # Create server instance
    server = AtlassianMCP(name="Direct Test Atlassian MCP")

    # Create configuration that should cause authentication failures
    # Use real URLs but invalid credentials to trigger actual auth errors
    jira_config = JiraConfig(
        url="https://test.atlassian.net",
        auth_type="oauth",
        # No actual credentials provided - should fail authentication
    )
    confluence_config = ConfluenceConfig(
        url="https://test.atlassian.net",
        auth_type="oauth",
        # No actual credentials provided - should fail authentication
    )

    # Create application context
    app_context = MainAppContext(
        full_jira_config=jira_config,
        full_confluence_config=confluence_config,
        read_only=False,
        enabled_tools=None
    )

    # Set up the server context
    server.ctx = app_context

    # Register the tools
    register_v2_tools(server)

    print("✅ Server setup complete. Testing operations...")

    # Test 1: Basic dry run operation (should work)
    print("\n" + "="*60)
    print("TEST 1: Dry run operation (should work)")
    print("="*60)

    try:
        result = await test_tool_call(
            server,
            "resource_manager_tool",
            {
                "service": "jira",
                "resource": "issue",
                "operation": "create",
                "dry_run": True,
                "data": {
                    "project_key": "FTEST",
                    "summary": "Test Issue",
                    "issue_type": "Task"
                }
            }
        )
        print("✅ Dry run succeeded:")
        print(result)
    except Exception as e:
        print(f"❌ Dry run failed: {type(e).__name__}: {e}")

    # Test 2: Real operation (should fail with auth error)
    print("\n" + "="*60)
    print("TEST 2: Real operation (should fail with auth error)")
    print("="*60)

    try:
        result = await test_tool_call(
            server,
            "resource_manager_tool",
            {
                "service": "jira",
                "resource": "issue",
                "operation": "create",
                "dry_run": False,
                "data": {
                    "project_key": "FTEST",
                    "summary": "Test Issue",
                    "issue_type": "Task"
                }
            }
        )
        print("⚠️  Real operation unexpectedly succeeded:")
        print(result)
    except Exception as e:
        print(f"❌ Real operation failed as expected: {type(e).__name__}: {e}")

    # Test 3: Search operation
    print("\n" + "="*60)
    print("TEST 3: Search operation (should fail with auth error)")
    print("="*60)

    try:
        result = await test_tool_call(
            server,
            "search_engine_tool",
            {
                "service": "jira",
                "query_type": "recent_issues",
                "options": {"limit": 10, "project": "FTEST"}
            }
        )
        print("⚠️  Search operation unexpectedly succeeded:")
        print(result)
    except Exception as e:
        print(f"❌ Search operation failed as expected: {type(e).__name__}: {e}")

    # Test 4: Health check
    print("\n" + "="*60)
    print("TEST 4: Health check (should indicate problems)")
    print("="*60)

    try:
        result = await test_tool_call(
            server,
            "connection_health_check",
            {"dry_run": False}
        )
        print("✅ Health check completed:")
        print(result)

        # Parse and analyze health check
        health_data = json.loads(result)
        overall_status = health_data.get("overall_status")
        print(f"\n📊 Overall health status: {overall_status}")

        if overall_status == "healthy":
            print("⚠️  WARNING: Health check reports healthy despite invalid auth!")
        else:
            print("✅ Health check correctly indicates problems")

    except Exception as e:
        print(f"❌ Health check failed: {type(e).__name__}: {e}")


async def test_tool_call(server: AtlassianMCP, tool_name: str, params: dict):
    """Test calling a tool and return the result."""
    # Find the tool function
    for tool in server._tools:
        if tool.__name__ == tool_name:
            return await tool(**params)

    raise ValueError(f"Tool {tool_name} not found")


if __name__ == "__main__":
    asyncio.run(test_actual_tool_behavior())