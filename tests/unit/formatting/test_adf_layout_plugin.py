"""Test ADF layout plugin."""

import pytest
from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestLayoutPlugin:
    """Test layout plugin rendering."""
    
    def test_simple_layout(self):
        """Test basic 2-column layout."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout columns=2
::: column
First column content.
:::
::: column
Second column content.
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        
        assert result['type'] == 'doc'
        assert len(result['content']) == 1
        
        layout = result['content'][0]
        assert layout['type'] == 'layout'
        assert len(layout['content']) == 2  # Two columns
        
        # Check first column
        col1 = layout['content'][0]
        assert col1['type'] == 'layoutColumn'
        assert col1['attrs']['width'] == 50.0
        assert len(col1['content']) == 1
        assert col1['content'][0]['type'] == 'layoutSection'
        
        # Check content
        section1 = col1['content'][0]
        assert len(section1['content']) == 1
        assert section1['content'][0]['type'] == 'paragraph'
        assert section1['content'][0]['content'][0]['text'] == 'First column content.'
        
        # Check second column
        col2 = layout['content'][1]
        assert col2['type'] == 'layoutColumn'
        assert col2['attrs']['width'] == 50.0
    
    def test_three_column_layout(self):
        """Test 3-column layout."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout columns=3
::: column
Column 1
:::
::: column
Column 2
:::
::: column
Column 3
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        layout = result['content'][0]
        
        assert layout['type'] == 'layout'
        assert len(layout['content']) == 3
        
        # Check column widths
        for col in layout['content']:
            assert col['attrs']['width'] == pytest.approx(33.33333, rel=1e-3)
    
    def test_layout_with_formatting(self):
        """Test layout with inline formatting."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout columns=2
::: column
This has **bold** text.
:::
::: column
This has *italic* text.
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        layout = result['content'][0]
        
        # Check first column has bold
        col1_content = layout['content'][0]['content'][0]['content'][0]['content']
        bold_found = False
        for node in col1_content:
            if node.get('type') == 'text' and node.get('text') == 'bold':
                bold_found = any(m['type'] == 'strong' for m in node.get('marks', []))
                break
        assert bold_found
        
        # Check second column has italic
        col2_content = layout['content'][1]['content'][0]['content'][0]['content']
        italic_found = False
        for node in col2_content:
            if node.get('type') == 'text' and node.get('text') == 'italic':
                italic_found = any(m['type'] == 'em' for m in node.get('marks', []))
                break
        assert italic_found
    
    def test_layout_multi_paragraph(self):
        """Test layout with multiple paragraphs per column."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout columns=2
::: column
First paragraph.

Second paragraph.
:::
::: column
Another first paragraph.

Another second paragraph.
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        layout = result['content'][0]
        
        # Check first column has 2 paragraphs
        col1_section = layout['content'][0]['content'][0]
        assert len(col1_section['content']) == 2
        assert col1_section['content'][0]['type'] == 'paragraph'
        assert col1_section['content'][1]['type'] == 'paragraph'
        
        # Check second column has 2 paragraphs
        col2_section = layout['content'][1]['content'][0]
        assert len(col2_section['content']) == 2
    
    def test_default_columns(self):
        """Test layout defaults to 2 columns."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout
::: column
First column.
:::
::: column
Second column.
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        layout = result['content'][0]
        
        assert layout['type'] == 'layout'
        assert len(layout['content']) == 2
        assert layout['content'][0]['attrs']['width'] == 50.0
        assert layout['content'][1]['attrs']['width'] == 50.0
    
    def test_missing_columns(self):
        """Test layout with fewer columns than specified."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::layout columns=3
::: column
Only one column provided.
:::
:::"""
        
        result = generator.markdown_to_adf(markdown)
        layout = result['content'][0]
        
        # Should still create 3 columns, with empty ones
        assert len(layout['content']) == 3
        
        # First column has content
        assert layout['content'][0]['content'][0]['content'][0]['content'][0]['text'] == 'Only one column provided.'
        
        # Other columns should be empty
        for i in [1, 2]:
            section = layout['content'][i]['content'][0]
            assert section['content'][0]['content'][0]['text'] == ''