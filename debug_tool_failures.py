#!/usr/bin/env python3
"""Debug script to reproduce the tool failures reported in QA testing.

This script will help identify why resource_manager_tool and search_engine_tool
are failing with generic "Error calling tool" messages while batch_processor_tool works.
"""

import asyncio
import json
import sys
from unittest.mock import Mock, AsyncMock

# Add src to path
sys.path.insert(0, 'src')

from src.mcp_atlassian.servers.main import AtlassianMCP, register_v2_tools
from src.mcp_atlassian.servers.context import MainAppContext
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig


async def setup_test_server():
    """Set up a test server similar to the QA environment."""
    print("Setting up test server...")

    # Create server instance
    server = AtlassianMCP(name="Debug Test Atlassian MCP")

    # Create minimal configuration to reproduce QA issues
    mock_lifespan_state = Mock()
    mock_lifespan_state.read_only = False
    mock_lifespan_state.enabled_tools = None

    # Create config objects with auto-extracted cloud_id
    from src.mcp_atlassian.utils.oauth import OAuthConfig

    # Create OAuth config with auto-extracted cloud_id
    oauth_config = OAuthConfig(
        client_id="",
        client_secret="",
        redirect_uri="",
        scope="",
        cloud_id="baseball"  # Auto-extracted from baseball.atlassian.net
    )

    mock_jira_config = JiraConfig(
        url="https://baseball.atlassian.net",
        auth_type="oauth",
        oauth_config=oauth_config,
    )
    mock_confluence_config = ConfluenceConfig(
        url="https://baseball.atlassian.net",
        auth_type="oauth",
        oauth_config=oauth_config,
    )

    mock_lifespan_state.full_jira_config = mock_jira_config
    mock_lifespan_state.full_confluence_config = mock_confluence_config

    # Mock the server context with proper setup
    server._mcp_server = Mock()
    server._mcp_server.request_context = Mock()
    server._mcp_server.request_context.lifespan_context = {
        "app_lifespan_context": mock_lifespan_state
    }

    # Mock application context that should provide working services
    mock_app_context = Mock()
    mock_app_context.jira_client = Mock()
    mock_app_context.confluence_client = Mock()
    server.ctx = mock_app_context

    # Register tools
    print("Registering v2 tools...")
    try:
        register_v2_tools(server)
        print("✅ Tools registered successfully")
    except Exception as e:
        print(f"❌ Tool registration failed: {e}")
        raise

    return server


async def test_tool_invocation(server, tool_name, params):
    """Test if a tool can be invoked without errors."""
    print(f"\n🔧 Testing {tool_name}...")
    print(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        # This simulates how the MCP framework would call the tool
        result = await server._mcp_call_tool(tool_name, params)
        print(f"✅ {tool_name} succeeded")
        print(f"Result type: {type(result)}")
        if isinstance(result, list) and len(result) > 0:
            content = result[0].text if hasattr(result[0], 'text') else str(result[0])
            print(f"Content preview: {content[:200]}...")
        else:
            print(f"Result: {str(result)[:200]}...")
        return True

    except Exception as e:
        print(f"❌ {tool_name} failed with error: {e}")
        print(f"Error type: {type(e)}")
        return False


async def main():
    """Main debug function to test tool failures."""
    print("🔍 Debug Tool Failures - Reproducing QA Report Issues")
    print("=" * 60)

    # Set up test server
    try:
        server = await setup_test_server()
    except Exception as e:
        print(f"❌ Failed to set up server: {e}")
        return

    # Test parameters that should work according to QA report
    test_cases = [
        {
            "tool": "batch_processor_tool",
            "params": {
                "service": "jira",
                "operation": "create",
                "resource": "issue",
                "items": [{
                    "project_key": "FTEST",
                    "summary": "Debug Test Issue",
                    "issue_type": "Task"
                }]
            }
        },
        {
            "tool": "resource_manager_tool",
            "params": {
                "service": "jira",
                "resource": "issue",
                "operation": "create",
                "data": {
                    "project_key": "FTEST",
                    "summary": "Debug Test Issue",
                    "issue_type": "Task"
                }
            }
        },
        {
            "tool": "search_engine_tool",
            "params": {
                "service": "jira",
                "query_type": "jql",
                "query": "project = FTEST"
            }
        },
        {
            "tool": "resource_manager_tool",
            "params": {
                "service": "confluence",
                "resource": "page",
                "operation": "create",
                "data": {
                    "space_key": "~911651470",
                    "title": "Debug Test Page",
                    "body": "Test content"
                }
            }
        }
    ]

    # Test each case
    results = {}
    for test_case in test_cases:
        tool_name = test_case["tool"]
        params = test_case["params"]

        success = await test_tool_invocation(server, tool_name, params)
        results[f"{tool_name}_{params.get('service', 'unknown')}"] = success

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF RESULTS:")
    print("=" * 60)

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")

    # Check if we reproduced the QA issues
    batch_success = results.get("batch_processor_tool_jira", False)
    resource_success = results.get("resource_manager_tool_jira", False)
    search_success = results.get("search_engine_tool_jira", False)
    confluence_success = results.get("resource_manager_tool_confluence", False)

    print(f"\n🔍 QA ISSUE REPRODUCTION:")
    if batch_success and not resource_success:
        print("✅ Reproduced: Batch Processor works but Resource Manager fails")
    if not search_success:
        print("✅ Reproduced: Search Engine fails")
    if not confluence_success:
        print("✅ Reproduced: Confluence operations fail")

    if not resource_success or not search_success or not confluence_success:
        print("\n❌ QA Issues successfully reproduced - now we can debug them!")
    else:
        print("\n🤔 Could not reproduce QA issues - they may already be fixed?")


if __name__ == "__main__":
    asyncio.run(main())