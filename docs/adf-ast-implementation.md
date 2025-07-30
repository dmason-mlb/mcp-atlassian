# ADF AST-Based Implementation Guide

## Overview

The MCP Atlassian server now uses an AST (Abstract Syntax Tree) based approach for converting markdown to ADF (Atlassian Document Format). This implementation replaces the previous line-by-line parser with a robust, extensible solution built on the `mistune` markdown parser.

## Architecture Overview

### Core Components

1. **ASTBasedADFGenerator** (`adf_ast.py`)
   - Main entry point for markdown to ADF conversion
   - Uses mistune parser with custom ADF renderer
   - Provides caching via `@lru_cache(maxsize=256)`

2. **ADFRenderer** (`adf_ast.py`)
   - Custom mistune renderer that outputs ADF JSON
   - Handles both block-level and inline elements
   - Integrates with the plugin system for extended nodes

3. **Plugin Architecture** (`adf_plugins.py`)
   - Extensible system for adding custom ADF nodes
   - Supports both block and inline plugins
   - Currently includes 8 built-in plugins

4. **FormatRouter** (`router.py`)
   - Routes content to appropriate formatter based on deployment type
   - Now uses ASTBasedADFGenerator for ADF output
   - Maintains backward compatibility with wiki markup

## Key Improvements Over Previous Implementation

### 1. Robust Parsing
- **Before**: Custom line-by-line parser with regex matching
- **After**: AST-based parsing with proper tokenization and context awareness

### 2. Better Error Handling
- **Before**: Fragile parsing that could fail on edge cases
- **After**: Graceful degradation with mistune's robust error recovery

### 3. Performance
- **Before**: O(n²) complexity for nested structures
- **After**: O(n) parsing with efficient tree traversal
- LRU caching for repeated conversions
- Configurable truncation limits for large content

### 4. Extensibility
- **Before**: Hard-coded node types in monolithic parser
- **After**: Plugin-based architecture for easy additions

## Implementation Details

### AST Processing Flow

1. **Markdown Input** → Mistune Parser
2. **Token Stream** → ADFRenderer
3. **Plugin Processing** → For extended nodes
4. **ADF JSON Output** → With validation

### Mistune Integration

The implementation leverages mistune's plugin system:

```python
# Core mistune plugins enabled
plugins = [
    'strikethrough',      # ~~text~~
    'table',             # Markdown tables
    'url',               # Auto-link URLs
    'task_lists',        # - [ ] checkboxes
    'def_list',          # Definition lists
    'abbr',              # Abbreviations
    'mark',              # ==marked text==
    'insert',            # ++inserted++
    'superscript',       # ^super^
    'subscript',         # ~sub~
    adf_extensions       # Custom ADF blocks
]
```

### Custom Block Parsing

ADF-specific blocks are registered with mistune:

```python
# Simple blocks (panel, expand, media)
pattern = r'^:::(panel|expand|media)(?:\\s+([^\\n]+))?\\n([\\s\\S]*?)^:::$'
md.block.register('adf_block', pattern, parse_adf_block, before='fenced_code')

# Layout blocks require special handling
layout_pattern = r'^:::layout(?:\\s|$)'
md.block.register('layout_block', layout_pattern, parse_layout_block, before='fenced_code')
```

### Inline Plugin Processing

Inline plugins are processed after mistune's inline parsing:

1. Text nodes are collected and merged
2. Plugin patterns are matched against plain text
3. Text is split and plugin nodes are inserted
4. Marked text (bold, italic) is preserved

## Supported Elements

### Standard Markdown
- **Headings**: H1-H6 with proper level attributes
- **Paragraphs**: With full inline formatting support
- **Lists**: Bullet and ordered, with deep nesting
- **Code**: Inline and blocks with language detection
- **Tables**: With header detection and cell formatting
- **Quotes**: Blockquotes with nested content
- **Links**: Including reference-style links
- **Images**: Converted to media nodes (requires Confluence IDs)

### Extended Markdown (via mistune plugins)
- **Strikethrough**: `~~text~~`
- **Task Lists**: `- [ ] todo item`
- **Definition Lists**: Term and definition pairs
- **Abbreviations**: `*[HTML]: Hyper Text Markup Language`
- **Marked Text**: `==highlighted==`
- **Superscript/Subscript**: `H~2~O`, `x^2^`

### ADF-Specific Elements (via plugins)

#### Block Plugins
1. **Panel**: Info, warning, error, success, note panels
2. **Expand**: Collapsible content sections
3. **Media**: Confluence media embedding
4. **Layout**: Multi-column layouts

#### Inline Plugins
1. **Status**: Colored status badges
2. **Date**: Date elements with timestamps
3. **Mention**: User mentions
4. **Emoji**: Emoji shortcodes

## Performance Considerations

### Truncation Limits
- **Tables**: Maximum 50 rows (configurable)
- **Lists**: Maximum 100 items (configurable)
- **Nesting**: Maximum 10 levels for lists

### Caching
- LRU cache with 256 entries for repeated conversions
- Cache key based on markdown content hash
- Automatic cache invalidation on content change

### Memory Efficiency
- Streaming token processing (no full AST in memory)
- Lazy evaluation for large structures
- Efficient text merging for inline processing

## Validation

The implementation includes comprehensive ADF validation:

1. **Node Type Validation**: Ensures correct ADF node types
2. **Attribute Validation**: Checks required/optional attributes
3. **Content Validation**: Verifies allowed child nodes
4. **Mark Validation**: Ensures valid mark combinations

Validation levels:
- `ERROR`: Fail conversion on invalid ADF
- `WARN`: Log warnings but continue
- `NONE`: Skip validation (production mode)

## Error Handling

### Graceful Degradation
1. **Parse Errors**: Fall back to paragraph with original text
2. **Plugin Errors**: Skip plugin node, preserve text
3. **Validation Errors**: Return error document with details

### Error Document Format
```json
{
  "version": 1,
  "type": "doc",
  "content": [{
    "type": "paragraph",
    "content": [{
      "type": "text",
      "text": "[ADF Conversion Error] Details..."
    }]
  }]
}
```

## Known Limitations

1. **Inline Plugins in Formatted Text**: Plugins inside bold/italic text are not processed
   - Example: `**@mention**` renders as bold text, not a mention
   - Workaround: Use plugins outside formatting marks

2. **Nested Plugin Blocks**: Complex nesting may not parse correctly
   - Example: Panel inside expand inside layout
   - Workaround: Simplify nesting structure

3. **Media References**: Require Confluence media IDs
   - Cannot directly convert image URLs
   - Must use Confluence's media upload API first

4. **Table Cell Content**: Limited to inline content
   - No block elements (lists, code blocks) in cells
   - This is an ADF limitation, not parser limitation

## Migration from Legacy Parser

### Code Changes

1. **Import Update**:
   ```python
   # Old
   from mcp_atlassian.formatting.adf import ADFGenerator
   
   # New (backward compatible)
   from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator as ADFGenerator
   ```

2. **API Compatibility**:
   - Same `markdown_to_adf()` method signature
   - Same return format (ADF JSON)
   - Drop-in replacement for most use cases

### Behavioral Differences

1. **Stricter Markdown Parsing**: Mistune is more strict about markdown syntax
2. **Better Unicode Handling**: Improved emoji and international character support
3. **Different Edge Case Behavior**: Some malformed markdown may parse differently

## Testing

### Unit Tests
- `test_adf_ast.py`: Core AST generator tests
- `test_adf_ast_plugins.py`: Plugin system tests
- `test_adf_edge_cases.py`: Edge case handling
- `test_adf_performance.py`: Performance benchmarks
- `test_adf_plugin_combinations.py`: Plugin interaction tests

### Integration Tests
- Format router integration
- Jira/Confluence preprocessing
- Real API validation

### Performance Tests
Run performance benchmarks:
```bash
uv run pytest tests/unit/formatting/test_adf_performance.py -v
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger('mcp_atlassian.formatting').setLevel(logging.DEBUG)
```

### Inspect Token Stream
```python
# See mistune tokens before rendering
generator = ASTBasedADFGenerator()
tokens = generator.markdown.parse(markdown_text)
print(tokens)
```

### Validate Output
```python
from mcp_atlassian.formatting.adf_validator import ADFValidator
validator = ADFValidator()
is_valid, errors = validator.validate(adf_output)
```

## Future Enhancements

1. **Streaming Processing**: Process large documents in chunks
2. **Async Rendering**: Parallel processing for independent blocks
3. **Custom Mistune Plugins**: Direct mistune integration for inline plugins
4. **Enhanced Media Support**: Better image/video handling
5. **Table Cell Blocks**: Workaround for ADF limitations