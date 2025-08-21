# Test Data Templates

This document describes the markdown templates used by the E2E testing seed script to create consistent test data across Jira and Confluence.

## Overview

The seed script (`seed/seed.py`) creates identical content in both Jira issues and Confluence pages to enable comprehensive ADF (Atlassian Document Format) validation. This ensures that markdown-to-ADF conversion works consistently across both platforms.

## Standard Test Template

The `md_fixture()` function in `seed/seed.py` generates the following markdown content:

```markdown
# Test Objectives

This is E2E test content for visual render validation.

## Bullet Points
- First bullet point
- Second bullet point
- Third bullet point

## Numbered Lists
1. One
2. Two
3. Three

## Code Examples
Here is some `inline code` for testing.

```javascript
console.log("Hello, world!");
```

## Tables
| Col A | Col B |
|-------|-------|
| A     | B     |
| 1     | 2     |

## Blockquote
> This is a Blockquote for testing purposes.

**Bold text** and *italic text* for formatting validation.
```

## Test Elements Validation

### Basic Formatting
- **Headings**: H1 and H2 levels for structure validation
- **Bold and Italic**: `**Bold text**` and `*italic text*` for inline formatting
- **Inline Code**: `` `inline code` `` for code mark validation

### Lists
- **Unordered Lists**: Three bullet points to test list rendering
- **Ordered Lists**: Numbered sequence to validate list ordering

### Code Blocks
- **Fenced Code Blocks**: JavaScript example with syntax highlighting
- **Language Detection**: Tests language-specific formatting in ADF

### Tables
- **Simple Table**: 2x2 table with headers to test table structure
- **ADF Table Conversion**: Validates markdown table to ADF table conversion

### Blockquotes
- **Quote Block**: Tests blockquote rendering and styling

## Additional Test Data

### Comments
The seed script also adds a comment to the Jira issue:
```markdown
E2E seed comment with `code` and bold **text**.
```

This tests comment rendering with mixed formatting.

### Attachments
When available, the seed script attaches:
1. **Text File**: `test-attachment.txt` with label identifier
2. **Image File**: `test-image.png` (if source image exists)

### Labels and Metadata
- **Jira Labels**: Process-specific label (`mcp-e2e-{pid}`) for cleanup identification
- **Confluence Labels**: Same label applied to pages for batch operations
- **Issue Type**: "Task" for consistent Jira issue categorization

## Template Customization

### Modifying Test Content
To modify the test template, edit the `md_fixture()` function in `seed/seed.py`:

```python
def md_fixture() -> str:
    return """# Your Custom Test Content

Add your markdown here for testing specific ADF elements.

## Example: Testing Panels
:::panel type="info"
This is an info panel for ADF testing.
:::

## Example: Testing Status
Status: {status:color=green}Complete{/status}
"""
```

### Adding ADF-Specific Elements
For testing ADF-specific syntax that doesn't exist in standard markdown:

```python
def adf_specific_fixture() -> str:
    return """# ADF-Specific Test Elements

## Panels
:::panel type="warning"
Warning panel with **bold** content.
:::

## Status Badges
Current status: {status:color=blue}In Progress{/status}

## Mentions
Assigned to: @john.doe

## Dates
Due date: {date:2025-02-15}

## Emojis
:thumbsup: :rocket: :warning:
"""
```

### Environment-Specific Templates
For different test environments, you can create conditional templates:

```python
def environment_fixture(env_type: str) -> str:
    if env_type == "cloud":
        return cloud_specific_markdown()
    elif env_type == "server":
        return server_specific_markdown()
    else:
        return md_fixture()  # Default template
```

## Validation Points

### Rendering Validation
Each template element tests specific ADF conversion:
- **Headings**: `heading` nodes with correct levels
- **Lists**: `bulletList` and `orderedList` with `listItem` children
- **Code**: `codeBlock` with language and `code` marks
- **Tables**: `table` with `tableRow`, `tableHeader`, and `tableCell`
- **Formatting**: `strong` and `em` marks for bold/italic

### Cross-Platform Consistency
The same template is used for both Jira and Confluence to ensure:
- Identical source markdown
- Consistent ADF output
- Uniform visual rendering
- Cross-platform compatibility validation

## Best Practices

### Template Design
1. **Keep it comprehensive**: Include all major markdown elements
2. **Make it readable**: Use clear, descriptive content
3. **Test edge cases**: Include mixed formatting and nested elements
4. **Stay focused**: Don't overload with too many variations

### Maintenance
1. **Update both platforms**: Changes should apply to Jira and Confluence
2. **Version control**: Document template changes for reproducibility
3. **Test locally**: Validate template changes before committing
4. **Clean up**: Use consistent labels for automated cleanup

## Troubleshooting

### Template Issues
- **Missing elements**: Check that all required markdown syntax is included
- **ADF conversion errors**: Validate syntax against ADF documentation
- **Platform differences**: Some elements may render differently on Cloud vs Server

### Content Problems
- **Special characters**: Escape characters that might break JSON or API calls
- **Long content**: Keep templates reasonably sized for performance
- **Unicode content**: Test with international characters if needed

## Related Files

- **`seed/seed.py`**: Contains the template and seeding logic
- **`cleanup/cleanup.py`**: Cleanup script that removes test data by label
- **`.artifacts/seed.json`**: Generated file with test URLs and metadata
- **Test specs**: Files in `tests/` that validate the rendered content

This template system ensures consistent, comprehensive testing of the MCP Atlassian ADF implementation across all supported platforms and deployment types.