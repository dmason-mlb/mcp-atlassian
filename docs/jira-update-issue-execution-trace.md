# JIRA Issue Update Execution Trace Analysis

This document provides a comprehensive precision trace analysis of the execution flow when updating a JIRA issue (specifically FRAMED-1294) with complex wiki markup formatting through the MCP Atlassian server.

## Overview

The trace follows the complete execution path from the MCP tool entry point through authentication, format conversion, and the final API call to update a JIRA issue with wiki markup content.

## Call Flow Diagram - Vertical Indented Style

```
[update_issue] (file: /src/mcp_atlassian/servers/jira.py, line: 858)
↓
[@check_write_access] (file: /src/mcp_atlassian/utils/decorators.py, line: 18)
↓
[JiraIssueService::update_issue] (file: /src/mcp_atlassian/jira/issues.py, line: 986)
  ↓
  [JiraIssueService::_markdown_to_jira] (file: /src/mcp_atlassian/jira/issues.py, line: 1019) ? if "description" in update_fields
  ↓
  [JiraClient::_markdown_to_jira] (file: /src/mcp_atlassian/jira/client.py, line: 207)
    ↓
    [JiraPreprocessor::markdown_to_jira] (file: /src/mcp_atlassian/preprocessing/jira.py, line: 235)
      ↓
      [FormatRouter::convert_markdown] (file: /src/mcp_atlassian/formatting/router.py, line: 79)
        ↓
        [FormatRouter::detect_deployment_type] (file: /src/mcp_atlassian/formatting/router.py, line: 156)
        ↓
        [FormatRouter::_get_format_for_deployment_with_rollout] (file: /src/mcp_atlassian/formatting/router.py, line: 247) ? if not force_format
        ↓
        [ASTBasedADFGenerator::markdown_to_adf] (file: /src/mcp_atlassian/formatting/adf_ast.py, line: imported) ? if format_type == FormatType.ADF
        →
        [FormatRouter::_markdown_to_wiki_markup] (file: /src/mcp_atlassian/formatting/router.py, line: 288) ? if format_type == FormatType.WIKI_MARKUP
  ↓
  [Jira::update_issue] (file: atlassian-python-api library, line: external) ? if update_fields
  ↓
  [JiraIssueService::upload_attachments] (file: /src/mcp_atlassian/jira/issues.py, line: 1069) ? if "attachments" in kwargs
  ↓
  [Jira::get_issue] (file: atlassian-python-api library, line: external)
  ↓
  [JiraIssue::from_api_response] (file: /src/mcp_atlassian/models/jira/issue.py, line: imported)
```

## Branching & Side Effect Analysis

### Conditional Execution Table

| Location | Condition | Branches | Uncertain |
|----------|-----------|----------|-----------|
| issues.py:1019 | if "description" in update_fields | _markdown_to_jira(), else skip | No |
| issues.py:1025 | if key == "status" | _update_issue_with_status(), else continue | No |
| issues.py:1031 | if key == "attachments" | process later, else continue | No |
| issues.py:1039 | if key == "assignee" | _get_account_id(), else continue | No |
| issues.py:1061 | if update_fields | jira.update_issue(), else skip | No |
| issues.py:1067 | if "attachments" in kwargs | upload_attachments(), else skip | No |
| router.py:108 | if force_format | use forced format, else auto-detect | No |
| router.py:120 | if format_type == FormatType.ADF | use ADF generator, else wiki markup | No |
| router.py:174 | if cache_key in deployment_cache | return cached, else detect | No |
| router.py:196 | if pattern.match(hostname) | CLOUD deployment, else continue | No |

### Side Effects

```
Side Effects:
- [network] REST API PUT request to /rest/api/2/issue/{issueKey} (issues.py:1062)
- [network] REST API GET request to fetch updated issue (issues.py:1082)
- [filesystem] Upload attachment files if provided (issues.py:1069)
- [state] Update deployment type cache with TTL (router.py:199)
- [state] Update performance metrics counters (router.py:151)
- [memory] LRU cache for deployment detection results (router.py:59)
- [memory] Performance metrics collection (router.py:70)
```

## Usage and Entry Points

### Usage Points

```
Usage Points:
1. servers/jira.py:858 - MCP tool endpoint for updating JIRA issues via AI assistant
2. tests/integration/test_mcp_protocol.py:## - Integration tests for MCP protocol compliance
3. README.md:## - Documentation example showing tool usage
4. External AI assistants - Called when user requests JIRA issue updates
```

### Entry Points

```
Entry Points:
- update_issue MCP tool (context: AI assistant receives user request to update JIRA issue)
- FastMCP framework (context: routes tool calls to appropriate handlers)
- HTTP transport layer (context: SSE or streamable HTTP requests trigger tool execution)
```

## Key Components

### 1. MCP Tool Entry (servers/jira.py:858)
- **Tool**: `mcp__atlassian__jira_update_issue`
- **Decorator**: `@check_write_access` validates not in read-only mode
- **Parameters**: issue_key, fields dict, optional additional_fields

### 2. Service Layer Processing (jira/issues.py:986-1098)
- **Method**: `JiraIssueService.update_issue()`
- **Line 1019**: Calls `_markdown_to_jira()` on description field
- **Line 1062**: Calls `self.jira.update_issue()` with formatted fields

### 3. Text Format Conversion (preprocessing/jira.py:235)
- **Method**: `JiraPreprocessor.markdown_to_jira(input_text, enable_adf=True)`
- **Delegates to**: `FormatRouter.convert_markdown()`
- **Configuration**: ADF can be controlled via env vars: ATLASSIAN_ENABLE_ADF, JIRA_ENABLE_ADF

### 4. Format Routing Logic (formatting/router.py:79-155)
- **Deployment Detection**: Based on base URL patterns (TTL cached)
- **Cloud (*.atlassian.net)**: Converts to ADF JSON via ASTBasedADFGenerator
- **Server/DC**: Returns wiki markup (or passes through if already wiki)
- **Performance**: Monitoring with 50ms threshold warnings

### 5. API Client Execution (jira/client.py + atlassian-python-api)
- **Client**: JiraClient wraps atlassian.Jira class
- **Authentication**: OAuth, PAT, or Basic auth configured in session
- **API Call**: REST API PUT request to /rest/api/2/issue/{issueKey}

## Wiki Markup Processing

For the provided wiki markup description, the processing depends on the JIRA deployment type:

1. **Server/DC Instance**: Wiki markup passes through unchanged
2. **Cloud Instance**: Wiki markup is converted to ADF (Atlassian Document Format) JSON

The system automatically detects the deployment type based on the URL:
- URLs matching `*.atlassian.net` are identified as Cloud
- Other URLs are treated as Server/DC deployments

## Performance Optimizations

1. **TTL Cache**: Deployment detection results cached for 1 hour
2. **Compiled Regex**: Pre-compiled patterns for efficient URL matching
3. **Performance Metrics**: Comprehensive monitoring with configurable thresholds
4. **LRU Cache**: For frequently converted markdown patterns

## Error Handling

1. **Authentication Errors**: HTTP 401/403 wrapped as MCPAtlassianAuthenticationError
2. **Field Validation**: Errors propagated with context
3. **Attachment Failures**: Logged but don't block the main update operation
4. **Format Conversion**: Fallback to legacy conversion on failure

## Configuration Options

### Environment Variables
- `ATLASSIAN_ENABLE_ADF`: Force enable ADF conversion
- `ATLASSIAN_DISABLE_ADF`: Force disable ADF conversion
- `JIRA_ENABLE_ADF`: JIRA-specific ADF control

### Read-Only Mode
The `@check_write_access` decorator ensures that update operations are blocked when the system is configured in read-only mode.

## Summary

The JIRA issue update flow is a multi-layered process that handles:
1. Security validation (write access check)
2. Field processing and normalization
3. Format detection and conversion based on deployment type
4. Authentication and API execution
5. Error handling and recovery

The wiki markup provided in the example would be preserved as-is for Server/DC instances or converted to ADF format for Cloud instances, ensuring compatibility with the target JIRA deployment.
