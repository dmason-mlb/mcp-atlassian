"""
Basic connectivity and smoke tests for MCP Atlassian E2E testing.

These tests validate that:
1. MCP server is accessible
2. Authentication is working
3. Basic tools are available
4. Environment configuration is correct
"""


import pytest


@pytest.mark.smoke
@pytest.mark.api
class TestMCPConnectivity:
    """Test basic MCP server connectivity and authentication."""

    @pytest.mark.asyncio
    async def test_mcp_server_connection(self, mcp_client):
        """Test that MCP server is accessible."""
        # Client fixture already validates connection, so this passes if we get here
        assert mcp_client is not None
        assert mcp_client.session is not None

    @pytest.mark.asyncio
    async def test_list_available_tools(self, mcp_client):
        """Test that MCP server returns available tools."""
        tools = await mcp_client.list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Each tool should have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool

    @pytest.mark.asyncio
    async def test_jira_tools_available(self, mcp_client):
        """Test that Jira-related tools are available."""
        tools = await mcp_client.list_tools()
        tool_names = [tool["name"] for tool in tools]

        # Check for essential Jira tools
        expected_jira_tools = [
            "jira_issues_create_issue",
            "jira_update_issue",
            "jira_add_comment",
            "jira_search",
        ]

        missing_tools = [tool for tool in expected_jira_tools if tool not in tool_names]
        assert not missing_tools, f"Missing Jira tools: {missing_tools}"

    @pytest.mark.asyncio
    async def test_confluence_tools_available(self, mcp_client):
        """Test that Confluence-related tools are available."""
        tools = await mcp_client.list_tools()
        tool_names = [tool["name"] for tool in tools]

        # Check for essential Confluence tools
        expected_confluence_tools = [
            "confluence_pages_create_page",
            "confluence_pages_update_page",
            "confluence_content_add_comment",
            "confluence_search_search",
        ]

        missing_tools = [
            tool for tool in expected_confluence_tools if tool not in tool_names
        ]
        assert not missing_tools, f"Missing Confluence tools: {missing_tools}"


@pytest.mark.smoke
@pytest.mark.api
class TestEnvironmentConfiguration:
    """Test environment configuration and setup."""

    def test_required_config_present(self, test_config):
        """Test that required configuration values are present."""
        required_keys = [
            "atlassian_url",
            "jira_project",
            "confluence_space",
            "mcp_url",
        ]

        for key in required_keys:
            assert key in test_config
            assert test_config[key] is not None
            assert len(test_config[key].strip()) > 0

    def test_atlassian_url_format(self, test_config):
        """Test that Atlassian URL is properly formatted."""
        url = test_config["atlassian_url"]

        assert url.startswith("https://")
        assert ".atlassian.net" in url or "atlassian.com" in url or "://" in url

    def test_test_label_unique(self, test_config):
        """Test that test label is unique for this run."""
        label = test_config["test_label"]

        assert label.startswith("mcp-test-")
        assert len(label) > len("mcp-test-")


@pytest.mark.smoke
@pytest.mark.api
class TestBasicToolExecution:
    """Test basic tool execution without side effects."""

    @pytest.mark.asyncio
    async def test_jira_search_basic(self, mcp_client, test_config):
        """Test basic Jira search functionality."""
        project_key = test_config["jira_project"]

        # Search for any issues in the project (should not create anything)
        result = await mcp_client.search_jira(jql=f"project = {project_key}", limit=1)

        # Should return search result structure
        assert isinstance(result, dict)
        assert "issues" in result or "total" in result or "startAt" in result

    @pytest.mark.asyncio
    async def test_confluence_search_basic(self, mcp_client, test_config):
        """Test basic Confluence search functionality."""
        space_key = test_config["confluence_space"]

        # Search in the space (should not create anything)
        result = await mcp_client.search_confluence(
            query=f"space = {space_key}", limit=1
        )

        # Should return search result structure
        assert isinstance(result, dict)
        # Note: Confluence search may return empty results, but should have structure


@pytest.mark.smoke
@pytest.mark.api
class TestAuthenticationValidation:
    """Test that authentication is working correctly."""

    @pytest.mark.asyncio
    async def test_authenticated_jira_access(self, mcp_client, test_config):
        """Test that we can access Jira with current authentication."""
        project_key = test_config["jira_project"]

        try:
            # Try to search for issues - requires authentication
            result = await mcp_client.search_jira(
                jql=f"project = {project_key}", limit=1
            )

            # If we get here without exception, auth is working
            assert isinstance(result, dict)

        except Exception as e:
            # If authentication fails, provide helpful error
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "forbidden" in error_msg:
                pytest.fail(f"Authentication failed for Jira: {e}")
            else:
                # Re-raise other exceptions
                raise

    @pytest.mark.asyncio
    async def test_authenticated_confluence_access(self, mcp_client, test_config):
        """Test that we can access Confluence with current authentication."""
        space_key = test_config["confluence_space"]

        try:
            # Try to search - requires authentication
            result = await mcp_client.search_confluence(
                query=f"space = {space_key}", limit=1
            )

            # If we get here without exception, auth is working
            assert isinstance(result, dict)

        except Exception as e:
            # If authentication fails, provide helpful error
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "forbidden" in error_msg:
                pytest.fail(f"Authentication failed for Confluence: {e}")
            else:
                # Re-raise other exceptions
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
