"""Issue linking tool functions for Jira operations."""

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
async def get_link_types(ctx: Context) -> str:
    """Get all available issue link types.

    Args:
        ctx: The FastMCP context.

    Returns:
        JSON string representing a list of issue link type objects.
    """
    jira = await get_jira_fetcher(ctx)
    link_types = jira.get_issue_link_types()
    formatted_link_types = [link_type.to_simplified_dict() for link_type in link_types]
    return json.dumps(formatted_link_types, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def link_to_epic(
    ctx: Context,
    issue_key: Annotated[
        str, Field(description="The key of the issue to link (e.g., 'PROJ-123')")
    ],
    epic_key: Annotated[
        str, Field(description="The key of the epic to link to (e.g., 'PROJ-456')")
    ],
) -> str:
    """Link an existing issue to an epic.

    Args:
        ctx: The FastMCP context.
        issue_key: The key of the issue to link.
        epic_key: The key of the epic to link to.

    Returns:
        JSON string representing the updated issue object.

    Raises:
        ValueError: If in read-only mode or Jira client unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    issue = jira.link_issue_to_epic(issue_key, epic_key)
    result = {
        "message": f"Issue {issue_key} has been linked to epic {epic_key}.",
        "issue": issue.to_simplified_dict(),
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_issue_link(
    ctx: Context,
    link_type: Annotated[
        str,
        Field(
            description="The type of link to create (e.g., 'Duplicate', 'Blocks', 'Relates to')"
        ),
    ],
    inward_issue_key: Annotated[
        str, Field(description="The key of the inward issue (e.g., 'PROJ-123')")
    ],
    outward_issue_key: Annotated[
        str, Field(description="The key of the outward issue (e.g., 'PROJ-456')")
    ],
    comment: Annotated[
        str | None, Field(description="(Optional) Comment to add to the link")
    ] = None,
    comment_visibility: Annotated[
        dict[str, str] | None,
        Field(
            description="(Optional) Visibility settings for the comment (e.g., {'type': 'group', 'value': 'jira-users'})",
            default=None,
        ),
    ] = None,
) -> str:
    """Create a link between two Jira issues.

    Args:
        ctx: The FastMCP context.
        link_type: The type of link (e.g., 'Blocks').
        inward_issue_key: The key of the source issue.
        outward_issue_key: The key of the target issue.
        comment: Optional comment text.
        comment_visibility: Optional dictionary for comment visibility.

    Returns:
        JSON string indicating success or failure.

    Raises:
        ValueError: If required fields are missing, invalid input, in read-only mode, or Jira client unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    if not all([link_type, inward_issue_key, outward_issue_key]):
        raise ValueError(
            "link_type, inward_issue_key, and outward_issue_key are required."
        )

    link_data = {
        "type": {"name": link_type},
        "inwardIssue": {"key": inward_issue_key},
        "outwardIssue": {"key": outward_issue_key},
    }

    if comment:
        comment_obj = {"body": comment}
        if comment_visibility and isinstance(comment_visibility, dict):
            if "type" in comment_visibility and "value" in comment_visibility:
                comment_obj["visibility"] = comment_visibility
            else:
                logger.warning("Invalid comment_visibility dictionary structure.")
        link_data["comment"] = comment_obj

    result = jira.create_issue_link(link_data)
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_remote_issue_link(
    ctx: Context,
    issue_key: Annotated[
        str,
        Field(description="The key of the issue to add the link to (e.g., 'PROJ-123')"),
    ],
    url: Annotated[
        str,
        Field(
            description="The URL to link to (e.g., 'https://example.com/page' or Confluence page URL)"
        ),
    ],
    title: Annotated[
        str,
        Field(
            description="The title/name of the link (e.g., 'Documentation Page', 'Confluence Page')"
        ),
    ],
    summary: Annotated[
        str | None, Field(description="(Optional) Description of the link")
    ] = None,
    relationship: Annotated[
        str | None,
        Field(
            description="(Optional) Relationship description (e.g., 'causes', 'relates to', 'documentation')"
        ),
    ] = None,
    icon_url: Annotated[
        str | None, Field(description="(Optional) URL to a 16x16 icon for the link")
    ] = None,
) -> str:
    """Create a remote issue link (web link or Confluence link) for a Jira issue.

    This tool allows you to add web links and Confluence links to Jira issues.
    The links will appear in the issue's "Links" section and can be clicked to navigate to external resources.

    Args:
        ctx: The FastMCP context.
        issue_key: The key of the issue to add the link to.
        url: The URL to link to (can be any web page or Confluence page).
        title: The title/name that will be displayed for the link.
        summary: Optional description of what the link is for.
        relationship: Optional relationship description.
        icon_url: Optional URL to a 16x16 icon for the link.

    Returns:
        JSON string indicating success or failure.

    Raises:
        ValueError: If required fields are missing, invalid input, in read-only mode, or Jira client unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    if not issue_key:
        raise ValueError("issue_key is required.")
    if not url:
        raise ValueError("url is required.")
    if not title:
        raise ValueError("title is required.")

    # Build the remote link data structure
    link_object = {
        "url": url,
        "title": title,
    }

    if summary:
        link_object["summary"] = summary

    if icon_url:
        link_object["icon"] = {"url16x16": icon_url, "title": title}

    link_data = {"object": link_object}

    if relationship:
        link_data["relationship"] = relationship

    result = jira.create_remote_issue_link(issue_key, link_data)
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def remove_issue_link(
    ctx: Context,
    link_id: Annotated[str, Field(description="The ID of the link to remove")],
) -> str:
    """Remove a link between two Jira issues.

    Args:
        ctx: The FastMCP context.
        link_id: The ID of the link to remove.

    Returns:
        JSON string indicating success.

    Raises:
        ValueError: If link_id is missing, in read-only mode, or Jira client unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    if not link_id:
        raise ValueError("link_id is required")

    result = jira.remove_issue_link(link_id)  # Returns dict on success
    return json.dumps(result, indent=2, ensure_ascii=False)