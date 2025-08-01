# JIRA ADF Format Fix Summary

## Issue Description
The JIRA update issue tool was failing with "Operation value must be a string" error when updating issues on JIRA Cloud instances with complex formatting.

## Root Cause Analysis

### 1. Deployment Type Detection
- JIRA Cloud instances (*.atlassian.net) require ADF (Atlassian Document Format) JSON
- Server/DC instances use wiki markup strings
- The FormatRouter correctly detected Cloud deployment and selected ADF format

### 2. Format Conversion Flow
- Input text (markdown or wiki markup) → JiraPreprocessor.markdown_to_jira()
- For Cloud: Converts to ADF dictionary using ASTBasedADFGenerator
- For Server/DC: Converts to wiki markup string

### 3. The Bug
- The atlassian-python-api library's update_issue() method expects field values as strings
- When ADF format was used, we were passing a dictionary directly
- JIRA Cloud API requires ADF content to be JSON-serialized string, not a raw dictionary

## Fix Implementation

In `/src/mcp_atlassian/jira/issues.py`, modified the update_issue method:

```python
# Handle both ADF (dict) and wiki markup (str) formats
if isinstance(description_content, dict):
    # For ADF format (Cloud), JIRA expects a JSON string
    logger.info("[DEBUG] Converting ADF dict to JSON string for API")
    update_fields["description"] = json.dumps(description_content)
else:
    # For wiki markup (Server/DC), use as-is
    update_fields["description"] = description_content
```

## Testing Results

### Test 1: Markdown Input
- Input: Proper markdown formatting
- Result: ✅ Successfully converted to ADF and updated in JIRA

### Test 2: Wiki Markup Input
- Input: JIRA wiki markup syntax
- Result: ✅ Successfully converted to ADF and updated in JIRA

Both tests now work correctly because:
1. The FormatRouter detects Cloud deployment
2. Converts any input (markdown or wiki) to ADF format
3. The fix serializes the ADF dictionary to JSON string
4. JIRA Cloud API accepts the properly formatted request

## Key Learnings

1. **JIRA Cloud API Requirement**: Description field must be a JSON string when using ADF format
2. **Format Detection**: The system correctly auto-detects deployment type based on URL
3. **Universal Conversion**: Both markdown and wiki markup inputs work because they're converted to the appropriate format for the deployment type

## Debug Logging Added

Enhanced debug logging was added to:
- FormatRouter: Deployment detection and format selection
- JiraPreprocessor: Format conversion process
- JiraIssueService: API payload structure

This logging helps trace the exact conversion flow and identify issues quickly.