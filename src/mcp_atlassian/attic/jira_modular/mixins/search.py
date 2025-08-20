"""Issue search mixin for Jira server."""

import json
import logging
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from mcp_atlassian.jira.constants import DEFAULT_READ_JIRA_FIELDS
from mcp_atlassian.servers.dependencies import get_jira_fetcher

logger = logging.getLogger(__name__)


class IssueSearchMixin:
    """Mixin providing issue search and retrieval tools."""

    async def get_issue(
        self,
        ctx: Context,
        issue_key: Annotated[
            str, Field(description="Jira issue key (e.g., 'PROJ-123')")
        ],
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
        """Get details of a specific Jira issue including its Epic links and relationship information.

        Args:
            ctx: The FastMCP context.
            issue_key: Jira issue key.
            fields: Comma-separated list of fields to return (e.g., 'summary,status,customfield_10010'), a single field as a string (e.g., 'duedate'), '*all' for all fields, or omitted for essentials.
            expand: Optional fields to expand.
            comment_limit: Maximum number of comments.
            properties: Issue properties to return.
            update_history: Whether to update issue view history.

        Returns:
            JSON string representing the Jira issue object.

        Raises:
            ValueError: If the Jira client is not configured or available.
        """
        jira = await get_jira_fetcher(ctx)
        fields_list: str | list[str] | None = fields
        if fields and fields != "*all":
            fields_list = [f.strip() for f in fields.split(",")]

        issue = jira.get_issue(
            issue_key=issue_key,
            fields=fields_list,
            expand=expand,
            comment_limit=comment_limit,
            properties=properties.split(",") if properties else None,
            update_history=update_history,
        )
        result = issue.to_simplified_dict()
        return json.dumps(result, indent=2, ensure_ascii=False)

    async def batch_get_changelogs(
        self,
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
