# MCP Atlassian Toolset

## Overview

The MCP Atlassian server provides AI assistants with secure access to Atlassian Jira and Confluence through a **meta-tool architecture**. This server has been optimized for token efficiency, consolidating 42+ legacy tools into **11 powerful meta-tools** that achieve the same functionality with 65%+ fewer tokens.

### Meta-Tool Benefits
- **Token Efficient**: 65%+ reduction in context window usage
- **Universal Operations**: Single tools handle multiple resource types
- **Parallel Processing**: Built-in bulk operations support
- **Schema Discovery**: Dynamic operation documentation
- **Future-Proof**: Easily extensible for new Atlassian features

## How to Use

See the [main README](../README.md) for installation and configuration instructions. Once configured, these tools are available through any MCP-compatible client.

## Tool Summary

| Tool | Purpose | Primary Use Cases | Services |
|------|---------|-------------------|----------|
| [resource_manager_tool](#resource_manager_tool) | Universal CRUD operations | Create/read/update/delete any resource | Jira, Confluence |
| [search_engine_tool](#search_engine_tool) | Universal search | JQL, CQL, and text search across services | Jira, Confluence |
| [workflow_engine_tool](#workflow_engine_tool) | Workflow management | Issue transitions, status changes | Jira |
| [relationship_manager_tool](#relationship_manager_tool) | Issue relationships | Links, epics, parent-child hierarchies | Jira |
| [batch_processor_tool](#batch_processor_tool) | Bulk operations | Parallel create/update/delete operations | Jira, Confluence |
| [attachment_handler_tool](#attachment_handler_tool) | File management | Upload, download, manage attachments | Jira, Confluence |
| [get_resource_schema](#get_resource_schema) | Schema discovery | Get field requirements for operations | Jira, Confluence |
| [get_capabilities](#get_capabilities) | Service capabilities | Discover available resources and operations | Jira, Confluence |
| [get_tool_examples](#get_tool_examples) | Usage examples | Get copy-paste ready examples | Jira, Confluence |
| [connection_health_check](#connection_health_check) | Health monitoring | Validate connectivity and authentication | Jira, Confluence |
| [debug_context_info](#debug_context_info) | Debugging | Inspect MCP context and diagnose issues | System |

## Core Meta-Tools

### resource_manager_tool

**Purpose**: Universal CRUD operations for all Jira and Confluence resources.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ✅ | "jira" or "confluence" |
| resource | string | ✅ | Resource type (see supported resources below) |
| operation | string | ✅ | "create", "get", "update", "delete", "add" |
| identifier | string | ❌ | Resource ID/key (required for get/update/delete) |
| data | object | ❌ | Resource data (required for create/update/add) |
| options | object | ❌ | Additional parameters (expand, fields, etc.) |

**Supported Resources**:

**Jira Resources**:
- `issue` - Jira issues/tickets
- `comment` - Comments on issues
- `worklog` - Time tracking entries
- `attachment` - File attachments
- `link` - Issue links between issues
- `sprint` - Agile sprint management
- `version` - Project versions/releases

**Confluence Resources**:
- `page` - Wiki pages and documents
- `comment` - Comments on pages
- `label` - Tags/labels on content
- `space` - Confluence spaces

**Output**: JSON string with operation results or error details.

**Examples**:

~~~json
{
  "tool": "resource_manager_tool",
  "input": {
    "service": "jira",
    "resource": "issue",
    "operation": "create",
    "data": {
      "project_key": "FTEST",
      "summary": "Fix authentication bug",
      "issue_type": "Bug",
      "description": "Users cannot log in with special characters in password",
      "priority": "High",
      "labels": ["security", "authentication"]
    }
  }
}
~~~

~~~json
{
  "tool": "resource_manager_tool",
  "input": {
    "service": "confluence",
    "resource": "page",
    "operation": "create",
    "data": {
      "space_key": "~911651470",
      "title": "API Documentation",
      "body": "# API Overview\n\n**Authentication**: Use API tokens\n\n## Endpoints\n- `/api/v1/users` - User management\n- `/api/v1/issues` - Issue operations"
    }
  }
}
~~~

~~~json
{
  "tool": "resource_manager_tool",
  "input": {
    "service": "jira",
    "resource": "comment",
    "operation": "add",
    "identifier": "FTEST-123",
    "data": {
      "body": "I've reproduced this issue and working on a fix."
    }
  }
}
~~~

---

### search_engine_tool

**Purpose**: Universal search across Jira and Confluence with support for JQL, CQL, and text search.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ✅ | "jira" or "confluence" |
| query_type | string | ✅ | Type of search (see query types below) |
| query | string/object | ❌ | Search query or structured parameters |
| options | object | ❌ | Search options (limit, start, expand, etc.) |

**Jira Query Types**:
- `jql` - JQL (Jira Query Language) search
- `issues` - Search issues using JQL
- `fields` - Discover available fields
- `users` - Search for users
- `projects` - List all projects
- `boards` - List agile boards
- `sprints` - Search sprints
- `versions` - Search project versions
- `components` - Search project components
- `issue_types` - List issue types
- `statuses` - List issue statuses
- `priorities` - List issue priorities
- `resolutions` - List issue resolutions

**Confluence Query Types**:
- `pages` - Search pages using CQL
- `spaces` - List all spaces
- `users` - Search for users
- `content` - Search all content types
- `labels` - Search labels
- `attachments` - Search attachments

**Output**: JSON string with search results including metadata and pagination info.

**Examples**:

~~~json
{
  "tool": "search_engine_tool",
  "input": {
    "service": "jira",
    "query_type": "jql",
    "query": "project = FTEST AND status = 'In Progress' ORDER BY updated DESC",
    "options": {"limit": 20}
  }
}
~~~

~~~json
{
  "tool": "search_engine_tool",
  "input": {
    "service": "confluence",
    "query_type": "pages",
    "query": "space = '~911651470' AND type = page AND title ~ 'API'",
    "options": {"limit": 25, "expand": "body.storage"}
  }
}
~~~

~~~json
{
  "tool": "search_engine_tool",
  "input": {
    "service": "jira",
    "query_type": "fields",
    "options": {"limit": 50}
  }
}
~~~

~~~json
{
  "tool": "search_engine_tool",
  "input": {
    "service": "jira",
    "query_type": "projects"
  }
}
~~~

---

### workflow_engine_tool

**Purpose**: Manage Jira issue workflows, transitions, and status changes.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| operation | string | ✅ | Workflow operation (see operations below) |
| issue_key | string | ❌ | Jira issue key (required for most operations) |
| transition_id | string | ❌ | Numeric ID of transition |
| transition_name | string | ❌ | Human-readable transition name |
| fields | object | ❌ | Additional field updates during transition |
| project_key | string | ❌ | Project key (for discovery operations) |
| issue_type | string | ❌ | Issue type (for some discovery operations) |
| options | object | ❌ | Additional parameters |

**Operations**:
- `transition` - Move issue through workflow
- `get_transitions` - Get available transitions for issue
- `get_workflow` - Get workflow info for project/issue type
- `get_statuses` - Get all possible statuses for project
- `validate_transition` - Validate if transition is possible

**Output**: JSON string with transition results or workflow information.

**Examples**:

~~~json
{
  "tool": "workflow_engine_tool",
  "input": {
    "operation": "transition",
    "issue_key": "FTEST-123",
    "transition_name": "In Progress",
    "fields": {
      "assignee": {"name": "john.doe@example.com"},
      "comment": "Starting work on this issue"
    }
  }
}
~~~

~~~json
{
  "tool": "workflow_engine_tool",
  "input": {
    "operation": "get_transitions",
    "issue_key": "FTEST-123"
  }
}
~~~

---

### relationship_manager_tool

**Purpose**: Manage relationships between Jira issues including links, epic assignments, and hierarchies.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| operation | string | ✅ | Relationship operation (see operations below) |
| issue_key | string | ✅ | Source issue key |
| target_issue_key | string | ❌ | Target issue for linking operations |
| link_type | string | ❌ | Type of link ("Blocks", "Duplicates", "Relates", etc.) |
| epic_key | string | ❌ | Epic issue key for epic operations |
| parent_key | string | ❌ | Parent issue key for sub-task operations |
| comment | string | ❌ | Optional comment for the relationship |
| link_id | string | ❌ | Existing link ID for unlink operations |
| options | object | ❌ | Additional parameters |

**Operations**:
- `create_link` - Create link between two issues
- `get_links` - Get all links for an issue
- `delete_link` - Delete issue link
- `add_to_epic` - Add issue to epic
- `remove_from_epic` - Remove issue from epic
- `get_epic_issues` - Get all issues in an epic
- `set_parent` - Set parent-child relationship
- `remove_parent` - Remove parent relationship
- `get_subtasks` - Get subtasks of an issue
- `validate_relationship` - Validate if relationship is possible

**Output**: JSON string with relationship operation results.

**Examples**:

~~~json
{
  "tool": "relationship_manager_tool",
  "input": {
    "operation": "create_link",
    "issue_key": "FTEST-123",
    "target_issue_key": "FTEST-456",
    "link_type": "Blocks",
    "comment": "This issue blocks the other"
  }
}
~~~

~~~json
{
  "tool": "relationship_manager_tool",
  "input": {
    "operation": "add_to_epic",
    "issue_key": "FTEST-123",
    "epic_key": "FTEST-100"
  }
}
~~~

~~~json
{
  "tool": "relationship_manager_tool",
  "input": {
    "operation": "get_epic_issues",
    "issue_key": "FTEST-100"
  }
}
~~~

~~~json
{
  "tool": "relationship_manager_tool",
  "input": {
    "operation": "set_parent",
    "issue_key": "FTEST-124",
    "parent_key": "FTEST-123"
  }
}
~~~

~~~json
{
  "tool": "relationship_manager_tool",
  "input": {
    "operation": "get_subtasks",
    "issue_key": "FTEST-123"
  }
}
~~~

---

### batch_processor_tool

**Purpose**: Process multiple operations in parallel for improved performance on bulk operations.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ✅ | "jira" or "confluence" |
| operation | string | ✅ | "create", "update", or "delete" |
| resource | string | ✅ | Resource type (issue, page, comment, etc.) |
| items | array | ✅ | List of data objects for the operations |
| concurrency | integer | ❌ | Number of parallel operations (default: 5, max: 10) |

**Output**: JSON string with batch operation results including success/failure details for each item.

**Examples**:

~~~json
{
  "tool": "batch_processor_tool",
  "input": {
    "service": "jira",
    "operation": "create",
    "resource": "issue",
    "items": [
      {
        "project_key": "FTEST",
        "summary": "Bug 1: Login issue",
        "issue_type": "Bug"
      },
      {
        "project_key": "FTEST",
        "summary": "Bug 2: Password reset",
        "issue_type": "Bug"
      }
    ],
    "concurrency": 3
  }
}
~~~

---

### attachment_handler_tool

**Purpose**: Upload, download, and manage file attachments for issues and pages.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ✅ | "jira" or "confluence" |
| operation | string | ✅ | "upload", "download", "list", "delete" |
| issue_key | string | ❌ | Jira issue key (for Jira attachments) |
| page_id | string | ❌ | Confluence page ID (for Confluence attachments) |
| attachment_id | string | ❌ | Existing attachment ID (for download/delete) |
| file_path | string | ❌ | Local file path for upload/download |
| file_name | string | ❌ | Name for uploaded file |
| file_content | bytes | ❌ | Raw file content (alternative to file_path) |
| download_path | string | ❌ | Where to save downloaded files |
| options | object | ❌ | Additional parameters |

**Output**: JSON string with attachment operation results.

**Examples**:

~~~json
{
  "tool": "attachment_handler_tool",
  "input": {
    "service": "jira",
    "operation": "upload",
    "issue_key": "FTEST-123",
    "file_path": "/path/to/screenshot.png",
    "file_name": "bug_screenshot.png"
  }
}
~~~

~~~json
{
  "tool": "attachment_handler_tool",
  "input": {
    "service": "jira",
    "operation": "list",
    "issue_key": "FTEST-123"
  }
}
~~~

---

## Discovery and Utility Tools

### get_resource_schema

**Purpose**: Get detailed schema information for specific resource operations.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ✅ | "jira" or "confluence" |
| resource | string | ✅ | Resource type (issue, page, comment, etc.) |
| operation | string | ❌ | Operation type (default: "create") |

**Output**: JSON string with detailed field requirements, types, and examples.

**Example**:

~~~json
{
  "tool": "get_resource_schema",
  "input": {
    "service": "jira",
    "resource": "issue",
    "operation": "create"
  }
}
~~~

---

### get_capabilities

**Purpose**: Get comprehensive overview of available services, resources, and operations.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ❌ | Optional service filter ("jira" or "confluence") |

**Output**: JSON string with capabilities overview including available resources and operations.

**Examples**:

~~~json
{
  "tool": "get_capabilities",
  "input": {}
}
~~~

~~~json
{
  "tool": "get_capabilities",
  "input": {
    "service": "jira"
  }
}
~~~

---

### get_tool_examples

**Purpose**: Get practical, copy-paste ready examples for common operations.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| operation_type | string | ❌ | Filter by operation ("create", "search", "update", etc.) |
| service | string | ❌ | Filter by service ("jira", "confluence") |

**Output**: JSON string with practical examples organized by use case.

**Examples**:

~~~json
{
  "tool": "get_tool_examples",
  "input": {
    "operation_type": "create"
  }
}
~~~

~~~json
{
  "tool": "get_tool_examples",
  "input": {
    "service": "jira"
  }
}
~~~

---

### connection_health_check

**Purpose**: Validate connectivity and authentication for Atlassian services.

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| service | string | ❌ | "jira", "confluence", or null for both |

**Output**: JSON string with health check results including configuration and connectivity status.

**Examples**:

~~~json
{
  "tool": "connection_health_check",
  "input": {}
}
~~~

~~~json
{
  "tool": "connection_health_check",
  "input": {
    "service": "jira"
  }
}
~~~

---

### debug_context_info

**Purpose**: Debug tool to inspect MCP Context object and diagnose integration issues.

**Parameters**: None required.

**Output**: JSON string with context analysis and diagnostic information.

**Example**:

~~~json
{
  "tool": "debug_context_info",
  "input": {}
}
~~~

---

## MCP Resources

The MCP Atlassian server provides several resources that can be accessed by MCP clients for additional context and help.

### confluence://troubleshooting

**Purpose**: Comprehensive troubleshooting guide for Confluence operations.

**Description**: Provides detailed troubleshooting steps, common issues, and solutions for Confluence page creation and management.

**Access**: Query this resource from your MCP client when encountering Confluence-related issues.

**Example**:
```
Read resource: confluence://troubleshooting
```

---

### atlassian://field-mappings

**Purpose**: Field mappings and examples for all MCP Atlassian operations.

**Description**: JSON file containing field mappings, required fields, and example values for creating and updating issues, pages, and other resources.

**Access**: Query this resource to understand the correct field names and formats for various operations.

**Example**:
```
Read resource: atlassian://field-mappings
```

---

### atlassian://help

**Purpose**: Quick help resource for common MCP Atlassian operations.

**Description**: Provides quick reference examples for the most common operations like creating Confluence pages and Jira issues.

**Access**: Query this resource for quick copy-paste examples.

**Example**:
```
Read resource: atlassian://help
```

**Content Preview**:
- Create Confluence Page examples
- Create Jira Issue examples
- Error handling guidance
- Links to other help resources

---

## Environment Configuration

The tools require proper environment configuration. Key variables:

### Required Configuration
```bash
# Atlassian instance URL
ATLASSIAN_URL=https://your-company.atlassian.net

# Authentication (choose one method)
ATLASSIAN_EMAIL=your.email@example.com
ATLASSIAN_API_TOKEN=your_api_token

# OR Personal Access Token (Server/DC)
ATLASSIAN_PAT=your_personal_access_token

# OR OAuth (Advanced)
ATLASSIAN_OAUTH_CLIENT_ID=your_oauth_client_id
ATLASSIAN_OAUTH_CLIENT_SECRET=your_oauth_client_secret
ATLASSIAN_OAUTH_CLOUD_ID=your_cloud_id
```

### Optional Configuration
```bash
# Content filtering
JIRA_PROJECTS_FILTER=PROJ1,PROJ2
CONFLUENCE_SPACES_FILTER=SPACE1,SPACE2

# Server behavior
READ_ONLY_MODE=false
ENABLED_TOOLS=resource_manager_tool,search_engine_tool
```

See the main [README](../README.md) for complete configuration details.

## Migration from Legacy Tools

If you were using the previous version with 42 individual tools, here's how to migrate:

### Legacy Tool Mapping

| Legacy Tool | Meta-Tool Equivalent |
|-------------|----------------------|
| `jira_create_issue` | `resource_manager_tool` (service="jira", resource="issue", operation="create") |
| `jira_get_issue` | `resource_manager_tool` (service="jira", resource="issue", operation="get") |
| `jira_search` | `search_engine_tool` (service="jira", query_type="jql") |
| `confluence_create_page` | `resource_manager_tool` (service="confluence", resource="page", operation="create") |
| `confluence_search` | `search_engine_tool` (service="confluence", query_type="pages") |
| `jira_transition_issue` | `workflow_engine_tool` (operation="transition") |
| `jira_add_comment` | `resource_manager_tool` (service="jira", resource="comment", operation="add") |
| And 35+ more... | Use corresponding meta-tool operations |

### Migration Benefits
- **Fewer tool registrations**: 11 tools instead of 42
- **Consistent interfaces**: All CRUD operations use the same pattern
- **Better error handling**: Structured error responses
- **Parallel processing**: Built-in bulk operations
- **Future-proof**: New Atlassian features can be added without new tools

## Common Error Patterns

### Authentication Errors
```json
{
  "error": "Authentication failed",
  "details": "Check ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN"
}
```

### Missing Required Fields
```json
{
  "error": "Missing required field: project_key",
  "suggestion": "Use get_resource_schema to see required fields"
}
```

### Invalid Resource/Operation
```json
{
  "error": "Invalid operation 'delete' for resource 'worklog'",
  "available_operations": ["create", "get", "update"]
}
```

## Support

- **Schema Discovery**: Use `get_resource_schema` when unsure about required fields
- **Examples**: Use `get_tool_examples` for copy-paste ready code
- **Health Checks**: Use `connection_health_check` to validate setup
- **Debugging**: Use `debug_context_info` for integration issues

For more help, see the [main documentation](../README.md) or check the [GitHub repository](https://github.com/dmason-mlb/mcp-atlassian).