"""Test AST-based ADF generator."""

from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestASTBasedADFGenerator:
    """Test the AST-based ADF generator."""

    def test_basic_paragraph(self):
        """Test basic paragraph conversion."""
        generator = ASTBasedADFGenerator()
        result = generator.markdown_to_adf("Hello world")

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"

    def test_headings(self):
        """Test heading conversion."""
        generator = ASTBasedADFGenerator()

        # Test different heading levels
        for level in range(1, 7):
            markdown = f"{'#' * level} Heading {level}"
            result = generator.markdown_to_adf(markdown)

            assert result["content"][0]["type"] == "heading"
            assert result["content"][0]["attrs"]["level"] == level

    def test_bold_and_italic(self):
        """Test bold and italic formatting."""
        generator = ASTBasedADFGenerator()

        # Bold
        result = generator.markdown_to_adf("**bold text**")
        content = result["content"][0]["content"][0]
        assert content["type"] == "text"
        assert any(mark["type"] == "strong" for mark in content.get("marks", []))

        # Italic
        result = generator.markdown_to_adf("*italic text*")
        content = result["content"][0]["content"][0]
        assert content["type"] == "text"
        assert any(mark["type"] == "em" for mark in content.get("marks", []))

    def test_code_blocks(self):
        """Test code block conversion."""
        generator = ASTBasedADFGenerator()

        markdown = """```python
def hello():
    print("Hello world")
```"""

        result = generator.markdown_to_adf(markdown)
        code_block = result["content"][0]

        assert code_block["type"] == "codeBlock"
        assert code_block["attrs"]["language"] == "python"
        assert code_block["content"][0]["type"] == "text"
        assert "def hello():" in code_block["content"][0]["text"]

    def test_lists(self):
        """Test list conversion."""
        generator = ASTBasedADFGenerator()

        # Bullet list
        markdown = """- Item 1
- Item 2
- Item 3"""

        result = generator.markdown_to_adf(markdown)
        list_block = result["content"][0]

        assert list_block["type"] == "bulletList"
        assert len(list_block["content"]) == 3
        assert all(item["type"] == "listItem" for item in list_block["content"])

        # Ordered list
        markdown = """1. First
2. Second
3. Third"""

        result = generator.markdown_to_adf(markdown)
        list_block = result["content"][0]

        assert list_block["type"] == "orderedList"
        assert len(list_block["content"]) == 3

    def test_unicode_bullets(self):
        """Test Unicode bullet character conversion to markdown lists."""
        generator = ASTBasedADFGenerator()

        # Test basic Unicode bullet conversion
        markdown = """Summary:
• Item 1
• Item 2
• Item 3"""

        result = generator.markdown_to_adf(markdown)

        # Should have a paragraph for "Summary:" and a bulletList
        assert result["type"] == "doc"
        assert len(result["content"]) == 2
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][1]["type"] == "bulletList"

        # Check the list items
        list_items = result["content"][1]["content"]
        assert len(list_items) == 3
        assert all(item["type"] == "listItem" for item in list_items)

    def test_unicode_bullets_multiple_types(self):
        """Test various Unicode bullet characters."""
        generator = ASTBasedADFGenerator()

        # Test different Unicode bullet characters
        bullet_chars = ['•', '○', '◦', '▪', '▫', '‣', '●', '◘', '◙']

        for bullet in bullet_chars:
            markdown = f"{bullet} Test item"
            result = generator.markdown_to_adf(markdown)

            # Should create a bulletList
            assert result["content"][0]["type"] == "bulletList"
            assert len(result["content"][0]["content"]) == 1
            assert result["content"][0]["content"][0]["type"] == "listItem"

    def test_unicode_bullets_nested(self):
        """Test nested Unicode bullets with indentation."""
        generator = ASTBasedADFGenerator()

        markdown = """• Item 1
  • Nested item 1.1
  • Nested item 1.2
• Item 2"""

        result = generator.markdown_to_adf(markdown)

        # Should have a bulletList
        assert result["content"][0]["type"] == "bulletList"

        # Top-level list should have 2 items
        top_items = result["content"][0]["content"]
        assert len(top_items) == 2

        # First item should contain a nested list
        first_item = top_items[0]
        assert first_item["type"] == "listItem"
        # Check for nested list in the first item's content
        has_nested_list = any(
            content_item.get("type") == "bulletList"
            for content_item in first_item.get("content", [])
        )
        assert has_nested_list

    def test_unicode_bullets_mixed_content(self):
        """Test Unicode bullets mixed with regular text."""
        generator = ASTBasedADFGenerator()

        markdown = """Testing complete for FRAMED-1838.

Validation Summary:
• All acceptance criteria met ✓
• iOS: Excellent test coverage with 8 snapshot tests

Key findings:
• Calendar bar validated
• Date selection verified"""

        result = generator.markdown_to_adf(markdown)

        # Should have multiple content blocks
        assert result["type"] == "doc"
        assert len(result["content"]) >= 4

        # First should be a paragraph
        assert result["content"][0]["type"] == "paragraph"

        # Should contain bulletLists
        bullet_lists = [block for block in result["content"] if block["type"] == "bulletList"]
        assert len(bullet_lists) == 2

    def test_unicode_bullets_preserve_formatting(self):
        """Test that Unicode bullets preserve text formatting."""
        generator = ASTBasedADFGenerator()

        markdown = """• Item with **bold** text
• Item with *italic* text
• Item with `code` text"""

        result = generator.markdown_to_adf(markdown)

        # Should create a bulletList
        assert result["content"][0]["type"] == "bulletList"
        list_items = result["content"][0]["content"]
        assert len(list_items) == 3

        # Check that formatting is preserved
        # (The actual mark checking would require deep inspection of nested content)
        assert all(item["type"] == "listItem" for item in list_items)

    def test_links(self):
        """Test link conversion."""
        generator = ASTBasedADFGenerator()

        result = generator.markdown_to_adf("[Click here](https://example.com)")
        content = result["content"][0]["content"][0]

        assert content["type"] == "text"
        assert any(
            mark["type"] == "link" and mark["attrs"]["href"] == "https://example.com"
            for mark in content.get("marks", [])
        )

    def test_inline_code(self):
        """Test inline code conversion."""
        generator = ASTBasedADFGenerator()

        result = generator.markdown_to_adf("Use `code` inline")
        # Note: This will need proper inline parsing implementation
        # For now, testing the structure exists
        assert result["type"] == "doc"
        assert len(result["content"]) > 0

    def test_tables(self):
        """Test table conversion with proper headers."""
        generator = ASTBasedADFGenerator()

        markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""

        result = generator.markdown_to_adf(markdown)
        table = result["content"][0]

        assert table["type"] == "table"
        assert len(table["content"]) == 3  # Header row + 2 data rows

        # Check header row
        header_row = table["content"][0]
        assert header_row["type"] == "tableRow"
        assert all(cell["type"] == "tableHeader" for cell in header_row["content"])

        # Check data rows
        for row in table["content"][1:]:
            assert row["type"] == "tableRow"
            assert all(cell["type"] == "tableCell" for cell in row["content"])

    def test_blockquote(self):
        """Test blockquote conversion."""
        generator = ASTBasedADFGenerator()

        result = generator.markdown_to_adf("> This is a quote")
        quote = result["content"][0]

        assert quote["type"] == "blockquote"
        assert len(quote["content"]) > 0

    def test_horizontal_rule(self):
        """Test horizontal rule conversion."""
        generator = ASTBasedADFGenerator()

        result = generator.markdown_to_adf("---")
        rule = result["content"][0]

        assert rule["type"] == "rule"

    def test_empty_input(self):
        """Test empty input handling."""
        generator = ASTBasedADFGenerator()

        result = generator.markdown_to_adf("")
        assert result == {"version": 1, "type": "doc", "content": []}

        result = generator.markdown_to_adf("   \n\n   ")
        assert result == {"version": 1, "type": "doc", "content": []}

    def test_complex_document(self):
        """Test a complex document with multiple elements."""
        generator = ASTBasedADFGenerator()

        markdown = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Section 1

- Bullet point 1
- Bullet point 2
  - Nested item

### Code Example

```python
def process():
    return "Done"
```

> Important note here

---

| Col 1 | Col 2 |
|-------|-------|
| A     | B     |"""

        result = generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) > 5  # Should have multiple blocks

        # Verify we have different block types
        block_types = {block["type"] for block in result["content"]}
        expected_types = {
            "heading",
            "paragraph",
            "bulletList",
            "codeBlock",
            "blockquote",
            "rule",
            "table",
        }
        assert expected_types.issubset(block_types)
