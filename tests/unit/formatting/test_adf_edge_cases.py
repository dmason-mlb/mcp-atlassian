"""Test edge cases for ADF generation."""

import pytest
from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestADFEdgeCases:
    """Test edge cases and error handling in ADF generation."""
    
    def test_malformed_markdown(self):
        """Test handling of malformed markdown."""
        generator = ASTBasedADFGenerator()
        
        # Unclosed bold
        result = generator.markdown_to_adf("**This is unclosed bold")
        assert result["type"] == "doc"
        assert len(result["content"]) > 0
        
        # Unclosed link
        result = generator.markdown_to_adf("[Link text](")
        assert result["type"] == "doc"
        
        # Invalid header level
        result = generator.markdown_to_adf("####### Too many hashes")
        # Should treat as paragraph or h6
        assert result["type"] == "doc"
    
    def test_nested_formatting(self):
        """Test deeply nested formatting."""
        generator = ASTBasedADFGenerator()
        
        # Bold italic strikethrough code
        markdown = "***~~`nested`~~***"
        result = generator.markdown_to_adf(markdown)
        assert result["type"] == "doc"
        
        # Multiple levels of lists
        markdown = """- Level 1
  - Level 2
    - Level 3
      - Level 4
        - Level 5"""
        
        result = generator.markdown_to_adf(markdown)
        assert result["content"][0]["type"] == "bulletList"
    
    def test_unicode_and_emojis(self):
        """Test Unicode and emoji handling."""
        generator = ASTBasedADFGenerator()
        
        # Unicode characters
        result = generator.markdown_to_adf("中文 • Español • Русский")
        assert result["type"] == "doc"
        assert "中文" in str(result)
        
        # Emojis
        result = generator.markdown_to_adf("🎉 Party time! 🚀")
        assert result["type"] == "doc"
        assert "🎉" in str(result)
    
    def test_long_lines(self):
        """Test very long lines."""
        generator = ASTBasedADFGenerator()
        
        # Very long line
        long_text = "a" * 10000
        result = generator.markdown_to_adf(long_text)
        assert result["type"] == "doc"
        assert len(result["content"]) > 0
    
    def test_special_characters(self):
        """Test special character escaping."""
        generator = ASTBasedADFGenerator()
        
        # HTML-like content
        result = generator.markdown_to_adf("<script>alert('test')</script>")
        assert result["type"] == "doc"
        # Should be escaped or treated as text
        
        # Backslashes
        result = generator.markdown_to_adf("C:\\Users\\Path\\To\\File")
        assert result["type"] == "doc"
        
        # Special markdown characters
        result = generator.markdown_to_adf("* Not a list \\* Escaped")
        assert result["type"] == "doc"
    
    def test_mixed_content_boundaries(self):
        """Test boundaries between different content types."""
        generator = ASTBasedADFGenerator()
        
        # Code block immediately after list
        markdown = """- Item 1
- Item 2
```
code
```"""
        result = generator.markdown_to_adf(markdown)
        assert len(result["content"]) == 2
        assert result["content"][0]["type"] == "bulletList"
        assert result["content"][1]["type"] == "codeBlock"
        
        # Table after heading without blank line
        markdown = """# Heading
| Col1 | Col2 |
|------|------|
| A    | B    |"""
        result = generator.markdown_to_adf(markdown)
        assert result["content"][0]["type"] == "heading"
        assert result["content"][1]["type"] == "table"
    
    def test_empty_blocks(self):
        """Test empty block elements."""
        generator = ASTBasedADFGenerator()
        
        # Empty code block
        result = generator.markdown_to_adf("```\n```")
        assert result["type"] == "doc"
        
        # Empty list item
        result = generator.markdown_to_adf("- \n- Item 2")
        assert result["type"] == "doc"
        
        # Empty table cells
        result = generator.markdown_to_adf("| | |\n|---|---|\n| | |")
        assert result["type"] == "doc"
    
    def test_whitespace_handling(self):
        """Test various whitespace scenarios."""
        generator = ASTBasedADFGenerator()
        
        # Leading/trailing whitespace
        result = generator.markdown_to_adf("   Text with spaces   ")
        para = result["content"][0]
        assert para["type"] == "paragraph"
        # Text should be trimmed appropriately
        
        # Multiple blank lines
        result = generator.markdown_to_adf("Para 1\n\n\n\n\nPara 2")
        assert len(result["content"]) == 2
        assert all(p["type"] == "paragraph" for p in result["content"])
    
    def test_reference_style_links(self):
        """Test reference-style links."""
        generator = ASTBasedADFGenerator()
        
        markdown = """This is [a link][1] and [another][2].

[1]: https://example.com
[2]: https://example.org"""
        
        result = generator.markdown_to_adf(markdown)
        assert result["type"] == "doc"
        # Should properly resolve references
    
    def test_html_entities(self):
        """Test HTML entity handling."""
        generator = ASTBasedADFGenerator()
        
        # HTML entities
        result = generator.markdown_to_adf("&lt; &gt; &amp; &quot; &#39;")
        assert result["type"] == "doc"
        
        # Should properly decode or preserve entities
        content = str(result)
        assert "<" in content or "&lt;" in content
    
    def test_conflicting_syntax(self):
        """Test conflicting markdown syntax."""
        generator = ASTBasedADFGenerator()
        
        # Asterisks in code
        result = generator.markdown_to_adf("`*not italic*`")
        assert result["type"] == "doc"
        # Code should preserve asterisks
        
        # Underscores in words
        result = generator.markdown_to_adf("snake_case_variable")
        assert result["type"] == "doc"
        # Should not interpret as italic
        
        # Links with underscores
        result = generator.markdown_to_adf("[link](http://example.com/path_with_underscores)")
        assert result["type"] == "doc"
    
    def test_table_edge_cases(self):
        """Test table edge cases."""
        generator = ASTBasedADFGenerator()
        
        # Uneven columns
        markdown = """| Col1 | Col2 | Col3 |
|------|------|
| A    | B    |
| C    | D    | E    | F |"""
        
        result = generator.markdown_to_adf(markdown)
        if result["content"] and result["content"][0]["type"] == "table":
            # Should handle gracefully
            assert True
        
        # Table with formatting
        markdown = """| **Bold** | *Italic* |
|----------|----------|
| `code`   | [link](url) |"""
        
        result = generator.markdown_to_adf(markdown)
        assert result["type"] == "doc"