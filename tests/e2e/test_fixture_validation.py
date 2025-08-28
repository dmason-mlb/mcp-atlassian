"""
Validation test for new MCP-focused fixtures.

This test validates that our new fixture system works correctly
before proceeding to rewrite the main test suites.
"""


import pytest


@pytest.mark.mcp
@pytest.mark.smoke
class TestFixtureValidation:
    """Test that our new MCP-focused fixtures work correctly."""

    def test_config_fixture(self, test_config):
        """Test that test_config fixture provides required configuration."""
        assert isinstance(test_config, dict)

        # Required keys must be present
        required_keys = ["atlassian_url", "jira_project", "confluence_space", "mcp_url"]
        for key in required_keys:
            assert key in test_config
            assert test_config[key] is not None
            assert len(test_config[key].strip()) > 0

    @pytest.mark.asyncio
    async def test_mcp_client_fixture(self, mcp_client):
        """Test that mcp_client fixture provides working MCP client."""
        assert mcp_client is not None
        assert hasattr(mcp_client, "mcp_url")

        # Test basic connectivity
        tools = await mcp_client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_atlassian_stub_fixture(self, atlassian_stub):
        """Test that atlassian_stub fixture provides HTTP mocking."""
        assert atlassian_stub is not None
        assert hasattr(atlassian_stub, "responses")
        assert hasattr(atlassian_stub, "call_log")
        assert hasattr(atlassian_stub, "stub_jira_search")
        assert hasattr(atlassian_stub, "stub_jira_create_issue")
        assert hasattr(atlassian_stub, "stub_confluence_create_page")
        assert hasattr(atlassian_stub, "assert_called_once_with")

    def test_sample_test_data_fixture(self, sample_test_data):
        """Test that sample_test_data fixture provides test content."""
        assert isinstance(sample_test_data, dict)

        # Required test data types
        required_data = [
            "jira_issue",
            "confluence_page",
            "basic_markdown",
            "adf_content",
        ]
        for data_type in required_data:
            assert data_type in sample_test_data
            assert sample_test_data[data_type] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
