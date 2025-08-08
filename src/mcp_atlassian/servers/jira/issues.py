"""Jira issue management tools with mixin-based architecture."""

import json
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp_atlassian.jira.constants import DEFAULT_READ_JIRA_FIELDS
from mcp_atlassian.servers.dependencies import get_jira_fetcher
from mcp_atlassian.utils.decorators import check_write_access
from mcp_atlassian.utils.tool_helpers import safe_tool_result

from .mixins import (
    IssueCreationMixin,
    IssueUpdateMixin, 
    IssueSearchMixin,
    IssueLinkingMixin
)

logger = logging.getLogger(__name__)

# Create FastMCP instance for issues
issues_mcp = FastMCP(
    name="Jira Issues Service",
    description="Provides tools for Jira issue management.",
)


class IssuesServer(IssueCreationMixin, IssueUpdateMixin, IssueSearchMixin, IssueLinkingMixin):
    """Container for Jira issue management tools using mixins."""
    
    def __init__(self):
        self.mcp = issues_mcp
        
    def get_tools(self):
        """Get all issue management tools."""
        return self.mcp.tools


# Register all mixin methods as FastMCP tools
server_instance = IssuesServer()

# Creation tools
@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
@safe_tool_result
async def create_issue(
    ctx: Context,
    project_key: Annotated[
        str,
        Field(
            description=(
                "The JIRA project key (e.g. 'PROJ', 'DEV', 'SUPPORT'). "
                "This is the prefix of issue keys in your project. "
                "Never assume what it might be, always ask the user."
            )
        ),
    ],
    summary: Annotated[str, Field(description="Summary/title of the issue")],
    issue_type: Annotated[
        str,
        Field(
            description=(
                "Issue type (e.g. 'Task', 'Bug', 'Story', 'Epic', 'Subtask'). "
                "The available types depend on your project configuration. "
                "For subtasks, use 'Subtask' (not 'Sub-task') and include parent in additional_fields."
            ),
        ),
    ],
    assignee: Annotated[
        str | None,
        Field(
            description="(Optional) Assignee's user identifier (string): Email, display name, or account ID (e.g., 'user@example.com', 'John Doe', 'accountid:...')",
            default=None,
        ),
    ] = None,
    description: Annotated[
        str | None, Field(description="Issue description", default=None)
    ] = None,
    components: Annotated[
        str | None,
        Field(
            description="(Optional) Comma-separated list of component names to assign (e.g., 'Frontend,API')",
            default=None,
        ),
    ] = None,
    additional_fields: Annotated[
        dict[str, Any] | str | None,
        Field(
            description=(
                "(Optional) Dictionary of additional fields to set. Examples:\n"
                "- Set priority: {'priority': {'name': 'High'}}\n"
                "- Add labels: {'labels': ['frontend', 'urgent']}\n"
                "- Link to parent (for any issue type): {'parent': 'PROJ-123'}\n"
                "- Set Fix Version/s: {'fixVersions': [{'id': '10020'}]}\n"
                "- Custom fields: {'customfield_10010': 'value'}"
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Create a new Jira issue with optional Epic link or parent for subtasks."""
    # Parse components from comma-separated string to list
    components_list = None
    if components and isinstance(components, str):
        components_list = [comp.strip() for comp in components.split(",") if comp.strip()]
    elif components:
        components_list = components

    # Normalize additional_fields: accept dict or JSON string
    normalized_additional_fields = None
    if additional_fields is not None:
        if isinstance(additional_fields, dict):
            normalized_additional_fields = additional_fields
        elif isinstance(additional_fields, str):
            import json as _json
            try:
                parsed = _json.loads(additional_fields)
                if isinstance(parsed, dict):
                    normalized_additional_fields = parsed
                else:
                    raise ValueError("additional_fields JSON must decode to an object")
            except Exception as e:
                raise ValueError(f"Invalid JSON for additional_fields: {e}") from e
        else:
            raise ValueError("additional_fields must be a dictionary or JSON string.")

    # Delegate to the mixin's tool (which returns a JSON string via its own decorator)
    return await server_instance.create_issue(
        ctx,
        project_key,
        summary,
        issue_type,
        assignee,
        description,
        components_list,
        normalized_additional_fields,
    )


@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
@safe_tool_result
async def batch_create_issues(
    ctx: Context,
    issues: Annotated[
        str,
        Field(
            description=(
                "JSON array of issue objects. Each object should contain:\n"
                "- project_key (required): The project key (e.g., 'PROJ')\n"
                "- summary (required): Issue summary/title\n"
                "- issue_type (required): Type of issue (e.g., 'Task', 'Bug')\n"
                "- description (optional): Issue description\n"
                "- assignee (optional): Assignee username or email\n"
                "- components (optional): Array of component names\n"
                "Example: [\n"
                '  {"project_key": "PROJ", "summary": "Issue 1", "issue_type": "Task"},\n'
                '  {"project_key": "PROJ", "summary": "Issue 2", "issue_type": "Bug", "components": ["Frontend"]}\n'
                "]"
            )
        ),
    ],
    validate_only: Annotated[
        bool,
        Field(
            description="If true, only validates the issues without creating them",
            default=False,
        ),
    ] = False,
) -> str:
    """Create multiple Jira issues in a batch."""
    return await server_instance.batch_create_issues(ctx, issues, validate_only)


# Update tools
@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
async def update_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    fields: Annotated[
        dict[str, Any],
        Field(
            description=(
                "Dictionary of fields to update. For 'assignee', provide a string identifier (email, name, or accountId). "
                "Example: `{'assignee': 'user@example.com', 'summary': 'New Summary'}`"
            )
        ),
    ],
    additional_fields: Annotated[
        dict[str, Any] | None,
        Field(
            description="(Optional) Dictionary of additional fields to update. Use this for custom fields or more complex updates.",
            default=None,
        ),
    ] = None,
    attachments: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) JSON string array or comma-separated list of file paths to attach to the issue. "
                "Example: '/path/to/file1.txt,/path/to/file2.txt' or ['/path/to/file1.txt','/path/to/file2.txt']"
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Update an existing Jira issue including changing status, adding Epic links, updating fields, etc."""
    return await server_instance.update_issue(ctx, issue_key, fields, additional_fields, attachments)


@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
async def delete_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g. PROJ-123)")],
) -> str:
    """Delete an existing Jira issue."""
    return await server_instance.delete_issue(ctx, issue_key)


@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
async def add_comment(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    comment: Annotated[str, Field(description="Comment text in Markdown format")],
) -> str:
    """Add a comment to a Jira issue."""
    return await server_instance.add_comment(ctx, issue_key, comment)


"""
Note: Worklog tools have been removed from MCP server; add_worklog is no longer available.
"""


@issues_mcp.tool(tags={"jira", "write"})
@check_write_access
async def transition_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    transition_id: Annotated[
        str,
        Field(
            description=(
                "ID of the transition to perform. Use the jira_get_transitions tool first "
                "to get the available transition IDs for the issue. Example values: '11', '21', '31'"
            )
        ),
    ],
    fields: Annotated[
        dict[str, Any] | None,
        Field(
            description=(
                "(Optional) Dictionary of fields to update during the transition. "
                "Some transitions require specific fields to be set (e.g., resolution). "
                "Example: {'resolution': {'name': 'Fixed'}}"
            ),
            default=None,
        ),
    ] = None,
    comment: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Comment to add during the transition. "
                "This will be visible in the issue history."
            ),
        ),
    ] = None,
) -> str:
    """Transition a Jira issue to a new status."""
    return await server_instance.transition_issue(ctx, issue_key, transition_id, fields, comment)


# Search tools
@issues_mcp.tool(tags={"jira", "read"})
async def get_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    fields: Annotated[
        str,
        Field(
            description=(
                "(Optional) Comma-separated list of fields to return (e.g., 'summary,status,customfield_10010'). "
                "You may also provide a single field as a string (e.g., 'duedate'). "
                "Use '*all' for all fields (including custom fields), or omit for essential fields only."
            ),
            default=",".join(DEFAULT_READ_JIRA_FIELDS),
        ),
    ] = ",".join(DEFAULT_READ_JIRA_FIELDS),
    expand: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Fields to expand. Examples: 'renderedFields' (for rendered content), "
                "'transitions' (for available status transitions), 'changelog' (for history)"
            ),
            default=None,
        ),
    ] = None,
    comment_limit: Annotated[
        int,
        Field(
            description="Maximum number of comments to include (0 or null for no comments)",
            default=10,
            ge=0,
            le=100,
        ),
    ] = 10,
    properties: Annotated[
        str | None,
        Field(
            description="(Optional) A comma-separated list of issue properties to return",
            default=None,
        ),
    ] = None,
    update_history: Annotated[
        bool,
        Field(
            description="Whether to update the issue view history for the requesting user",
            default=True,
        ),
    ] = True,
) -> str:
    """Get details of a specific Jira issue including its Epic links and relationship information."""
    return await server_instance.get_issue(
        ctx, issue_key, fields, expand, comment_limit, properties, update_history
    )


@issues_mcp.tool(tags={"jira", "read"})
async def batch_get_changelogs(
    ctx: Context,
    issue_ids_or_keys: Annotated[
        list[str],
        Field(
            description="List of Jira issue IDs or keys, e.g. ['PROJ-123', 'PROJ-124']"
        ),
    ],
    fields: Annotated[
        list[str] | None,
        Field(
            description="(Optional) Filter the changelogs by fields, e.g. ['status', 'assignee']. Default to None for all fields.",
            default=None,
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(
            description=(
                "Maximum number of changelogs to return in result for each issue. "
                "Default to -1 for all changelogs. "
                "Notice that it only limits the results in the response, "
                "the function will still fetch all the data."
            ),
            default=-1,
        ),
    ] = -1,
) -> str:
    """Get changelogs for multiple Jira issues (Cloud only)."""
    return await server_instance.batch_get_changelogs(ctx, issue_ids_or_keys, fields, limit)