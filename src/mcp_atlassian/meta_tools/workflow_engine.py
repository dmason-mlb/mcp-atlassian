"""Workflow Engine Meta-Tool for MCP Atlassian.

This module handles all workflow-related operations including transitions,
workflow management, and status changes in a unified interface.
"""

import json
import logging
from typing import Any, Literal

from .errors import MetaToolError
from ..jira.client import JiraClient

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Universal workflow engine for Jira workflow operations.

    Consolidates workflow-related tools:
    - transition_issue
    - get_transitions
    - get_workflow
    - get_workflow_statuses
    """

    # Supported workflow operations
    WORKFLOW_OPERATIONS = {
        "transition": "Transition issue to new status",
        "get_transitions": "Get available transitions for issue",
        "get_workflow": "Get workflow details for project/issue type",
        "get_statuses": "Get available statuses",
        "validate_transition": "Validate if transition is possible",
    }

    def __init__(self) -> None:
        """Initialize the WorkflowEngine."""
        pass

    async def execute_workflow_operation(
        self,
        ctx: Any,  # FastMCP Context
        operation: str,
        issue_key: str | None = None,
        transition_id: str | None = None,
        transition_name: str | None = None,
        fields: dict[str, Any] | None = None,
        project_key: str | None = None,
        issue_type: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Execute a workflow operation.

        Args:
            ctx: The FastMCP context
            operation: Type of workflow operation to perform
            issue_key: Issue key for transitions and getting available transitions
            transition_id: ID of transition to execute
            transition_name: Name of transition to execute (alternative to ID)
            fields: Additional fields to set during transition
            project_key: Project key for workflow information
            issue_type: Issue type for workflow information
            options: Additional operation options

        Returns:
            JSON string with operation results
        """
        try:
            # Validate inputs
            self._validate_workflow_inputs(
                operation, issue_key, transition_id, transition_name,
                project_key, issue_type, options
            )

            # Get Jira fetcher
            from ..servers.dependencies import get_jira_fetcher
            client = await get_jira_fetcher(ctx)

            return await self._execute_workflow_operation_impl(
                client, operation, issue_key, transition_id, transition_name,
                fields, project_key, issue_type, options
            )

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in workflow_engine: {e}", exc_info=True)
            raise MetaToolError.from_exception(
                error=e,
                error_code="WORKFLOW_ENGINE_ERROR",
                user_message=f"Failed to execute {operation} workflow operation",
                suggestions=["Check the Jira configuration and try again"],
                context={
                    "operation": operation,
                    "issue_key": issue_key,
                    "transition_id": transition_id,
                    "has_fields": fields is not None,
                },
            )

    def _validate_workflow_inputs(
        self,
        operation: str,
        issue_key: str | None,
        transition_id: str | None,
        transition_name: str | None,
        project_key: str | None,
        issue_type: str | None,
        options: dict[str, Any] | None,
    ) -> None:
        """Validate workflow operation inputs."""
        if operation not in self.WORKFLOW_OPERATIONS:
            raise MetaToolError(
                error_code="INVALID_WORKFLOW_OPERATION",
                user_message=f"Operation '{operation}' is not supported",
                suggestions=[
                    f"Supported workflow operations: {', '.join(self.WORKFLOW_OPERATIONS.keys())}"
                ],
                context={
                    "provided_operation": operation,
                    "supported_operations": list(self.WORKFLOW_OPERATIONS.keys()),
                },
            )

        # Validate operation-specific requirements
        if operation in ["transition", "get_transitions", "validate_transition"]:
            if not issue_key:
                raise MetaToolError(
                    error_code="MISSING_ISSUE_KEY",
                    user_message=f"Operation '{operation}' requires an issue_key",
                    suggestions=["Provide a valid Jira issue key (e.g., 'PROJ-123')"],
                    context={"operation": operation},
                )

        if operation == "transition":
            if not transition_id and not transition_name:
                raise MetaToolError(
                    error_code="MISSING_TRANSITION_IDENTIFIER",
                    user_message="Transition operation requires either transition_id or transition_name",
                    suggestions=[
                        "Provide transition_id (e.g., '11') or transition_name (e.g., 'In Progress')",
                        "Use get_transitions to see available transitions first"
                    ],
                    context={"operation": operation, "issue_key": issue_key},
                )

        if operation == "get_workflow":
            if not project_key:
                raise MetaToolError(
                    error_code="MISSING_PROJECT_KEY",
                    user_message="get_workflow operation requires a project_key",
                    suggestions=["Provide a valid Jira project key (e.g., 'PROJ')"],
                    context={"operation": operation},
                )


    async def _execute_workflow_operation_impl(
        self,
        client: JiraClient,
        operation: str,
        issue_key: str | None,
        transition_id: str | None,
        transition_name: str | None,
        fields: dict[str, Any] | None,
        project_key: str | None,
        issue_type: str | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute the actual workflow operation."""
        try:
            if operation == "transition":
                # Execute issue transition
                result = await self._execute_transition(
                    client, issue_key, transition_id, transition_name, fields
                )

            elif operation == "get_transitions":
                # Get available transitions for issue
                result = client.get_available_transitions(issue_key=issue_key)

            elif operation == "get_workflow":
                # Get workflow details - not directly available, return error
                raise MetaToolError(
                    error_code="WORKFLOW_NOT_SUPPORTED",
                    user_message="Workflow metadata operation not available in current API",
                    suggestions=["Use get_transitions to see available transitions for specific issues"],
                    context={"operation": operation, "project_key": project_key}
                )

            elif operation == "get_statuses":
                # Get available statuses
                if project_key:
                    # Get statuses for specific project
                    result = client.get_project_statuses(project_key=project_key)
                else:
                    # Get all statuses in the instance
                    result = client.get_all_statuses()

            elif operation == "validate_transition":
                # Validate if transition is possible
                transitions = client.get_available_transitions(issue_key=issue_key)
                result = self._validate_transition_availability(
                    transitions, transition_id, transition_name
                )

            else:
                raise ValueError(f"Unsupported workflow operation: {operation}")

            # Convert results to JSON-serializable format
            if hasattr(result, 'to_simplified_dict'):
                result_data = result.to_simplified_dict()
            elif hasattr(result, 'to_dict'):
                result_data = result.to_dict()
            elif hasattr(result, 'model_dump'):
                result_data = result.model_dump(exclude_none=True)
            elif isinstance(result, list):
                result_data = []
                for item in result:
                    if hasattr(item, 'to_simplified_dict'):
                        result_data.append(item.to_simplified_dict())
                    elif hasattr(item, 'to_dict'):
                        result_data.append(item.to_dict())
                    elif hasattr(item, 'model_dump'):
                        result_data.append(item.model_dump(exclude_none=True))
                    else:
                        result_data.append(item)
            else:
                result_data = result

            return json.dumps(
                {
                    "success": True,
                    "operation": operation,
                    "issue_key": issue_key,
                    "project_key": project_key,
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"WORKFLOW_{operation.upper()}_FAILED",
                api_endpoint=self._get_api_endpoint(operation),
                suggestions=self._get_error_suggestions(operation, e),
                context={
                    "operation": operation,
                    "issue_key": issue_key,
                    "transition_id": transition_id,
                    "transition_name": transition_name,
                },
            )

    async def _execute_transition(
        self,
        client: JiraClient,
        issue_key: str,
        transition_id: str | None,
        transition_name: str | None,
        fields: dict[str, Any] | None,
    ) -> Any:
        """Execute issue transition."""
        # If transition_name is provided but not transition_id, resolve it
        if transition_name and not transition_id:
            transitions = client.get_available_transitions(issue_key=issue_key)
            transition_id = self._resolve_transition_name_to_id(
                transitions, transition_name
            )

        # Execute the transition
        return client.transition_issue(
            issue_key=issue_key,
            transition_id=transition_id,
            fields=fields,
            comment=None
        )

    def _resolve_transition_name_to_id(
        self, transitions: list[dict[str, Any]], transition_name: str
    ) -> str:
        """Resolve transition name to ID."""
        # transitions is a list of dicts from get_available_transitions
        if not isinstance(transitions, list):
            raise MetaToolError(
                error_code="TRANSITION_FORMAT_ERROR",
                user_message="Unable to parse transitions response",
                suggestions=["Check issue permissions and try again"],
            )

        # Find matching transition
        for transition in transitions:
            if not isinstance(transition, dict):
                continue

            name = transition.get('name', '')
            id_val = transition.get('id', '')

            if name.lower() == transition_name.lower():
                return str(id_val)

        # If not found, provide helpful error
        available_transitions = [
            transition.get('name', 'Unknown')
            for transition in transitions
            if isinstance(transition, dict)
        ]

        raise MetaToolError(
            error_code="TRANSITION_NOT_FOUND",
            user_message=f"Transition '{transition_name}' not found",
            suggestions=[
                f"Available transitions: {', '.join(available_transitions)}",
                "Check transition name spelling and case"
            ],
            context={
                "requested_transition": transition_name,
                "available_transitions": available_transitions,
            },
        )

    def _validate_transition_availability(
        self,
        transitions: list[dict[str, Any]],
        transition_id: str | None,
        transition_name: str | None,
    ) -> dict[str, Any]:
        """Validate if a transition is available."""
        # transitions is a list of dicts from get_available_transitions
        if not isinstance(transitions, list):
            return {
                "available": False,
                "reason": "Unable to parse transitions response"
            }

        # Check if transition is available
        for transition in transitions:
            if not isinstance(transition, dict):
                continue

            name = transition.get('name', '')
            id_val = str(transition.get('id', ''))

            # Check if this transition matches
            if transition_id and id_val == transition_id:
                return {"available": True, "transition": {"id": id_val, "name": name}}
            elif transition_name and name.lower() == transition_name.lower():
                return {"available": True, "transition": {"id": id_val, "name": name}}

        return {
            "available": False,
            "reason": f"Transition not found: {transition_id or transition_name}",
            "available_transitions": [
                {
                    "id": str(t.get('id', '')),
                    "name": t.get('name', '')
                }
                for t in transitions
                if isinstance(t, dict)
            ]
        }

    def _get_api_endpoint(self, operation: str) -> str:
        """Get the API endpoint for error reporting."""
        endpoints = {
            "transition": "/rest/api/3/issue/{issueIdOrKey}/transitions",
            "get_transitions": "/rest/api/3/issue/{issueIdOrKey}/transitions",
            "get_workflow": "N/A - Operation not supported",
            "get_statuses": "N/A - Operation not supported",
            "validate_transition": "/rest/api/3/issue/{issueIdOrKey}/transitions",
        }
        return endpoints.get(operation, f"/rest/api/3/{operation}")

    def _get_error_suggestions(self, operation: str, error: Exception) -> list[str]:
        """Get error-specific suggestions."""
        suggestions = [
            "Verify the Jira configuration and permissions",
        ]

        error_str = str(error).lower()

        if "authentication" in error_str or "unauthorized" in error_str:
            suggestions.append("Check your authentication credentials")
        elif "not found" in error_str:
            if operation in ["transition", "get_transitions"]:
                suggestions.append("Verify the issue key exists and is accessible")
            elif operation == "get_workflow":
                suggestions.append("Verify the project key and issue type exist")
        elif "permission" in error_str:
            suggestions.append(f"Ensure you have permission to perform {operation} operations")
            if operation == "transition":
                suggestions.append("Check if you can edit the issue and perform transitions")

        return suggestions


# Export the main class
__all__ = ["WorkflowEngine"]