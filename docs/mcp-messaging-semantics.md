# MCP Messaging Semantics and Tool Result Sequencing

## Overview

This document explains the messaging semantics required by the Model Context Protocol (MCP) when integrated with Anthropic's API, specifically regarding tool_use and tool_result sequencing.

## The Problem

When using MCP tools with Anthropic's API, every `tool_use` block sent by the assistant must be immediately followed by a corresponding `tool_result` block in the user's response. This is a strict requirement of the Anthropic messages API.

### Error Example
```
API Error 400: "messages.112: `tool_use` ids were found without `tool_result` blocks immediately after: toolu_01SRcSArRcRoPdA6qnUk6kXj"
```

This error occurs when:
1. The assistant sends a `tool_use` request
2. The MCP server fails to emit a proper `tool_result` response
3. The API rejects the message sequence as invalid

## Root Causes

### 1. Uncaught Exceptions in Tools

When a tool function raises an exception that isn't caught, FastMCP cannot emit a proper tool_result. Common sources include:

- **Access control decorators** (e.g., `@check_write_access`) raising `ValueError`
- **Dependency providers** (e.g., `get_jira_fetcher`) raising exceptions when configuration is missing
- **Unexpected errors** during tool execution

### 2. Expected Behavior

FastMCP expects all tool functions to:
- Return a JSON string on success
- Return a JSON error string on failure
- Never raise uncaught exceptions

## The Solution

### 1. Safe Tool Result Wrapper

We implemented a `safe_tool_result` decorator that catches all exceptions and converts them to JSON error responses:

```python
@safe_tool_result
async def my_tool(ctx: Context, ...) -> str:
    # Tool implementation
    return json.dumps({"result": "success"})
```

### 2. Automatic Tool Wrapping

All tools are automatically wrapped with error handling when the server starts:

```python
# In main.py after mounting sub-servers
wrap_all_tools_with_error_handling(jira_mcp)
wrap_all_tools_with_error_handling(confluence_mcp)
```

### 3. Decorator Modifications

The `@check_write_access` decorator now returns JSON errors instead of raising exceptions:

```python
if app_lifespan_ctx is not None and app_lifespan_ctx.read_only:
    return json.dumps({
        "error": f"Cannot {action_description} in read-only mode.",
        "success": False,
        "read_only_mode": True
    }, indent=2, ensure_ascii=False)
```

## Error Response Format

All error responses follow a consistent JSON format:

```json
{
    "error": "Human-readable error message",
    "success": false,
    "error_type": "validation_error|unexpected_error",
    "tool": "tool_name",
    // Additional context fields as needed
}
```

### Error Types

- **validation_error**: Known validation failures (missing config, read-only mode, etc.)
- **unexpected_error**: Unforeseen exceptions during execution

## Testing

### Integration Tests

The `test_tool_result_sequencing.py` file contains comprehensive tests for:
- Read-only mode enforcement
- Missing configuration handling
- Exception handling
- Successful execution paths

### Live Validation

Use the `test_live_validation.py` script to verify the fix in a real environment:

```bash
python test_live_validation.py
```

## Best Practices

### 1. Always Return JSON

Tools should always return valid JSON strings:

```python
# Good
return json.dumps({"result": data})

# Bad
return data  # Not JSON
raise ValueError("Error")  # Uncaught exception
```

### 2. Use Consistent Error Format

When handling errors manually, use the standard format:

```python
return json.dumps({
    "error": "Descriptive error message",
    "success": False,
    "error_type": "validation_error"
})
```

### 3. Leverage Automatic Wrapping

Don't manually wrap every tool with `@safe_tool_result`. The automatic wrapping ensures all tools are protected, including those added in the future.

### 4. Test Error Paths

Always test both success and error paths for tools:
- Valid input → successful result
- Invalid input → JSON error response
- Missing dependencies → JSON error response
- Unexpected exceptions → JSON error response

## Troubleshooting

### Still Getting tool_result Errors?

1. **Check tool registration**: Ensure tools are registered through FastMCP's `@tool` decorator
2. **Verify wrapping**: Check that `wrap_all_tools_with_error_handling` is called after mounting
3. **Test in isolation**: Use the validation script to test specific scenarios
4. **Enable debug logging**: Set log level to DEBUG to see error handling in action

### Common Pitfalls

1. **Direct imports**: Importing tool functions directly bypasses wrapping
2. **Early exceptions**: Exceptions before the wrapper is applied won't be caught
3. **Non-async tools**: The wrapper expects async functions

## Implementation Details

### Tool Wrapper Utility

The `tool_wrapper.py` utility automatically wraps all tools:

```python
def wrap_all_tools_with_error_handling(mcp_server: FastMCP[Any]) -> None:
    tools = mcp_server._tool_manager._tools
    for tool_name, tool in tools.items():
        if not already_wrapped(tool.fn):
            tool.fn = safe_tool_result(tool.fn)
```

### Decorator Stack

When multiple decorators are used, they're applied bottom to top:

```python
@jira_mcp.tool(tags={"jira", "write"})  # Applied third
@check_write_access                      # Applied second  
@safe_tool_result                        # Applied first (closest to function)
async def create_issue(...):
    pass
```

## References

- [Anthropic Messages API Documentation](https://docs.anthropic.com/claude/reference/messages)
- [Model Context Protocol Specification](https://github.com/anthropics/model-context-protocol)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)