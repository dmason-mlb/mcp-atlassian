"""Integration tests for preprocessing pipeline with ADF support."""


from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor
from mcp_atlassian.preprocessing.jira import JiraPreprocessor


class TestPreprocessingIntegration:
    """Test preprocessing integration with ADF support."""

    def test_jira_preprocessor_cloud_returns_adf(self):
        """Test that JiraPreprocessor returns ADF for Cloud instances."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = JiraPreprocessor(base_url=cloud_url)

        markdown = "This is **bold** text with *italic* formatting."
        result = preprocessor.markdown_to_jira(markdown, enable_adf=True)

        # Should return ADF JSON dictionary for Cloud
        assert isinstance(result, dict)
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert "content" in result

    def test_jira_preprocessor_server_returns_wiki_markup(self):
        """Test that JiraPreprocessor returns wiki markup for Server instances."""
        server_url = "https://jira.example.com"
        preprocessor = JiraPreprocessor(base_url=server_url)

        markdown = "This is **bold** text with *italic* formatting."
        result = preprocessor.markdown_to_jira(markdown)

        # With ADF enabled by default, Server/DC should still get wiki markup based on URL detection
        assert isinstance(result, str)
        assert "*bold*" in result
        assert "_italic_" in result

    def test_jira_preprocessor_adf_disabled_fallback(self):
        """Test that JiraPreprocessor falls back to wiki markup when ADF disabled."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = JiraPreprocessor(base_url=cloud_url)

        markdown = "This is **bold** text."
        result = preprocessor.markdown_to_jira(markdown, enable_adf=False)

        # Should return wiki markup even for Cloud when ADF disabled
        assert isinstance(result, str)
        assert "*bold*" in result

    def test_confluence_preprocessor_cloud_returns_adf(self):
        """Test that ConfluencePreprocessor returns ADF for Cloud instances."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = ConfluencePreprocessor(base_url=cloud_url)

        markdown = "This is **bold** text with *italic* formatting."
        result = preprocessor.markdown_to_confluence(markdown, enable_adf=True)

        # Should return ADF JSON dictionary for Cloud
        assert isinstance(result, dict)
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert "content" in result

    def test_confluence_preprocessor_server_returns_storage_format(self):
        """Test that ConfluencePreprocessor returns storage format for Server instances."""
        server_url = "https://confluence.example.com"
        preprocessor = ConfluencePreprocessor(base_url=server_url)

        markdown = "This is **bold** text."
        result = preprocessor.markdown_to_confluence(markdown)

        # Should return storage format string for Server/DC
        assert isinstance(result, str)
        # Storage format contains HTML-like tags
        assert "<" in result and ">" in result

    def test_confluence_preprocessor_adf_disabled_fallback(self):
        """Test that ConfluencePreprocessor falls back to storage format when ADF disabled."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = ConfluencePreprocessor(base_url=cloud_url)

        markdown = "This is **bold** text."
        result = preprocessor.markdown_to_confluence(markdown, enable_adf=False)

        # Should return storage format even for Cloud when ADF disabled
        assert isinstance(result, str)
        assert "<" in result and ">" in result

    def test_empty_markdown_handling_jira(self):
        """Test handling of empty markdown in Jira preprocessor."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = JiraPreprocessor(base_url=cloud_url)

        # Test empty string
        result = preprocessor.markdown_to_jira("", enable_adf=True)
        assert isinstance(result, dict)  # Should be empty ADF for Cloud
        assert result["content"] == []

        # Test None
        result = preprocessor.markdown_to_jira(None, enable_adf=True)
        assert isinstance(result, dict)
        assert result["content"] == []

    def test_empty_markdown_handling_confluence(self):
        """Test handling of empty markdown in Confluence preprocessor."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = ConfluencePreprocessor(base_url=cloud_url)

        # Test empty string
        result = preprocessor.markdown_to_confluence("", enable_adf=True)
        assert isinstance(result, dict)  # Should be empty ADF for Cloud
        assert result["content"] == []

        # Test None
        result = preprocessor.markdown_to_confluence(None, enable_adf=True)
        assert isinstance(result, dict)
        assert result["content"] == []

    def test_complex_markdown_conversion_jira(self):
        """Test complex markdown conversion in Jira preprocessor."""
        cloud_url = "https://test.atlassian.net"
        preprocessor = JiraPreprocessor(base_url=cloud_url)

        complex_markdown = """# Main Heading

This paragraph has **bold**, *italic*, and `code` text.

## Subheading

- List item 1
- List item 2 with [link](https://example.com)

```python
print("Hello, world!")
```

Final paragraph."""

        result = preprocessor.markdown_to_jira(complex_markdown, enable_adf=True)

        # Should return ADF JSON for Cloud
        assert isinstance(result, dict)
        assert result["type"] == "doc"
        assert len(result["content"]) >= 5  # Should have multiple content blocks

    def test_error_handling_jira(self):
        """Test error handling in Jira preprocessor."""
        # Use an invalid URL to potentially trigger errors
        invalid_url = "not-a-valid-url"
        preprocessor = JiraPreprocessor(base_url=invalid_url)

        markdown = "This is **bold** text."
        result = preprocessor.markdown_to_jira(markdown)

        # Should still return some result (fallback)
        assert result is not None

    def test_error_handling_confluence(self):
        """Test error handling in Confluence preprocessor."""
        # Use an invalid URL to potentially trigger errors
        invalid_url = "not-a-valid-url"
        preprocessor = ConfluencePreprocessor(base_url=invalid_url)

        markdown = "This is **bold** text."
        result = preprocessor.markdown_to_confluence(markdown)

        # Should still return some result (fallback)
        assert result is not None
