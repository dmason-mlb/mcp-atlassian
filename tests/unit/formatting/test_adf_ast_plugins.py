"""Test ADF AST integration with plugins."""

import pytest
from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestASTPluginIntegration:
    """Test that plugins work through the full AST pipeline."""
    
    def test_panel_rendering(self):
        """Test that panel blocks are rendered correctly."""
        generator = ASTBasedADFGenerator()
        
        # Test basic panel
        markdown = """:::panel type="info"
This is an information panel.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        
        assert result['type'] == 'doc'
        assert len(result['content']) == 1
        
        panel = result['content'][0]
        assert panel['type'] == 'panel'
        assert panel['attrs']['panelType'] == 'info'
        assert len(panel['content']) == 1
        assert panel['content'][0]['type'] == 'paragraph'
        assert panel['content'][0]['content'][0]['text'] == 'This is an information panel.'
    
    def test_panel_types(self):
        """Test all panel types."""
        generator = ASTBasedADFGenerator()
        
        for panel_type in ['info', 'note', 'warning', 'success', 'error']:
            markdown = f""":::panel type="{panel_type}"
{panel_type.capitalize()} panel content.
:::"""
            
            result = generator.markdown_to_adf(markdown)
            panel = result['content'][0]
            
            assert panel['type'] == 'panel'
            assert panel['attrs']['panelType'] == panel_type
    
    def test_panel_with_formatting(self):
        """Test panel with inline formatting."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::panel type="warning"
This is **bold** and *italic* text with `code`.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        panel = result['content'][0]
        
        assert panel['type'] == 'panel'
        assert panel['attrs']['panelType'] == 'warning'
        
        # Check inline formatting
        content = panel['content'][0]['content']
        assert len(content) == 7  # "This is ", bold, " and ", italic, " text with ", code, "."
        
        # Check bold
        bold_node = content[1]
        assert bold_node['type'] == 'text'
        assert bold_node['text'] == 'bold'
        assert any(m['type'] == 'strong' for m in bold_node.get('marks', []))
        
        # Check italic
        italic_node = content[3]
        assert italic_node['type'] == 'text'
        assert italic_node['text'] == 'italic'
        assert any(m['type'] == 'em' for m in italic_node.get('marks', []))
        
        # Check code
        code_node = content[5]
        assert code_node['type'] == 'text'
        assert code_node['text'] == 'code'
        assert any(m['type'] == 'code' for m in code_node.get('marks', []))
    
    def test_panel_multiline(self):
        """Test panel with multiple paragraphs."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::panel type="note"
First paragraph.

Second paragraph with **emphasis**.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        panel = result['content'][0]
        
        assert panel['type'] == 'panel'
        assert panel['attrs']['panelType'] == 'note'
        assert len(panel['content']) == 2
        
        # First paragraph
        assert panel['content'][0]['type'] == 'paragraph'
        assert panel['content'][0]['content'][0]['text'] == 'First paragraph.'
        
        # Second paragraph
        assert panel['content'][1]['type'] == 'paragraph'
        assert panel['content'][1]['content'][0]['text'] == 'Second paragraph with '
        assert panel['content'][1]['content'][1]['text'] == 'emphasis'
        assert any(m['type'] == 'strong' for m in panel['content'][1]['content'][1].get('marks', []))
    
    def test_panel_in_mixed_content(self):
        """Test panel mixed with other markdown elements."""
        generator = ASTBasedADFGenerator()
        
        markdown = """# Heading

Regular paragraph.

:::panel type="success"
Success panel content.
:::

Another paragraph after panel."""
        
        result = generator.markdown_to_adf(markdown)
        
        assert len(result['content']) == 4
        
        # Check structure
        assert result['content'][0]['type'] == 'heading'
        assert result['content'][1]['type'] == 'paragraph'
        assert result['content'][2]['type'] == 'panel'
        assert result['content'][3]['type'] == 'paragraph'
        
        # Check panel
        panel = result['content'][2]
        assert panel['attrs']['panelType'] == 'success'
    
    def test_default_panel_type(self):
        """Test panel without explicit type defaults to info."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::panel
Default panel content.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        panel = result['content'][0]
        
        assert panel['type'] == 'panel'
        assert panel['attrs']['panelType'] == 'info'  # Should default to info
    
    def test_empty_panel(self):
        """Test empty panel gets placeholder content."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::panel type="error"
:::"""
        
        result = generator.markdown_to_adf(markdown)
        panel = result['content'][0]
        
        assert panel['type'] == 'panel'
        assert panel['attrs']['panelType'] == 'error'
        assert len(panel['content']) == 1
        assert panel['content'][0]['type'] == 'paragraph'
        # Empty panels should have empty text content
        assert panel['content'][0]['content'][0]['text'] == ''
    
    def test_media_plugin(self):
        """Test media plugin rendering."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::media
type: image
id: attachment-123
collection: contentId-456
width: 800
height: 600
layout: center
:::"""
        
        result = generator.markdown_to_adf(markdown)
        media = result['content'][0]
        
        assert media['type'] == 'mediaSingle'
        assert media['attrs']['layout'] == 'center'
        
        media_node = media['content'][0]
        assert media_node['type'] == 'media'
        assert media_node['attrs']['type'] == 'image'
        assert media_node['attrs']['id'] == 'attachment-123'
        assert media_node['attrs']['collection'] == 'contentId-456'
        assert media_node['attrs']['width'] == 800
        assert media_node['attrs']['height'] == 600
    
    def test_media_types(self):
        """Test different media types."""
        generator = ASTBasedADFGenerator()
        
        # Test video
        markdown = """:::media
type: video
id: video-456
:::"""
        
        result = generator.markdown_to_adf(markdown)
        media = result['content'][0]
        assert media['content'][0]['attrs']['type'] == 'video'
        
        # Test file
        markdown = """:::media
type: file
id: file-789
:::"""
        
        result = generator.markdown_to_adf(markdown)
        media = result['content'][0]
        assert media['content'][0]['attrs']['type'] == 'file'
    
    def test_expand_plugin(self):
        """Test expand plugin rendering."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::expand title="Technical Details"
This section contains technical implementation details.

Including multiple paragraphs with **formatting**.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        expand = result['content'][0]
        
        assert expand['type'] == 'expand'
        assert expand['attrs']['title'] == 'Technical Details'
        assert len(expand['content']) == 2  # Two paragraphs
        
        # Check first paragraph
        first_para = expand['content'][0]
        assert first_para['type'] == 'paragraph'
        assert first_para['content'][0]['text'] == 'This section contains technical implementation details.'
        
        # Check second paragraph with formatting
        second_para = expand['content'][1]
        assert second_para['type'] == 'paragraph'
        assert len(second_para['content']) == 3
        assert second_para['content'][1]['text'] == 'formatting'
        assert any(m['type'] == 'strong' for m in second_para['content'][1].get('marks', []))
    
    def test_expand_default_title(self):
        """Test expand with default title."""
        generator = ASTBasedADFGenerator()
        
        markdown = """:::expand
Hidden content here.
:::"""
        
        result = generator.markdown_to_adf(markdown)
        expand = result['content'][0]
        
        assert expand['type'] == 'expand'
        assert expand['attrs']['title'] == 'Click to expand'
    
    def test_mixed_plugins(self):
        """Test document with multiple plugin types."""
        generator = ASTBasedADFGenerator()
        
        markdown = """# Document with Mixed Content

:::panel type="info"
This is an info panel.
:::

:::expand title="Show Media"
Here's an image description.
:::

Final paragraph."""
        
        result = generator.markdown_to_adf(markdown)
        
        assert len(result['content']) == 4
        
        # Check heading
        assert result['content'][0]['type'] == 'heading'
        
        # Check panel
        assert result['content'][1]['type'] == 'panel'
        
        # Check expand
        expand = result['content'][2]
        assert expand['type'] == 'expand'
        
        # Check final paragraph
        assert result['content'][3]['type'] == 'paragraph'