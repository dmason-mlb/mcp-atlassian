# JIRA Formatting Issue Analysis - MCP Atlassian Tool Documentation Gap

**Date:** August 27, 2025  
**Issue:** JIRA issue creation resulted in broken formatting due to unclear tool documentation  
**Impact:** Created tickets with unreadable content requiring manual correction  

## Problem Summary

The MCP Atlassian tool documentation for `jira_create_issue` and `jira_update_issue` does not specify the expected markup format for the `description` parameter, leading to incorrect formatting assumptions and broken ticket content.

## Root Cause Analysis

### Documentation Inconsistency
- **`jira_add_comment`**: Explicitly states "Comment text in Markdown format"
- **`jira_create_issue`**: No format specification for `description` parameter
- **`jira_update_issue`**: No format specification for `description` parameter

### Incorrect Initial Assumption
Based on traditional JIRA experience, I assumed the description field would use JIRA wiki markup syntax (e.g., `h2.`, `{code:kotlin}`, `{{monospace}}`). This assumption was reinforced by the lack of explicit guidance in the tool documentation.

## Initial Failed Tool Request

### Original `jira_create_issue` Call
```python
mcp__atlassian__jira_create_issue(
    project_key="MLBAPP",
    summary="Mini Gameday displays blank content after Gameday navigation in QA environment (authenticated users)",
    issue_type="Bug",
    description="h2. Summary\nThe mini gameday component on the Home screen displays a completely blank/black content area after users navigate from the full Gameday view back to Home screen. This issue is specific to authenticated users in the QA environment during postseason games and prevents critical postseason testing workflows.\n\nh2. Environment\n* *Environment:* QA\n* *Platform:* Android Mobile\n* *App Version:* Current development build\n* *Device:* Android emulator and physical devices\n* *Affected Users:* Authenticated users during postseason testing\n\nh2. Impact\n* *User Impact:* Complete loss of mini gameday functionality for authenticated users\n* *Testing Impact:* Blocks postseason testing scenarios\n* *Business Impact:* Critical postseason features cannot be validated\n* *Frequency:* 100% reproduction rate under specific conditions\n\nh2. Reproduction Steps\nh3. Prerequisites\n# QA environment access\n# Android app with postseason configuration\n# Valid QA user account\n\nh3. Steps to Reproduce\n# Launch MLB Android app in QA environment\n# Log in with QA account credentials\n# Navigate to Home screen (mini gameday displays correctly if present)\n# Navigate to a postseason game's full Gameday view\n# Interact with gameday content and allow it to fully load\n# Navigate back to Home screen using back button or tab navigation\n# *Observe:* Mini gameday component shows team logos/scores but content area is completely black\n# *Confirm:* Pull-to-refresh does not resolve the issue\n\nh2. Expected vs Actual Behavior\n*Expected:* Mini gameday should display correctly with all content visible (scoreboard, batter/pitcher info, game metadata) after navigation from Gameday back to Home.\n\n*Actual:* Mini gameday displays team logos and scores at the top, but the main content area is completely black/blank. Interactive elements are non-functional.\n\nh2. Root Cause Analysis\n*Primary Issue:* WebView Cache Corruption\n\n* The {{GamedayMini}} component uses a shared WebView cache ({{MutableMap<String, SurfaceWebView>}})\n* Navigation from full Gameday to Home screen doesn't properly clear the WebView cache\n* Cached WebView state from full Gameday is incompatible with mini gameday display requirements\n* The {{GamedayMiniBattersBox}} component (which renders the main content area) fails due to corrupted cache state\n\nh3. Technical Components Affected\n* {{GamedayMini.kt}} (main component)\n* {{GamedayMiniBattersBox.kt}} (WebView rendering)\n* WebView cache management system\n* GraphQL endpoint: {{data-graph-qa.mlb.com/graphql}}\n\nh2. Workaround\n*Temporary Solution:* Log out of account, perform pull-to-refresh, then log back in. This temporarily resolves the issue but it reappears upon subsequent navigation.\n\nh2. Proposed Solution\nImplement WebView cache clearing on navigation from Gameday back to Home screen:\n\n{code:kotlin}\n@Composable\nfun GamedayMini(\n    // existing parameters\n    navigationSource: NavigationSource = NavigationSource.DIRECT,\n) {\n    LaunchedEffect(navigationSource) {\n        if (navigationSource == NavigationSource.FROM_GAMEDAY) {\n            webViewCache.clear() // Clear corrupted cache\n        }\n    }\n    // rest of implementation\n}\n{code}\n\nh2. Investigation Materials\nAll investigation materials stored in: {{Test/Bugs/postseason-mini-gameday-blank/}}\n\n* Comprehensive technical analysis\n* Test scripts for API validation\n* Detailed reproduction steps\n* Proposed implementation solutions\n\nh2. Acceptance Criteria\n* Mini gameday displays correctly after Gameday → Home navigation (100% success rate)\n* Pull-to-refresh maintains functionality\n* Authentication state changes handled properly\n* No blank content areas observed\n* Multiple navigation cycles work consistently",
    additional_fields={"priority": {"name": "High"}, "labels": ["postseason", "android", "webview", "qa-environment", "mini-gameday"]}
)
```

### Resulting Broken Formatting
The JIRA API returned the content with broken formatting:
- Headers appeared as plain text (`h2. Summary` instead of a proper heading)
- Wiki markup syntax was not interpreted (`{{code}}` displayed as literal text)
- Code blocks failed to render (`{code:kotlin}` showed as plain text)
- List formatting was inconsistent
- Overall readability was severely compromised

## Discovery of Correct Format

### Through Trial and Error
When attempting to add a comment using Markdown syntax (`##` for headers, ``` for code blocks), the formatting worked perfectly. This led to the realization that JIRA descriptions also expect Markdown format.

### Working Solution
```python
mcp__atlassian__jira_update_issue(
    issue_key="MLBAPP-5479",
    fields={
        "description": "## Summary\nThe mini gameday component...\n\n## Environment\n- **Environment:** QA\n- **Platform:** Android Mobile\n...\n\n```kotlin\n@Composable\nfun GamedayMini(\n    // existing parameters\n    navigationSource: NavigationSource = NavigationSource.DIRECT,\n) {\n    LaunchedEffect(navigationSource) {\n        if (navigationSource == NavigationSource.FROM_GAMEDAY) {\n            webViewCache.clear() // Clear corrupted cache\n        }\n    }\n    // rest of implementation\n}\n```"
    }
)
```

## Key Findings

### Correct Format Expectations
- **Descriptions**: Markdown format (same as comments)
- **Comments**: Explicitly documented as Markdown format
- **Headers**: Use `##` not `h2.`
- **Code blocks**: Use ``` not `{code:}`
- **Inline code**: Use backticks not `{{}}`
- **Bold text**: Use `**bold**` not `*bold*`

### API Behavior
- JIRA API accepts the input without validation errors
- Invalid formatting is rendered as plain text rather than rejected
- No warning or error indicates formatting issues
- Users must visually inspect the created ticket to detect problems

## Impact Assessment

### User Experience Impact
- **High**: Created tickets with unreadable formatting
- **Time Loss**: Required manual correction and reformatting
- **Professional Impact**: Poorly formatted tickets reflect negatively on quality
- **Workflow Disruption**: Broke the automated investigation → ticket creation flow

### Development Process Impact
- **Confidence Loss**: Uncertainty about tool behavior and reliability
- **Additional Testing**: Required experimentation to determine correct format
- **Documentation Debt**: Need to document findings for future use

## Recommended Solutions

### 1. Immediate Documentation Updates

#### Update `jira_create_issue` Documentation
```python
def jira_create_issue(
    project_key: str,
    summary: str,
    issue_type: str,
    description: str,  # Add: "Issue description in Markdown format (same as comments)"
    assignee: Optional[str] = None,
    components: Optional[str] = None,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new Jira issue with optional Epic link or parent for subtasks.

    Args:
        ctx: The FastMCP context.
        project_key: The JIRA project key.
        summary: Summary/title of the issue.
        issue_type: Issue type (e.g., 'Task', 'Bug', 'Story', 'Epic', 'Subtask').
        assignee: Assignee's user identifier (string): Email, display name, or account ID.
        description: Issue description in Markdown format (e.g., ## Headers, **bold**, ```code blocks```).
        components: Comma-separated list of component names.
        additional_fields: Dictionary of additional fields.
    ...
```

#### Update `jira_update_issue` Documentation
```python
def jira_update_issue(
    issue_key: str,
    fields: Dict[str, Any],  # Add note: "For 'description' field, use Markdown format"
    additional_fields: Optional[Dict[str, Any]] = None,
    attachments: Optional[str] = None,
) -> str:
    """Update an existing Jira issue including changing status, adding Epic links, updating fields, etc.

    Args:
        ctx: The FastMCP context.
        issue_key: Jira issue key.
        fields: Dictionary of fields to update. For 'description' field, use Markdown format (## headers, **bold**, ```code blocks```).
        additional_fields: Optional dictionary of additional fields.
        attachments: Optional JSON array string or comma-separated list of file paths.
    ...
```

### 2. Format Validation

#### Add Input Validation Helper
```python
def validate_jira_description_format(description: str) -> List[str]:
    """Validate JIRA description format and return warnings for common issues."""
    warnings = []
    
    # Check for wiki markup that should be Markdown
    if 'h1.' in description or 'h2.' in description or 'h3.' in description:
        warnings.append("Found wiki markup headers (h1., h2., h3.). Use Markdown headers (##) instead.")
    
    if '{code:' in description:
        warnings.append("Found wiki markup code blocks ({code:}). Use Markdown code blocks (```) instead.")
    
    if '{{' in description and '}}' in description:
        warnings.append("Found wiki markup monospace ({{}}). Use Markdown inline code (`) instead.")
    
    return warnings
```

### 3. Enhanced Error Handling

#### Pre-submission Format Check
```python
def create_issue_with_validation(description: str, **kwargs):
    """Create JIRA issue with format validation."""
    warnings = validate_jira_description_format(description)
    
    if warnings:
        formatted_warnings = "\n".join(f"- {warning}" for warning in warnings)
        raise ValueError(f"Description format issues detected:\n{formatted_warnings}")
    
    return jira_create_issue(description=description, **kwargs)
```

### 4. Documentation Examples

#### Add Format Examples to Tool Documentation
```markdown
## JIRA Description Format Examples

### Correct Markdown Format:
```markdown
## Summary
This is a **bold** statement with `inline code`.

### Steps to Reproduce
1. First step
2. Second step

### Code Example
```python
def example_function():
    return "Hello World"
```

### Wrong Wiki Markup Format:
```
h2. Summary
This is a *bold* statement with {{inline code}}.

h3. Steps to Reproduce
# First step
# Second step

h3. Code Example
{code:python}
def example_function():
    return "Hello World"
{code}
```

## Testing Recommendations

### 1. Automated Format Testing
- Create unit tests that validate description formatting
- Test with both correct and incorrect format examples
- Verify API response matches expected rendering

### 2. Documentation Testing
- Include format examples in tool documentation
- Test examples to ensure they work correctly
- Validate that documentation matches actual API behavior

### 3. User Experience Testing
- Test common formatting scenarios users might encounter
- Validate that error messages are helpful and actionable
- Ensure format validation doesn't break valid use cases

## Prevention Measures

### 1. Clear Documentation Standards
- All text input parameters should specify their expected format
- Provide examples of correct and incorrect usage
- Link to format reference documentation when applicable

### 2. Consistent Format Requirements
- Use the same format (Markdown) for all text fields across JIRA tools
- Document any exceptions or special cases clearly
- Maintain consistency with Confluence tools where applicable

### 3. Validation and Feedback
- Implement client-side validation for common format errors
- Provide clear error messages with correction suggestions
- Consider warnings for potentially incorrect formatting

## Conclusion

This formatting issue demonstrates the critical importance of comprehensive tool documentation, especially for parameters that accept formatted text. The lack of format specification for JIRA description fields led to:

1. **Broken user experience**: Unreadable ticket content
2. **Time waste**: Manual correction and debugging
3. **Reduced confidence**: Uncertainty about tool reliability

By implementing the recommended documentation updates, validation helpers, and testing procedures, we can prevent similar issues and improve the overall developer experience with the MCP Atlassian tools.

### Key Takeaway
**All text input parameters in MCP tools should explicitly specify their expected format, with examples of correct usage.** This is especially critical for formatted text fields that may have multiple possible markup syntaxes.

---
**Status:** Documented - Ready for implementation  
**Priority:** High - Affects user experience and tool reliability  
**Next Steps:** Update tool documentation and implement validation helpers