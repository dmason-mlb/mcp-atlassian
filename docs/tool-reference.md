# MCP Atlassian Tool Reference

This document provides a comprehensive reference for all tools available in the MCP Atlassian server, including their arguments and descriptions.

## Table of Contents

- [Jira Tools](#jira-tools)
  - [Read Operations](#jira-read-operations)
  - [Write Operations](#jira-write-operations)
  - [Agile Operations](#jira-agile-operations)
- [Confluence Tools](#confluence-tools)
  - [Read Operations](#confluence-read-operations)
  - [Write Operations](#confluence-write-operations)

## Jira Tools

### Jira Read Operations

#### jira_get_user_profile
Retrieve profile information for a specific Jira user.

**Arguments:**
- `user_identifier` (string, required): User identifier (email, username, key, or account ID)

**Returns:** JSON string representing the Jira user profile object

---

#### jira_get_issue
Get details of a specific Jira issue including its Epic links and relationship information.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `fields` (string, optional): Comma-separated list of fields to return (e.g., 'summary,status,customfield_10010'), '*all' for all fields, or omit for essentials
- `expand` (string, optional): Fields to expand (e.g., 'renderedFields', 'transitions', 'changelog')
- `comment_limit` (integer, optional, default: 10): Maximum number of comments (0-100)
- `properties` (string, optional): Issue properties to return
- `update_history` (boolean, optional, default: true): Whether to update issue view history

**Returns:** JSON string representing the Jira issue object

---

#### jira_search
Search Jira issues using JQL (Jira Query Language).

**Arguments:**
- `jql` (string, required): JQL query string. Examples:
  - Find Epics: `"issuetype = Epic AND project = PROJ"`
  - Find issues in Epic: `"parent = PROJ-123"`
  - Find by status: `"status = 'In Progress' AND project = PROJ"`
  - Find by assignee: `"assignee = currentUser()"`
  - Find recently updated: `"updated >= -7d AND project = PROJ"`
- `fields` (string, optional): Comma-separated fields to return
- `limit` (integer, optional, default: 10): Maximum results (1-50)
- `start_at` (integer, optional, default: 0): Starting index for pagination
- `projects_filter` (string, optional): Comma-separated project keys to filter by
- `expand` (string, optional): Fields to expand

**Returns:** JSON string with search results and pagination info

---

#### jira_search_fields
Search Jira fields by keyword with fuzzy match.

**Arguments:**
- `keyword` (string, optional): Keyword for fuzzy search. If empty, lists first available fields
- `limit` (integer, optional, default: 10): Maximum results
- `refresh` (boolean, optional, default: false): Force refresh field list

**Returns:** JSON string representing matching field definitions

---

#### jira_get_project_issues
Get all issues for a specific Jira project.

**Arguments:**
- `project_key` (string, required): The project key
- `limit` (integer, optional, default: 10): Maximum results (1-50)
- `start_at` (integer, optional, default: 0): Starting index for pagination

**Returns:** JSON string with search results and pagination info

---

#### jira_get_transitions
Get available status transitions for a Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')

**Returns:** JSON string representing available transitions

---

#### jira_get_worklog
Get worklog entries for a Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')

**Returns:** JSON string representing worklog entries

---

#### jira_download_attachments
Download attachments from a Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `target_dir` (string, required): Directory to save attachments

**Returns:** JSON string indicating download operation result

---

#### jira_get_link_types
Get all available issue link types.

**Arguments:** None

**Returns:** JSON string representing issue link type objects

---

#### jira_get_project_versions
Get all fix versions for a specific Jira project.

**Arguments:**
- `project_key` (string, required): Jira project key (e.g., 'PROJ')

**Returns:** JSON string representing project versions

---

#### jira_get_all_projects
Get all Jira projects accessible to the current user.

**Arguments:**
- `include_archived` (boolean, optional, default: false): Include archived projects

**Returns:** JSON string representing accessible projects (filtered by JIRA_PROJECTS_FILTER if configured)

---

#### jira_batch_get_changelogs
Get changelogs for multiple Jira issues (Cloud only).

**Arguments:**
- `issue_ids_or_keys` (array, required): List of issue IDs or keys
- `fields` (array, optional): Filter changelogs by specific fields
- `limit` (integer, optional, default: -1): Max changelogs per issue (-1 for all)

**Returns:** JSON string representing issues with their changelogs

**Note:** Not supported on Jira Server/Data Center

---

### Jira Write Operations

#### jira_create_issue
Create a new Jira issue with optional Epic link or parent for subtasks.

**Arguments:**
- `project_key` (string, required): The JIRA project key (e.g., 'PROJ', 'DEV')
- `summary` (string, required): Summary/title of the issue
- `issue_type` (string, required): Issue type (e.g., 'Task', 'Bug', 'Story', 'Epic', 'Subtask')
- `assignee` (string, optional): Assignee's identifier (email, display name, or account ID)
- `description` (string, optional): Issue description
- `components` (string, optional): Comma-separated component names
- `additional_fields` (object, optional): Dictionary of additional fields. Examples:
  - Set priority: `{'priority': {'name': 'High'}}`
  - Add labels: `{'labels': ['frontend', 'urgent']}`
  - Link to parent: `{'parent': 'PROJ-123'}`

**Returns:** JSON string representing the created issue

---

#### jira_batch_create_issues
Create multiple Jira issues in a batch.

**Arguments:**
- `issues` (string, required): JSON array of issue objects. Each should contain:
  - `project_key` (required): The project key
  - `summary` (required): Issue title
  - `issue_type` (required): Type of issue
  - `description` (optional): Issue description
  - `assignee` (optional): Assignee username or email
  - `components` (optional): Array of component names
- `validate_only` (boolean, optional, default: false): Only validate without creating

**Returns:** JSON string indicating success and listing created issues

---

#### jira_update_issue
Update an existing Jira issue including status, fields, Epic links, etc.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `fields` (object, required): Dictionary of fields to update
- `additional_fields` (object, optional): Additional fields for complex updates
- `attachments` (string, optional): JSON array or comma-separated file paths to attach

**Returns:** JSON string representing updated issue and attachment results

---

#### jira_delete_issue
Delete an existing Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')

**Returns:** JSON string indicating success

---

#### jira_add_comment
Add a comment to a Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `comment` (string, required): Comment text in Markdown format

**Returns:** JSON string representing the added comment

---

#### jira_add_worklog
Add a worklog entry to a Jira issue.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `time_spent` (string, required): Time in Jira format (e.g., '1h 30m', '1d', '4h')
- `comment` (string, optional): Comment for the worklog in Markdown
- `started` (string, optional): Start time in ISO format
- `original_estimate` (string, optional): New original estimate
- `remaining_estimate` (string, optional): New remaining estimate

**Returns:** JSON string representing the added worklog

---

#### jira_link_to_epic
Link an existing issue to an epic.

**Arguments:**
- `issue_key` (string, required): Issue to link (e.g., 'PROJ-123')
- `epic_key` (string, required): Epic to link to (e.g., 'PROJ-456')

**Returns:** JSON string representing the updated issue

---

#### jira_create_issue_link
Create a link between two Jira issues.

**Arguments:**
- `link_type` (string, required): Type of link (e.g., 'Blocks', 'Relates to', 'Duplicate')
- `inward_issue_key` (string, required): Source issue key
- `outward_issue_key` (string, required): Target issue key
- `comment` (string, optional): Comment to add to the link
- `comment_visibility` (object, optional): Visibility settings for comment

**Returns:** JSON string indicating success or failure

---

#### jira_create_remote_issue_link
Create a remote issue link (web link or Confluence link) for a Jira issue.

**Arguments:**
- `issue_key` (string, required): Issue to add link to (e.g., 'PROJ-123')
- `url` (string, required): URL to link to (web page or Confluence page)
- `title` (string, required): Title/name displayed for the link
- `summary` (string, optional): Description of the link
- `relationship` (string, optional): Relationship description
- `icon_url` (string, optional): URL to 16x16 icon

**Returns:** JSON string indicating success or failure

---

#### jira_remove_issue_link
Remove a link between two Jira issues.

**Arguments:**
- `link_id` (string, required): The ID of the link to remove

**Returns:** JSON string indicating success

---

#### jira_transition_issue
Transition a Jira issue to a new status.

**Arguments:**
- `issue_key` (string, required): Jira issue key (e.g., 'PROJ-123')
- `transition_id` (string, required): ID of the transition (use jira_get_transitions first)
- `fields` (object, optional): Fields to update during transition
- `comment` (string, optional): Comment to add during transition

**Returns:** JSON string representing the updated issue

---

#### jira_create_version
Create a new fix version in a Jira project.

**Arguments:**
- `project_key` (string, required): Jira project key (e.g., 'PROJ')
- `name` (string, required): Name of the version
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `release_date` (string, optional): Release date (YYYY-MM-DD)
- `description` (string, optional): Description of the version

**Returns:** JSON string of the created version

---

#### jira_batch_create_versions
Batch create multiple versions in a Jira project.

**Arguments:**
- `project_key` (string, required): Jira project key (e.g., 'PROJ')
- `versions` (string, required): JSON array of version objects containing:
  - `name` (required): Name of the version
  - `startDate` (optional): Start date (YYYY-MM-DD)
  - `releaseDate` (optional): Release date (YYYY-MM-DD)
  - `description` (optional): Description

**Returns:** JSON array of results with success flag and version or error

---

### Jira Agile Operations

#### jira_get_agile_boards
Get jira agile boards by name, project key, or type.

**Arguments:**
- `board_name` (string, optional): Name of board (fuzzy search)
- `project_key` (string, optional): Project key
- `board_type` (string, optional): Board type ('scrum' or 'kanban')
- `start_at` (integer, optional, default: 0): Starting index
- `limit` (integer, optional, default: 10): Maximum results (1-50)

**Returns:** JSON string representing board objects

---

#### jira_get_board_issues
Get all issues linked to a specific board filtered by JQL.

**Arguments:**
- `board_id` (string, required): The ID of the board (e.g., '1001')
- `jql` (string, required): JQL query string to filter issues
- `fields` (string, optional): Comma-separated fields to return
- `start_at` (integer, optional, default: 0): Starting index
- `limit` (integer, optional, default: 10): Maximum results (1-50)
- `expand` (string, optional, default: 'version'): Fields to expand

**Returns:** JSON string with search results and pagination info

---

#### jira_get_sprints_from_board
Get jira sprints from board by state.

**Arguments:**
- `board_id` (string, required): The ID of the board (e.g., '1000')
- `state` (string, optional): Sprint state ('active', 'future', 'closed')
- `start_at` (integer, optional, default: 0): Starting index
- `limit` (integer, optional, default: 10): Maximum results (1-50)

**Returns:** JSON string representing sprint objects

---

#### jira_get_sprint_issues
Get jira issues from sprint.

**Arguments:**
- `sprint_id` (string, required): The ID of the sprint (e.g., '10001')
- `fields` (string, optional): Comma-separated fields to return
- `start_at` (integer, optional, default: 0): Starting index
- `limit` (integer, optional, default: 10): Maximum results (1-50)

**Returns:** JSON string with search results and pagination info

---

#### jira_create_sprint
Create Jira sprint for a board.

**Arguments:**
- `board_id` (string, required): The ID of board (e.g., '1000')
- `sprint_name` (string, required): Name of the sprint
- `start_date` (string, required): Start date (ISO 8601 format)
- `end_date` (string, required): End date (ISO 8601 format)
- `goal` (string, optional): Sprint goal

**Returns:** JSON string representing the created sprint

---

#### jira_update_sprint
Update jira sprint.

**Arguments:**
- `sprint_id` (string, required): The ID of sprint (e.g., '10001')
- `sprint_name` (string, optional): New name for the sprint
- `state` (string, optional): New state (future|active|closed)
- `start_date` (string, optional): New start date
- `end_date` (string, optional): New end date
- `goal` (string, optional): New goal

**Returns:** JSON string representing the updated sprint

---

## Confluence Tools

### Confluence Read Operations

#### confluence_search
Search Confluence content using simple terms or CQL.

**Arguments:**
- `query` (string, required): Search query - simple text or CQL. Examples:
  - Basic search: `'type=page AND space=DEV'`
  - Personal space: `'space="~username"'` (quotes required)
  - Title search: `'title~"Meeting Notes"'`
  - Recent content: `'created >= "2023-01-01"'`
- `limit` (integer, optional, default: 10): Maximum results (1-50)
- `spaces_filter` (string, optional): Comma-separated space keys to filter by

**Returns:** JSON string representing simplified Confluence page objects

---

#### confluence_get_page
Get content of a specific Confluence page by ID, or by title and space key.

**Arguments:**
- `page_id` (string, optional): Confluence page ID (numeric ID from URL)
- `title` (string, optional): Exact page title (use with space_key)
- `space_key` (string, optional): Space key (use with title)
- `include_metadata` (boolean, optional, default: true): Include page metadata
- `convert_to_markdown` (boolean, optional, default: true): Convert to markdown or keep HTML

**Returns:** JSON string representing page content and/or metadata

**Note:** Provide either `page_id` OR both `title` and `space_key`

---

#### confluence_get_page_children
Get child pages of a specific Confluence page.

**Arguments:**
- `parent_id` (string, required): ID of the parent page
- `expand` (string, optional, default: 'version'): Fields to expand
- `limit` (integer, optional, default: 25): Maximum child pages (1-50)
- `include_content` (boolean, optional, default: false): Include page content
- `convert_to_markdown` (boolean, optional, default: true): Convert content to markdown
- `start` (integer, optional, default: 0): Starting index for pagination

**Returns:** JSON string representing child page objects

---

#### confluence_get_comments
Get comments for a specific Confluence page.

**Arguments:**
- `page_id` (string, required): Confluence page ID

**Returns:** JSON string representing comment objects

---

#### confluence_get_labels
Get labels for a specific Confluence page.

**Arguments:**
- `page_id` (string, required): Confluence page ID

**Returns:** JSON string representing label objects

---

#### confluence_search_user
Search Confluence users using CQL.

**Arguments:**
- `query` (string, required): CQL query for user search (e.g., `'user.fullname ~ "First Last"'`)
- `limit` (integer, optional, default: 10): Maximum results (1-50)

**Returns:** JSON string representing user search results

---

### Confluence Write Operations

#### confluence_create_page
Create a new Confluence page.

**Arguments:**
- `space_key` (string, required): Space key (e.g., 'DEV', 'TEAM')
- `title` (string, required): Page title
- `content` (string, required): Page content (Markdown by default)
- `parent_id` (string, optional): Parent page ID for child pages
- `content_format` (string, optional, default: 'markdown'): Format ('markdown', 'wiki', 'storage')
- `enable_heading_anchors` (boolean, optional, default: false): Enable heading anchors (markdown only)

**Returns:** JSON string representing the created page

---

#### confluence_update_page
Update an existing Confluence page.

**Arguments:**
- `page_id` (string, required): ID of the page to update
- `title` (string, required): New page title
- `content` (string, required): New page content
- `is_minor_edit` (boolean, optional, default: false): Mark as minor edit
- `version_comment` (string, optional): Comment for this version
- `parent_id` (string, optional): New parent page ID
- `content_format` (string, optional, default: 'markdown'): Format ('markdown', 'wiki', 'storage')
- `enable_heading_anchors` (boolean, optional, default: false): Enable heading anchors

**Returns:** JSON string representing the updated page

---

#### confluence_delete_page
Delete an existing Confluence page.

**Arguments:**
- `page_id` (string, required): ID of the page to delete

**Returns:** JSON string indicating success or failure

---

#### confluence_add_comment
Add a comment to a Confluence page.

**Arguments:**
- `page_id` (string, required): ID of the page to comment on
- `content` (string, required): Comment content in Markdown format

**Returns:** JSON string representing the created comment

---

#### confluence_add_label
Add label to an existing Confluence page.

**Arguments:**
- `page_id` (string, required): ID of the page to update
- `name` (string, required): Name of the label

**Returns:** JSON string representing updated label list

---

## Tool Categories

### Read vs Write Operations

**Read Operations** - Available in all modes:
- All `get_`, `search_`, `list_`, and `download_` tools
- No modifications to Atlassian data

**Write Operations** - Disabled in read-only mode:
- All `create_`, `update_`, `delete_`, `add_`, and `transition_` tools
- Any operation that modifies Atlassian data

### Authentication Requirements

All tools require proper authentication:
- **Cloud**: API token or OAuth 2.0
- **Server/DC**: Personal Access Token or API token

### Error Handling

All tools return JSON responses:
- **Success**: JSON with requested data
- **Error**: JSON with error details and `success: false`

Common error scenarios:
- Missing authentication
- Insufficient permissions
- Invalid parameters
- Read-only mode violations
- Service unavailable

## Notes

1. **Markdown Support**: Both Jira and Confluence tools accept Markdown content which is automatically converted to the appropriate format (ADF for Cloud, wiki markup for Server/DC)

2. **Pagination**: Most list/search operations support pagination via `start_at`/`start` and `limit` parameters

3. **Field Selection**: Many read operations allow field selection to optimize response size

4. **Project/Space Filtering**: Can be configured via environment variables to restrict access to specific projects/spaces

5. **Rate Limiting**: Be aware of Atlassian API rate limits when making bulk operations
