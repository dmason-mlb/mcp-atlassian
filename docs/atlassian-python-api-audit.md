# Atlassian-Python-API Usage Audit

## Overview
This document provides a comprehensive audit of all `atlassian-python-api` library usage in the MCP Atlassian codebase, as part of the migration to direct REST API calls using JIRA v3 and Confluence v2 APIs.

## Import Locations

### Direct Imports
1. **src/mcp_atlassian/jira/client.py**
   - Line 7: `from atlassian import Jira`

2. **src/mcp_atlassian/confluence/client.py**
   - Line 6: `from atlassian import Confluence`

3. **tests/unit/jira/test_fix.py**
   - Line 5: `from atlassian.jira import Jira`

### Re-exports
1. **src/mcp_atlassian/jira/__init__.py**
   - Line 9: `from atlassian.jira import Jira`

## Instance Creation

### JIRA Client Instantiation (src/mcp_atlassian/jira/client.py)
1. **OAuth Authentication** (lines 68-73):
   ```python
   self.jira = Jira(
       url=api_url,
       session=session,
       cloud=True,
       verify_ssl=self.config.ssl_verify,
   )
   ```

2. **PAT Authentication** (lines 80-85):
   ```python
   self.jira = Jira(
       url=self.config.url,
       token=self.config.personal_token,
       cloud=self.config.is_cloud,
       verify_ssl=self.config.ssl_verify,
   )
   ```

3. **Basic Authentication** (lines 93-99):
   ```python
   self.jira = Jira(
       url=self.config.url,
       username=self.config.username,
       password=self.config.api_token,
       cloud=self.config.is_cloud,
       verify_ssl=self.config.ssl_verify,
   )
   ```

### Confluence Client Instantiation (src/mcp_atlassian/confluence/client.py)
Similar pattern with 3 authentication methods: OAuth, PAT, and Basic Auth.

## Method Usage by Module

### JIRA Methods Used

#### issues.py
- `self.jira.get_issue()` - Get issue details
- `self.jira.issue_get_comments()` - Get issue comments
- `self.jira.create_issue()` - Create new issue
- `self.jira.update_issue()` - Update existing issue
- `self.jira.set_issue_status_by_transition_id()` - Transition issue status
- `self.jira.delete_issue()` - Delete issue
- `self.jira.get_issue_transitions()` - Get available transitions
- `self.jira.set_issue_status()` - Set issue status
- `self.jira.create_issues()` - Batch create issues

#### client.py
- `self.jira.myself()` - Get current user info (auth validation)
- `self.jira.get()` - Generic GET request
- `self.jira.post()` - Generic POST request (for paged requests and version creation)
- `self.jira._session` - Access to underlying requests session

#### users.py
- `self.jira.user()`
- `self.jira.myself()`
- `self.jira.user_find_by_user_string()`

#### links.py
- `self.jira.get_issue_link_types()`
- `self.jira.create_issue_link()`
- `self.jira.delete_issue_link()`
- `self.jira.create_or_update_issue_remote_links()`

#### epics.py
- `self.jira.get_issue()`
- `self.jira.update_issue()`

#### worklog.py
- `self.jira.get_issue_worklog()`
- `self.jira.issue_add_worklog()`

#### transitions.py
- `self.jira.get_issue_transitions()`

#### sprints.py
- `self.jira.get_all_agile_boards()`
- `self.jira.get_board_by_filter_id()`
- `self.jira.get_board_by_name()`
- `self.jira.get_board_issues()`
- `self.jira.get_all_sprint()`
- `self.jira.get_sprint_issues()`
- `self.jira.create_sprint()`
- `self.jira.update_sprint()`
- `self.jira.get_issues_for_sprint()`

#### search.py
- `self.jira.jql()`

#### projects.py
- `self.jira.projects()`
- `self.jira.get_all_project_issues()`
- `self.jira.get_project_versions()`

#### fields.py
- `self.jira.get_all_fields()`

#### comments.py
- `self.jira.issue_add_comment()`

#### boards.py
- `self.jira.get_all_agile_boards()`
- `self.jira.get_board()`

#### attachments.py
- `self.jira.download_attachments_from_issue()`

### Confluence Methods Used

#### pages.py
- `self.confluence.get_page_by_id()`
- `self.confluence.get_page_ancestors()`
- `self.confluence.get_page_by_title()`
- `self.confluence.get_all_pages_from_space()`
- `self.confluence.create_page()`
- `self.confluence.update_page()`
- `self.confluence.get_page_child_by_type()`
- `self.confluence.remove_page()`

#### comments.py
- `self.confluence.get_page_comments()`
- `self.confluence.add_comment()`

#### users.py
- `self.confluence.cql()`

#### spaces.py
- `self.confluence.get_all_spaces()`
- `self.confluence.get_space()`

#### search.py
- `self.confluence.cql()`

#### labels.py
- `self.confluence.get_page_labels()`
- `self.confluence.set_page_label()`

#### client.py
- `self.confluence.get_user_details_by_username()`
- `self.confluence._session`

## API Version Mapping

### JIRA API Endpoints Needed (v3)
1. **Issues**
   - GET /rest/api/3/issue/{issueIdOrKey}
   - POST /rest/api/3/issue
   - PUT /rest/api/3/issue/{issueIdOrKey}
   - DELETE /rest/api/3/issue/{issueIdOrKey}
   - POST /rest/api/3/issue/bulk

2. **Comments**
   - GET /rest/api/3/issue/{issueIdOrKey}/comment
   - POST /rest/api/3/issue/{issueIdOrKey}/comment

3. **Transitions**
   - GET /rest/api/3/issue/{issueIdOrKey}/transitions
   - POST /rest/api/3/issue/{issueIdOrKey}/transitions

4. **Worklogs**
   - GET /rest/api/3/issue/{issueIdOrKey}/worklog
   - POST /rest/api/3/issue/{issueIdOrKey}/worklog

5. **Links**
   - GET /rest/api/3/issueLinkType
   - POST /rest/api/3/issueLink
   - DELETE /rest/api/3/issueLink/{linkId}
   - GET /rest/api/3/issue/{issueIdOrKey}/remotelink
   - POST /rest/api/3/issue/{issueIdOrKey}/remotelink

6. **Search**
   - POST /rest/api/3/search

7. **Projects**
   - GET /rest/api/3/project
   - GET /rest/api/3/project/{projectIdOrKey}/version

8. **Fields**
   - GET /rest/api/3/field

9. **Users**
   - GET /rest/api/3/myself
   - GET /rest/api/3/user
   - GET /rest/api/3/user/search

10. **Agile/Boards** (Agile API)
    - GET /rest/agile/1.0/board
    - GET /rest/agile/1.0/board/{boardId}
    - GET /rest/agile/1.0/board/{boardId}/issue
    - GET /rest/agile/1.0/board/{boardId}/sprint
    - GET /rest/agile/1.0/sprint/{sprintId}/issue
    - POST /rest/agile/1.0/sprint
    - PUT /rest/agile/1.0/sprint/{sprintId}

11. **Attachments**
    - GET /rest/api/3/attachment/{id}

12. **Versions**
    - POST /rest/api/3/version

### Confluence API Endpoints Needed (v2)
1. **Pages/Content**
   - GET /wiki/api/v2/pages/{id}
   - GET /wiki/api/v2/pages
   - POST /wiki/api/v2/pages
   - PUT /wiki/api/v2/pages/{id}
   - DELETE /wiki/api/v2/pages/{id}

2. **Comments**
   - GET /wiki/api/v2/pages/{id}/comments
   - POST /wiki/api/v2/comments

3. **Search**
   - GET /wiki/api/v2/search

4. **Spaces**
   - GET /wiki/api/v2/spaces
   - GET /wiki/api/v2/spaces/{id}

5. **Labels**
   - GET /wiki/api/v2/pages/{id}/labels
   - POST /wiki/api/v2/pages/{id}/labels

6. **Users**
   - GET /wiki/rest/api/user/current

## Key Considerations

1. **Authentication Handling**
   - Need to replicate OAuth, PAT, and Basic Auth support
   - Session management for custom headers and proxies
   - SSL verification configuration

2. **Response Format Changes**
   - JIRA v3 expects ADF for description/comments (JSON objects)
   - Confluence v2 also uses ADF for content
   - Different pagination mechanisms

3. **Error Handling**
   - Need consistent error handling across all endpoints
   - Map atlassian-python-api exceptions to new exceptions

4. **Session Access**
   - Several modules access `self.jira._session` or `self.confluence._session`
   - Need to expose session for custom configuration

5. **Generic Methods**
   - `get()` and `post()` methods used for custom endpoints
   - Need to provide similar flexibility in new client

## Migration Priority
1. **High Priority** (blocking ADF support):
   - issues.py - create_issue, update_issue
   - comments.py - issue_add_comment
   - pages.py - create_page, update_page

2. **Medium Priority** (core functionality):
   - search.py - jql, cql
   - users.py - authentication methods
   - transitions.py - status changes

3. **Low Priority** (less frequently used):
   - boards.py - agile functionality
   - attachments.py - file handling
   - links.py - issue linking