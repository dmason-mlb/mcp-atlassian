"""Test ADF plugin architecture."""

import re

from src.mcp_atlassian.formatting.adf_plugins import (
    BaseADFPlugin,
    PanelPlugin,
    PluginRegistry,
    registry,
)


class TestPanelPlugin:
    """Test the PanelPlugin implementation."""

    def test_panel_pattern_matching(self):
        """Test that panel pattern correctly matches panel blocks."""
        plugin = PanelPlugin()
        pattern = plugin.block_pattern

        # Test basic panel
        text = """:::panel type="info"
This is panel content
:::"""
        match = pattern.search(text)
        assert match is not None
        assert match.group(1) == "info"
        assert match.group(2).strip() == "This is panel content"

        # Test panel without type (should default)
        text = """:::panel
Default panel
:::"""
        match = pattern.search(text)
        assert match is not None
        assert match.group(1) is None
        assert match.group(2).strip() == "Default panel"

        # Test all panel types
        for panel_type in ["info", "note", "warning", "success", "error"]:
            text = f''':::panel type="{panel_type}"
Content for {panel_type}
:::'''
            match = pattern.search(text)
            assert match is not None
            assert match.group(1) == panel_type

    def test_panel_parse_and_render(self):
        """Test parsing and rendering of panel blocks."""
        plugin = PanelPlugin()

        # Mock render_content function
        def mock_render_content(content, block_mode=False):
            return [
                {"type": "paragraph", "content": [{"type": "text", "text": content}]}
            ]

        # Test info panel
        text = """:::panel type="info"
Information panel content
:::"""
        match = plugin.block_pattern.search(text)
        data = plugin.parse_block(match, text)

        assert data["type"] == "panel"
        assert data["panel_type"] == "info"
        assert data["content"] == "Information panel content"

        # Render to ADF
        node = plugin.render_block(data, mock_render_content)

        assert node["type"] == "panel"
        assert node["attrs"]["panelType"] == "info"
        assert len(node["content"]) == 1
        assert node["content"][0]["type"] == "paragraph"

    def test_panel_validation(self):
        """Test panel node validation."""
        plugin = PanelPlugin()

        # Valid panel
        valid_node = {
            "type": "panel",
            "attrs": {"panelType": "info"},
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}
            ],
        }
        is_valid, errors = plugin.validate(valid_node)
        assert is_valid
        assert len(errors) == 0

        # Invalid panel type
        invalid_type_node = {
            "type": "panel",
            "attrs": {"panelType": "custom"},
            "content": [{"type": "paragraph", "content": []}],
        }
        is_valid, errors = plugin.validate(invalid_type_node)
        assert not is_valid
        assert any("Invalid panelType" in e for e in errors)

        # Missing content
        no_content_node = {
            "type": "panel",
            "attrs": {"panelType": "info"},
            "content": [],
        }
        is_valid, errors = plugin.validate(no_content_node)
        assert not is_valid
        assert any("must have content" in e for e in errors)

        # Invalid content type
        invalid_content_node = {
            "type": "panel",
            "attrs": {"panelType": "info"},
            "content": [{"type": "codeBlock", "content": []}],
        }
        is_valid, errors = plugin.validate(invalid_content_node)
        assert not is_valid
        assert any("cannot contain codeBlock" in e for e in errors)


class TestPluginRegistry:
    """Test the PluginRegistry functionality."""

    def test_plugin_registration(self):
        """Test registering and unregistering plugins."""
        registry = PluginRegistry()
        plugin = PanelPlugin()

        # Register plugin
        registry.register(plugin)
        assert "panel" in registry.plugins
        assert plugin in registry.get_block_plugins()
        assert plugin not in registry.get_inline_plugins()

        # Unregister plugin
        registry.unregister("panel")
        assert "panel" not in registry.plugins
        assert plugin not in registry.get_block_plugins()

    def test_process_block_text(self):
        """Test processing text for block plugins."""
        registry = PluginRegistry()
        registry.register(PanelPlugin())

        def mock_render_content(content, block_mode=False):
            return [
                {"type": "paragraph", "content": [{"type": "text", "text": content}]}
            ]

        text = """:::panel type="warning"
This is a warning
:::"""

        nodes = registry.process_block_text(text, mock_render_content)

        assert len(nodes) == 1
        assert nodes[0]["type"] == "panel"
        assert nodes[0]["attrs"]["panelType"] == "warning"

    def test_multiple_plugins(self):
        """Test registry with multiple plugins."""

        # Create a mock inline plugin
        class MockInlinePlugin(BaseADFPlugin):
            @property
            def name(self):
                return "mock_inline"

            @property
            def block_pattern(self):
                return None

            @property
            def inline_pattern(self):
                return re.compile(r"\[mock:(\w+)\]")

            def parse_block(self, match, content):
                raise NotImplementedError()

            def parse_inline(self, match):
                return {"type": "mock", "value": match.group(1)}

            def render_block(self, data, render_content):
                raise NotImplementedError()

            def render_inline(self, data):
                return {"type": "mock", "text": data["value"]}

        registry = PluginRegistry()
        registry.register(PanelPlugin())
        registry.register(MockInlinePlugin())

        assert len(registry.plugins) == 2
        assert len(registry.get_block_plugins()) == 1
        assert len(registry.get_inline_plugins()) == 1


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_panel_plugin_registered(self):
        """Test that PanelPlugin is registered by default."""
        assert "panel" in registry.plugins
        assert isinstance(registry.plugins["panel"], PanelPlugin)
