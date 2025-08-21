# MCP Atlassian Toolset

This document provides a comprehensive catalog of all **42 tools** available in the MCP Atlassian server. The server provides Model Context Protocol (MCP) access to both Jira and Confluence, supporting Cloud and Server/Data Center deployments.

## How to Use

To use these tools, you need to have the MCP Atlassian server running and configured with proper authentication. See the [README](../README.md) for setup instructions. Once configured, AI assistants can access these tools through the MCP protocol.

## Tool Categories

- **Jira Tools**: 31 tools for issue management, project management, agile workflows, and search
- **Confluence Tools**: 11 tools for content management, search, and collaboration

## Summary Table

| Tool | Purpose | Type | Inputs | Outputs |
|------|---------|------|--------|---------|
| **Jira User Management** |
| `get_user_profile` | Get user profile information | Read | user_identifier | User profile JSON |
| **Jira Issue Management** |
| `get_issue` | Get issue details with custom fields | Read | issue_key, fields, expand | Issue details JSON |
| `create_issue` | Create a new Jira issue | Write | project_key, summary, issue_type, description, assignee | Created issue JSON |
| `batch_create_issues` | Create multiple issues efficiently | Write | issues (JSON array), validate_only | Batch creation results |
| `update_issue` | Update existing issue fields | Write | issue_key, fields, attachments | Updated issue JSON |
| `delete_issue` | Permanently delete an issue | Write | issue_key | Deletion confirmation |
| `add_comment` | Add comment to issue | Write | issue_key, comment (Markdown) | Comment JSON |
| `transition_issue` | Change issue status/workflow | Write | issue_key, transition_id, fields, comment | Transition result |
| `issues_create_issue` | Legacy alias for create_issue | Write | Same as create_issue | Created issue JSON |
| **Jira Search & Discovery** |
| `search` | Search issues using JQL | Read | jql, fields, limit, start_at | Search results JSON |
| `search_fields` | Find available Jira fields | Read | keyword, limit, refresh | Field definitions |
| `get_project_issues` | Get all issues for a project | Read | project_key, limit, start_at | Project issues JSON |
| **Jira Agile & Boards** |
| `get_agile_boards` | List available Agile boards | Read | board_name, project_key, board_type | Boards JSON |
| `get_board_issues` | Get issues on specific board | Read | board_id, jql, fields, limit | Board issues JSON |
| `get_sprints_from_board` | List sprints for a board | Read | board_id, state, start_at, limit | Sprints JSON |
| `get_sprint_issues` | Get issues in specific sprint | Read | sprint_id, fields, limit | Sprint issues JSON |
| `create_sprint` | Create new sprint | Write | board_id, sprint_name, start_date, end_date, goal | Created sprint JSON |
| `update_sprint` | Update sprint details | Write | sprint_id, sprint_name, state, start_date, end_date, goal | Updated sprint JSON |
| **Jira Project Management** |
| `get_all_projects` | List all accessible projects | Read | include_archived | Projects JSON |
| `get_project_versions` | Get fix versions for project | Read | project_key | Versions JSON |
| `create_version` | Create new fix version | Write | project_key, name, start_date, release_date, description | Created version JSON |
| `batch_create_versions` | Create multiple versions | Write | project_key, versions (JSON array) | Batch results JSON |
| **Jira Issue Relationships** |
| `get_link_types` | Get available issue link types | Read | None | Link types JSON |
| `link_to_epic` | Link issue to an epic | Write | issue_key, epic_key | Link result JSON |
| `create_issue_link` | Create link between issues | Write | link_type, inward_issue_key, outward_issue_key, comment | Link creation result |
| `create_remote_issue_link` | Add external/web link to issue | Write | issue_key, url, title, summary, relationship | Remote link result |
| `remove_issue_link` | Remove existing issue link | Write | link_id | Removal confirmation |
| **Jira Attachments** |
| `download_attachments` | Download issue attachments | Read | issue_key, target_dir | Download results |
| `upload_attachment` | Upload file to issue | Write | issue_key, file_path | Upload result JSON |
| **Jira Workflow** |
| `get_transitions` | Get available status transitions | Read | issue_key | Available transitions JSON |
| **Jira History & Analytics** |
| `batch_get_changelogs` | Get change history for issues | Read | issue_ids_or_keys, fields, limit | Change history JSON |
| **Confluence Search** |
| `search` | Search Confluence content | Read | query (CQL or text), limit, spaces_filter | Search results JSON |
| `search_user` | Search Confluence users | Read | query (CQL), limit | User search results |
| **Confluence Page Management** |
| `get_page` | Get page content and metadata | Read | page_id OR title+space_key, include_metadata, convert_to_markdown | Page content JSON |
| `get_page_children` | Get child pages of a page | Read | parent_id, expand, limit, include_content | Children JSON |
| `create_page` | Create new Confluence page | Write | space_id, title, content, parent_id, content_format | Created page JSON |
| `update_page` | Update existing page | Write | page_id, title, content, is_minor_edit, version_comment | Updated page JSON |
| `delete_page` | Delete a page permanently | Write | page_id | Deletion confirmation |
| **Confluence Content Interaction** |
| `get_comments` | Get comments on a page | Read | page_id | Comments JSON |
| `add_comment` | Add comment to page | Write | page_id, content (Markdown) | Created comment JSON |
| `get_labels` | Get labels on a page | Read | page_id | Labels JSON |
| `add_label` | Add label to page | Write | page_id, name | Updated labels JSON |

---

## Detailed Tool Descriptions

### Jira User Management

#### get_user_profile
Retrieve profile information for a specific Jira user by email, username, account ID, or key.

**Parameters:**
- `user_identifier` (string, required): User identifier (e.g., 'user@example.com', 'johndoe', 'accountid:...')

**Returns:** JSON object with user profile details including display name, email, account ID, and active status.

**Example:**
```json
{
  "success": true,
  "user": {
    "accountId": "accountid:...",
    "displayName": "John Doe",
    "emailAddress": "john@example.com",
    "active": true
  }
}
```

---

### Jira Issue Management

#### get_issue
Get detailed information about a Jira issue including custom fields and Epic relationships.

**Parameters:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `fields` (string, optional): Comma-separated fields to return or '*all' for everything
- `expand` (string, optional): Fields to expand like 'renderedFields', 'transitions', 'changelog'
- `comment_limit` (number, optional): Maximum comments to include (default: 10)
- `properties` (string, optional): Issue properties to return
- `update_history` (boolean, optional): Whether to update view history (default: true)

**Returns:** JSON object with comprehensive issue details including fields, comments, and Epic links.

#### create_issue
Create a new Jira issue with support for epics, subtasks, and custom fields.

**Parameters:**
- `project_key` (string, required): Project key (e.g., 'PROJ', 'DEV')
- `summary` (string, required): Issue title/summary
- `issue_type` (string, required): Issue type ('Task', 'Bug', 'Story', 'Epic', 'Subtask')
- `description` (string, optional): Issue description
- `assignee` (string, optional): Assignee email, username, or account ID
- `components` (string, optional): Comma-separated component names
- `additional_fields` (object, optional): Custom fields like priority, labels, parent, fixVersions

**Returns:** JSON object with created issue details including key and ID.

**Example:**
```json
{
  "project_key": "PROJ",
  "summary": "Fix login bug",
  "issue_type": "Bug",
  "description": "Users cannot log in with special characters",
  "assignee": "developer@company.com",
  "additional_fields": {
    "priority": {"name": "High"},
    "labels": ["frontend", "urgent"]
  }
}
```

#### batch_create_issues
Create multiple issues efficiently in a single operation.

**Parameters:**
- `issues` (string, required): JSON array of issue objects
- `validate_only` (boolean, optional): Only validate without creating (default: false)

**Returns:** JSON with batch creation results including success/failure for each issue.

#### update_issue
Update fields on an existing Jira issue including adding attachments.

**Parameters:**
- `issue_key` (string, required): Issue key to update
- `fields` (object, required): Fields to update (assignee, summary, etc.)
- `additional_fields` (object, optional): Additional custom fields
- `attachments` (string, optional): File paths to attach (comma-separated or JSON array)

**Returns:** JSON object with updated issue details and attachment results.

#### delete_issue
Permanently delete a Jira issue. Cannot be undone.

**Parameters:**
- `issue_key` (string, required): Issue key to delete

**Returns:** JSON confirmation of deletion.

#### add_comment
Add a comment to a Jira issue with Markdown formatting support.

**Parameters:**
- `issue_key` (string, required): Target issue key
- `comment` (string, required): Comment text in Markdown format

**Returns:** JSON object with created comment details.

#### transition_issue
Change an issue's status through workflow transitions.

**Parameters:**
- `issue_key` (string, required): Issue to transition
- `transition_id` (string, required): Transition ID (use get_transitions to find)
- `fields` (object, optional): Fields to set during transition
- `comment` (string, optional): Comment for the transition

**Returns:** JSON object with transition results and updated issue.

---

### Jira Search & Discovery

#### search
Search Jira issues using JQL (Jira Query Language) with advanced filtering.

**Parameters:**
- `jql` (string, required): JQL query (e.g., 'project = PROJ AND status = "In Progress"')
- `fields` (string, optional): Fields to return in results
- `limit` (number, optional): Maximum results (1-50, default: 10)
- `start_at` (number, optional): Starting index for pagination
- `projects_filter` (string, optional): Project keys to filter by
- `expand` (string, optional): Fields to expand

**Returns:** JSON with search results including issues and pagination info.

**Example JQL Queries:**
- Find open bugs: `project = PROJ AND issuetype = Bug AND status != Closed`
- Recent updates: `updated >= -7d AND assignee = currentUser()`
- Epic contents: `parent = EPIC-123`

#### search_fields
Search and discover available Jira fields with fuzzy matching.

**Parameters:**
- `keyword` (string, optional): Search term for field names
- `limit` (number, optional): Maximum results (default: 10)
- `refresh` (boolean, optional): Force refresh field cache

**Returns:** JSON array of matching field definitions with names, IDs, and types.

#### get_project_issues
Get all issues for a specific project with pagination.

**Parameters:**
- `project_key` (string, required): Project key
- `limit` (number, optional): Maximum results (1-50, default: 10)
- `start_at` (number, optional): Starting index

**Returns:** JSON with project issues and pagination information.

---

### Jira Agile & Boards

#### get_agile_boards
List Agile boards with filtering by name, project, or type.

**Parameters:**
- `board_name` (string, optional): Board name for fuzzy search
- `project_key` (string, optional): Filter by project
- `board_type` (string, optional): Board type ('scrum' or 'kanban')
- `start_at` (number, optional): Starting index
- `limit` (number, optional): Maximum results

**Returns:** JSON array of board objects with names, IDs, and types.

#### get_board_issues
Get issues associated with a specific Agile board.

**Parameters:**
- `board_id` (string, required): Board ID
- `jql` (string, required): JQL filter for issues
- `fields` (string, optional): Fields to return
- `start_at` (number, optional): Starting index
- `limit` (number, optional): Maximum results
- `expand` (string, optional): Fields to expand

**Returns:** JSON with filtered board issues.

#### get_sprints_from_board
List sprints for an Agile board by state.

**Parameters:**
- `board_id` (string, required): Board ID
- `state` (string, optional): Sprint state ('active', 'future', 'closed')
- `start_at` (number, optional): Starting index
- `limit` (number, optional): Maximum results

**Returns:** JSON array of sprint objects with names, dates, and states.

#### get_sprint_issues
Get issues assigned to a specific sprint.

**Parameters:**
- `sprint_id` (string, required): Sprint ID
- `fields` (string, optional): Fields to return
- `start_at` (number, optional): Starting index
- `limit` (number, optional): Maximum results

**Returns:** JSON with sprint issues and their status.

#### create_sprint
Create a new sprint for a board.

**Parameters:**
- `board_id` (string, required): Board ID
- `sprint_name` (string, required): Sprint name
- `start_date` (string, required): Start date (ISO 8601 format)
- `end_date` (string, required): End date (ISO 8601 format)
- `goal` (string, optional): Sprint goal

**Returns:** JSON object with created sprint details.

#### update_sprint
Update an existing sprint's properties.

**Parameters:**
- `sprint_id` (string, required): Sprint ID to update
- `sprint_name` (string, optional): New sprint name
- `state` (string, optional): New state ('future', 'active', 'closed')
- `start_date` (string, optional): New start date
- `end_date` (string, optional): New end date
- `goal` (string, optional): New sprint goal

**Returns:** JSON object with updated sprint information.

---

### Jira Project Management

#### get_all_projects
List all Jira projects accessible to the current user.

**Parameters:**
- `include_archived` (boolean, optional): Include archived projects (default: false)

**Returns:** JSON array of project objects with keys, names, and types.

#### get_project_versions
Get all fix versions for a specific project.

**Parameters:**
- `project_key` (string, required): Project key

**Returns:** JSON array of version objects with names, dates, and release status.

#### create_version
Create a new fix version in a project.

**Parameters:**
- `project_key` (string, required): Target project
- `name` (string, required): Version name
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `release_date` (string, optional): Release date (YYYY-MM-DD)
- `description` (string, optional): Version description

**Returns:** JSON object with created version details.

#### batch_create_versions
Create multiple fix versions efficiently.

**Parameters:**
- `project_key` (string, required): Target project
- `versions` (string, required): JSON array of version objects

**Returns:** JSON array with creation results for each version.

---

### Jira Issue Relationships

#### get_link_types
Get all available issue link types for creating relationships between issues.

**Parameters:** None

**Returns:** JSON array of link type objects with names and directions.

#### link_to_epic
Link an issue to an Epic for hierarchical organization.

**Parameters:**
- `issue_key` (string, required): Issue to link
- `epic_key` (string, required): Epic to link to

**Returns:** JSON object with link operation result.

#### create_issue_link
Create a directional link between two issues.

**Parameters:**
- `link_type` (string, required): Link type name (e.g., 'Blocks', 'Relates to')
- `inward_issue_key` (string, required): Source issue key
- `outward_issue_key` (string, required): Target issue key
- `comment` (string, optional): Comment for the link
- `comment_visibility` (object, optional): Comment visibility settings

**Returns:** JSON confirmation of link creation.

#### create_remote_issue_link
Add an external web link or Confluence page link to an issue.

**Parameters:**
- `issue_key` (string, required): Target issue
- `url` (string, required): URL to link
- `title` (string, required): Link display title
- `summary` (string, optional): Link description
- `relationship` (string, optional): Relationship type
- `icon_url` (string, optional): 16x16 icon URL

**Returns:** JSON object with remote link creation result.

#### remove_issue_link
Remove an existing link between issues.

**Parameters:**
- `link_id` (string, required): Link ID to remove

**Returns:** JSON confirmation of link removal.

---

### Jira Attachments

#### download_attachments
Download all attachments from a Jira issue to a local directory.

**Parameters:**
- `issue_key` (string, required): Source issue
- `target_dir` (string, required): Local directory path

**Returns:** JSON object with download results and file paths.

#### upload_attachment
Upload a single file as an attachment to a Jira issue.

**Parameters:**
- `issue_key` (string, required): Target issue
- `file_path` (string, required): Path to file to upload

**Returns:** JSON object with upload result and attachment details.

---

### Jira Workflow

#### get_transitions
Get available status transitions for an issue based on current workflow state.

**Parameters:**
- `issue_key` (string, required): Issue to check

**Returns:** JSON array of available transitions with IDs and names.

---

### Jira History & Analytics

#### batch_get_changelogs
Get change history for multiple issues (Cloud only).

**Parameters:**
- `issue_ids_or_keys` (array, required): List of issue IDs or keys
- `fields` (array, optional): Specific fields to track changes for
- `limit` (number, optional): Maximum changelog entries per issue

**Returns:** JSON with change history for all specified issues.

---

## Confluence Tools

### Confluence Search

#### search
Search Confluence content using CQL queries or simple text with automatic format detection.

**Parameters:**
- `query` (string, required): Search query (CQL or plain text)
- `limit` (number, optional): Maximum results (1-50, default: 10)
- `spaces_filter` (string, optional): Comma-separated space keys to filter

**Returns:** JSON array of simplified page objects with titles, URLs, and summaries.

**Example CQL Queries:**
- Basic search: `type=page AND space=DEV`
- Personal space: `space="~username"`
- Recent content: `created >= "2023-01-01"`
- By label: `label=documentation`
- Text search: `text ~ "important concept"`

#### search_user
Search Confluence users using CQL queries.

**Parameters:**
- `query` (string, required): CQL query for user search
- `limit` (number, optional): Maximum results (1-50, default: 10)

**Returns:** JSON array of user search result objects.

**Example:**
```json
{
  "query": "user.fullname ~ \"John Doe\""
}
```

---

### Confluence Page Management

#### get_page
Retrieve Confluence page content and metadata by ID or title+space.

**Parameters:**
- `page_id` (string, optional): Page ID (numeric)
- `title` (string, optional): Exact page title (use with space_key)
- `space_key` (string, optional): Space key (use with title)
- `include_metadata` (boolean, optional): Include creation date, version, labels (default: true)
- `convert_to_markdown` (boolean, optional): Convert to Markdown vs raw HTML (default: true)

**Returns:** JSON object with page content, metadata, and version information.

#### get_page_children
Get child pages of a specific parent page.

**Parameters:**
- `parent_id` (string, required): Parent page ID
- `expand` (string, optional): Fields to expand (default: 'version')
- `limit` (number, optional): Maximum children (1-50, default: 25)
- `include_content` (boolean, optional): Include page content (default: false)
- `convert_to_markdown` (boolean, optional): Convert content format (default: true)
- `start` (number, optional): Starting index for pagination

**Returns:** JSON array of child page objects.

#### create_page
Create a new Confluence page with flexible content format support.

**Parameters:**
- `space_id` (string, required): Target space ID
- `title` (string, required): Page title
- `content` (string, required): Page content
- `parent_id` (string, optional): Parent page ID for hierarchy
- `content_format` (string, optional): Content format ('markdown', 'wiki', 'storage', default: 'markdown')
- `enable_heading_anchors` (boolean, optional): Enable anchor generation (default: false)

**Returns:** JSON object with created page details including ID and URL.

#### update_page
Update an existing Confluence page with version control.

**Parameters:**
- `page_id` (string, required): Page ID to update
- `title` (string, required): New page title
- `content` (string, required): New page content
- `is_minor_edit` (boolean, optional): Mark as minor edit (default: false)
- `version_comment` (string, optional): Version comment
- `parent_id` (string, optional): New parent page
- `content_format` (string, optional): Content format (default: 'markdown')
- `enable_heading_anchors` (boolean, optional): Enable anchors (default: false)

**Returns:** JSON object with updated page information and new version.

#### delete_page
Permanently delete a Confluence page.

**Parameters:**
- `page_id` (string, required): Page ID to delete

**Returns:** JSON confirmation of deletion.

---

### Confluence Content Interaction

#### get_comments
Retrieve comments on a Confluence page.

**Parameters:**
- `page_id` (string, required): Page ID

**Returns:** JSON array of comment objects with content and author information.

#### add_comment
Add a comment to a Confluence page with Markdown support.

**Parameters:**
- `page_id` (string, required): Target page ID
- `content` (string, required): Comment content in Markdown

**Returns:** JSON object with created comment details.

#### get_labels
Get all labels attached to a Confluence page.

**Parameters:**
- `page_id` (string, required): Page ID

**Returns:** JSON array of label objects with names and types.

#### add_label
Add a label to a Confluence page for categorization.

**Parameters:**
- `page_id` (string, required): Target page ID
- `name` (string, required): Label name

**Returns:** JSON object with updated label list.

---

## Authentication & Configuration

All tools require proper authentication configuration. The server supports:

- **API Token** (Cloud): Username + API token
- **Personal Access Token** (Server/DC): PAT-based authentication  
- **OAuth 2.0** (Cloud): Standard OAuth flow with refresh tokens
- **BYOT OAuth** (Cloud): Bring Your Own Token for external management
- **Multi-user HTTP**: Per-request authentication via headers

See the main README for detailed authentication setup instructions.

## Error Handling

All tools return consistent JSON responses with error handling:

```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional context"
}
```

Common error types:
- **Authentication errors**: Invalid credentials or permissions
- **Network errors**: Connection timeouts or API unavailability  
- **Validation errors**: Invalid parameters or missing required fields
- **Not found errors**: Non-existent issues, pages, or users

## Rate Limits & Performance

- Tools respect Atlassian API rate limits automatically
- Batch operations are preferred for bulk actions
- Pagination is supported where applicable
- Caching is implemented for frequently accessed data

## Version Compatibility

- **Jira Cloud**: Full API v3 support
- **Jira Server/DC**: API v2 with graceful degradation
- **Confluence Cloud**: API v2 with ADF format support
- **Confluence Server/DC**: API v1 with wiki markup format

---

*This toolset documentation is automatically maintained and reflects the current server implementation.*