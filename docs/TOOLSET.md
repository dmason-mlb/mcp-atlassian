# MCP Atlassian Toolset

This document provides a comprehensive catalog of all tools available in the MCP Atlassian server. The server provides Model Context Protocol (MCP) access to both Jira and Confluence, supporting Cloud and Server/Data Center deployments.

## How to Use

To use these tools, you need to have the MCP Atlassian server running and configured with proper authentication. See the [README](../README.md) for setup instructions. Once configured, AI assistants can access these tools through the MCP protocol.

## Summary Table

| Tool | Purpose | Inputs | Outputs | Notes |
|------|---------|--------|---------|-------|
| **Jira Tools** |
| `jira_issues_create_issue` | Create a new Jira issue | project_key, summary, issue_type, optional fields | Created issue details | Supports epics, subtasks, custom fields |
| `jira_issues_batch_create_issues` | Create multiple issues at once | issues (JSON array) | Batch creation results | Efficient for bulk operations |
| `jira_issues_update_issue` | Update an existing issue | issue_key, fields to update | Updated issue details | Supports attachments |
| `jira_issues_delete_issue` | Delete an issue | issue_key | Deletion confirmation | Permanent deletion |
| `jira_issues_add_comment` | Add comment to issue | issue_key, comment | Comment details | Markdown format supported |
| `jira_issues_transition_issue` | Change issue status | issue_key, transition_id | Transition result | Use get_transitions first |
| `jira_issues_get_issue` | Get issue details | issue_key, fields | Issue details with Epic links | Customizable field selection |
| `jira_issues_batch_get_changelogs` | Get change history | issue_ids_or_keys | Change history | Cloud only |
| `jira_search_search` | Search issues with JQL | jql query | Matching issues | Powerful query language |
| `jira_search_search_fields` | Search field definitions | keyword | Field metadata | Fuzzy matching |
| `jira_search_get_project_issues` | Get all project issues | project_key | Project issues | Paginated results |
| `jira_agile_get_agile_boards` | List Agile boards | board_name, type | Board list | Scrum/Kanban support |
| `jira_agile_get_board_issues` | Get board issues | board_id, jql | Board issues | Filtered by JQL |
| `jira_agile_get_sprints_from_board` | List board sprints | board_id, state | Sprint list | Active/future/closed |
| `jira_agile_get_sprint_issues` | Get sprint issues | sprint_id | Sprint issues | With status |
| `jira_agile_create_sprint` | Create new sprint | board_id, name, dates | Created sprint | Requires dates |
| `jira_agile_update_sprint` | Update sprint | sprint_id, updates | Updated sprint | Name, dates, state |
| `jira_management_get_user_profile` | Get user details | user_identifier | User profile | Email/username/ID |
| `jira_management_get_transitions` | Get status transitions | issue_key | Available transitions | Required for status changes |
| `jira_management_download_attachments` | Download attachments | issue_key, target_dir | Download results | Saves to local directory |
| `jira_management_upload_attachment` | Upload attachment | issue_key, file_path | Upload result | Single file upload |
| `jira_management_get_link_types` | Get link types | - | Link type definitions | For issue linking |
| `jira_management_link_to_epic` | Link issue to epic | issue_key, epic_key | Link result | Epic relationship |
| `jira_management_create_issue_link` | Create issue link | link_type, issue keys | Link creation result | Between two issues |
| `jira_management_create_remote_issue_link` | Add external link | issue_key, url, title | Remote link result | Web links, Confluence |
| `jira_management_remove_issue_link` | Remove issue link | link_id | Removal confirmation | Unlinks issues |
| `jira_management_get_project_versions` | Get fix versions | project_key | Version list | For version management |
| `jira_management_get_all_projects` | List all projects | include_archived | Project list | Respects filters |
| `jira_management_create_version` | Create fix version | project_key, name | Created version | With optional dates |
| `jira_management_batch_create_versions` | Create multiple versions | project_key, versions | Batch results | Efficient bulk creation |
| **Confluence Tools** |
| `confluence_search_search` | Search content | query, limit, spaces | Matching pages | CQL or simple text |
| `confluence_search_search_user` | Search users | query, limit | User results | CQL query |
| `confluence_pages_get_page` | Get page content | page_id or title+space | Page content & metadata | Markdown conversion |
| `confluence_pages_get_page_children` | Get child pages | parent_id | Child page list | With optional content |
| `confluence_pages_create_page` | Create new page | space_id, title, content | Created page | Markdown/wiki/storage format |
| `confluence_pages_update_page` | Update page | page_id, title, content | Updated page | Version control |
| `confluence_pages_delete_page` | Delete page | page_id | Deletion result | Permanent deletion |
| `confluence_content_get_comments` | Get page comments | page_id | Comment list | Threaded discussions |
| `confluence_content_add_comment` | Add comment | page_id, content | Created comment | Markdown format |
| `confluence_content_get_labels` | Get page labels | page_id | Label list | For categorization |
| `confluence_content_add_label` | Add label to page | page_id, name | Updated labels | Tag pages |

## Jira Tools

### jira_issues_create_issue
Create a new Jira issue with optional Epic link or parent for subtasks.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| project_key | string | Yes | The JIRA project key (e.g. 'PROJ', 'DEV') | Valid project key |
| summary | string | Yes | Summary/title of the issue | Any text |
| issue_type | string | Yes | Issue type | Task, Bug, Story, Epic, Subtask, etc. |
| assignee | string | No | Assignee's identifier | Email, display name, or account ID |
| description | string | No | Issue description | Any text |
| components | string | No | Comma-separated component names | Component names |
| additional_fields | dict/string | No | Additional fields as dictionary or JSON | Custom field values |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| issue | object | Created issue details with key, id, self URL |
| error | string | Error message if failed |

**Preconditions:**
- Requires write access (disabled in read-only mode)
- Project must exist and be accessible
- Issue type must be valid for the project
- User must have create issue permission

**Example:**
~~~json
{
  "tool": "jira_issues_create_issue",
  "input": {
    "project_key": "PROJ",
    "summary": "Implement user authentication",
    "issue_type": "Task",
    "description": "Add OAuth 2.0 authentication to the API",
    "assignee": "john.doe@example.com",
    "components": "Backend,Security",
    "additional_fields": {
      "priority": {"name": "High"},
      "labels": ["security", "oauth"]
    }
  }
}
~~~

### jira_issues_update_issue
Update an existing Jira issue including changing status, adding Epic links, updating fields, etc.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| issue_key | string | Yes | Jira issue key | e.g., 'PROJ-123' |
| fields | dict | Yes | Dictionary of fields to update | Field names and values |
| attachments | string | No | File paths to attach | Comma-separated paths or JSON array |
| additional_fields | dict | No | Additional fields to update | Custom fields |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success status |
| issue | object | Updated issue details |
| warnings | array | Any warnings during update |

**Preconditions:**
- Requires write access
- Issue must exist
- User must have edit permission

**Example:**
~~~json
{
  "tool": "jira_issues_update_issue",
  "input": {
    "issue_key": "PROJ-123",
    "fields": {
      "summary": "Updated: Implement user authentication",
      "assignee": "jane.smith@example.com",
      "priority": {"name": "Critical"}
    }
  }
}
~~~

### jira_search_search
Search Jira issues using JQL (Jira Query Language).

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| jql | string | Yes | JQL query string | Valid JQL syntax |
| fields | string | No | Comma-separated fields to return | Field names or '*all' |
| limit | integer | No | Maximum results (1-50) | 1-50, default 10 |
| start_at | integer | No | Starting index for pagination | >= 0, default 0 |
| projects_filter | string | No | Project keys to filter | Comma-separated keys |
| expand | string | No | Fields to expand | e.g., 'renderedFields' |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| issues | array | List of matching issues |
| total | integer | Total number of matches |
| startAt | integer | Starting index |
| maxResults | integer | Number returned |

**Example JQL Queries:**
~~~
# Find high priority bugs
"priority = High AND issuetype = Bug AND status != Resolved"

# Find issues in current sprint
"sprint in openSprints() AND project = PROJ"

# Find my assigned issues updated this week
"assignee = currentUser() AND updated >= -7d"

# Find issues in Epic
"parent = PROJ-100 OR 'Epic Link' = PROJ-100"
~~~

### jira_agile_get_agile_boards
Get Jira agile boards by name, project key, or type.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| board_name | string | No | Board name (fuzzy search) | Any text |
| project_key | string | No | Project key filter | Valid project key |
| board_type | string | No | Board type filter | 'scrum' or 'kanban' |
| start_at | integer | No | Pagination start | >= 0 |
| limit | integer | No | Max results (1-50) | 1-50, default 10 |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| values | array | List of board objects |
| total | integer | Total boards found |
| isLast | boolean | Last page indicator |

**Example:**
~~~json
{
  "tool": "jira_agile_get_agile_boards",
  "input": {
    "project_key": "PROJ",
    "board_type": "scrum"
  }
}
~~~

### jira_management_create_remote_issue_link
Create a remote issue link (web link or Confluence link) for a Jira issue.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| issue_key | string | Yes | Issue to add link to | e.g., 'PROJ-123' |
| url | string | Yes | URL to link to | Any valid URL |
| title | string | Yes | Link title/name | Display text |
| summary | string | No | Link description | Optional description |
| relationship | string | No | Relationship type | e.g., 'documentation' |
| icon_url | string | No | Icon URL (16x16) | Image URL |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Operation success |
| id | string | Remote link ID |
| self | string | Link API URL |

**Preconditions:**
- Requires write access
- Issue must exist
- User must have link permission

**Example:**
~~~json
{
  "tool": "jira_management_create_remote_issue_link",
  "input": {
    "issue_key": "PROJ-123",
    "url": "https://confluence.example.com/display/PROJ/Design",
    "title": "Design Documentation",
    "summary": "Technical design document for this feature",
    "relationship": "documentation"
  }
}
~~~

## Confluence Tools

### confluence_search_search
Search Confluence content using simple terms or CQL (Confluence Query Language).

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| query | string | Yes | Search query | Simple text or CQL |
| limit | integer | No | Max results (1-50) | 1-50, default 10 |
| spaces_filter | string | No | Space keys to filter | Comma-separated |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| results | array | List of matching pages |
| id | string | Page ID for each result |
| title | string | Page title |
| space | object | Space information |
| url | string | Page URL |

**Example CQL Queries:**
~~~
# Find pages in DEV space
"type=page AND space=DEV"

# Find recently modified pages
"lastModified > startOfMonth('-1M')"

# Find pages with specific label
"label=documentation AND space=PROJ"

# Search in page content
"text ~ 'deployment guide'"
~~~

### confluence_pages_get_page
Get content of a specific Confluence page by its ID, or by its title and space key.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| page_id | string | No* | Confluence page ID | Numeric ID |
| title | string | No* | Exact page title | Any text |
| space_key | string | No* | Space key | Valid space key |
| include_metadata | boolean | No | Include metadata | true/false, default true |
| convert_to_markdown | boolean | No | Convert to markdown | true/false, default true |

*Note: Provide either page_id OR both title and space_key

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Page ID |
| title | string | Page title |
| content | string | Page content (markdown or HTML) |
| metadata | object | Creation date, version, labels, etc. |
| url | string | Page URL |

**Example:**
~~~json
{
  "tool": "confluence_pages_get_page",
  "input": {
    "title": "Architecture Overview",
    "space_key": "DEV",
    "convert_to_markdown": true
  }
}
~~~

### confluence_pages_create_page
Create a new Confluence page.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| space_id | string | Yes | Space ID to create page in | Numeric space ID |
| title | string | Yes | Page title | Any text |
| content | string | Yes | Page content | Markdown, wiki, or storage format |
| parent_id | string | No | Parent page ID | For child pages |
| content_format | string | No | Content format | 'markdown', 'wiki', 'storage' |
| enable_heading_anchors | boolean | No | Enable heading anchors | For markdown only |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Created page ID |
| title | string | Page title |
| version | object | Version information |
| url | string | Page URL |

**Preconditions:**
- Requires write access
- Space must exist
- User must have create permission
- Parent page must exist if specified

**Example:**
~~~json
{
  "tool": "confluence_pages_create_page",
  "input": {
    "space_id": "123456789",
    "title": "Sprint 23 Retrospective",
    "content": "# Sprint 23 Retrospective\n\n## What went well\n- Feature X delivered on time\n- Good team collaboration\n\n## Areas for improvement\n- Need better test coverage\n- Documentation updates lagging",
    "content_format": "markdown"
  }
}
~~~

### confluence_pages_update_page
Update an existing Confluence page.

**Inputs:**
| Property | Type | Required | Description | Allowed Values |
|----------|------|----------|-------------|----------------|
| page_id | string | Yes | Page ID to update | Numeric ID |
| title | string | Yes | New page title | Any text |
| content | string | Yes | New page content | Format per content_format |
| is_minor_edit | boolean | No | Mark as minor edit | true/false, default false |
| version_comment | string | No | Version comment | Optional comment |
| parent_id | string | No | New parent page ID | To move page |
| content_format | string | No | Content format | 'markdown', 'wiki', 'storage' |

**Outputs:**
| Field | Type | Description |
|-------|------|-------------|
| id | string | Page ID |
| title | string | Updated title |
| version | object | New version info |
| url | string | Page URL |

**Preconditions:**
- Requires write access
- Page must exist
- User must have edit permission
- Version conflict detection

**Example:**
~~~json
{
  "tool": "confluence_pages_update_page",
  "input": {
    "page_id": "123456789",
    "title": "Sprint 23 Retrospective - Updated",
    "content": "# Sprint 23 Retrospective\n\n## Updated content here...",
    "version_comment": "Added action items from meeting",
    "content_format": "markdown"
  }
}
~~~

## Authentication & Permissions

All tools respect the authentication method configured for the server:
- **API Token** (Cloud): Username + API token
- **Personal Access Token** (Server/DC): PAT-based authentication
- **OAuth 2.0** (Cloud): Standard OAuth flow with refresh tokens
- **BYOT OAuth** (Cloud): Bring Your Own Token
- **Multi-user HTTP**: Per-request authentication via headers

Tools tagged with `write` require write access and are disabled in read-only mode.

## Error Handling

All tools return structured error responses:
~~~json
{
  "success": false,
  "error": "Error message",
  "details": {
    "status_code": 404,
    "error_type": "NotFoundError"
  }
}
~~~

Common error types:
- **Authentication errors**: Invalid credentials or expired tokens
- **Permission errors**: Insufficient permissions for the operation
- **Validation errors**: Invalid input parameters
- **Not found errors**: Resource doesn't exist
- **Rate limit errors**: API rate limits exceeded

## Rate Limits

Both Jira and Confluence APIs have rate limits:
- **Jira Cloud**: 5000 requests per hour
- **Confluence Cloud**: 5000 requests per hour
- **Server/DC**: Configured by administrator

The MCP server implements exponential backoff for rate limit handling.

## Change Log

For the latest changes to tools, see the main [CHANGELOG](../CHANGELOG.md) or check the release notes for version-specific tool updates.