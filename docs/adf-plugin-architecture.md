# ADF Plugin Architecture

## Overview

The ADF (Atlassian Document Format) plugin architecture provides an extensible system for adding custom node types to the markdown-to-ADF conversion process. This architecture allows for easy addition of new ADF node types without modifying the core parser.

## Architecture Components

### BaseADFPlugin

The foundation of the plugin system is the `BaseADFPlugin` abstract base class that all plugins must extend:

```python
class BaseADFPlugin(ABC):
    """Base class for ADF node plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the plugin."""
        pass
    
    @property
    @abstractmethod
    def block_pattern(self) -> Optional[Pattern[str]]:
        """Regex pattern for block-level node detection."""
        pass
    
    @property
    @abstractmethod
    def inline_pattern(self) -> Optional[Pattern[str]]:
        """Regex pattern for inline node detection."""
        pass
```

### Plugin Types

Plugins can be categorized into two types:

1. **Block Plugins**: Handle block-level nodes (panels, expands, media, layouts)
2. **Inline Plugins**: Handle inline nodes (status, date, mention, emoji)

### Plugin Registry

The `PluginRegistry` manages all registered plugins:

```python
registry = PluginRegistry()

# Register plugins
registry.register(PanelPlugin())
registry.register(StatusPlugin())
```

## Built-in Plugins

### 1. PanelPlugin

Creates ADF panel nodes with different types (info, note, warning, success, error).

**Syntax:**
```markdown
:::panel type="info"
This is an informational panel.

It can have multiple paragraphs.
:::
```

**Output ADF:**
```json
{
  "type": "panel",
  "attrs": {
    "panelType": "info"
  },
  "content": [
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "This is an informational panel."}]
    }
  ]
}
```

### 2. MediaPlugin

Embeds media content (images, videos, files) with Confluence-specific attributes.

**Syntax:**
```markdown
:::media
type: image
id: confluence-media-id
collection: contentId-123456
width: 800
height: 600
layout: center
:::
```

### 3. ExpandPlugin

Creates collapsible content sections.

**Syntax:**
```markdown
:::expand title="Click to expand"
Hidden content that can be expanded.

Supports multiple paragraphs and formatting.
:::
```

### 4. StatusPlugin

Creates inline status badges.

**Syntax:**
```markdown
{status:color=green}Done{/status}
{status:color=yellow}In Progress{/status}
{status:color=red}Blocked{/status}
```

### 5. DatePlugin

Inserts date elements with timestamps.

**Syntax:**
```markdown
{date:2025-01-30}
```

### 6. MentionPlugin

Creates user mentions.

**Syntax:**
```markdown
@username
@[John Doe]
@john.doe
```

### 7. EmojiPlugin

Adds emoji support.

**Syntax:**
```markdown
:smile:
:thumbsup:
:warning:
```

### 8. LayoutPlugin

Creates multi-column layouts.

**Syntax:**
```markdown
:::layout columns=2
::: column
First column content.
:::
::: column
Second column content.
:::
:::
```

## Creating Custom Plugins

### Step 1: Define Your Plugin Class

```python
from mcp_atlassian.formatting.adf_plugins import BaseADFPlugin
import re

class CustomPlugin(BaseADFPlugin):
    """Plugin for custom ADF nodes."""
    
    @property
    def name(self) -> str:
        return "custom"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        # Return regex pattern for block-level matching
        return re.compile(r'^:::custom\s*\n(.*?)\n:::$', re.MULTILINE | re.DOTALL)
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        # Return None for block-only plugins
        return None
```

### Step 2: Implement Parse Methods

```python
def parse_block(self, match: re.Match[str], content: str) -> Dict[str, Any]:
    """Parse block match into plugin data."""
    return {
        'type': 'custom',
        'content': match.group(1).strip()
    }

def parse_inline(self, match: re.Match[str]) -> Dict[str, Any]:
    """Parse inline match (not used for block-only plugins)."""
    raise NotImplementedError("Custom is a block-only node")
```

### Step 3: Implement Render Methods

```python
def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
    """Render plugin data to ADF node."""
    # render_content is a function to process nested markdown
    inline_content = render_content(data['content'])
    
    return {
        "type": "customBlock",
        "content": [{
            "type": "paragraph",
            "content": inline_content
        }]
    }

def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Render inline data (not used for block-only plugins)."""
    raise NotImplementedError("Custom is a block-only node")
```

### Step 4: Register Your Plugin

```python
from mcp_atlassian.formatting.adf_plugins import registry

# Register the plugin
registry.register(CustomPlugin())
```

## Integration with AST Generator

The plugin system is integrated with the AST-based ADF generator in two ways:

### 1. Block Plugin Integration

Block plugins are processed through mistune's block parser extensions:

```python
# In adf_extensions function
pattern = r'^:::(panel|expand|media)(?:\\s+([^\\n]+))?\\n([\\s\\S]*?)^:::$'
md.block.register('adf_block', pattern, parse_adf_block, before='fenced_code')
```

Special handling for layout blocks:

```python
# Layout blocks need special parsing due to nested ::: markers
md.block.register('layout_block', layout_pattern, parse_layout_block, before='fenced_code')
```

### 2. Inline Plugin Integration

Inline plugins are processed after mistune's inline parsing:

```python
def _process_inline_plugins(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process inline nodes for plugin patterns."""
    # Merge adjacent text nodes first
    merged_nodes = self._merge_text_nodes(nodes)
    
    # Process each text node for plugin matches
    for node in merged_nodes:
        if node.get('type') == 'text' and not node.get('marks'):
            # Collect all plugin matches
            all_matches = self._collect_plugin_matches(node['text'])
            # Split text and insert plugin nodes
            result.extend(self._split_and_render(node['text'], all_matches))
```

## Plugin Validation

Plugins can implement validation to ensure generated ADF nodes are valid:

```python
def validate(self, node: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the rendered ADF node."""
    errors = []
    
    if node.get('type') != 'expectedType':
        errors.append("Invalid node type")
    
    # Additional validation logic
    
    return len(errors) == 0, errors
```

## Best Practices

1. **Pattern Design**: Use non-greedy patterns and proper flags (MULTILINE, DOTALL)
2. **Error Handling**: Gracefully handle parsing errors and invalid input
3. **Content Rendering**: Always use the provided `render_content` function for nested markdown
4. **Validation**: Implement thorough validation to ensure ADF compliance
5. **Performance**: Consider caching for expensive operations

## Examples

### Creating a Custom Alert Plugin

```python
class AlertPlugin(BaseADFPlugin):
    """Plugin for custom alert boxes."""
    
    @property
    def name(self) -> str:
        return "alert"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return re.compile(
            r'^:::alert(?:\s+level="(low|medium|high|critical)")?\\s*\\n'
            r'(.*?)\\n'
            r'^:::$',
            re.MULTILINE | re.DOTALL
        )
    
    def render_block(self, data: Dict[str, Any], render_content) -> Dict[str, Any]:
        level = data.get('level', 'medium')
        color_map = {
            'low': 'green',
            'medium': 'yellow', 
            'high': 'orange',
            'critical': 'red'
        }
        
        return {
            "type": "panel",
            "attrs": {"panelType": color_map.get(level, 'note')},
            "content": [{
                "type": "paragraph",
                "content": render_content(data['content'])
            }]
        }
```

### Creating an Inline Variable Plugin

```python
class VariablePlugin(BaseADFPlugin):
    """Plugin for inline variables."""
    
    @property
    def name(self) -> str:
        return "variable"
    
    @property
    def inline_pattern(self) -> Optional[Pattern[str]]:
        return re.compile(r'\{\{(\w+)\}\}')
    
    def render_inline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "text",
            "text": f"[{data['var_name']}]",
            "marks": [{"type": "code"}]
        }
```

## Debugging Tips

1. **Enable Debug Logging**:
   ```python
   import logging
   logging.getLogger('mcp_atlassian.formatting').setLevel(logging.DEBUG)
   ```

2. **Test Patterns Independently**:
   ```python
   pattern = plugin.block_pattern
   match = pattern.search(test_text)
   if match:
       print(f"Matched: {match.groups()}")
   ```

3. **Validate Output**:
   ```python
   from mcp_atlassian.formatting.adf_validator import ADFValidator
   validator = ADFValidator()
   is_valid, errors = validator.validate(adf_output)
   ```

## Future Enhancements

1. **Dynamic Plugin Loading**: Load plugins from external modules
2. **Plugin Configuration**: Allow plugins to accept configuration parameters
3. **Plugin Dependencies**: Support plugins that depend on other plugins
4. **Async Rendering**: Support for async plugin rendering
5. **Plugin Marketplace**: Central repository for community plugins