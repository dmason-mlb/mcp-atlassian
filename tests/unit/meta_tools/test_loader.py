#!/usr/bin/env python3
"""Tests for meta_tools loader functionality."""

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
    log_tool_loading_decision,
)


class TestLoaderFunctions:
    """Test the loader utility functions."""

    def test_tool_version_enum_values(self):
        """Test ToolVersion enum has correct values."""
        assert ToolVersion.V1.value == "v1"
        assert ToolVersion.V2.value == "v2"

    def test_get_tool_version_no_env(self):
        """Test get_tool_version with no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            version = get_tool_version()
            assert version == ToolVersion.V1

    def test_get_tool_version_with_env(self):
        """Test get_tool_version with environment variable."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            version = get_tool_version()
            assert version == ToolVersion.V2

    def test_get_tool_version_invalid_value(self):
        """Test get_tool_version with invalid environment variable."""
        with patch.dict(os.environ, {"MCP_VERSION": "invalid"}):
            with pytest.raises(ValueError) as exc_info:
                get_tool_version()
            assert "Invalid tool version 'invalid'" in str(exc_info.value)
            assert "Valid options: ['v1', 'v2']" in str(exc_info.value)

    def test_should_load_functions_v1(self):
        """Test should_load functions for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            assert should_load_v1_tools() is True
            assert should_load_v2_tools() is False

    def test_should_load_functions_v2(self):
        """Test should_load functions for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            assert should_load_v1_tools() is False
            assert should_load_v2_tools() is True

    def test_validate_version_exclusivity_valid(self):
        """Test validate_version_exclusivity with valid configurations."""
        # Test v1
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            validate_version_exclusivity()  # Should not raise

        # Test v2
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            validate_version_exclusivity()  # Should not raise

    def test_get_version_tag_values(self):
        """Test get_version_tag returns correct string values."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            assert get_version_tag() == "v1"

        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            assert get_version_tag() == "v2"

    @patch("mcp_atlassian.meta_tools.loader.logger")
    def test_log_tool_loading_decision_v1(self, mock_logger):
        """Test log_tool_loading_decision for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            log_tool_loading_decision()
            
            # Check that appropriate log messages were called
            mock_logger.info.assert_any_call("Tool version selected: v1 (~42 tools estimated)")
            mock_logger.info.assert_any_call("Loading legacy tools for backward compatibility")

    @patch("mcp_atlassian.meta_tools.loader.logger")
    def test_log_tool_loading_decision_v2(self, mock_logger):
        """Test log_tool_loading_decision for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            log_tool_loading_decision()
            
            # Check that appropriate log messages were called
            mock_logger.info.assert_any_call("Tool version selected: v2 (~10 tools estimated)")
            mock_logger.info.assert_any_call("Loading optimized meta-tools for token efficiency")

    def test_case_insensitive_version_parsing(self):
        """Test that version parsing is case insensitive."""
        test_cases = [
            ("v1", ToolVersion.V1),
            ("V1", ToolVersion.V1), 
            ("v2", ToolVersion.V2),
            ("V2", ToolVersion.V2),
        ]
        
        for env_value, expected_version in test_cases:
            with patch.dict(os.environ, {"MCP_VERSION": env_value}):
                version = get_tool_version()
                assert version == expected_version

    def test_module_exports(self):
        """Test that all expected functions are exported."""
        from mcp_atlassian.meta_tools.loader import __all__
        
        expected_exports = [
            "ToolVersion",
            "get_tool_version", 
            "should_load_v1_tools",
            "should_load_v2_tools",
            "validate_version_exclusivity",
            "get_version_tag",
            "log_tool_loading_decision"
        ]
        
        assert set(__all__) == set(expected_exports)


class TestLoaderEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string_version(self):
        """Test handling of empty string version."""
        with patch.dict(os.environ, {"MCP_VERSION": ""}):
            with pytest.raises(ValueError):
                get_tool_version()

    def test_whitespace_version(self):
        """Test handling of whitespace in version."""
        with patch.dict(os.environ, {"MCP_VERSION": " v1 "}):
            # Should still fail as we don't strip whitespace
            with pytest.raises(ValueError):
                get_tool_version()

    def test_numeric_version(self):
        """Test handling of numeric versions."""
        with patch.dict(os.environ, {"MCP_VERSION": "1"}):
            with pytest.raises(ValueError):
                get_tool_version()

    def test_partial_version(self):
        """Test handling of partial version strings."""
        with patch.dict(os.environ, {"MCP_VERSION": "v"}):
            with pytest.raises(ValueError):
                get_tool_version()

    @patch("mcp_atlassian.meta_tools.loader.logger")
    def test_debug_logging(self, mock_logger):
        """Test that debug logging works correctly."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            version = get_tool_version()
            
            # The function should have logged the determined version
            mock_logger.debug.assert_called_with("Tool version determined: v2")
            assert version == ToolVersion.V2


class TestVersionConsistency:
    """Test consistency between different version functions."""

    def test_version_functions_consistency_v1(self):
        """Test all version functions are consistent for v1."""
        with patch.dict(os.environ, {"MCP_VERSION": "v1"}):
            version_enum = get_tool_version()
            version_tag = get_version_tag()
            should_v1 = should_load_v1_tools()
            should_v2 = should_load_v2_tools()
            
            assert version_enum == ToolVersion.V1
            assert version_tag == "v1"
            assert should_v1 is True
            assert should_v2 is False

    def test_version_functions_consistency_v2(self):
        """Test all version functions are consistent for v2."""
        with patch.dict(os.environ, {"MCP_VERSION": "v2"}):
            version_enum = get_tool_version()
            version_tag = get_version_tag()
            should_v1 = should_load_v1_tools()
            should_v2 = should_load_v2_tools()
            
            assert version_enum == ToolVersion.V2
            assert version_tag == "v2"
            assert should_v1 is False
            assert should_v2 is True

    def test_mutual_exclusivity(self):
        """Test that v1 and v2 are mutually exclusive."""
        for version in ["v1", "v2"]:
            with patch.dict(os.environ, {"MCP_VERSION": version}):
                v1_enabled = should_load_v1_tools()
                v2_enabled = should_load_v2_tools()
                
                # Exactly one should be True
                assert v1_enabled != v2_enabled
                assert (v1_enabled and not v2_enabled) or (not v1_enabled and v2_enabled)


if __name__ == "__main__":
    pytest.main([__file__])