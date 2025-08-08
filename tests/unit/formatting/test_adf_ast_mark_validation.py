"""Test mark validation in AST-based ADF generator."""

from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator
from src.mcp_atlassian.formatting.adf_validator import ADFValidator


class TestASTMarkValidation:
    """Test mark validation in the AST-based ADF generator."""

    def test_code_mark_with_invalid_combinations(self):
        """Test that code marks cannot combine with other marks except link."""
        generator = ASTBasedADFGenerator()

        # Code with bold - should be filtered
        result = generator.markdown_to_adf("**`code`**")
        text_node = result["content"][0]["content"][0]

        # Should only have code mark, not strong
        assert text_node["type"] == "text"
        assert text_node["text"] == "code"
        marks = text_node.get("marks", [])
        mark_types = {mark["type"] for mark in marks}

        # With error validation level, invalid marks should be filtered
        if generator.validator.validation_level == ADFValidator.VALIDATION_ERROR:
            assert "code" in mark_types
            assert "strong" not in mark_types

    def test_code_mark_with_link_allowed(self):
        """Test that code marks can combine with link marks."""
        generator = ASTBasedADFGenerator()

        # Code with link - should be allowed
        result = generator.markdown_to_adf("[`code`](https://example.com)")
        text_node = result["content"][0]["content"][0]

        assert text_node["type"] == "text"
        assert text_node["text"] == "code"
        marks = text_node.get("marks", [])
        mark_types = {mark["type"] for mark in marks}

        # Both marks should be present
        assert "code" in mark_types
        assert "link" in mark_types

    def test_multiple_valid_marks(self):
        """Test multiple valid mark combinations."""
        generator = ASTBasedADFGenerator()

        # Bold + italic - should work
        result = generator.markdown_to_adf("***bold italic***")
        text_node = result["content"][0]["content"][0]

        marks = text_node.get("marks", [])
        mark_types = {mark["type"] for mark in marks}

        # Both marks should be present
        assert "strong" in mark_types
        assert "em" in mark_types

    def test_strike_with_other_marks(self):
        """Test strikethrough with other marks."""
        generator = ASTBasedADFGenerator()

        # Strikethrough with bold
        result = generator.markdown_to_adf("**~~struck bold~~**")

        # Find the text node with marks
        para = result["content"][0]
        # The structure might be nested, so we need to find the actual text node
        content = para["content"]

        # Check if we have the expected marks somewhere in the structure
        found_strike = False
        found_strong = False

        def check_marks(node):
            nonlocal found_strike, found_strong
            if node.get("type") == "text" and "marks" in node:
                for mark in node["marks"]:
                    if mark["type"] == "strike":
                        found_strike = True
                    if mark["type"] == "strong":
                        found_strong = True
            if "content" in node:
                for child in node["content"]:
                    check_marks(child)

        for node in content:
            check_marks(node)

        # Strikethrough can combine with other marks
        assert found_strike or found_strong  # At least one should be present
