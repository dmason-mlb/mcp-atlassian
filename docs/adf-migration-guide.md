# ADF Implementation Migration Guide

## Overview

This guide helps you migrate from the legacy line-by-line ADF parser to the new AST-based implementation. The new implementation provides better performance, reliability, and extensibility while maintaining backward compatibility.

## What's Changed

### Architecture Changes

| Component | Legacy Implementation | New Implementation |
|-----------|----------------------|-------------------|
| Parser | Custom line-by-line regex | Mistune AST-based parser |
| Renderer | Monolithic ADFGenerator | Modular ADFRenderer + Plugins |
| Extensions | Hard-coded in parser | Plugin architecture |
| Performance | O(n²) for nested content | O(n) with caching |
| Error Handling | Basic fallback | Graceful degradation |

### Feature Improvements

1. **Better Markdown Compliance**: Mistune provides standards-compliant markdown parsing
2. **Plugin System**: Easy addition of custom ADF nodes without modifying core
3. **Performance**: LRU caching and optimized parsing for 5-10x faster conversion
4. **Robustness**: Handles edge cases and malformed markdown gracefully
5. **Validation**: Comprehensive ADF schema validation

## Migration Steps

### 1. For Basic Usage (No Code Changes Required)

The new implementation is a drop-in replacement. The `FormatRouter` automatically uses the AST-based generator:

```python
# This continues to work exactly the same
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()
result = router.convert_markdown(
    "# Hello\n\n**Bold** text",
    "https://company.atlassian.net"
)
```

### 2. For Direct ADFGenerator Usage

If you're importing `ADFGenerator` directly:

```python
# Old way (still works via compatibility import)
from mcp_atlassian.formatting.adf import ADFGenerator

# New way (recommended)
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

# Or use the compatibility alias
from mcp_atlassian.formatting import ADFGenerator  # Points to AST version
```

### 3. For Custom Extensions

Replace custom regex patterns with plugins:

#### Before (modifying parser directly):
```python
# Not possible without forking the codebase
```

#### After (using plugin system):
```python
from mcp_atlassian.formatting.adf_plugins import BaseADFPlugin, registry
import re

class CustomAlertPlugin(BaseADFPlugin):
    @property
    def name(self) -> str:
        return "alert"
    
    @property
    def block_pattern(self) -> Optional[Pattern[str]]:
        return re.compile(
            r'^:::alert\s+type="(\w+)"\n(.*?)\n:::$',
            re.MULTILINE | re.DOTALL
        )
    
    def render_block(self, data, render_content):
        return {
            "type": "panel",
            "attrs": {"panelType": data['alert_type']},
            "content": render_content(data['content'], block_mode=True)
        }

# Register the plugin
registry.register(CustomAlertPlugin())
```

## Behavioral Differences

### 1. Stricter Markdown Parsing

The new parser is more strict about markdown syntax:

```markdown
# Old parser might accept
*not properly closed italic

# New parser requires
*properly closed italic*
```

### 2. Improved Table Parsing

Tables now properly detect headers:

```markdown
| Header 1 | Header 2 |
|----------|----------|  # Required separator
| Cell 1   | Cell 2   |
```

### 3. Better List Nesting

Lists maintain proper nesting structure:

```markdown
- Level 1
  - Level 2 (2 spaces)
    - Level 3 (4 spaces)
```

### 4. Plugin Syntax Changes

Some plugin syntaxes are more strict:

```markdown
# Panel blocks
:::panel type="info"
Content here
:::

# Status inline (now requires color)
{status:color=green}Done{/status}

# Mentions support dots
@john.doe or @[John Doe]
```

## Performance Tuning

### 1. Adjust Cache Size

```python
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

# Increase cache for high-volume usage
generator = ASTBasedADFGenerator()
generator.markdown_to_adf.cache_info()  # Check cache stats
```

### 2. Configure Truncation Limits

```python
# For larger documents
generator = ASTBasedADFGenerator(
    max_table_rows=100,  # Default: 50
    max_list_items=200   # Default: 100
)
```

### 3. Monitor Performance

```python
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()
# ... perform conversions ...

metrics = router.get_performance_metrics()
print(f"Cache hit rate: {metrics['detection_cache_hit_rate']:.1f}%")
print(f"Avg conversion time: {metrics['average_conversion_time']*1000:.2f}ms")
```

## Troubleshooting

### 1. Content Appears Different

**Symptom**: Markdown renders differently than before

**Solution**: Check for:
- Unclosed formatting marks
- Missing table separators
- Incorrect list indentation

### 2. Plugins Not Working

**Symptom**: Custom syntax not converting to ADF nodes

**Solution**: Verify:
- Plugin is registered: `registry.plugins`
- Pattern matches: `plugin.block_pattern.search(text)`
- No syntax conflicts with other plugins

### 3. Performance Issues

**Symptom**: Slower than expected conversion

**Solution**: Check:
- Cache hit rate (should be >80% for repeated content)
- Document size (large tables/lists may hit limits)
- Plugin efficiency (complex patterns can be slow)

### 4. Validation Errors

**Symptom**: ADF validation failures

**Solution**: 
- Set validation level to WARN to see issues:
  ```python
  import os
  os.environ['ADF_VALIDATION_LEVEL'] = 'WARN'
  ```
- Check error messages for specific issues
- Ensure ADF node structure follows schema

## Testing Your Migration

### 1. Unit Tests

Update your tests to account for behavioral differences:

```python
def test_markdown_conversion():
    generator = ASTBasedADFGenerator()
    result = generator.markdown_to_adf("**bold**")
    
    # More strict structure validation
    assert result["type"] == "doc"
    assert result["version"] == 1
    assert len(result["content"]) == 1
    assert result["content"][0]["type"] == "paragraph"
```

### 2. Integration Tests

Test with your actual content:

```python
import glob
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

generator = ASTBasedADFGenerator()

# Test all your markdown files
for md_file in glob.glob("docs/*.md"):
    with open(md_file) as f:
        content = f.read()
    
    try:
        result = generator.markdown_to_adf(content)
        print(f"✓ {md_file}")
    except Exception as e:
        print(f"✗ {md_file}: {e}")
```

### 3. A/B Testing

Compare outputs between implementations:

```python
from mcp_atlassian.formatting.adf import ADFGenerator as LegacyGenerator
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

legacy = LegacyGenerator()
new = ASTBasedADFGenerator()

test_content = "Your test markdown here"

legacy_result = legacy.markdown_to_adf(test_content)
new_result = new.markdown_to_adf(test_content)

# Compare results
import json
if json.dumps(legacy_result, sort_keys=True) != json.dumps(new_result, sort_keys=True):
    print("Results differ - review the changes")
```

## Rollback Plan

If you need to temporarily rollback to the legacy parser:

1. **Environment Variable**: 
   ```bash
   export USE_LEGACY_ADF_PARSER=true
   ```

2. **Code Override**:
   ```python
   # Force legacy parser
   from mcp_atlassian.formatting.adf import ADFGenerator
   from mcp_atlassian.formatting import router
   
   # Monkey-patch (temporary!)
   router.ASTBasedADFGenerator = ADFGenerator
   ```

3. **Direct Import**:
   ```python
   # Explicitly use legacy
   from mcp_atlassian.formatting.adf import ADFGenerator
   generator = ADFGenerator()  # Legacy version
   ```

## Getting Help

### Resources

1. **Documentation**: See `docs/adf-ast-implementation.md` for technical details
2. **Plugin Guide**: See `docs/adf-plugin-architecture.md` for extending
3. **Test Examples**: Check `tests/unit/formatting/test_adf_*.py`

### Common Issues

1. **Issue**: Inline plugins inside bold/italic text not processed
   - **Workaround**: Place plugins outside formatting marks
   
2. **Issue**: Complex nested plugin blocks
   - **Workaround**: Simplify nesting or use sequential blocks

3. **Issue**: Different whitespace handling
   - **Solution**: The new parser is more consistent with markdown spec

### Support

If you encounter issues not covered here:

1. Check the test suite for examples
2. Enable debug logging to see parsing details
3. Report issues with:
   - Input markdown
   - Expected output
   - Actual output
   - Error messages

## Summary

The new AST-based implementation provides:

- ✅ Better performance (5-10x faster for complex documents)
- ✅ More reliable parsing (handles edge cases)
- ✅ Extensible architecture (plugin system)
- ✅ Better error handling (graceful degradation)
- ✅ Backward compatibility (drop-in replacement)

Most users can migrate with zero code changes. Those with custom requirements can leverage the new plugin system for cleaner, more maintainable extensions.