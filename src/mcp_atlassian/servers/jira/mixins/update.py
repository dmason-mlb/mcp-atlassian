"""Issue update mixin for Jira server."""

import json
import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from mcp_atlassian.servers.dependencies import get_jira_fetcher
from mcp_atlassian.utils.decorators import check_write_access

logger = logging.getLogger(__name__)


class IssueUpdateMixin:
    """Mixin providing issue update and modification tools."""

    @check_write_access
    async def update_issue(
        self,
        ctx: Context,
        issue_key: Annotated[
            str, Field(description="Jira issue key (e.g., 'PROJ-123')")
        ],
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
        """Update an existing Jira issue including changing status, adding Epic links, updating fields, etc.

        Args:
            ctx: The FastMCP context.
            issue_key: Jira issue key.
            fields: Dictionary of fields to update.
            additional_fields: Optional dictionary of additional fields.
            attachments: Optional JSON array string or comma-separated list of file paths.

        Returns:
            JSON string representing the updated issue object and attachment results.

        Raises:
            ValueError: If in read-only mode or Jira client unavailable, or invalid input.
        """
        jira = await get_jira_fetcher(ctx)
        # Use fields directly as dict
        if not isinstance(fields, dict):
            raise ValueError("fields must be a dictionary.")
        update_fields = fields

        # Use additional_fields directly as dict
        extra_fields = additional_fields or {}
        if not isinstance(extra_fields, dict):
            raise ValueError("additional_fields must be a dictionary.")

        # Parse attachments
        attachment_paths = []
        if attachments:
            if isinstance(attachments, str):
                try:
                    parsed = json.loads(attachments)
                    if isinstance(parsed, list):
                        attachment_paths = [str(p) for p in parsed]
                    else:
                        raise ValueError("attachments JSON string must be an array.")
                except json.JSONDecodeError:
                    # Assume comma-separated if not valid JSON array
                    attachment_paths = [
                        p.strip() for p in attachments.split(",") if p.strip()
                    ]
            else:
                raise ValueError(
                    "attachments must be a JSON array string or comma-separated string."
                )

        # Combine fields and additional_fields
        all_updates = {**update_fields, **extra_fields}
        if attachment_paths:
            all_updates["attachments"] = attachment_paths

        try:
            issue = jira.update_issue(issue_key=issue_key, **all_updates)
            result = issue.to_simplified_dict()
            if (
                hasattr(issue, "custom_fields")
                and "attachment_results" in issue.custom_fields
            ):
                result["attachment_results"] = issue.custom_fields["attachment_results"]
            return json.dumps(
                {"message": "Issue updated successfully", "issue": result},
                indent=2,
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to update issue {issue_key}: {str(e)}")

    @check_write_access
    async def delete_issue(
        self,
        ctx: Context,
        issue_key: Annotated[str, Field(description="Jira issue key (e.g. PROJ-123)")],
    ) -> str:
        """Delete an existing Jira issue.

        Args:
            ctx: The FastMCP context.
            issue_key: Jira issue key.

        Returns:
            JSON string indicating success.

        Raises:
            ValueError: If in read-only mode or Jira client unavailable.
        """
        jira = await get_jira_fetcher(ctx)
        jira.delete_issue(issue_key)
        return json.dumps({"message": f"Issue {issue_key} deleted successfully"})

    @check_write_access
    async def add_comment(
        self,
        ctx: Context,
        issue_key: Annotated[
            str, Field(description="Jira issue key (e.g., 'PROJ-123')")
        ],
        comment: Annotated[str, Field(description="Comment text in Markdown format")],
    ) -> str:
        """Add a comment to a Jira issue.

        Args:
            ctx: The FastMCP context.
            issue_key: Jira issue key.
            comment: Comment text in Markdown.

        Returns:
            JSON string representing the added comment object.

        Raises:
            ValueError: If in read-only mode or Jira client unavailable.
        """
        jira = await get_jira_fetcher(ctx)
        # add_comment returns dict
        result = jira.add_comment(issue_key, comment)
        return json.dumps(result, indent=2, ensure_ascii=False)

    # Note: Worklog tool removed. This mixin no longer exposes add_worklog.

    @check_write_access
    async def transition_issue(
        self,
        ctx: Context,
        issue_key: Annotated[
            str, Field(description="Jira issue key (e.g., 'PROJ-123')")
        ],
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
