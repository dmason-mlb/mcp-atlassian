"""Issue creation mixin for Jira server."""

import json
import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from mcp_atlassian.servers.dependencies import get_jira_fetcher
from mcp_atlassian.utils.decorators import check_write_access
from mcp_atlassian.utils.tool_helpers import safe_tool_result

logger = logging.getLogger(__name__)


class IssueCreationMixin:
    """Mixin providing issue creation tools."""

    @check_write_access
    @safe_tool_result
    async def create_issue(
        self,
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
            dict[str, Any] | None,
            Field(
                description=(
                    "(Optional) Dictionary of additional fields to set. Examples:\\n"
                    "- Set priority: {'priority': {'name': 'High'}}\\n"
                    "- Add labels: {'labels': ['frontend', 'urgent']}\\n"
                    "- Link to parent (for any issue type): {'parent': 'PROJ-123'}\\n"
                    "- Set Fix Version/s: {'fixVersions': [{'id': '10020'}]}\\n"
                    "- Custom fields: {'customfield_10010': 'value'}"
                ),
                default=None,
            ),
        ] = None,
    ) -> str:
        """Create a new Jira issue with optional Epic link or parent for subtasks.

        Args:
            ctx: The FastMCP context.
            project_key: The JIRA project key.
            summary: Summary/title of the issue.
            issue_type: Issue type (e.g., 'Task', 'Bug', 'Story', 'Epic', 'Subtask').
            assignee: Assignee's user identifier (string): Email, display name, or account ID (e.g., 'user@example.com', 'John Doe', 'accountid:...').
            description: Issue description.
            components: Comma-separated list of component names.
            additional_fields: Dictionary of additional fields.

        Returns:
            JSON string representing the created issue object.

        Raises:
            ValueError: If in read-only mode or Jira client is unavailable.
        """
        jira = await get_jira_fetcher(ctx)
        # Parse components from comma-separated string to list
        components_list = None
        if components and isinstance(components, str):
            components_list = [
                comp.strip() for comp in components.split(",") if comp.strip()
            ]

        # Use additional_fields directly as dict
        extra_fields = additional_fields or {}
        if not isinstance(extra_fields, dict):
            raise ValueError("additional_fields must be a dictionary.")

        issue = jira.create_issue(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            assignee=assignee,
            components=components_list,
            **extra_fields,
        )
        result = issue.to_simplified_dict()
        return json.dumps(
            {"message": "Issue created successfully", "issue": result},
            indent=2,
            ensure_ascii=False,
        )

    @check_write_access
    @safe_tool_result
    async def batch_create_issues(
        self,
        ctx: Context,
        issues: Annotated[
            str,
            Field(
                description=(
                    "JSON array of issue objects. Each object should contain:\\n"
                    "- project_key (required): The project key (e.g., 'PROJ')\\n"
                    "- summary (required): Issue summary/title\\n"
                    "- issue_type (required): Type of issue (e.g., 'Task', 'Bug')\\n"
                    "- description (optional): Issue description\\n"
                    "- assignee (optional): Assignee username or email\\n"
                    "- components (optional): Array of component names\\n"
                    "Example: [\\n"
                    '  {"project_key": "PROJ", "summary": "Issue 1", "issue_type": "Task"},\\n'
                    '  {"project_key": "PROJ", "summary": "Issue 2", "issue_type": "Bug", "components": ["Frontend"]}\\n'
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
        created_issues = jira.batch_create_issues(
            issues_list, validate_only=validate_only
        )

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
