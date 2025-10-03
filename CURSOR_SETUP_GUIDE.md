# Cursor IDE Setup Guide for Enhanced MCP Atlassian Tools

This guide provides instructions for testing the enhanced MCP Atlassian server with Cursor IDE to validate that the original schema documentation issue has been resolved.

## Background

The original issue was that Cursor couldn't understand how to create Confluence pages because the MCP tool descriptions were too minimal. The enhanced implementation now provides:

- Comprehensive tool descriptions with parameter details
- Real usage examples with environment-specific values
- Clear required vs optional field specifications
- Copy-paste ready code samples

## Setup Instructions

### 1. Install Cursor IDE

Download and install Cursor from https://cursor.sh/

### 2. Configure MCP Atlassian Server

Create or update your Cursor MCP configuration file:

**Location:** `~/.cursor/mcp_servers.json` (or equivalent on your system)

```json
{
  "mcpServers": {
    "atlassian-enhanced": {
      "command": "uv",
      "args": ["run", "mcp-atlassian"],
      "cwd": "/Users/douglas.mason/Documents/GitHub/mcp-atlassian.worktrees/develop",
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net",
        "ATLASSIAN_EMAIL": "user@example.com",
        "ATLASSIAN_API_TOKEN": "ATATT3xFfGF0abcd1234efgh5678ijklmnopqrstuvwxyz"
      }
    }
  }
}
```

### 3. Test the Original Scenario

Open Cursor and try the exact prompt that caused the original issue:

```
Create a new page in my Confluence personal space using a wide variety of formatting to test that it is being created and displayed correctly.
```

## Expected Results

With the enhanced tool schemas, Cursor should now be able to:

1. **Discover available tools** - See all enhanced meta-tools including `resource_manager_tool`

2. **Understand tool parameters** - The `resource_manager_tool` description now includes:
   - Detailed parameter explanations
   - Available resources (page, issue, comment, etc.)
   - Supported operations (create, get, update, delete, add)
   - Required vs optional fields

3. **Use environment-specific examples** - The description includes examples with:
   - Personal space key: `~1234567890`
   - Project key: `FTEST`
   - Real data structures for Confluence page creation

4. **Generate correct tool calls** - Cursor should be able to create:
   ```python
   await resource_manager_tool(
       service="confluence",
       resource="page",
       operation="create",
       data={
           "space_key": "~1234567890",
           "title": "Test Page with Rich Formatting",
           "body": "# Welcome to My Test Page\n\nThis is a test page with **bold** and *italic* text..."
       }
   )
   ```

## Validation Checklist

When testing with Cursor, verify:

- [ ] **Tool Discovery**: Cursor can see the `resource_manager_tool`
- [ ] **Parameter Understanding**: Cursor understands the `service`, `resource`, `operation`, and `data` parameters
- [ ] **Example Usage**: Cursor can extract the Confluence page creation example
- [ ] **Environment Values**: Cursor uses the correct space key (`~1234567890`) and format
- [ ] **Data Structure**: Cursor understands the required fields (space_key, title, body)
- [ ] **Success**: The tool call is properly formatted and executable

## Troubleshooting

If Cursor still has issues:

1. **Check MCP server connection** - Verify the server starts without errors
2. **Validate tool listing** - Use `get_tool_examples` to see available examples
3. **Check schema discovery** - Use `get_resource_schema` for specific operation details
4. **Review logs** - Check Cursor's MCP connection logs for any protocol issues

## Additional Test Scenarios

Try these additional scenarios to validate the enhancements:

### 1. Search Confluence Pages
```
Search for pages in my personal Confluence space that contain "test"
```

Expected tool usage:
```python
await search_engine_tool(
    service="confluence",
    query_type="cql",
    query="space = '~1234567890' AND type = page AND title ~ 'test'"
)
```

### 2. Create Jira Issue
```
Create a high priority bug issue in the FTEST project about authentication problems
```

Expected tool usage:
```python
await resource_manager_tool(
    service="jira",
    resource="issue",
    operation="create",
    data={
        "project_key": "FTEST",
        "summary": "Authentication problems",
        "issue_type": "Bug",
        "priority": "High"
    }
)
```

### 3. Get Tool Examples
```
Show me examples of common operations I can perform
```

Expected tool usage:
```python
await get_tool_examples()
```

## Success Criteria

The enhancement is successful if:

1. **Original issue resolved** - Cursor can now create Confluence pages without confusion
2. **Schema clarity** - Tool parameters and data structures are clearly understood
3. **Practical examples** - Real, working examples are available and usable
4. **Environment integration** - Uses actual space keys and project names from configuration

## Documentation

After successful testing, document:

- What scenarios worked correctly
- Any remaining issues or improvements needed
- Performance and usability observations
- Recommendations for further enhancements