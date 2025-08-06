# MCP Atlassian Issues to Fix

## Description Format Issues

### Issue 1: Description Field Validation Error
**Problem**: When creating or updating Jira issues, the description field fails with validation error:
```
Validation error: description: Operation value must be an Atlassian Document (see the Atlassian Document Format)
```

**Impact**: Cannot add detailed descriptions to Jira tickets through the MCP interface.

**Root Cause**: The MCP is not properly formatting descriptions according to Atlassian Document Format (ADF).

**Expected Behavior**: Should accept plain text descriptions and convert them to proper ADF format internally.

### Issue 2: Comment Body Validation Error  
**Problem**: When adding comments to Jira issues, the comment field fails with validation error:
```
Error adding comment: Validation error: comment: Comment body is not valid!
```

**Impact**: Cannot add comments to existing Jira tickets through the MCP interface.

**Root Cause**: Similar to description issue - comments need to be in ADF format but MCP isn't handling the conversion.

**Expected Behavior**: Should accept markdown or plain text comments and convert to ADF format.

## Missing Features

### Issue 3: File Attachment Support
**Problem**: No apparent method to attach files (images, documents) to Jira tickets through the MCP.

**Impact**: Cannot attach screenshots or other supporting files to bug reports.

**Expected Behavior**: Should have a method to attach files to issues, either through:
- Direct file upload parameter in create/update issue
- Separate attachment upload method
- Support for base64 encoded files

## Suggested Fixes

1. **Implement ADF Conversion**: Add automatic conversion from plain text/markdown to Atlassian Document Format for description and comment fields.

2. **Add File Attachment Support**: Implement file attachment functionality through one of these approaches:
   - `attachments` parameter in `jira_update_issue` that accepts file paths or base64 data
   - Separate `jira_add_attachment` method
   - Support in `jira_create_issue` for initial file attachments

3. **Better Error Handling**: Provide more descriptive error messages that explain the ADF format requirement and suggest workarounds.

4. **Documentation**: Add examples of proper ADF format for descriptions and comments.

## Test Case
Created ticket **FTEST-9** "MLB App Display Issue - Score Layout and Navigation Problems" where these issues were encountered when trying to:
1. Add detailed description with formatting
2. Add explanatory comment  
3. Attach screenshot image

## Issue 4: Missing JiraAdapter.add_attachment Method

### Problem
When attempting to upload file attachments to Jira issues through the `jira_update_issue` method with the `attachments` parameter, the operation fails with:

```
'JiraAdapter' object has no attribute 'add_attachment'
```

### Detailed Error Context
- **Ticket**: FTEST-9 "MLB App Display Issue - Score Layout and Navigation Problems"
- **Attempted Action**: Upload screenshot file via `attachments` parameter
- **File Path**: `/tmp/mlb_app_screenshot.txt`
- **Result**: `attachment_results.failed` with missing method error

### Impact
- Cannot attach files to Jira issues through MCP
- Severely limits bug reporting capabilities where visual evidence is needed
- Forces manual attachment through Jira web interface

### Root Cause Analysis
The `JiraAdapter` class is missing the `add_attachment` method that the `jira_update_issue` function expects to call when processing the `attachments` parameter.

### Implementation Requirements

#### Required Method Signature
```python
def add_attachment(self, issue_key: str, attachment_path: str) -> dict:
    """
    Add an attachment to a Jira issue
    
    Args:
        issue_key: The Jira issue key (e.g., 'FTEST-9')
        attachment_path: Path to the file to attach
        
    Returns:
        dict: Result of attachment operation with success/failure status
    """
```

#### Expected Behavior
1. **File Validation**: Check if file exists and is readable
2. **Size Limits**: Respect Jira attachment size limits
3. **File Type Support**: Handle common file types (images, documents, logs)
4. **Error Handling**: Proper error messages for various failure scenarios
5. **Return Format**: Consistent response format matching other MCP methods

#### Integration Points
- Should be called from `jira_update_issue` when `attachments` parameter is provided
- Should support both single file and multiple file attachments
- Should work with various file types including images, text files, PDFs

### Test Case
```python
# This should work after implementation
result = jira_update_issue(
    issue_key="FTEST-9",
    fields={},
    attachments="/path/to/screenshot.png"
)
```

### Priority
**Critical** - File attachments are essential for bug reporting and documentation workflows.

## Overall Priority
High - These are core functionalities needed for basic Jira ticket management.