# Confluence Page Creation Troubleshooting Guide

This guide helps AI agents troubleshoot common issues when creating Confluence pages using the MCP Atlassian server.

## Required Fields

For Confluence page creation, you **must** provide these three fields:

1. **space_key** - The space identifier where the page will be created
2. **title** - The page title (must be unique within the space)
3. **body** - The page content in markdown format

## Common Field Names and Examples

### Space Key Examples
- **Personal spaces**: `"space_key": "~911651470"` (format: ~<account_id>)
- **Team spaces**: `"space_key": "TEAMSPACE"` (the actual space key from the URL)
- **Project spaces**: `"space_key": "PROJ"` (usually uppercase abbreviation)

### Title Examples
- `"title": "My Test Page"`
- `"title": "API Documentation"`
- `"title": "Meeting Notes - 2024-01-15"`

### Body Examples
- Simple: `"body": "This is a simple page with plain text."`
- Markdown: `"body": "# Heading\n\n**Bold** text and *italic* text.\n\n## Subheading\n\n- Bullet point\n- Another point"`
- Rich content: `"body": "# Welcome\n\nThis page contains:\n\n## Features\n- **Bold** formatting\n- *Italic* text\n- [Links](https://example.com)\n- Code blocks\n\n```python\nprint('Hello World')\n```\n\n| Column 1 | Column 2 |\n|----------|----------|\n| Value 1  | Value 2  |"`

## Common Error Patterns and Solutions

### 1. Missing Required Fields

**Error**: `CONFLUENCE_MISSING_SPACE`, `CONFLUENCE_MISSING_TITLE`, `CONFLUENCE_MISSING_BODY`

**Solution**: Ensure all three required fields are present:
```json
{
  "service": "confluence",
  "resource": "page",
  "operation": "create",
  "data": {
    "space_key": "~911651470",
    "title": "My Page Title",
    "body": "# Page content goes here"
  }
}
```

### 2. Space Not Found

**Error**: `CONFLUENCE_SPACE_NOT_FOUND`

**Possible causes and solutions**:
- **Wrong space key**: Double-check the space key format
  - Personal spaces: Use `~<account_id>` (e.g., `~911651470`)
  - Team spaces: Use the exact key from the space URL
- **No access**: Verify you have permission to view/create pages in the space
- **Typo**: Check for extra spaces, wrong case, or missing characters

### 3. Duplicate Title

**Error**: `CONFLUENCE_DUPLICATE_TITLE`

**Solution**: Choose a different page title or update the existing page instead:
```json
{
  "title": "My Page Title (Updated)",
  // or use update operation instead
  "operation": "update",
  "identifier": "existing_page_id"
}
```

### 4. Permission Denied

**Error**: `CONFLUENCE_PERMISSION_DENIED`

**Solutions**:
- Check your API token has the required scopes
- Verify you have "Add Page" permission in the target space
- Contact your Confluence administrator for access
- Ensure your authentication is working correctly

### 5. Field Name Confusion

**Common mistake**: Using `space_id` instead of `space_key`

**Solution**: Always use `space_key` (the server accepts both for compatibility):
```json
{
  "data": {
    "space_key": "~911651470",  // ✅ Correct
    "space_id": "~911651470",   // ✅ Also works (legacy)
    "title": "Page Title",
    "body": "Content"
  }
}
```

## Testing and Validation

### Use Dry Run Mode
Always test your parameters first:
```json
{
  "service": "confluence",
  "resource": "page",
  "operation": "create",
  "data": {
    "space_key": "~911651470",
    "title": "Test Page",
    "body": "Test content"
  },
  "dry_run": true
}
```

### Minimal Working Example
```json
{
  "service": "confluence",
  "resource": "page",
  "operation": "create",
  "data": {
    "space_key": "~911651470",
    "title": "My Test Page",
    "body": "# Welcome\n\nThis is a test page created via MCP."
  }
}
```

## Advanced Features

### Optional Fields
- `parent_id`: Create page as child of another page
- `is_markdown`: Set to false if providing raw HTML/storage format
- `enable_heading_anchors`: Enable automatic heading anchor generation

### Markdown Support
The `body` field supports full markdown including:
- Headers (`#`, `##`, `###`)
- **Bold** and *italic* text
- Lists (bulleted and numbered)
- Links `[text](url)`
- Code blocks with syntax highlighting
- Tables
- Images
- Blockquotes

### Error Recovery
If you receive an error:
1. Read the error message and suggestions carefully
2. Check the `working_example` in the error response
3. Verify your field names and values
4. Use `dry_run=True` to test without creating
5. Try the minimal working example above first

## Quick Reference

| Field | Required | Example | Notes |
|-------|----------|---------|-------|
| `space_key` | ✅ | `"~911651470"` | Personal spaces start with ~ |
| `title` | ✅ | `"Page Title"` | Must be unique in space |
| `body` | ✅ | `"# Content"` | Markdown format |
| `parent_id` | ❌ | `"123456"` | Optional parent page |
| `dry_run` | ❌ | `true` | Test mode |

## Getting Help

If you continue to have issues:
1. Check the error code and suggestions in the response
2. Verify your authentication and permissions
3. Try the minimal working example
4. Use dry_run mode to test parameters
5. Check that the space exists and you have access