"""Performance tests for ADF generation."""

import time
import pytest
from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestADFPerformance:
    """Test performance characteristics of ADF generation."""
    
    def test_large_document_performance(self):
        """Test performance with large documents."""
        generator = ASTBasedADFGenerator()
        
        # Create a large document
        sections = []
        for i in range(20):
            sections.append(f"""# Section {i}

This is paragraph {i} with **bold** and *italic* text.

## Subsection {i}.1

- List item 1
- List item 2
- List item 3

### Code Example {i}

```python
def function_{i}():
    return "Result {i}"
```

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

> Quote {i}

---
""")
        
        large_markdown = "\n".join(sections)
        
        # Measure conversion time
        start_time = time.time()
        result = generator.markdown_to_adf(large_markdown)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should complete in reasonable time (< 1 second for 20 sections)
        assert conversion_time < 1.0
        assert result["type"] == "doc"
        assert len(result["content"]) > 100  # Many blocks
        
        # Log performance for monitoring
        print(f"Large document ({len(large_markdown)} chars) converted in {conversion_time:.3f}s")
    
    def test_deep_nesting_performance(self):
        """Test performance with deeply nested structures."""
        generator = ASTBasedADFGenerator()
        
        # Create deeply nested lists
        nested_list = "- Level 1\n"
        indent = "  "
        for i in range(2, 11):  # 10 levels deep
            nested_list += f"{indent * (i-1)}- Level {i}\n"
        
        start_time = time.time()
        result = generator.markdown_to_adf(nested_list)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should handle deep nesting efficiently
        assert conversion_time < 0.1
        assert result["type"] == "doc"
    
    def test_table_performance(self):
        """Test performance with large tables."""
        generator = ASTBasedADFGenerator(max_table_rows=100)
        
        # Create a large table (50 rows x 10 columns)
        header = "| " + " | ".join([f"Col{i}" for i in range(10)]) + " |"
        separator = "|" + "|".join(["---" for _ in range(10)]) + "|"
        rows = []
        for r in range(50):
            row = "| " + " | ".join([f"R{r}C{c}" for c in range(10)]) + " |"
            rows.append(row)
        
        table_markdown = "\n".join([header, separator] + rows)
        
        start_time = time.time()
        result = generator.markdown_to_adf(table_markdown)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should handle large tables efficiently
        assert conversion_time < 0.5
        assert result["type"] == "doc"
        
        # Table should be truncated at max_table_rows
        if result["content"] and result["content"][0]["type"] == "table":
            # First row is header, so content rows = total - 1
            assert len(result["content"][0]["content"]) <= 51  # 50 + header
    
    def test_repeated_conversion_performance(self):
        """Test performance of repeated conversions (caching)."""
        generator = ASTBasedADFGenerator()
        
        markdown = """# Test Document

This is a test with **formatting** and [links](https://example.com).

- List item 1
- List item 2"""
        
        # First conversion (cold)
        start_time = time.time()
        result1 = generator.markdown_to_adf(markdown)
        cold_time = time.time() - start_time
        
        # Repeated conversions (should benefit from any caching)
        warm_times = []
        for _ in range(5):
            start_time = time.time()
            result = generator.markdown_to_adf(markdown)
            warm_times.append(time.time() - start_time)
        
        avg_warm_time = sum(warm_times) / len(warm_times)
        
        # Warm conversions should be at least as fast as cold
        assert avg_warm_time <= cold_time * 1.1  # Allow 10% variance
        
        # All results should be identical
        assert result1 == result
    
    def test_plugin_performance(self):
        """Test performance with plugin-heavy content."""
        generator = ASTBasedADFGenerator()
        
        # Create content with many plugin blocks
        plugin_content = """# Document with Plugins

:::panel type="info"
This is an info panel with content.
:::

:::expand title="Expandable Section"
Hidden content here with **formatting**.
:::

:::media
type: image
id: test-123
:::

:::layout columns=3
::: column
Column 1 content
:::
::: column
Column 2 content
:::
::: column
Column 3 content
:::
:::

Regular paragraph with @mentions and :emoji: and {status:Green} markers.
"""
        
        # Repeat the content
        large_plugin_doc = (plugin_content + "\n") * 10
        
        start_time = time.time()
        result = generator.markdown_to_adf(large_plugin_doc)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should handle plugins efficiently
        assert conversion_time < 0.5
        assert result["type"] == "doc"
        
        # Check that plugins were processed
        block_types = {block["type"] for block in result["content"] if isinstance(block, dict)}
        assert "panel" in block_types
        assert "expand" in block_types
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large documents."""
        generator = ASTBasedADFGenerator()
        
        # Create a document with many repeated elements
        # This tests if we're creating unnecessary copies
        repeated_para = "This is a paragraph. " * 100
        sections = []
        for i in range(50):
            sections.append(f"## Section {i}\n\n{repeated_para}\n")
        
        large_doc = "\n".join(sections)
        
        # Should complete without memory issues
        result = generator.markdown_to_adf(large_doc)
        assert result["type"] == "doc"
        assert len(result["content"]) == 100  # 50 headings + 50 paragraphs
    
    def test_pathological_input_performance(self):
        """Test performance with pathological inputs."""
        generator = ASTBasedADFGenerator()
        
        # Many unclosed brackets (regex catastrophic backtracking)
        pathological = "[" * 100 + "text" + "]" * 50
        
        start_time = time.time()
        result = generator.markdown_to_adf(pathological)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should complete in reasonable time even with bad input
        assert conversion_time < 1.0
        assert result["type"] == "doc"
    
    @pytest.mark.parametrize("size", [10, 50, 100, 500])
    def test_scaling_performance(self, size):
        """Test how performance scales with document size."""
        generator = ASTBasedADFGenerator()
        
        # Create document of specified size
        content = []
        for i in range(size):
            content.append(f"Paragraph {i} with **bold** and *italic* text.")
        
        markdown = "\n\n".join(content)
        
        start_time = time.time()
        result = generator.markdown_to_adf(markdown)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Performance should scale roughly linearly
        # Allow up to 2ms per paragraph
        assert conversion_time < size * 0.002
        assert len(result["content"]) == size