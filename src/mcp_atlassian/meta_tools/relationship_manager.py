"""Relationship Manager Meta-Tool for MCP Atlassian.

This module handles all relationship operations including issue links,
epic relationships, parent-child relationships, and dependencies.
"""

import json
import logging
from typing import Any, Literal

from .errors import MetaToolError
from ..jira.client import JiraClient

logger = logging.getLogger(__name__)


class RelationshipManager:
    """Universal relationship manager for Jira relationship operations.

    Consolidates relationship-related tools:
    - create_issue_link
    - get_issue_links
    - delete_issue_link
    - add_issue_to_epic
    - get_epic_issues
    - set_parent_child_relationship
    """

    # Supported relationship operations
    RELATIONSHIP_OPERATIONS = {
        "create_link": "Create link between two issues",
        "get_links": "Get links for an issue",
        "delete_link": "Delete issue link",
        "add_to_epic": "Add issue to epic",
        "remove_from_epic": "Remove issue from epic",
        "get_epic_issues": "Get issues in an epic",
        "set_parent": "Set parent-child relationship",
        "remove_parent": "Remove parent relationship",
        "get_subtasks": "Get subtasks of an issue",
        "validate_relationship": "Validate if relationship is possible",
    }

    # Common link types
    COMMON_LINK_TYPES = {
        "blocks": "This issue blocks another",
        "is_blocked_by": "This issue is blocked by another",
        "relates_to": "This issue relates to another",
        "duplicates": "This issue duplicates another",
        "is_duplicated_by": "This issue is duplicated by another",
        "causes": "This issue causes another",
        "is_caused_by": "This issue is caused by another",
        "clones": "This issue clones another",
        "is_cloned_by": "This issue is cloned by another",
    }

    def __init__(self) -> None:
        """Initialize the RelationshipManager."""
        pass

    async def execute_relationship_operation(
        self,
        ctx: Any,  # FastMCP Context
        operation: str,
        issue_key: str,
        target_issue_key: str | None = None,
        link_type: str | None = None,
        epic_key: str | None = None,
        parent_key: str | None = None,
        comment: str | None = None,
        link_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Execute a relationship operation.

        Args:
            ctx: The FastMCP context
            operation: Type of relationship operation to perform
            issue_key: Primary issue key
            target_issue_key: Target issue for linking operations
            link_type: Type of link to create (blocks, relates_to, etc.)
            epic_key: Epic key for epic operations
            parent_key: Parent issue key for hierarchy operations
            comment: Optional comment for the relationship
            link_id: Link ID for delete operations
            options: Additional operation options

        Returns:
            JSON string with operation results
        """
        try:
            # Validate inputs
            self._validate_relationship_inputs(
                operation, issue_key, target_issue_key, link_type,
                epic_key, parent_key, link_id, options
            )

            # Get Jira fetcher
            from ..servers.dependencies import get_jira_fetcher
            client = await get_jira_fetcher(ctx)

            return await self._execute_relationship_operation_impl(
                client, operation, issue_key, target_issue_key, link_type,
                epic_key, parent_key, comment, link_id, options
            )

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in relationship_manager: {e}", exc_info=True)
            raise MetaToolError.from_exception(
                error=e,
                error_code="RELATIONSHIP_MANAGER_ERROR",
                user_message=f"Failed to execute {operation} relationship operation",
                suggestions=["Check the Jira configuration and try again"],
                context={
                    "operation": operation,
                    "issue_key": issue_key,
                    "target_issue_key": target_issue_key,
                    "link_type": link_type,
                },
            )

    def _validate_relationship_inputs(
        self,
        operation: str,
        issue_key: str,
        target_issue_key: str | None,
        link_type: str | None,
        epic_key: str | None,
        parent_key: str | None,
        link_id: str | None,
        options: dict[str, Any] | None,
    ) -> None:
        """Validate relationship operation inputs."""
        if operation not in self.RELATIONSHIP_OPERATIONS:
            raise MetaToolError(
                error_code="INVALID_RELATIONSHIP_OPERATION",
                user_message=f"Operation '{operation}' is not supported",
                suggestions=[
                    f"Supported relationship operations: {', '.join(self.RELATIONSHIP_OPERATIONS.keys())}"
                ],
                context={
                    "provided_operation": operation,
                    "supported_operations": list(self.RELATIONSHIP_OPERATIONS.keys()),
                },
            )

        if not issue_key:
            raise MetaToolError(
                error_code="MISSING_ISSUE_KEY",
                user_message="All relationship operations require an issue_key",
                suggestions=["Provide a valid Jira issue key (e.g., 'PROJ-123')"],
                context={"operation": operation},
            )

        # Validate operation-specific requirements
        if operation == "create_link":
            if not target_issue_key:
                raise MetaToolError(
                    error_code="MISSING_TARGET_ISSUE",
                    user_message="create_link operation requires a target_issue_key",
                    suggestions=["Provide the issue key to link to (e.g., 'PROJ-456')"],
                    context={"operation": operation, "issue_key": issue_key},
                )
            if not link_type:
                raise MetaToolError(
                    error_code="MISSING_LINK_TYPE",
                    user_message="create_link operation requires a link_type",
                    suggestions=[
                        f"Common link types: {', '.join(self.COMMON_LINK_TYPES.keys())}",
                        "Use validate_relationship to check available link types"
                    ],
                    context={"operation": operation, "issue_key": issue_key},
                )

        elif operation == "delete_link":
            if not link_id:
                raise MetaToolError(
                    error_code="MISSING_LINK_ID",
                    user_message="delete_link operation requires a link_id",
                    suggestions=[
                        "Use get_links to find the link ID first",
                        "Provide the numeric link ID"
                    ],
                    context={"operation": operation, "issue_key": issue_key},
                )

        elif operation in ["add_to_epic", "remove_from_epic"]:
            if not epic_key:
                raise MetaToolError(
                    error_code="MISSING_EPIC_KEY",
                    user_message=f"{operation} operation requires an epic_key",
                    suggestions=["Provide the epic issue key (e.g., 'PROJ-100')"],
                    context={"operation": operation, "issue_key": issue_key},
                )

        elif operation == "set_parent":
            if not parent_key:
                raise MetaToolError(
                    error_code="MISSING_PARENT_KEY",
                    user_message="set_parent operation requires a parent_key",
                    suggestions=["Provide the parent issue key (e.g., 'PROJ-200')"],
                    context={"operation": operation, "issue_key": issue_key},
                )


    async def _execute_relationship_operation_impl(
        self,
        client: JiraClient,
        operation: str,
        issue_key: str,
        target_issue_key: str | None,
        link_type: str | None,
        epic_key: str | None,
        parent_key: str | None,
        comment: str | None,
        link_id: str | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute the actual relationship operation."""
        try:
            if operation == "create_link":
                # Create issue link
                link_data = {
                    "type": {"name": link_type},
                    "inwardIssue": {"key": issue_key},
                    "outwardIssue": {"key": target_issue_key}
                }
                if comment:
                    link_data["comment"] = {"body": comment}
                result = client.create_issue_link(data=link_data)

            elif operation == "get_links":
                # Get issue links by fetching issue with issuelinks field
                issue = client.get_issue(
                    issue_key=issue_key,
                    fields="issuelinks"
                )
                result = getattr(issue, 'issuelinks', [])

            elif operation == "delete_link":
                # Delete issue link
                result = client.remove_issue_link(link_id=link_id)

            elif operation == "add_to_epic":
                # Add issue to epic using link_issue_to_epic
                result = client.link_issue_to_epic(
                    issue_key=issue_key,
                    epic_key=epic_key
                )

            elif operation == "remove_from_epic":
                # Remove issue from epic - not directly available, use update_issue
                result = client.update_issue(
                    issue_key=issue_key,
                    fields={"parent": None}  # Remove parent relationship
                )

            elif operation == "get_epic_issues":
                # Get issues in epic
                result = client.get_epic_issues(
                    epic_key=epic_key or issue_key,
                    start=options.get("start_at", 0) if options else 0,
                    limit=options.get("limit", 50) if options else 50
                )

            elif operation == "set_parent":
                # Set parent-child relationship
                result = client.update_issue(
                    issue_key=issue_key,
                    fields={"parent": {"key": parent_key}}
                )

            elif operation == "remove_parent":
                # Remove parent relationship
                result = client.update_issue(
                    issue_key=issue_key,
                    fields={"parent": None}
                )

            elif operation == "get_subtasks":
                # Get subtasks of an issue
                issue = client.get_issue(
                    issue_key=issue_key,
                    fields="subtasks",
                    expand="subtasks"
                )
                result = getattr(issue, 'subtasks', [])

            elif operation == "validate_relationship":
                # Validate relationship possibility
                result = await self._validate_relationship_possibility(
                    client, issue_key, target_issue_key, link_type,
                    epic_key, parent_key
                )

            else:
                raise ValueError(f"Unsupported relationship operation: {operation}")

            # Convert results to JSON-serializable format
            if hasattr(result, 'to_simplified_dict'):
                result_data = result.to_simplified_dict()
            elif hasattr(result, 'to_dict'):
                result_data = result.to_dict()
            elif hasattr(result, 'model_dump'):
                # For Pydantic models without custom serialization methods
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
                    "target_issue_key": target_issue_key,
                    "epic_key": epic_key,
                    "parent_key": parent_key,
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"RELATIONSHIP_{operation.upper()}_FAILED",
                api_endpoint=self._get_api_endpoint(operation),
                suggestions=self._get_error_suggestions(operation, e),
                context={
                    "operation": operation,
                    "issue_key": issue_key,
                    "target_issue_key": target_issue_key,
                    "link_type": link_type,
                },
            )

    async def _validate_relationship_possibility(
        self,
        client: JiraClient,
        issue_key: str,
        target_issue_key: str | None,
        link_type: str | None,
        epic_key: str | None,
        parent_key: str | None,
    ) -> dict[str, Any]:
        """Validate if a relationship operation is possible."""
        validation_result = {
            "issue_exists": False,
            "target_exists": False,
            "epic_exists": False,
            "parent_exists": False,
            "link_type_valid": False,
            "relationship_possible": False,
            "issues": []
        }

        try:
            # Check if primary issue exists
            issue = client.get_issue(issue_key=issue_key, fields="key,summary")
            validation_result["issue_exists"] = True
            validation_result["issues"].append({
                "key": issue_key,
                "exists": True,
                "summary": getattr(issue, 'summary', 'No summary')
            })
        except Exception:
            validation_result["issues"].append({
                "key": issue_key,
                "exists": False,
                "error": "Issue not found or no access"
            })

        # Check target issue if provided
        if target_issue_key:
            try:
                target_issue = client.get_issue(issue_key=target_issue_key, fields="key,summary")
                validation_result["target_exists"] = True
                validation_result["issues"].append({
                    "key": target_issue_key,
                    "exists": True,
                    "summary": getattr(target_issue, 'summary', 'No summary')
                })
            except Exception:
                validation_result["issues"].append({
                    "key": target_issue_key,
                    "exists": False,
                    "error": "Target issue not found or no access"
                })

        # Check epic if provided
        if epic_key:
            try:
                epic_issue = client.get_issue(issue_key=epic_key, fields="key,summary,issuetype")
                validation_result["epic_exists"] = True
                validation_result["issues"].append({
                    "key": epic_key,
                    "exists": True,
                    "summary": getattr(epic_issue, 'summary', 'No summary'),
                    "is_epic": True
                })
            except Exception:
                validation_result["issues"].append({
                    "key": epic_key,
                    "exists": False,
                    "error": "Epic not found or no access"
                })

        # Check parent if provided
        if parent_key:
            try:
                parent_issue = client.get_issue(issue_key=parent_key, fields="key,summary")
                validation_result["parent_exists"] = True
                validation_result["issues"].append({
                    "key": parent_key,
                    "exists": True,
                    "summary": getattr(parent_issue, 'summary', 'No summary'),
                    "is_parent": True
                })
            except Exception:
                validation_result["issues"].append({
                    "key": parent_key,
                    "exists": False,
                    "error": "Parent issue not found or no access"
                })

        # Check link type validity
        if link_type:
            try:
                link_types = client.get_issue_link_types()
                valid_types = []
                # link_types is a list of JiraIssueLinkType objects
                if isinstance(link_types, list):
                    for lt in link_types:
                        if hasattr(lt, 'name'):
                            valid_types.append(getattr(lt, 'name', '').lower())
                        elif isinstance(lt, dict):
                            valid_types.append(lt.get('name', '').lower())

                validation_result["link_type_valid"] = link_type.lower() in valid_types
                validation_result["available_link_types"] = valid_types
            except Exception:
                validation_result["link_type_valid"] = link_type.lower() in self.COMMON_LINK_TYPES

        # Determine overall possibility
        validation_result["relationship_possible"] = (
            validation_result["issue_exists"] and
            (not target_issue_key or validation_result["target_exists"]) and
            (not epic_key or validation_result["epic_exists"]) and
            (not parent_key or validation_result["parent_exists"]) and
            (not link_type or validation_result["link_type_valid"])
        )

        return validation_result

    def _get_api_endpoint(self, operation: str) -> str:
        """Get the API endpoint for error reporting."""
        endpoints = {
            "create_link": "/rest/api/3/issueLink",
            "get_links": "/rest/api/3/issue/{issueIdOrKey}",
            "delete_link": "/rest/api/3/issueLink/{linkId}",
            "add_to_epic": "/rest/agile/1.0/epic/{epicIdOrKey}/issue",
            "remove_from_epic": "/rest/agile/1.0/epic/{epicIdOrKey}/issue",
            "get_epic_issues": "/rest/agile/1.0/epic/{epicIdOrKey}/issue",
            "set_parent": "/rest/api/3/issue/{issueIdOrKey}",
            "remove_parent": "/rest/api/3/issue/{issueIdOrKey}",
            "get_subtasks": "/rest/api/3/issue/{issueIdOrKey}",
            "validate_relationship": "/rest/api/3/issue/{issueIdOrKey}",
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
            if operation in ["create_link", "get_links"]:
                suggestions.append("Verify both issue keys exist and are accessible")
            elif operation in ["add_to_epic", "get_epic_issues"]:
                suggestions.append("Verify the epic exists and is accessible")
            elif operation == "set_parent":
                suggestions.append("Verify the parent issue exists and is accessible")
        elif "permission" in error_str:
            suggestions.append(f"Ensure you have permission to perform {operation} operations")
            if operation == "create_link":
                suggestions.append("Check if you can edit both issues and create links")
            elif operation in ["add_to_epic", "remove_from_epic"]:
                suggestions.append("Check if you have agile/epic management permissions")

        return suggestions


# Export the main class
__all__ = ["RelationshipManager"]