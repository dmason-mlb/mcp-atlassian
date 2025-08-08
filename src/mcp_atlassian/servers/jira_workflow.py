"""Workflow and transition tool functions for Jira operations."""

from .jira_shared import (
    Annotated,
    Any,
    Context,
    Field,
    HTTPError,
    MCPAtlassianAuthenticationError,
    DEFAULT_READ_JIRA_FIELDS,
    JiraUser,
    check_write_access,
    get_jira_fetcher,
    jira_mcp,
    json,
    logger,
    safe_tool_result,
)


@jira_mcp.tool(tags={"jira", "read"})
async def get_transitions(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
) -> str:
    """Get available status transitions for a Jira issue.

    Args:
        ctx: The FastMCP context.
        issue_key: Jira issue key.

    Returns:
        JSON string representing a list of available transitions.
    """
    jira = await get_jira_fetcher(ctx)
    # Underlying method returns list[dict] in the desired format
    transitions = jira.get_available_transitions(issue_key)
    return json.dumps(transitions, indent=2, ensure_ascii=False)


"""
Note: Worklog tools have been removed from MCP server; get_worklog is no longer available.
"""


@jira_mcp.tool(tags={"jira", "read"})
async def download_attachments(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    target_dir: Annotated[
        str, Field(description="Directory where attachments should be saved")
    ],
) -> str:
    """Download attachments from a Jira issue.

    Args:
        ctx: The FastMCP context.
        issue_key: Jira issue key.
        target_dir: Directory to save attachments.

    Returns:
        JSON string indicating the result of the download operation.
    """
    jira = await get_jira_fetcher(ctx)
    result = jira.download_issue_attachments(issue_key=issue_key, target_dir=target_dir)
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def upload_attachment(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    file_path: Annotated[
        str, Field(description="Absolute or relative path to a file to upload as an attachment")
    ],
) -> str:
    """Upload a single attachment to a Jira issue.

    Uses Jira REST API v3 attachments endpoint (multipart/form-data with X-Atlassian-Token: no-check).

    Args:
        ctx: The FastMCP context.
        issue_key: Jira issue key.
        file_path: Path to the local file to upload.

    Returns:
        JSON string indicating the result of the upload operation.
    """
    jira = await get_jira_fetcher(ctx)
    result = jira.upload_attachment(issue_key, file_path)
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
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
    """Transition a Jira issue to a new status.

    Args:
        ctx: The FastMCP context.
        issue_key: Jira issue key.
        transition_id: ID of the transition.
        fields: Optional dictionary of fields to update during transition.
        comment: Optional comment for the transition.

    Returns:
        JSON string representing the updated issue object.

    Raises:
        ValueError: If required fields missing, invalid input, in read-only mode, or Jira client unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    if not issue_key or not transition_id:
        raise ValueError("issue_key and transition_id are required.")

    # Use fields directly as dict
    update_fields = fields or {}
    if not isinstance(update_fields, dict):
        raise ValueError("fields must be a dictionary.")

    issue = jira.transition_issue(
        issue_key=issue_key,
        transition_id=transition_id,
        fields=update_fields,
        comment=comment,
    )

    result = {
        "message": f"Issue {issue_key} transitioned successfully",
        "issue": issue.to_simplified_dict() if issue else None,
    }
    return json.dumps(result, indent=2, ensure_ascii=False)