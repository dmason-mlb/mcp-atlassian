"""Simple integration tests for ADF conversion."""

import json
import time
from typing import Any

from mcp_atlassian.formatting.adf import ADFGenerator
from mcp_atlassian.formatting.router import FormatRouter


class TestADFIntegration:
    """Simple integration tests for ADF functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adf_generator = ADFGenerator()
        self.format_router = FormatRouter(cache_ttl=60)

    def test_adf_spec_compliance(self):
        """Test ADF output against basic specification requirements."""
        # Test various markdown elements
        test_cases = [
            ("# Heading 1", "heading"),
            ("**Bold text**", "paragraph"),
            ("- List item", "bulletList"),
            ("1. Ordered item", "orderedList"),
            ("`code`", "paragraph"),
            ("```\ncode block\n```", "codeBlock"),
            ("> Blockquote", "blockquote"),
            ("---", "rule"),
            ("[Link](http://example.com)", "paragraph"),
        ]
        
        for markdown, expected_type in test_cases:
            adf_result = self.adf_generator.markdown_to_adf(markdown)
            
            # Validate basic structure
            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1 
            assert isinstance(adf_result["content"], list)
            
            # Check that expected content types are present
            adf_str = json.dumps(adf_result)
            assert expected_type in adf_str, f"Expected {expected_type} not found in ADF for: {markdown}"

    def test_performance_benchmark(self):
        """Test ADF conversion performance meets target (<100ms)."""
        # Generate test content
        sections = []
        for i in range(10):
            section = f"""## Section {i+1}

This is section {i+1} with **bold**, *italic*, and `code` formatting.

- List item 1 for section {i+1}
- List item 2 for section {i+1}

```python
def section_{i+1}_function():
    return "Section {i+1} code example"
```

> Blockquote for section {i+1}.
"""
            sections.append(section)
        
        large_markdown = "# Performance Test\n\n" + "\n".join(sections)
        
        # Test conversion performance
        start_time = time.time()
        adf_result = self.adf_generator.markdown_to_adf(large_markdown)
        end_time = time.time()
        
        conversion_time = end_time - start_time
        
        # Should complete within target time (100ms per plan)
        assert conversion_time < 0.1, f"Conversion took {conversion_time:.3f}s, should be < 0.1s"
        
        # Validate result structure
        assert adf_result["type"] == "doc"
        assert len(adf_result["content"]) >= 20  # Multiple content blocks

    def test_error_recovery(self):
        """Test ADF generation error recovery."""
        problematic_cases = [
            "**Bold with unclosed markup",
            "[Invalid link]()",
            "```\nUnclosed code block",
            "![Invalid image](nonexistent.jpg)",
        ]
        
        for problematic_markdown in problematic_cases:
            # Should not crash and should produce valid ADF
            adf_result = self.adf_generator.markdown_to_adf(problematic_markdown)
            
            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1
            assert isinstance(adf_result["content"], list)
            
            # Should be JSON serializable
            adf_json = json.dumps(adf_result)
            assert len(adf_json) > 20
            
            # Validate ADF structure
            assert self.adf_generator.validate_adf(adf_result) is True

    def test_format_router_integration(self):
        """Test format router integration with various deployment types."""
        markdown_content = """# Test Document

This is a test with **bold** and *italic* text.

- List item 1
- List item 2

```python
print("Hello, ADF!")
```"""

        # Test Cloud deployment
        cloud_result = self.format_router.convert_markdown(
            markdown_content, 
            "https://test.atlassian.net"
        )
        
        assert cloud_result["format"] == "adf"
        assert cloud_result["deployment_type"] == "cloud"
        assert isinstance(cloud_result["content"], dict)
        
        # Test Server deployment
        server_result = self.format_router.convert_markdown(
            markdown_content,
            "https://jira.company.com"
        )
        
        assert server_result["format"] == "wiki_markup"
        assert server_result["deployment_type"] == "server"
        assert isinstance(server_result["content"], str)

    def test_real_world_samples(self):
        """Test with realistic markdown samples."""
        # GitHub issue template
        github_issue = """## Bug Report

**Describe the bug**
A clear description of the bug.

**To Reproduce**
1. Go to page
2. Click button
3. See error

**Environment:**
- OS: macOS
- Browser: Chrome
- Version: 1.0

**Additional context**
More details here."""

        # API documentation
        api_docs = """# REST API

## Authentication
Use API tokens for authentication:

```bash
curl -H "Authorization: Bearer TOKEN" \\
     https://api.example.com/v1/users
```

## Endpoints

### GET /users
Returns user list.

**Response:**
```json
{
  "users": [{"id": 1, "name": "John"}]
}
```"""

        samples = [github_issue, api_docs]
        
        for sample in samples:
            # Convert to ADF
            adf_result = self.adf_generator.markdown_to_adf(sample)
            
            # Validate structure
            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1
            assert len(adf_result["content"]) >= 3
            
            # Validate JSON serialization
            adf_json = json.dumps(adf_result)
            assert len(adf_json) > 100
            
            # Validate ADF compliance
            assert self.adf_generator.validate_adf(adf_result) is True
            
            # Test with format router  
            cloud_result = self.format_router.convert_markdown(sample, "https://test.atlassian.net")
            assert cloud_result["format"] == "adf"
            assert cloud_result["content"] == adf_result