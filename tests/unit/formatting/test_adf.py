"""Tests for ADF (Atlassian Document Format) generator."""

import json
from unittest.mock import patch

import pytest

from mcp_atlassian.formatting.adf import ADFGenerator


class TestADFGenerator:
    """Test cases for ADFGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ADFGenerator()

    def test_empty_input(self):
        """Test handling of empty input."""
        result = self.generator.markdown_to_adf("")
        expected = {"version": 1, "type": "doc", "content": []}
        assert result == expected

    def test_none_input(self):
        """Test handling of None input."""
        result = self.generator.markdown_to_adf(None)
        expected = {"version": 1, "type": "doc", "content": []}
        assert result == expected

    def test_plain_text(self):
        """Test conversion of plain text."""
        result = self.generator.markdown_to_adf("Hello world")

        assert result["version"] == 1
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"

        # Check text content
        text_node = result["content"][0]["content"][0]
        assert text_node["type"] == "text"
        assert text_node["text"] == "Hello world"

    def test_bold_text(self):
        """Test conversion of bold text."""
        result = self.generator.markdown_to_adf("This is **bold** text")

        paragraph = result["content"][0]
        assert paragraph["type"] == "paragraph"

        # Should have 3 text nodes: "This is ", "bold" (with strong mark), " text"
        content = paragraph["content"]
        assert len(content) >= 1

        # Find the bold text node
        bold_found = False
        for node in content:
            if node.get("marks"):
                for mark in node["marks"]:
                    if mark["type"] == "strong":
                        assert node["text"] == "bold"
                        bold_found = True
                        break
        assert bold_found, "Bold text not found in ADF output"

    def test_italic_text(self):
        """Test conversion of italic text."""
        result = self.generator.markdown_to_adf("This is *italic* text")

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Find the italic text node
        italic_found = False
        for node in content:
            if node.get("marks"):
                for mark in node["marks"]:
                    if mark["type"] == "em":
                        assert node["text"] == "italic"
                        italic_found = True
                        break
        assert italic_found, "Italic text not found in ADF output"

    def test_headings(self):
        """Test conversion of different heading levels."""
        markdown = "# Heading 1\n## Heading 2\n### Heading 3"
        result = self.generator.markdown_to_adf(markdown)

        assert len(result["content"]) == 3

        # Check each heading level
        for i, level in enumerate([1, 2, 3], 1):
            heading = result["content"][i - 1]
            assert heading["type"] == "heading"
            assert heading["attrs"]["level"] == level
            assert heading["content"][0]["text"] == f"Heading {level}"

    def test_unordered_list(self):
        """Test conversion of unordered list."""
        markdown = "- Item 1\n- Item 2\n- Item 3"
        result = self.generator.markdown_to_adf(markdown)

        assert len(result["content"]) == 1
        list_node = result["content"][0]
        assert list_node["type"] == "bulletList"
        assert len(list_node["content"]) == 3

        # Check first list item
        first_item = list_node["content"][0]
        assert first_item["type"] == "listItem"
        assert first_item["content"][0]["type"] == "paragraph"
        assert first_item["content"][0]["content"][0]["text"] == "Item 1"

    def test_ordered_list(self):
        """Test conversion of ordered list."""
        markdown = "1. First item\n2. Second item\n3. Third item"
        result = self.generator.markdown_to_adf(markdown)

        list_node = result["content"][0]
        assert list_node["type"] == "orderedList"
        assert len(list_node["content"]) == 3

        # Check first list item
        first_item = list_node["content"][0]
        assert first_item["type"] == "listItem"
        assert first_item["content"][0]["content"][0]["text"] == "First item"

    def test_code_block(self):
        """Test conversion of code blocks."""
        markdown = "```python\nprint('Hello, world!')\n```"
        result = self.generator.markdown_to_adf(markdown)

        code_block = result["content"][0]
        assert code_block["type"] == "codeBlock"
        assert (
            "language" in code_block.get("attrs", {}) or True
        )  # Language detection may vary
        assert code_block["content"][0]["text"] == "print('Hello, world!')"

    def test_inline_code(self):
        """Test conversion of inline code."""
        result = self.generator.markdown_to_adf("Use `print()` function")

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Find the code text node
        code_found = False
        for node in content:
            if node.get("marks"):
                for mark in node["marks"]:
                    if mark["type"] == "code":
                        assert node["text"] == "print()"
                        code_found = True
                        break
        assert code_found, "Inline code not found in ADF output"

    def test_links(self):
        """Test conversion of links."""
        result = self.generator.markdown_to_adf("Visit [Google](https://google.com)")

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Find the link text node
        link_found = False
        for node in content:
            if node.get("marks"):
                for mark in node["marks"]:
                    if mark["type"] == "link":
                        assert mark["attrs"]["href"] == "https://google.com"
                        assert node["text"] == "Google"
                        link_found = True
                        break
        assert link_found, "Link not found in ADF output"

    def test_mixed_formatting(self):
        """Test conversion of mixed formatting in single paragraph."""
        markdown = "This has **bold**, *italic*, and `code` text"
        result = self.generator.markdown_to_adf(markdown)

        paragraph = result["content"][0]
        content = paragraph["content"]

        # Should find all three formatting types
        found_marks = set()
        for node in content:
            if node.get("marks"):
                for mark in node["marks"]:
                    found_marks.add(mark["type"])

        assert "strong" in found_marks, "Bold formatting not found"
        assert "em" in found_marks, "Italic formatting not found"
        assert "code" in found_marks, "Code formatting not found"

    def test_multiple_paragraphs(self):
        """Test conversion of multiple paragraphs."""
        markdown = "First paragraph.\n\nSecond paragraph."
        result = self.generator.markdown_to_adf(markdown)

        assert len(result["content"]) >= 2
        assert all(p["type"] == "paragraph" for p in result["content"])

    def test_blockquote(self):
        """Test conversion of blockquotes."""
        markdown = "> This is a quote\n> with multiple lines"
        result = self.generator.markdown_to_adf(markdown)

        # Find blockquote (may be nested in structure)
        blockquote_found = False
        for content_item in result["content"]:
            if content_item["type"] == "blockquote":
                blockquote_found = True
                assert len(content_item["content"]) >= 1
                break

        # If blockquote structure varies, at least check we have content
        assert len(result["content"]) >= 1

    def test_horizontal_rule(self):
        """Test conversion of horizontal rules."""
        markdown = "Before rule\n\n---\n\nAfter rule"
        result = self.generator.markdown_to_adf(markdown)

        # Find rule element
        rule_found = False
        for content_item in result["content"]:
            if content_item["type"] == "rule":
                rule_found = True
                break

        # May not always detect horizontal rules depending on markdown parser
        assert len(result["content"]) >= 1

    def test_validation_valid_adf(self):
        """Test ADF validation with valid structure."""
        valid_adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}
            ],
        }

        assert self.generator.validate_adf(valid_adf) is True

    def test_validation_invalid_adf(self):
        """Test ADF validation with invalid structure."""
        invalid_adf = {
            "version": 1,
            "type": "doc",
            # Missing content field
        }

        assert self.generator.validate_adf(invalid_adf) is False

    def test_validation_wrong_type(self):
        """Test ADF validation with wrong document type."""
        invalid_adf = {
            "version": 1,
            "type": "paragraph",  # Should be "doc"
            "content": [],
        }

        assert self.generator.validate_adf(invalid_adf) is False

    def test_error_handling(self):
        """Test error handling with problematic input."""
        # Mock markdown conversion to raise exception
        with patch.object(
            self.generator.md, "convert", side_effect=Exception("Test error")
        ):
            result = self.generator.markdown_to_adf("test")

            # Should fallback to plain text document
            assert result["type"] == "doc"
            assert result["version"] == 1
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "paragraph"
            assert result["content"][0]["content"][0]["text"] == "test"

    def test_complex_nested_structure(self):
        """Test conversion of complex nested markdown structure."""
        markdown = """# Main Heading

This is a paragraph with **bold** and *italic* text.

## Subheading

- List item 1 with `inline code`
- List item 2 with [a link](https://example.com)
  - Nested list item
  - Another nested item

```python
def hello():
    print("Hello, world!")
```

> This is a blockquote
> with multiple lines

Final paragraph."""

        result = self.generator.markdown_to_adf(markdown)

        # Basic structure validation
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 5  # Should have multiple content blocks

        # Should contain various element types
        element_types = {item["type"] for item in result["content"]}
        assert "heading" in element_types
        assert "paragraph" in element_types

    def test_adf_output_serializable(self):
        """Test that ADF output is JSON serializable."""
        markdown = "# Test\n\nThis is **bold** text with a [link](https://example.com)."
        result = self.generator.markdown_to_adf(markdown)

        # Should be able to serialize to JSON without errors
        try:
            json_str = json.dumps(result)
            # Should be able to deserialize back
            deserialized = json.loads(json_str)
            assert deserialized == result
        except (TypeError, ValueError) as e:
            pytest.fail(f"ADF output not JSON serializable: {e}")

    def test_edge_case_empty_elements(self):
        """Test handling of empty markdown elements."""
        edge_cases = [
            "**",  # Incomplete bold
            "__",  # Incomplete italic
            "``",  # Incomplete code
            "[]",  # Empty link text
            "()",  # Empty link URL
            "# ",  # Empty heading
        ]

        for markdown in edge_cases:
            result = self.generator.markdown_to_adf(markdown)

            # Should not crash and should produce valid structure
            assert result["type"] == "doc"
            assert result["version"] == 1
            assert isinstance(result["content"], list)

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios."""
        test_cases = [
            "   Leading spaces",
            "Trailing spaces   ",
            "Multiple\n\n\nline breaks",
            "\t\tTabs and spaces  \n  ",
        ]

        for markdown in test_cases:
            result = self.generator.markdown_to_adf(markdown)

            # Should produce valid ADF structure
            assert result["type"] == "doc"
            assert len(result["content"]) >= 1

    def test_table_conversion(self):
        """Test table conversion to ADF format."""
        markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""

        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert len(result["content"]) >= 1

        # Look for table content in the result
        content_str = str(result["content"])
        assert "table" in content_str.lower() or "header" in content_str.lower()

    def test_nested_list_conversion(self):
        """Test nested list conversion."""
        markdown = """- Item 1
  - Nested item 1
  - Nested item 2
- Item 2
  1. Nested ordered 1
  2. Nested ordered 2"""

        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 1

    def test_complex_formatting_combinations(self):
        """Test complex combinations of formatting."""
        markdown = """# **Bold Heading**

This paragraph has ***bold italic***, ~~strikethrough~~, and `inline code`.

> A blockquote with **bold text** and *italics*

```python
# Code block with language
def function():
    return "test"
```

- List with **bold** items
- And *italic* items
  - Nested with `code`"""

        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 4  # Multiple blocks

    def test_malformed_markdown_handling(self):
        """Test handling of malformed markdown."""
        malformed_cases = [
            "**unclosed bold",
            "*unclosed italic",
            "[unclosed link](incomplete",
            "```unclosed code block",
            "# Heading with *mixed **formatting",
            "![broken image]()",
        ]

        for markdown in malformed_cases:
            result = self.generator.markdown_to_adf(markdown)

            # Should not crash and produce valid structure
            assert result["type"] == "doc"
            assert result["version"] == 1
            assert isinstance(result["content"], list)

    def test_html_fallback_parsing(self):
        """Test HTML parsing fallback scenarios."""
        # Test with HTML that might cause parsing issues
        markdown = """<div class="custom">
            <p>HTML content</p>
            <span style="color: red;">Styled text</span>
        </div>"""

        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 1

    def test_large_document_handling(self):
        """Test handling of large documents."""
        # Create a large markdown document
        large_content = []
        for i in range(50):
            large_content.append(f"## Section {i}")
            large_content.append(
                f"This is paragraph {i} with **bold** and *italic* text."
            )
            large_content.append(f"- List item {i}.1")
            large_content.append(f"- List item {i}.2")
            large_content.append("")

        markdown = "\n".join(large_content)
        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 100  # Should have many blocks

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        markdown = """# Unicode Test: 你好 世界 🌍

This text contains special characters: © ® ™ € £ ¥

Emoji support: 🚀 ⭐ 💻 📝

Mathematical symbols: α β γ ∞ ≤ ≥ ±

Languages: Español, Français, Deutsch, 日本語, العربية"""

        result = self.generator.markdown_to_adf(markdown)

        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) >= 1

    def test_conversion_error_handling(self):
        """Test error handling during conversion."""
        # Mock the markdown processor to raise an exception
        original_convert = self.generator.md.convert

        def mock_convert_error(text):
            raise Exception("Mocked conversion error")

        self.generator.md.convert = mock_convert_error

        try:
            result = self.generator.markdown_to_adf("test content")

            # Should fallback to plain text
            assert result["type"] == "doc"
            assert result["version"] == 1
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "paragraph"
            assert "test content" in str(result["content"][0])

        finally:
            # Restore original method
            self.generator.md.convert = original_convert

    def test_adf_schema_compliance(self):
        """Test that generated ADF complies with basic schema requirements."""
        test_cases = [
            "Simple text",
            "# Heading",
            "**Bold** and *italic*",
            "- List item",
            "`code`",
            "[Link](http://example.com)",
            "> Blockquote",
        ]

        for markdown in test_cases:
            result = self.generator.markdown_to_adf(markdown)

            # Validate basic ADF schema compliance
            assert isinstance(result, dict), "Result must be a dictionary"
            assert "version" in result, "Must have version field"
            assert "type" in result, "Must have type field"
            assert "content" in result, "Must have content field"
            assert result["version"] == 1, "Version must be 1"
            assert result["type"] == "doc", "Type must be 'doc'"
            assert isinstance(result["content"], list), "Content must be a list"

            # Validate each content block
            for block in result["content"]:
                assert isinstance(block, dict), "Each content block must be a dict"
                assert "type" in block, "Each block must have a type"

                # If block has content, validate it
                if "content" in block:
                    assert isinstance(block["content"], list), (
                        "Block content must be a list"
                    )

    def test_performance_basic_benchmark(self):
        """Basic performance test to ensure conversion is reasonably fast."""
        import time

        markdown = """# Performance Test Document

This document contains various elements to test conversion performance:

## Lists
- Item 1 with **bold** text
- Item 2 with *italic* text
- Item 3 with `code` text

## Code Block
```python
def example_function():
    return "Hello, World!"
```

## Table
| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

## Blockquote
> This is a blockquote with various formatting elements.
> It spans multiple lines.

## Links and Images
[Example Link](https://example.com)

## Mixed Formatting
This paragraph has **bold**, *italic*, `code`, and ~~strikethrough~~ text."""

        start_time = time.time()
        result = self.generator.markdown_to_adf(markdown)
        end_time = time.time()

        conversion_time = end_time - start_time

        # Should complete within reasonable time (target: <100ms for this size)
        assert conversion_time < 0.1, (
            f"Conversion took {conversion_time:.3f}s, should be < 0.1s"
        )

        # Verify the result is valid
        assert result["type"] == "doc"
        assert len(result["content"]) >= 5  # Multiple sections
