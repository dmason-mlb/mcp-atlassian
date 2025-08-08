"""Tests for format router functionality."""

from unittest.mock import patch

from mcp_atlassian.formatting.router import DeploymentType, FormatRouter, FormatType


class TestFormatRouter:
    """Test cases for FormatRouter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = FormatRouter(cache_ttl=60)

    def test_cloud_deployment_detection(self):
        """Test detection of Atlassian Cloud deployments."""
        cloud_urls = [
            "https://mycompany.atlassian.net",
            "https://test-instance.atlassian.net/jira",
            "https://dev.atlassian.com",
            "https://staging.jira-dev.com",
        ]

        for url in cloud_urls:
            deployment_type = self.router.detect_deployment_type(url)
            assert deployment_type == DeploymentType.CLOUD, (
                f"Failed to detect cloud for {url}"
            )

    def test_server_deployment_detection(self):
        """Test detection of Server/Data Center deployments."""
        server_urls = [
            "https://jira.mycompany.com",
            "https://confluence.internal.org",
            "https://atlassian.example.com",
            "http://jira-server.local:8080",
        ]

        for url in server_urls:
            deployment_type = self.router.detect_deployment_type(url)
            assert deployment_type == DeploymentType.SERVER, (
                f"Failed to detect server for {url}"
            )

    def test_unknown_deployment_detection(self):
        """Test handling of unknown deployment types."""
        unknown_urls = [
            "",
            "invalid-url",
            "ftp://example.com",
            None,
        ]

        for url in unknown_urls:
            deployment_type = self.router.detect_deployment_type(url)
            assert deployment_type == DeploymentType.UNKNOWN, (
                f"Should be unknown for {url}"
            )

    def test_deployment_cache(self):
        """Test that deployment detection uses cache."""
        url = "https://test.atlassian.net"

        # First call
        result1 = self.router.detect_deployment_type(url)
        assert result1 == DeploymentType.CLOUD

        # Second call should use cache
        result2 = self.router.detect_deployment_type(url)
        assert result2 == DeploymentType.CLOUD

        # Check cache contains the URL
        cache_stats = self.router.get_cache_stats()
        assert url.lower() in cache_stats["cached_deployments"]

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        url = "https://test.atlassian.net"

        # Populate cache
        self.router.detect_deployment_type(url)
        assert len(self.router.deployment_cache) == 1

        # Clear cache
        self.router.clear_cache()
        assert len(self.router.deployment_cache) == 0

    def test_format_selection_cloud(self):
        """Test format selection for Cloud deployments."""
        format_type = self.router._get_format_for_deployment(DeploymentType.CLOUD)
        assert format_type == FormatType.ADF

    def test_format_selection_server(self):
        """Test format selection for Server/DC deployments."""
        format_type = self.router._get_format_for_deployment(DeploymentType.SERVER)
        assert format_type == FormatType.WIKI_MARKUP

    def test_format_selection_unknown(self):
        """Test format selection for unknown deployments."""
        format_type = self.router._get_format_for_deployment(DeploymentType.UNKNOWN)
        assert format_type == FormatType.WIKI_MARKUP

    def test_markdown_conversion_cloud(self):
        """Test markdown conversion for Cloud deployment (ADF format)."""
        markdown = "This is **bold** text"
        cloud_url = "https://test.atlassian.net"

        result = self.router.convert_markdown(markdown, cloud_url)

        assert result["format"] == "adf"
        assert result["deployment_type"] == "cloud"
        assert isinstance(result["content"], dict)
        assert result["content"]["type"] == "doc"
        assert result["content"]["version"] == 1

    def test_markdown_conversion_server(self):
        """Test markdown conversion for Server deployment (wiki markup)."""
        markdown = "This is **bold** text"
        server_url = "https://jira.mycompany.com"

        result = self.router.convert_markdown(markdown, server_url)

        assert result["format"] == "wiki_markup"
        assert result["deployment_type"] == "server"
        assert isinstance(result["content"], str)
        assert "*bold*" in result["content"]

    def test_forced_format_adf(self):
        """Test forced ADF format conversion."""
        markdown = "**bold** text"
        server_url = "https://jira.mycompany.com"  # Would normally use wiki markup

        result = self.router.convert_markdown(
            markdown, server_url, force_format=FormatType.ADF
        )

        assert result["format"] == "adf"
        assert isinstance(result["content"], dict)

    def test_forced_format_wiki(self):
        """Test forced wiki markup format conversion."""
        markdown = "**bold** text"
        cloud_url = "https://test.atlassian.net"  # Would normally use ADF

        result = self.router.convert_markdown(
            markdown, cloud_url, force_format=FormatType.WIKI_MARKUP
        )

        assert result["format"] == "wiki_markup"
        assert isinstance(result["content"], str)
        assert "*bold*" in result["content"]

    def test_wiki_markup_conversion_basic(self):
        """Test basic wiki markup conversion functionality."""
        test_cases = [
            ("**bold**", "*bold*"),
            ("*italic*", "_italic_"),
            ("# Heading", "h1. Heading"),
            ("## Heading 2", "h2. Heading 2"),
            ("`code`", "{code}"),
            ("- List item", "* List item"),
            ("1. Ordered item", "# Ordered item"),
            ("[Link](http://example.com)", "[Link|http://example.com]"),
        ]

        for markdown, expected_wiki in test_cases:
            result = self.router._markdown_to_wiki_markup(markdown)
            assert expected_wiki in result, f"Failed conversion: {markdown} -> {result}"

    def test_wiki_markup_code_blocks(self):
        """Test wiki markup conversion of code blocks."""
        markdown = "```python\nprint('hello')\n```"
        result = self.router._markdown_to_wiki_markup(markdown)

        assert "{code:python}" in result
        assert "print('hello')" in result
        assert "{code}" in result

    def test_error_handling_conversion(self):
        """Test error handling during conversion."""
        # Mock ADF generator to raise exception
        with patch.object(
            self.router.adf_generator,
            "markdown_to_adf",
            side_effect=Exception("Test error"),
        ):
            result = self.router.convert_markdown("test", "https://test.atlassian.net")

            # Should fallback to plain text
            assert result["content"] == "test"
            assert result["format"] == "plain_text"
            assert "error" in result

    def test_cache_stats(self):
        """Test cache statistics functionality."""
        # Populate cache with some entries
        urls = [
            "https://cloud1.atlassian.net",
            "https://cloud2.atlassian.net",
            "https://server.example.com",
        ]

        for url in urls:
            self.router.detect_deployment_type(url)

        stats = self.router.get_cache_stats()

        assert stats["cache_size"] == 3
        assert stats["cache_maxsize"] == 100
        assert stats["cache_ttl"] == 60
        assert len(stats["cached_deployments"]) == 3

    def test_empty_markdown_handling(self):
        """Test handling of empty markdown input."""
        empty_inputs = ["", None, "   ", "\n\n"]

        for empty_input in empty_inputs:
            result = self.router.convert_markdown(
                empty_input, "https://test.atlassian.net"
            )

            assert result["format"] == "adf"
            assert result["content"]["type"] == "doc"
            assert result["content"]["content"] == []

    def test_complex_markdown_cloud(self):
        """Test complex markdown conversion for Cloud (ADF)."""
        complex_markdown = """# Main Heading

This paragraph has **bold**, *italic*, and `code` text.

## Subheading

- List item 1
- List item 2 with [link](https://example.com)

```python
print("Hello, world!")
```

> This is a blockquote

Final paragraph."""

        result = self.router.convert_markdown(
            complex_markdown, "https://test.atlassian.net"
        )

        assert result["format"] == "adf"
        assert result["deployment_type"] == "cloud"

        # Validate ADF structure
        adf_content = result["content"]
        assert adf_content["type"] == "doc"
        assert adf_content["version"] == 1
        assert len(adf_content["content"]) >= 5  # Multiple content blocks

    def test_complex_markdown_server(self):
        """Test complex markdown conversion for Server (wiki markup)."""
        complex_markdown = """# Main Heading

This paragraph has **bold**, *italic*, and `code` text.

- List item 1
- List item 2"""

        result = self.router.convert_markdown(
            complex_markdown, "https://jira.example.com"
        )

        assert result["format"] == "wiki_markup"
        assert result["deployment_type"] == "server"

        wiki_content = result["content"]
        assert "h1. Main Heading" in wiki_content
        assert "*bold*" in wiki_content
        assert "_italic_" in wiki_content
        assert "* List item 1" in wiki_content

    def test_url_parsing_edge_cases(self):
        """Test URL parsing edge cases."""
        edge_cases = [
            ("HTTPS://TEST.ATLASSIAN.NET", DeploymentType.CLOUD),  # Uppercase
            ("https://test.atlassian.net/", DeploymentType.CLOUD),  # Trailing slash
            (
                "https://test.atlassian.net/jira/browse/",
                DeploymentType.CLOUD,
            ),  # Deep path
            ("http://localhost:8080", DeploymentType.SERVER),  # Localhost
            ("jira.company.com", DeploymentType.SERVER),  # No protocol
        ]

        for url, expected_type in edge_cases:
            if url == "jira.company.com":
                # No protocol will result in UNKNOWN
                deployment_type = self.router.detect_deployment_type(url)
                assert deployment_type == DeploymentType.UNKNOWN
            else:
                deployment_type = self.router.detect_deployment_type(url)
                assert deployment_type == expected_type, f"Failed for {url}"

    def test_case_insensitive_detection(self):
        """Test that deployment detection is case insensitive."""
        urls = [
            "https://TEST.ATLASSIAN.NET",
            "https://test.ATLASSIAN.net",
            "HTTPS://JIRA.EXAMPLE.COM",
        ]

        # First URL should be Cloud
        assert self.router.detect_deployment_type(urls[0]) == DeploymentType.CLOUD
        assert self.router.detect_deployment_type(urls[1]) == DeploymentType.CLOUD

        # Third URL should be Server
        assert self.router.detect_deployment_type(urls[2]) == DeploymentType.SERVER
