# MCP Atlassian JIRA Formatting Issues Guide

**Document Created:** July 29, 2025  
**For:** Claude Code instances working with MCP Atlassian  
**Issue:** Asterisks and underscores appearing literally instead of formatted text in JIRA

## Problem Summary

When using MCP Atlassian to create JIRA issues or add comments, formatting symbols like `**bold**` and `_italic_` appear literally in JIRA instead of being rendered as **bold** and *italic* text.

## Root Cause Analysis

The issue stems from a **format mismatch** between what the MCP sends and what JIRA Cloud expects:

### Current (Problematic) Flow:
1. User provides markdown text: `**bold text**`
2. MCP converts markdown to JIRA wiki markup: `*bold text*` 
3. Wiki markup string sent to JIRA Cloud v3 API
4. **PROBLEM**: JIRA Cloud v3 API expects ADF (Atlassian Document Format) JSON, not wiki markup strings
5. Result: Asterisks appear literally instead of formatting

### Technical Details:

- **File**: `src/mcp_atlassian/preprocessing/jira.py:307-313`
- **Method**: `JiraPreprocessor.markdown_to_jira()`
- **Issue**: Converts `**text**` → `*text*` (wiki markup) but JIRA Cloud needs ADF JSON
- **Library Limitation**: `atlassian-python-api` has known ADF support limitations

## Code Locations

Key files involved in the formatting pipeline:

1. **`src/mcp_atlassian/jira/comments.py:71`**
   ```python
   jira_formatted_comment = self._markdown_to_jira(comment)
   ```

2. **`src/mcp_atlassian/jira/issues.py:567`**
   ```python
   fields["description"] = self._markdown_to_jira(description)
   ```

3. **`src/mcp_atlassian/preprocessing/jira.py:233-380`**
   - Contains the `markdown_to_jira()` method performing the problematic conversion

## Current Workarounds

Until a permanent fix is implemented, Claude Code instances should:

### Option 1: Use Plain Text
- Avoid markdown formatting in JIRA descriptions and comments
- Use plain text without asterisks or underscores for emphasis

### Option 2: Use JIRA Wiki Markup Directly
- Instead of markdown `**bold**`, use JIRA wiki markup `*bold*`
- Instead of markdown `*italic*`, use JIRA wiki markup `_italic_`
- **Note**: This still may not work due to the ADF format requirement

### Option 3: Use HTML-like Formatting
- Some basic HTML tags may work: `<strong>bold</strong>`, `<em>italic</em>`
- Test before relying on this approach

## Permanent Solution Direction

The proper fix requires updating the MCP to generate ADF (Atlassian Document Format) JSON instead of wiki markup strings:

### Current Format (Problematic):
```python
description = "*bold text*"  # Wiki markup string
```

### Required Format (ADF JSON):
```python
description = {
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "bold text",
                    "marks": [{"type": "strong"}]
                }
            ]
        }
    ]
}
```

## Development Recommendations

When working on this codebase:

1. **Immediate**: Use plain text for JIRA operations to avoid formatting issues
2. **Investigation**: Consider implementing ADF JSON generation in `JiraPreprocessor`
3. **Testing**: Always test JIRA formatting with actual JIRA Cloud instances
4. **Library**: Evaluate alternatives to `atlassian-python-api` with better ADF support

## References

- [Atlassian Document Format (ADF)](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)
- [JIRA Cloud REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- MCP Atlassian Repository: `/Users/douglas.mason/Documents/GitHub/mcp-atlassian`

---

*This guide was created through systematic code analysis and investigation of the MCP Atlassian formatting pipeline.*