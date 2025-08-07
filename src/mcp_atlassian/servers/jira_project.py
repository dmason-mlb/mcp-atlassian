"""Project and version management tool functions for Jira operations."""

import logging

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


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
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
    """Create multiple Jira issues in a batch.

    Args:
        ctx: The FastMCP context.
        issues: JSON array string of issue objects.
        validate_only: If true, only validates without creating.

    Returns:
        JSON string indicating success and listing created issues (or validation result).

    Raises:
        ValueError: If in read-only mode, Jira client unavailable, or invalid JSON.
    """
    jira = await get_jira_fetcher(ctx)
    # Parse issues from JSON string
    try:
        issues_list = json.loads(issues)
        if not isinstance(issues_list, list):
            raise ValueError("Input 'issues' must be a JSON array string.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in issues")
    except Exception as e:
        raise ValueError(f"Invalid input for issues: {e}") from e

    # Create issues in batch
    created_issues = jira.batch_create_issues(issues_list, validate_only=validate_only)

    message = (
        "Issues validated successfully"
        if validate_only
        else "Issues created successfully"
    )
    result = {
        "message": message,
        "issues": [issue.to_simplified_dict() for issue in created_issues],
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "read"})
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
    """Get changelogs for multiple Jira issues (Cloud only).

    Args:
        ctx: The FastMCP context.
        issue_ids_or_keys: List of issue IDs or keys.
        fields: List of fields to filter changelogs by. None for all fields.
        limit: Maximum changelogs per issue (-1 for all).

    Returns:
        JSON string representing a list of issues with their changelogs.

    Raises:
        NotImplementedError: If run on Jira Server/Data Center.
        ValueError: If Jira client is unavailable.
    """
    jira = await get_jira_fetcher(ctx)
    # Ensure this runs only on Cloud, as per original function docstring
    if not jira.config.is_cloud:
        raise NotImplementedError(
            "Batch get issue changelogs is only available on Jira Cloud."
        )

    # Call the underlying method
    issues_with_changelogs = jira.batch_get_changelogs(
        issue_ids_or_keys=issue_ids_or_keys, fields=fields
    )

    # Format the response
    results = []
    limit_val = None if limit == -1 else limit
    for issue in issues_with_changelogs:
        results.append(
            {
                "issue_id": issue.id,
                "changelogs": [
                    changelog.to_simplified_dict()
                    for changelog in issue.changelogs[:limit_val]
                ],
            }
        )
    return json.dumps(results, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "read"})
async def get_project_versions(
    ctx: Context,
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
) -> str:
    """Get all fix versions for a specific Jira project."""
    jira = await get_jira_fetcher(ctx)
    versions = jira.get_project_versions(project_key)
    return json.dumps(versions, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "read"})
async def get_all_projects(
    ctx: Context,
    include_archived: Annotated[
        bool,
        Field(
            description="Whether to include archived projects in the results",
            default=False,
        ),
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
    try:
        jira = await get_jira_fetcher(ctx)
        projects = jira.get_all_projects(include_archived=include_archived)
    except (MCPAtlassianAuthenticationError, HTTPError, OSError, ValueError) as e:
        error_message = ""
        log_level = logging.ERROR
        if isinstance(e, MCPAtlassianAuthenticationError):
            error_message = f"Authentication/Permission Error: {str(e)}"
        elif isinstance(e, OSError | HTTPError):
            error_message = f"Network or API Error: {str(e)}"
        elif isinstance(e, ValueError):
            error_message = f"Configuration Error: {str(e)}"

        error_result = {
            "success": False,
            "error": error_message,
        }
        logger.log(log_level, f"get_all_projects failed: {error_message}")
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    # Ensure all project keys are uppercase
    for project in projects:
        if "key" in project:
            project["key"] = project["key"].upper()

    # Apply project filter if configured
    if jira.config.projects_filter:
        # Split projects filter by commas and handle possible whitespace
        allowed_project_keys = {
            p.strip().upper() for p in jira.config.projects_filter.split(",")
        }
        projects = [
            project
            for project in projects
            if project.get("key") in allowed_project_keys
        ]

    return json.dumps(projects, indent=2, ensure_ascii=False)


@jira_mcp.tool(tags={"jira", "write"})
@check_write_access
async def create_version(
    ctx: Context,
    project_key: Annotated[str, Field(description="Jira project key (e.g., 'PROJ')")],
    name: Annotated[str, Field(description="Name of the version")],
    start_date: Annotated[
        str | None, Field(description="Start date (YYYY-MM-DD)", default=None)
    ] = None,
    release_date: Annotated[
        str | None, Field(description="Release date (YYYY-MM-DD)", default=None)
    ] = None,
    description: Annotated[
        str | None, Field(description="Description of the version", default=None)
    ] = None,
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
    try:
        version = jira.create_project_version(
            project_key=project_key,
            name=name,
            start_date=start_date,
            release_date=release_date,
            description=description,
        )
        return json.dumps(version, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(
            f"Error creating version in project {project_key}: {str(e)}", exc_info=True
        )
        return json.dumps(
            {"success": False, "error": str(e)}, indent=2, ensure_ascii=False
        )