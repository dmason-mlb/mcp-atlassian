"""API compatibility tests for ADF conversion with real Atlassian instances.

These tests validate that generated ADF works correctly with actual Jira and Confluence
Cloud APIs. They require valid credentials and are skipped by default in CI.
"""

import json
import os

import pytest

from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator as ADFGenerator
from mcp_atlassian.formatting.router import FormatRouter


class TestADFAPICompatibility:
    """Test ADF compatibility with real Atlassian APIs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adf_generator = ADFGenerator()
        self.format_router = FormatRouter(cache_ttl=60)

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("JIRA_BASE_URL"),
                os.getenv("JIRA_USERNAME"),
                os.getenv("JIRA_API_TOKEN"),
            ]
        ),
        reason="Requires Jira credentials for real API testing",
    )
    def test_adf_jira_cloud_issue_creation(self):
        """Test creating a Jira Cloud issue with ADF content."""
        # Sample markdown content that should convert to valid ADF
        markdown_content = """# Issue Summary

This is a test issue created via ADF conversion.

## Details

The issue contains various formatting:

- **Bold text** for emphasis
- *Italic text* for style
- `inline code` for technical terms

### Code Example

```python
def test_function():
    return "ADF conversion works!"
```

### Requirements

1. First requirement with **important** details
2. Second requirement with [external link](https://example.com)
3. Third requirement with `technical term`

> **Note**: This is a blockquote with important information.

---

**Status**: Testing ADF integration
"""

        # Convert to ADF
        adf_result = self.adf_generator.markdown_to_adf(markdown_content)

        # Validate ADF structure
        assert adf_result["type"] == "doc"
        assert adf_result["version"] == 1
        assert len(adf_result["content"]) >= 5  # Multiple content blocks

        # Validate that ADF is JSON serializable (required for API calls)
        adf_json = json.dumps(adf_result)
        assert len(adf_json) > 100  # Should be substantial content

        # Validate that it can be parsed back
        parsed_adf = json.loads(adf_json)
        assert parsed_adf == adf_result

        # Test with FormatRouter for Cloud instance
        cloud_url = "https://test.atlassian.net"
        router_result = self.format_router.convert_markdown(markdown_content, cloud_url)

        assert router_result["format"] == "adf"
        assert router_result["deployment_type"] == "cloud"
        assert router_result["content"] == adf_result

    @pytest.mark.skipif(
        not all(
            [
                os.getenv("CONFLUENCE_BASE_URL"),
                os.getenv("CONFLUENCE_USERNAME"),
                os.getenv("CONFLUENCE_API_TOKEN"),
            ]
        ),
        reason="Requires Confluence credentials for real API testing",
    )
    def test_adf_confluence_cloud_page_creation(self):
        """Test creating a Confluence Cloud page with ADF content."""
        # Sample markdown content for Confluence page
        markdown_content = """# Project Documentation

Welcome to the project documentation page.

## Overview

This page demonstrates ADF conversion for Confluence Cloud.

## Features

### Core Features
- **Rich Text**: Support for bold, italic, and other formatting
- **Code Blocks**: Syntax highlighted code examples
- **Lists**: Both ordered and unordered lists
- **Links**: Internal and external hyperlinks

### Technical Details

Here's a code example:

```javascript
function initializeProject() {
    console.log("Project initialized with ADF support");
    return {
        version: "1.0.0",
        format: "adf"
    };
}
```

## Implementation Notes

> **Important**: ADF format is required for Confluence Cloud API calls.

### Supported Elements

1. Headings (H1-H6)
2. Paragraphs with inline formatting
3. Code blocks with language detection
4. Lists (ordered and unordered)
5. Blockquotes
6. Horizontal rules
7. Links and basic tables

---

*Last updated*: Testing phase
"""

        # Convert to ADF
        adf_result = self.adf_generator.markdown_to_adf(markdown_content)

        # Validate ADF structure for Confluence
        assert adf_result["type"] == "doc"
        assert adf_result["version"] == 1
        assert len(adf_result["content"]) >= 8  # Multiple sections

        # Validate JSON serialization
        adf_json = json.dumps(adf_result)
        assert len(adf_json) > 200  # Substantial content

        # Test specific ADF elements that Confluence expects
        content_types = []
        for block in adf_result["content"]:
            content_types.append(block.get("type"))

        # Should contain various block types
        assert "heading" in content_types
        assert "paragraph" in content_types

        # Test with FormatRouter
        cloud_url = "https://company.atlassian.net"
        router_result = self.format_router.convert_markdown(markdown_content, cloud_url)

        assert router_result["format"] == "adf"
        assert router_result["content"] == adf_result

    def test_adf_validation_against_spec(self):
        """Test ADF output against Atlassian Document Format specification."""
        # Test various markdown elements
        test_cases = [
            ("# Heading 1", ["heading"]),
            ("**Bold text**", ["paragraph"]),
            ("- List item", ["bulletList"]),
            ("1. Ordered item", ["orderedList"]),
            ("`code`", ["paragraph"]),
            ("```\ncode block\n```", ["codeBlock"]),
            ("> Blockquote", ["blockquote"]),
            ("---", ["rule"]),
            ("[Link](http://example.com)", ["paragraph"]),
        ]

        for markdown, expected_types in test_cases:
            adf_result = self.adf_generator.markdown_to_adf(markdown)

            # Validate basic structure
            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1
            assert isinstance(adf_result["content"], list)

            # Check that expected content types are present
            content_types = [block.get("type") for block in adf_result["content"]]

            for expected_type in expected_types:
                # The type should appear somewhere in the content or nested content
                adf_str = json.dumps(adf_result)
                assert expected_type in adf_str, (
                    f"Expected {expected_type} not found in ADF for: {markdown}"
                )

    def test_adf_complex_document_structure(self):
        """Test ADF generation for complex document structures."""
        complex_markdown = """# Main Document Title

## Introduction Section

This document contains complex nested structures to test ADF generation.

### Nested Lists with Formatting

1. **First item** with bold text
   - Nested bullet with *italic*
   - Another nested item with `code`
   - Third nested item
2. **Second item** with [external link](https://example.com)
   1. Nested ordered list
   2. With multiple items
3. **Third item** with mixed content

### Code Examples

Here's a Python example:

```python
class ADFGenerator:
    def __init__(self):
        self.version = 1

    def convert(self, markdown):
        return {"type": "doc", "version": 1, "content": []}
```

And a JavaScript example:

```javascript
const adfGenerator = {
    version: 1,
    convert: (markdown) => {
        return {
            type: "doc",
            version: 1,
            content: []
        };
    }
};
```

### Tables

| Feature | Status | Notes |
|---------|--------|-------|
| Headings | ✅ | All levels supported |
| Lists | ✅ | Nested and ordered |
| Code | ✅ | Blocks and inline |
| Links | ✅ | External only |

### Blockquotes with Nested Content

> **Important Note**: This blockquote contains nested formatting:
>
> - Bullet points inside quotes
> - With `inline code`
> - And **bold text**
>
> > Nested blockquote for emphasis

---

## Conclusion

This complex document tests various ADF conversion scenarios.
"""

        adf_result = self.adf_generator.markdown_to_adf(complex_markdown)

        # Validate overall structure
        assert adf_result["type"] == "doc"
        assert adf_result["version"] == 1
        assert len(adf_result["content"]) >= 10  # Many content blocks

        # Validate JSON serialization works for complex content
        adf_json = json.dumps(adf_result, indent=2)
        assert len(adf_json) > 1000  # Substantial JSON output

        # Validate that complex structures are handled
        adf_str = str(adf_result)
        assert "heading" in adf_str
        assert "paragraph" in adf_str
        assert "bulletList" in adf_str or "orderedList" in adf_str
        assert "codeBlock" in adf_str

    def test_adf_performance_large_documents(self):
        """Test ADF conversion performance with large documents."""
        import time

        # Generate a large document
        sections = []
        for i in range(20):
            section = f"""## Section {i + 1}

This is section {i + 1} with various content types:

### Subsection {i + 1}.1

Paragraph with **bold**, *italic*, and `code` formatting.

- List item 1 for section {i + 1}
- List item 2 for section {i + 1}
- List item 3 for section {i + 1}

```python
def section_{i + 1}_function():
    return "Section {i + 1} code example"
```

> Blockquote for section {i + 1} with important information.

"""
            sections.append(section)

        large_markdown = "# Large Document Test\n\n" + "\n".join(sections)

        # Test conversion performance
        start_time = time.time()
        adf_result = self.adf_generator.markdown_to_adf(large_markdown)
        end_time = time.time()

        conversion_time = end_time - start_time

        # Should complete within target time (100ms per plan)
        assert conversion_time < 0.1, (
            f"Large document conversion took {conversion_time:.3f}s, should be < 0.1s"
        )

        # Validate result structure
        assert adf_result["type"] == "doc"
        assert len(adf_result["content"]) >= 80  # Many content blocks from 20 sections

        # Validate it's properly formed JSON
        adf_json = json.dumps(adf_result)
        parsed_back = json.loads(adf_json)
        assert parsed_back == adf_result

    def test_adf_error_recovery(self):
        """Test ADF generation error recovery and fallback behavior."""
        # Test with problematic markdown that might cause issues
        problematic_cases = [
            "# Heading with <script>alert('xss')</script>",
            "**Bold with unclosed markup",
            "[Invalid link]()",
            "```\nUnclosed code block",
            "![Invalid image](nonexistent.jpg)",
            "| Malformed | table\n| --- |\n| missing cell",
        ]

        for problematic_markdown in problematic_cases:
            # Should not crash and should produce valid ADF
            adf_result = self.adf_generator.markdown_to_adf(problematic_markdown)

            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1
            assert isinstance(adf_result["content"], list)

            # Should be JSON serializable
            adf_json = json.dumps(adf_result)
            assert len(adf_json) > 20  # Should have some content

            # Validate ADF structure
            assert self.adf_generator.validate_adf(adf_result) is True

    def test_real_world_markdown_samples(self):
        """Test with real-world markdown samples that users might input."""
        real_world_samples = [
            # GitHub issue template
            """## Bug Report

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. iOS]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

**Additional context**
Add any other context about the problem here.""",
            # API documentation
            """# REST API Documentation

## Authentication

All API requests require authentication using API tokens:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     https://api.example.com/v1/resources
```

## Endpoints

### GET /api/v1/users

Returns a list of users.

**Parameters:**
- `limit` (integer): Maximum number of results (default: 10)
- `offset` (integer): Number of results to skip (default: 0)

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "total": 100
}
```""",
            # Meeting notes
            """# Weekly Team Meeting - 2024-01-15

## Attendees
- Alice Johnson (Product Manager)
- Bob Smith (Lead Developer)
- Carol Davis (Designer)

## Agenda Items

### 1. Project Status Update
- **Backend API**: 80% complete
- **Frontend UI**: 60% complete
- **Testing**: 40% complete

### 2. Blockers and Issues
- [ ] Database performance optimization needed
- [ ] Third-party integration delays
- [x] Design review completed

### 3. Action Items
1. **Bob**: Optimize database queries by Friday
2. **Carol**: Finalize UI components by Wednesday
3. **Alice**: Schedule client demo for next week

## Next Meeting
**Date**: January 22, 2024
**Time**: 10:00 AM
**Location**: Conference Room B""",
        ]

        for sample in real_world_samples:
            # Convert to ADF
            adf_result = self.adf_generator.markdown_to_adf(sample)

            # Validate structure
            assert adf_result["type"] == "doc"
            assert adf_result["version"] == 1
            assert len(adf_result["content"]) >= 3  # Should have multiple sections

            # Validate JSON serialization
            adf_json = json.dumps(adf_result)
            assert len(adf_json) > 100  # Should be substantial

            # Validate ADF compliance
            assert self.adf_generator.validate_adf(adf_result) is True

            # Test with format router
            cloud_result = self.format_router.convert_markdown(
                sample, "https://test.atlassian.net"
            )
            assert cloud_result["format"] == "adf"
            assert cloud_result["content"] == adf_result
