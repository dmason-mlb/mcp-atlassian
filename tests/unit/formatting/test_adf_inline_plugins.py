"""Test inline ADF plugins."""

import pytest
from src.mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator


class TestInlinePlugins:
    """Test inline plugin rendering."""
    
    def test_status_plugin(self):
        """Test status inline plugin."""
        generator = ASTBasedADFGenerator()
        
        markdown = "Task is {status:color=green}Done{/status} and ready."
        result = generator.markdown_to_adf(markdown)
        
        assert result['type'] == 'doc'
        assert len(result['content']) == 1
        
        para = result['content'][0]
        assert para['type'] == 'paragraph'
        
        # Should have text, status, and more text
        content = para['content']
        assert len(content) >= 3
        
        # Find status node
        status_node = None
        for node in content:
            if node.get('type') == 'status':
                status_node = node
                break
        
        assert status_node is not None
        assert status_node['attrs']['text'] == 'Done'
        assert status_node['attrs']['color'] == 'green'
    
    def test_date_plugin(self):
        """Test date inline plugin."""
        generator = ASTBasedADFGenerator()
        
        markdown = "Meeting scheduled for {date:2025-03-15}."
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # Find date node
        date_node = None
        for node in content:
            if node.get('type') == 'date':
                date_node = node
                break
        
        assert date_node is not None
        assert 'timestamp' in date_node['attrs']
        assert isinstance(date_node['attrs']['timestamp'], (int, float))
    
    def test_mention_plugin(self):
        """Test mention inline plugin."""
        generator = ASTBasedADFGenerator()
        
        # Test simple mention
        markdown = "CC @john.doe on this."
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # Find mention node
        mention_node = None
        for node in content:
            if node.get('type') == 'mention':
                mention_node = node
                break
        
        assert mention_node is not None
        assert mention_node['attrs']['text'] == '@john.doe'
        assert mention_node['attrs']['id'] == 'john.doe'
    
    def test_mention_with_full_name(self):
        """Test mention with full name syntax."""
        generator = ASTBasedADFGenerator()
        
        markdown = "Assign to @[John Doe] please."
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # Find mention node
        mention_node = None
        for node in content:
            if node.get('type') == 'mention':
                mention_node = node
                break
        
        assert mention_node is not None
        assert mention_node['attrs']['text'] == '@John Doe'
        assert mention_node['attrs']['id'] == 'john.doe'
    
    def test_emoji_plugin(self):
        """Test emoji inline plugin."""
        generator = ASTBasedADFGenerator()
        
        markdown = "Great work :thumbsup: and :smile:!"
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # Find emoji nodes
        emoji_nodes = [n for n in content if n.get('type') == 'emoji']
        
        assert len(emoji_nodes) == 2
        assert emoji_nodes[0]['attrs']['shortName'] == ':thumbsup:'
        assert emoji_nodes[0]['attrs']['text'] == '👍'
        assert emoji_nodes[1]['attrs']['shortName'] == ':smile:'
        assert emoji_nodes[1]['attrs']['text'] == '😊'
    
    def test_mixed_inline_plugins(self):
        """Test multiple inline plugins in one paragraph."""
        generator = ASTBasedADFGenerator()
        
        markdown = "@alice, the task is {status:color=yellow}In Progress{/status} as of {date:2025-01-15} :fire:"
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # Should have mention, status, date, and emoji
        node_types = [n.get('type') for n in content]
        assert 'mention' in node_types
        assert 'status' in node_types
        assert 'date' in node_types
        assert 'emoji' in node_types
    
    def test_inline_plugins_with_formatting(self):
        """Test inline plugins don't interfere with text formatting."""
        generator = ASTBasedADFGenerator()
        
        markdown = "**Important**: Task is {status:color=red}Blocked{/status}!"
        result = generator.markdown_to_adf(markdown)
        
        para = result['content'][0]
        content = para['content']
        
        # First should be bold text
        assert content[0]['type'] == 'text'
        assert content[0]['text'] == 'Important'
        assert any(m['type'] == 'strong' for m in content[0].get('marks', []))
        
        # Should still have status node
        status_node = None
        for node in content:
            if node.get('type') == 'status':
                status_node = node
                break
        
        assert status_node is not None
        assert status_node['attrs']['color'] == 'red'