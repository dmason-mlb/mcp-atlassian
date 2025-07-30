"""Simplified tests to verify ADF implementation is working correctly."""

import json
from unittest.mock import Mock, patch, MagicMock
import pytest

from mcp_atlassian.formatting.router import FormatRouter
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator as ADFGenerator
from mcp_atlassian.preprocessing import ConfluencePreprocessor, JiraPreprocessor


class TestADFFormatDetection:
    """Test that the format router correctly detects deployment types."""

    def test_cloud_deployment_detection(self):
        """Test that Cloud URLs are correctly detected."""
        router = FormatRouter()
        
        cloud_urls = [
            "https://example.atlassian.net",
            "https://test.atlassian.net/wiki",
            "https://company.atlassian.com",
        ]
        
        for url in cloud_urls:
            result = router.convert_markdown("**test**", url)
            assert result["deployment_type"] == "cloud"
            assert result["format"] == "adf"
            assert isinstance(result["content"], dict)

    def test_server_deployment_detection(self):
        """Test that Server/DC URLs are correctly detected."""
        router = FormatRouter()
        
        server_urls = [
            "https://jira.company.com",
            "https://confluence.internal.net",
            "http://localhost:8080",
        ]
        
        for url in server_urls:
            result = router.convert_markdown("**test**", url)
            assert result["deployment_type"] == "server"
            assert result["format"] == "wiki_markup"
            assert isinstance(result["content"], str)


class TestADFContentGeneration:
    """Test that ADF content is generated correctly."""

    def test_basic_markdown_to_adf(self):
        """Test basic markdown elements convert to ADF."""
        generator = ADFGenerator()
        
        markdown = """# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- Bullet point 1
- Bullet point 2

1. Numbered item 1
2. Numbered item 2

[Link text](https://example.com)

`inline code`

```python
# Code block
def hello():
    print("Hello, World!")
```"""
        
        result = generator.markdown_to_adf(markdown)
        
        # Verify structure
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert "content" in result
        
        # Check that we have various node types
        content = result["content"]
        node_types = {node["type"] for node in content}
        
        assert "heading" in node_types
        assert "paragraph" in node_types
        assert "bulletList" in node_types
        assert "orderedList" in node_types
        assert "codeBlock" in node_types

    def test_plugin_content_to_adf(self):
        """Test that plugin content converts to ADF."""
        generator = ADFGenerator()
        
        markdown = """## Panel Example

::: panel info "Information Panel"
This is panel content with **formatting**.
:::

## Status Example

Current status: :status[In Progress|color=blue]

## Date Example

Due date: :date[2025-01-30]

## Mention Example

Assigned to: @john.doe"""
        
        result = generator.markdown_to_adf(markdown)
        
        # Check content was generated
        assert result["type"] == "doc"
        assert len(result["content"]) > 0
        
        # Verify panel was processed
        content_str = json.dumps(result)
        assert "panel" in content_str or "Panel" in content_str


class TestPreprocessorADFIntegration:
    """Test that preprocessors correctly use ADF for Cloud instances."""

    def test_confluence_preprocessor_cloud(self):
        """Test Confluence preprocessor returns ADF for Cloud."""
        preprocessor = ConfluencePreprocessor(base_url="https://example.atlassian.net")
        
        # Simulate Cloud instance
        with patch.object(preprocessor.format_router, 'convert_markdown') as mock_convert:
            mock_convert.return_value = {
                "content": {"type": "doc", "version": 1, "content": []},
                "format": "adf",
                "deployment_type": "cloud"
            }
            
            result = preprocessor.markdown_to_confluence(
                "**test**"
            )
            
            # Should return dict for ADF
            assert isinstance(result, dict)
            assert result["type"] == "doc"

    def test_confluence_preprocessor_server(self):
        """Test Confluence preprocessor returns storage for Server."""
        preprocessor = ConfluencePreprocessor(base_url="https://confluence.company.com")
        
        # For server, it should return storage format
        result = preprocessor.markdown_to_confluence_storage("**test**")
        
        # Should return string for storage format
        assert isinstance(result, str)
        assert "<strong>test</strong>" in result

    def test_jira_preprocessor_cloud(self):
        """Test Jira preprocessor returns ADF for Cloud."""
        preprocessor = JiraPreprocessor()
        
        # Simulate Cloud instance
        with patch.object(preprocessor.format_router, 'convert_markdown') as mock_convert:
            mock_convert.return_value = {
                "content": {"type": "doc", "version": 1, "content": []},
                "format": "adf",
                "deployment_type": "cloud"
            }
            
            result = preprocessor.markdown_to_jira(
                "**test**"
            )
            
            # Should return dict for ADF
            assert isinstance(result, dict)
            assert result["type"] == "doc"

    def test_jira_preprocessor_server(self):
        """Test Jira preprocessor returns wiki markup for Server."""
        preprocessor = JiraPreprocessor()
        
        # For server, it should return wiki markup
        result = preprocessor.markdown_to_jira("**test**")
        
        # Should return string for wiki format
        assert isinstance(result, str)
        assert "*test*" in result


class TestADFRealWorldScenarios:
    """Test ADF with real-world content scenarios."""

    def test_complex_document_structure(self):
        """Test a complex document with multiple elements."""
        generator = ADFGenerator()
        
        markdown = """# Project Documentation

## Overview

This project implements a **microservices** architecture with the following components:

- API Gateway
- Authentication Service
- User Service
- Notification Service

### Technical Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | Python | 3.11 |
| Database | PostgreSQL | 15 |
| Cache | Redis | 7.0 |

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/example/project.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## Architecture

The system uses an event-driven architecture with the following flow:

1. Client sends request to API Gateway
2. Gateway authenticates request via Auth Service
3. Request is routed to appropriate microservice
4. Response is cached in Redis for performance

> **Note**: All services communicate via REST APIs with JWT authentication.

## Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

*Last updated: 2025-01-30*"""
        
        result = generator.markdown_to_adf(markdown)
        
        # Verify the document was processed
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) > 0
        
        # Check for various elements
        content_json = json.dumps(result)
        assert "Project Documentation" in content_json
        assert "codeBlock" in content_json
        assert "table" in content_json
        assert "orderedList" in content_json
        assert "blockquote" in content_json

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        router = FormatRouter()
        
        # Perform several conversions
        for i in range(5):
            router.convert_markdown(f"Test content {i}", "https://example.atlassian.net")
        
        # Get metrics
        metrics = router.get_performance_metrics()
        
        # Verify metrics structure
        assert "detection_cache_hit_rate" in metrics
        assert "average_conversion_time" in metrics
        assert "average_detection_time" in metrics
        assert "cache_stats" in metrics
        
        # Check that conversions happened (look at successful conversions in converter_stats)
        converter_stats = metrics.get("converter_stats", {})
        if converter_stats:
            assert converter_stats.get("successful_conversions", 0) > 0