"""Test table header detection in ADF conversion."""

from src.mcp_atlassian.formatting.adf import ADFGenerator


class TestADFTableHeaders:
    """Test that table headers are properly detected and converted to tableHeader nodes."""

    def test_table_with_headers(self):
        """Test that th elements are converted to tableHeader nodes."""
        generator = ADFGenerator()

        # Markdown table with headers
        markdown = """
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""

        result = generator.markdown_to_adf(markdown)

        # Verify it's a valid ADF document
        assert result["type"] == "doc"
        assert result["version"] == 1

        # Find the table
        table = None
        for node in result["content"]:
            if node["type"] == "table":
                table = node
                break

        assert table is not None, "Table not found in ADF output"

        # Check first row contains tableHeader cells
        first_row = table["content"][0]
        assert first_row["type"] == "tableRow"

        # All cells in first row should be tableHeader
        for cell in first_row["content"]:
            assert cell["type"] == "tableHeader", (
                f"Expected tableHeader but got {cell['type']}"
            )

        # Check subsequent rows contain tableCell
        for row in table["content"][1:]:
            for cell in row["content"]:
                assert cell["type"] == "tableCell", (
                    f"Expected tableCell but got {cell['type']}"
                )

    def test_html_table_with_th_tags(self):
        """Test that HTML tables with th tags are properly converted."""
        generator = ADFGenerator()

        # HTML table embedded in markdown
        markdown = """
<table>
<tr>
<th>Name</th>
<th>Age</th>
<th>City</th>
</tr>
<tr>
<td>John</td>
<td>30</td>
<td>New York</td>
</tr>
</table>
"""

        result = generator.markdown_to_adf(markdown)

        # Find the table
        table = None
        for node in result["content"]:
            if node["type"] == "table":
                table = node
                break

        assert table is not None, "Table not found in ADF output"

        # First row should have tableHeader cells
        first_row = table["content"][0]
        for i, cell in enumerate(first_row["content"]):
            assert cell["type"] == "tableHeader", (
                f"Cell {i} in first row should be tableHeader"
            )
            # Verify content
            para = cell["content"][0]
            assert para["type"] == "paragraph"
            text = para["content"][0]
            assert text["type"] == "text"
            assert text["text"] in ["Name", "Age", "City"]

        # Second row should have tableCell
        second_row = table["content"][1]
        for i, cell in enumerate(second_row["content"]):
            assert cell["type"] == "tableCell", (
                f"Cell {i} in second row should be tableCell"
            )
