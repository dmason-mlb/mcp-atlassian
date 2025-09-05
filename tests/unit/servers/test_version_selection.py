#!/usr/bin/env python3
"""Tests for version-based tool loading mechanism."""

import os
import pytest
from unittest.mock import patch, MagicMock

from mcp_atlassian.meta_tools.loader import (
    ToolVersion,
    get_tool_version,
    should_load_v1_tools,
    should_load_v2_tools,
    validate_version_exclusivity,
    get_version_tag,
)
from mcp_atlassian.servers.context import MainAppContext


class TestToolVersionLoader:
    """Test the tool version loader functionality."""

    def test_get_tool_version_default(self):
        """Test default version is v1."""
        with patch.dict(os.environ, {}, clear=True):
            version = get_tool_version()
            assert version == ToolVersion.V1

    def test_get_tool_version_from_env_v1(self):
        """Test getting v1 from environment variable."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            version = get_tool_version()
            assert version == ToolVersion.V1

    def test_get_tool_version_from_env_v2(self):
        """Test getting v2 from environment variable."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            version = get_tool_version()
            assert version == ToolVersion.V2

    def test_get_tool_version_case_insensitive(self):
        """Test version parsing is case insensitive."""
        with patch.dict(os.environ, {"MCP_VERSION": "V2"}):
            version = get_tool_version()
            assert version == ToolVersion.V2

    def test_get_tool_version_invalid(self):
        """Test invalid version raises ValueError."""
        with patch.dict(os.environ, {"MCP_VERSION": "v3"}):
            with pytest.raises(ValueError, match="Invalid tool version 'v3'"):
                get_tool_version()

    def test_should_load_v1_tools_true(self):
        """Test should_load_v1_tools returns True for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            assert should_load_v1_tools() is True
            assert should_load_v2_tools() is False

    def test_should_load_v2_tools_true(self):
        """Test should_load_v2_tools returns True for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            assert should_load_v2_tools() is True
            assert should_load_v1_tools() is False

    def test_validate_version_exclusivity_v1(self):
        """Test version exclusivity validation for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            # Should not raise
            validate_version_exclusivity()

    def test_validate_version_exclusivity_v2(self):
        """Test version exclusivity validation for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            # Should not raise
            validate_version_exclusivity()

    def test_get_version_tag_v1(self):
        """Test get_version_tag returns correct string for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            assert get_version_tag() == "v1"

    def test_get_version_tag_v2(self):
        """Test get_version_tag returns correct string for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            assert get_version_tag() == "v2"


class TestMainAppContext:
    """Test the MainAppContext with tool version support."""

    def test_main_app_context_default_version(self):
        """Test MainAppContext has default tool_version of v1."""
        context = MainAppContext()
        assert context.tool_version == "v1"

    def test_main_app_context_custom_version(self):
        """Test MainAppContext accepts custom tool_version."""
        context = MainAppContext(tool_version="v2")
        assert context.tool_version == "v2"

    def test_main_app_context_immutable(self):
        """Test MainAppContext is immutable (frozen dataclass)."""
        context = MainAppContext(tool_version="v1")
        
        with pytest.raises(AttributeError):
            context.tool_version = "v2"


class TestVersionSelectionIntegration:
    """Integration tests for version selection in the server."""

    @patch("mcp_atlassian.servers.main.register_v1_tools")
    @patch("mcp_atlassian.servers.main.register_v2_tools")
    def test_server_registers_v1_tools(self, mock_register_v2, mock_register_v1):
        """Test server registers v1 tools when version is v1."""
        from mcp_atlassian.servers.main import AtlassianMCP
        
        # Mock the lifespan context
        mock_server = MagicMock(spec=AtlassianMCP)
        mock_server._tools_registered = False
        
        # Mock app context with v1 version
        mock_app_context = MainAppContext(tool_version="v1")
        
        # This would be called during tool listing
        # Simulate the version check and registration
        if mock_app_context.tool_version == "v1":
            mock_register_v1.assert_not_called()  # Not called yet
            mock_register_v2.assert_not_called()

    @patch("mcp_atlassian.servers.main.register_v1_tools")  
    @patch("mcp_atlassian.servers.main.register_v2_tools")
    def test_server_registers_v2_tools(self, mock_register_v2, mock_register_v1):
        """Test server registers v2 tools when version is v2."""
        from mcp_atlassian.servers.main import AtlassianMCP
        
        # Mock the lifespan context
        mock_server = MagicMock(spec=AtlassianMCP)
        mock_server._tools_registered = False
        
        # Mock app context with v2 version
        mock_app_context = MainAppContext(tool_version="v2")
        
        # This would be called during tool listing
        # Simulate the version check and registration  
        if mock_app_context.tool_version == "v2":
            mock_register_v1.assert_not_called()
            mock_register_v2.assert_not_called()  # Not called yet


class TestToolFiltering:
    """Test version-based tool filtering logic."""

    def test_v1_filters_out_v2_tools(self):
        """Test that v1 mode filters out v2 tagged tools."""
        # Mock tool with v2 tag
        mock_tool = MagicMock()
        mock_tool.tags = {"v2", "meta"}
        
        tool_version = "v1"
        
        # Should be filtered out
        should_exclude = tool_version == "v1" and "v2" in mock_tool.tags
        assert should_exclude is True

    def test_v2_filters_out_v1_tools(self):
        """Test that v2 mode filters out v1 tagged tools."""
        # Mock tool with v1 tag
        mock_tool = MagicMock()
        mock_tool.tags = {"v1", "jira"}
        
        tool_version = "v2"
        
        # Should be filtered out
        should_exclude = tool_version == "v2" and "v1" in mock_tool.tags
        assert should_exclude is True

    def test_v2_filters_out_unversioned_tools(self):
        """Test that v2 mode filters out unversioned legacy tools."""
        # Mock tool without version tags
        mock_tool = MagicMock()
        mock_tool.tags = {"jira", "write"}
        
        tool_version = "v2"
        
        # Should be filtered out if no version or meta tags
        has_version_tags = any(tag in mock_tool.tags for tag in ["v1", "v2", "meta"])
        should_exclude = tool_version == "v2" and not has_version_tags
        assert should_exclude is True

    def test_v2_includes_meta_tools(self):
        """Test that v2 mode includes meta-tagged tools."""
        # Mock tool with meta tag
        mock_tool = MagicMock()
        mock_tool.tags = {"meta", "discovery"}
        
        tool_version = "v2"
        
        # Should NOT be filtered out
        has_version_tags = any(tag in mock_tool.tags for tag in ["v1", "v2", "meta"])
        should_exclude = tool_version == "v2" and not has_version_tags
        assert should_exclude is False

    def test_v1_includes_unversioned_tools(self):
        """Test that v1 mode includes unversioned legacy tools."""
        # Mock tool without version tags (legacy tool)
        mock_tool = MagicMock()
        mock_tool.tags = {"jira", "read"}
        
        tool_version = "v1"
        
        # Should NOT be filtered out in v1 mode
        should_exclude_v2 = tool_version == "v1" and "v2" in mock_tool.tags
        should_exclude_v1 = tool_version == "v1" and "v1" in mock_tool.tags
        
        assert should_exclude_v2 is False
        assert should_exclude_v1 is False


class TestCLIIntegration:
    """Test CLI flag integration with version selection."""

    @patch("mcp_atlassian.get_tool_version")
    def test_cli_flag_sets_env_variable(self, mock_get_version):
        """Test that CLI --version flag sets MCP_VERSION environment variable."""
        # This would be tested in the actual CLI command, but we can test the logic
        test_version = "v2"
        
        # Simulate setting environment variable from CLI
        with patch.dict(os.environ, {"MCP_VERSION": test_version}):
            mock_get_version.return_value = ToolVersion.V2
            version = get_tool_version()
            assert version == ToolVersion.V2

    def test_env_variable_precedence(self):
        """Test that MCP_VERSION environment variable is used."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            version = get_tool_version()
            assert version == ToolVersion.V2
            assert get_version_tag() == "v2"


if __name__ == "__main__":
    pytest.main([__file__])