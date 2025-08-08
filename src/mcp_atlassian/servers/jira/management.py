"""Jira management and administrative tools."""

import json
import logging
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.models.jira.common import JiraUser
from mcp_atlassian.servers.dependencies import get_jira_fetcher
from mcp_atlassian.utils.decorators import check_write_access
from mcp_atlassian.utils.tool_helpers import safe_tool_result

logger = logging.getLogger(__name__)

management_mcp = FastMCP(
    name="Jira Management Service",
    description="Provides tools for Jira management and administration.",
)


class ManagementServer:
    """Container for Jira management tools."""
    
    def __init__(self):
        self.mcp = management_mcp
        
    def get_tools(self):
        """Get all management tools."""
        return self.mcp.tools


@management_mcp.tool(tags={"jira", "read"})
async def get_user_profile(
    ctx: Context,
    user_identifier: Annotated[
        str,
        Field(
            description="Identifier for the user (e.g., email address 'user@example.com', username 'johndoe', account ID 'accountid:...', or key for Server/DC)."
        ),
    ],
) -> str:
    """Retrieve profile information for a specific Jira user.

    Args:
        ctx: The FastMCP context.
        user_identifier: User identifier (email, username, key, or account ID).

    Returns:
        JSON string representing the Jira user profile object, or an error object if not found.

    Raises:
        ValueError: If the Jira client is not configured or available.
    """
    jira = await get_jira_fetcher(ctx)
    try:
        user_data = jira.get_user_profile(user_identifier)
        if isinstance(user_data, JiraUser):
            result = user_data.to_simplified_dict()
        elif isinstance(user_data, dict):
            result = user_data
        else:
            result = {"error": f"User '{user_identifier}' not found"}
        return json.dumps(result, indent=2, ensure_ascii=False)
    except (ValueError, HTTPError, MCPAtlassianAuthenticationError) as e:
        error_result = {"error": f"Failed to get user profile: {str(e)}"}
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "read"})
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
    transitions = jira.get_issue_transitions(issue_key)
    return json.dumps(transitions, indent=2, ensure_ascii=False)


"""
Note: Worklog tools have been removed from MCP server; this module no longer provides worklog operations.
"""


@management_mcp.tool(tags={"jira", "read"})
async def download_attachments(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    target_dir: Annotated[str, Field(description="Directory where attachments should be saved")],
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
    try:
        result = jira.download_attachments(issue_key, target_dir)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_result = {"error": f"Failed to download attachments: {str(e)}"}
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "write"})
@check_write_access
async def upload_attachment(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g., 'PROJ-123')")],
    file_path: Annotated[str, Field(description="Absolute or relative path to a file to upload as an attachment")],
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
    try:
        result = jira.upload_attachment(issue_key, file_path)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        error_result = {"error": f"Failed to upload attachment: {str(e)}"}
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "read"})
async def get_link_types(ctx: Context) -> str:
    """Get all available issue link types.

    Args:
        ctx: The FastMCP context.

    Returns:
        JSON string representing a list of issue link type objects.
    """
    jira = await get_jira_fetcher(ctx)
    link_types = jira.get_issue_link_types()
    return json.dumps(link_types, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "write"})
@check_write_access
async def link_to_epic(
    ctx: Context,
    issue_key: Annotated[str, Field(description="The key of the issue to link (e.g., 'PROJ-123')")],
    epic_key: Annotated[str, Field(description="The key of the epic to link to (e.g., 'PROJ-456')")],
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
    issue = jira.link_issue_to_epic(issue_key=issue_key, epic_key=epic_key)
    result = issue.to_simplified_dict()
    return json.dumps(
        {"message": f"Issue {issue_key} linked to epic {epic_key}", "issue": result},
        indent=2,
        ensure_ascii=False,
    )


@management_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_issue_link(
    ctx: Context,
    link_type: Annotated[str, Field(description="The type of link to create (e.g., 'Duplicate', 'Blocks', 'Relates to')")],
    inward_issue_key: Annotated[str, Field(description="The key of the inward issue (e.g., 'PROJ-123')")],
    outward_issue_key: Annotated[str, Field(description="The key of the outward issue (e.g., 'PROJ-456')")],
    comment: Annotated[str | None, Field(description="(Optional) Comment to add to the link")] = None,
    comment_visibility: Annotated[
        dict[str, str] | None,
        Field(description="(Optional) Visibility settings for the comment (e.g., {'type': 'group', 'value': 'jira-users'})"),
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
    if not link_type or not inward_issue_key or not outward_issue_key:
        raise ValueError("link_type, inward_issue_key, and outward_issue_key are required.")

    # Use comment_visibility directly as dict
    visibility = comment_visibility or {}
    if not isinstance(visibility, dict):
        raise ValueError("comment_visibility must be a dictionary.")

    success = jira.create_issue_link(
        link_type=link_type,
        inward_issue_key=inward_issue_key,
        outward_issue_key=outward_issue_key,
        comment=comment,
        comment_visibility=visibility,
    )

    if success:
        result = {
            "message": f"Link created between {inward_issue_key} and {outward_issue_key}",
            "link_type": link_type,
        }
    else:
        result = {"error": "Failed to create issue link"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_remote_issue_link(
    ctx: Context,
    issue_key: Annotated[str, Field(description="The key of the issue to add the link to (e.g., 'PROJ-123')")],
    url: Annotated[str, Field(description="The URL to link to (e.g., 'https://example.com/page' or Confluence page URL)")],
    title: Annotated[str, Field(description="The title/name of the link (e.g., 'Documentation Page', 'Confluence Page')")],
    summary: Annotated[str | None, Field(description="(Optional) Description of the link")] = None,
    relationship: Annotated[
        str | None,
        Field(description="(Optional) Relationship description (e.g., 'causes', 'relates to', 'documentation')"),
    ] = None,
    icon_url: Annotated[str | None, Field(description="(Optional) URL to a 16x16 icon for the link")] = None,
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
    if not issue_key or not url or not title:
        raise ValueError("issue_key, url, and title are required.")

    success = jira.create_remote_issue_link(
        issue_key=issue_key,
        url=url,
        title=title,
        summary=summary,
        relationship=relationship,
        icon_url=icon_url,
    )

    if success:
        result = {
            "message": f"Remote link added to issue {issue_key}",
            "url": url,
            "title": title,
        }
    else:
        result = {"error": "Failed to create remote issue link"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "write"})
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
        raise ValueError("link_id is required.")

    success = jira.remove_issue_link(link_id)
    if success:
        result = {"message": f"Link {link_id} removed successfully"}
    else:
        result = {"error": f"Failed to remove link {link_id}"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "read"})
async def get_project_versions(
    ctx: Context,
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
) -> str:
    """Get all fix versions for a specific Jira project."""
    jira = await get_jira_fetcher(ctx)
    versions = jira.get_project_versions(project_key)
    return json.dumps(versions, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "read"})
async def get_all_projects(
    ctx: Context,
    include_archived: Annotated[
        bool,
        Field(description="Whether to include archived projects in the results", default=False),
    ] = False,
) -> str:
    """Get all Jira projects accessible to the current user.

    Args:
        ctx: The FastMCP context.
        include_archived: Whether to include archived projects.

    Returns:
        JSON string representing a list of project objects accessible to the user.
        Project keys are always returned in uppercase.
        If JIRA_PROJECTS_FILTER is configured, only returns projects matching those keys.

    Raises:
        ValueError: If the Jira client is not configured or available.
    """
    jira = await get_jira_fetcher(ctx)
    projects = jira.get_all_projects(include_archived=include_archived)
    result = [project.to_simplified_dict() for project in projects]
    return json.dumps(result, indent=2, ensure_ascii=False)


@management_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_version(
    ctx: Context,
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
    name: Annotated[str, Field(description="Name of the version")],
    start_date: Annotated[str | None, Field(description="Start date (YYYY-MM-DD)")] = None,
    release_date: Annotated[str | None, Field(description="Release date (YYYY-MM-DD)")] = None,
    description: Annotated[str | None, Field(description="Description of the version")] = None,
) -> str:
    """Create a new fix version in a Jira project.

    Args:
        ctx: The FastMCP context.
        project_key: The project key.
        name: Name of the version.
        start_date: Start date (optional).
        release_date: Release date (optional).
        description: Description (optional).

    Returns:
        JSON string of the created version object.
    """
    jira = await get_jira_fetcher(ctx)
    version = jira.create_version(
        project_key=project_key,
        name=name,
        start_date=start_date,
        release_date=release_date,
        description=description,
    )
    result = version.to_simplified_dict()
    return json.dumps(
        {"message": f"Version '{name}' created in project {project_key}", "version": result},
        indent=2,
        ensure_ascii=False,
    )


@management_mcp.tool(name="batch_create_versions", tags={"jira", "write"})
@check_write_access
@safe_tool_result
async def batch_create_versions(
    ctx: Context,
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
    versions: Annotated[
        str,
        Field(
            description=(
                "JSON array of version objects. Each object should contain:\\n"
                "- name (required): Name of the version\\n"
                "- startDate (optional): Start date (YYYY-MM-DD)\\n"
                "- releaseDate (optional): Release date (YYYY-MM-DD)\\n"
                "- description (optional): Description of the version\\n"
                "Example: [\\n"
                '  {"name": "v1.0", "startDate": "2025-01-01", "releaseDate": "2025-02-01", "description": "First release"},\\n'
                '  {"name": "v2.0"}\\n'
                "]"
            )
        ),
    ],
) -> str:
    """Batch create multiple versions in a Jira project.

    Args:
        ctx: The FastMCP context.
        project_key: The project key.
        versions: JSON array string of version objects.

    Returns:
        JSON array of results, each with success flag, version or error.
    """
    jira = await get_jira_fetcher(ctx)
    # Parse versions from JSON string
    try:
        versions_list = json.loads(versions)
        if not isinstance(versions_list, list):
            raise ValueError("Input 'versions' must be a JSON array string.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in versions")
    except Exception as e:
        raise ValueError(f"Invalid input for versions: {e}") from e

    results = []
    for version_data in versions_list:
        if not isinstance(version_data, dict):
            results.append({"success": False, "error": "Invalid version object format"})
            continue

        name = version_data.get("name")
        if not name:
            results.append({"success": False, "error": "Version name is required"})
            continue

        try:
            version = jira.create_version(
                project_key=project_key,
                name=name,
                start_date=version_data.get("startDate"),
                release_date=version_data.get("releaseDate"),
                description=version_data.get("description"),
            )
            results.append({
                "success": True,
                "version": version.to_simplified_dict(),
            })
        except Exception as e:
            results.append({
                "success": False,
                "error": f"Failed to create version '{name}': {str(e)}",
            })

    return json.dumps(results, indent=2, ensure_ascii=False)