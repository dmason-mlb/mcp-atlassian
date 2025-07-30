"""Test plugin integration with AST generator."""

import pytest
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator
from mcp_atlassian.formatting.adf_plugins import registry


def test_plugin_registry_populated():
    """Test that all expected plugins are registered."""
    expected_plugins = {
        'panel', 'media', 'expand', 'status', 
        'date', 'mention', 'emoji', 'layout'
    }
    
    registered_plugins = set(registry.plugins.keys())
    assert expected_plugins == registered_plugins


def test_block_plugins_registered():
    """Test that block plugins are properly categorized."""
    block_plugins = registry.get_block_plugins()
    block_plugin_names = {p.name for p in block_plugins}
    
    expected_block = {'panel', 'media', 'expand', 'layout'}
    assert expected_block == block_plugin_names


def test_inline_plugins_registered():
    """Test that inline plugins are properly categorized."""
    inline_plugins = registry.get_inline_plugins()
    inline_plugin_names = {p.name for p in inline_plugins}
    
    expected_inline = {'status', 'date', 'mention', 'emoji'}
    assert expected_inline == inline_plugin_names


def test_plugin_integration_with_ast():
    """Test that plugins work with the AST generator."""
    generator = ASTBasedADFGenerator()
    
    # Test all plugins in one document
    markdown = """:::panel type="info"
# Project Update

Last updated: {date:2025-01-30}

:::expand title="Details"
Status: {status:color=green}On Track{/status} :thumbsup:
Lead: @john.doe
:::

:::layout columns=2
::: column
## Development
Progress is good.
:::
::: column  
## Testing
QA in progress.
:::
:::

Contact @[Jane Smith] for questions :smile:
:::"""
    
    result = generator.markdown_to_adf(markdown)
    
    # Verify structure
    assert result['type'] == 'doc'
    assert result['version'] == 1
    
    # Check panel exists
    panel = result['content'][0]
    assert panel['type'] == 'panel'
    assert panel['attrs']['panelType'] == 'info'
    
    # Check content has various plugin nodes
    content_str = str(result)
    assert 'date' in content_str
    assert 'status' in content_str
    assert 'mention' in content_str
    assert 'emoji' in content_str
    assert 'expand' in content_str
    assert 'layout' in content_str


def test_plugin_error_handling():
    """Test that plugin errors don't crash the parser."""
    generator = ASTBasedADFGenerator()
    
    # Malformed plugin syntax should still produce output
    markdown = """:::panel
Content

{status:color=invalid}Test{/status}

{date:not-a-date}

@

:not_an_emoji:
"""
    
    result = generator.markdown_to_adf(markdown)
    
    # Should still produce a valid document
    assert result['type'] == 'doc'
    assert len(result['content']) > 0


def test_nested_plugin_content():
    """Test plugins with nested markdown content."""
    generator = ASTBasedADFGenerator()
    
    markdown = """:::panel type="warning"
## Warning Panel

This panel contains:
- **Bold text**
- *Italic text*
- `Code snippets`
- [Links](https://example.com)

And inline plugins: {status:color=red}Critical{/status}
:::"""
    
    result = generator.markdown_to_adf(markdown)
    
    # Check panel
    panel = result['content'][0]
    assert panel['type'] == 'panel'
    assert panel['attrs']['panelType'] == 'warning'
    
    # Verify nested content is properly rendered
    content_str = str(panel)
    assert 'heading' in content_str
    assert 'bulletList' in content_str
    assert 'strong' in content_str
    assert 'em' in content_str
    assert 'code' in content_str
    assert 'link' in content_str
    assert 'status' in content_str