"""Universal Resource Manager meta-tool.

Consolidates all CRUD operations for Jira and Confluence resources into a single
unified interface, reducing token usage while maintaining full functionality.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from ..confluence import ConfluenceFetcher
from ..jira import JiraFetcher
from ..servers.dependencies import get_confluence_fetcher, get_jira_fetcher
from .errors import MetaToolError
from .schema_discovery import schema_discovery

logger = logging.getLogger(__name__)


class ResourceManager:
    """Universal resource manager for CRUD operations across Jira and Confluence.
    
    This manager provides a unified interface for creating, reading, updating, and deleting
    resources across both Jira and Confluence. It automatically handles content formatting
    by delegating to the underlying service layer, which converts markdown content to the
    appropriate format:
    
    - **Cloud instances**: Markdown is converted to ADF (Atlassian Document Format)
    - **Server/DC instances**: Markdown is converted to wiki markup
    
    All text content (descriptions, comments, page bodies) can be provided in markdown
    format and will be automatically converted to the correct format for the target
    deployment type.
    """

    # Mapping of resource types to their respective service methods
    JIRA_RESOURCE_OPERATIONS = {
        "issue": {
            "get": "_get_jira_issue",
            "create": "_create_jira_issue",
            "update": "_update_jira_issue",
            "delete": "_delete_jira_issue",
        },
        "comment": {
            "get": "_get_jira_comment",
            "add": "_add_jira_comment",
            "update": "_update_jira_comment",
            "delete": "_delete_jira_comment",
        },
        "worklog": {
            "get": "_get_jira_worklog",
            "add": "_add_jira_worklog",
            "update": "_update_jira_worklog",
            "delete": "_delete_jira_worklog",
        },
        "attachment": {
            "get": "_get_jira_attachment",
            "add": "_add_jira_attachment",
            "delete": "_delete_jira_attachment",
        },
        "link": {
            "create": "_create_jira_issue_link",
            "delete": "_delete_jira_issue_link",
        },
        "sprint": {
            "get": "_get_jira_sprint",
            "create": "_create_jira_sprint",
            "update": "_update_jira_sprint",
        },
        "version": {
            "get": "_get_jira_version",
            "create": "_create_jira_version",
            "update": "_update_jira_version",
            "delete": "_delete_jira_version",
        },
    }

    CONFLUENCE_RESOURCE_OPERATIONS = {
        "page": {
            "get": "_get_confluence_page",
            "create": "_create_confluence_page",
            "update": "_update_confluence_page",
            "delete": "_delete_confluence_page",
        },
        "comment": {
            "get": "_get_confluence_comment",
            "add": "_add_confluence_comment",
            "update": "_update_confluence_comment",
            "delete": "_delete_confluence_comment",
        },
        "label": {
            "add": "_add_confluence_label",
            "delete": "_delete_confluence_label",
        },
        "space": {
            "get": "_get_confluence_space",
            "create": "_create_confluence_space",
            "update": "_update_confluence_space",
            "delete": "_delete_confluence_space",
        },
    }

    def __init__(self) -> None:
        """Initialize ResourceManager."""
        pass

    def _serialize_result(self, result: Any) -> dict[str, Any] | Any:
        """
        Safely serialize API results to dict.
        
        Args:
            result: The API result to serialize
            
        Returns:
            Dictionary representation of the result
        """
        if hasattr(result, 'to_simplified_dict'):
            return result.to_simplified_dict()
        elif hasattr(result, 'to_dict'):
            return result.to_dict()
        elif hasattr(result, 'model_dump'):
            return result.model_dump(exclude_none=True)
        elif isinstance(result, dict):
            return result
        else:
            return result

    def get_resource_schema(
        self,
        service: Literal["jira", "confluence"],
        resource: str,
        operation: Literal["get", "create", "update", "delete", "add"],
    ) -> str:
        """Get minimal schema for a resource operation.

        Args:
            service: Target service ("jira" or "confluence")
            resource: Resource type (e.g., "issue", "page", "comment")
            operation: Operation type (e.g., "create", "update", "get")

        Returns:
            JSON string containing minimal schema with examples
        """
        try:
            schema = schema_discovery.get_resource_schema(service, resource, operation)
            return json.dumps(schema.model_dump(), indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(
                f"Failed to get schema for {service} {resource} {operation}: {e}"
            )
            return json.dumps(
                {
                    "error": f"Schema not available for {service} {resource} {operation}",
                    "fallback": "Check the schema documentation for required field structure",
                },
                indent=2,
            )

    async def execute_operation(
        self,
        ctx: Any,  # FastMCP Context
        service: Literal["jira", "confluence"],
        resource: str,
        operation: Literal["get", "create", "update", "delete", "add"],
        identifier: str | None = None,
        data: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Execute a resource operation.

        Args:
            ctx: The FastMCP context
            service: Target service ("jira" or "confluence")
            resource: Resource type (e.g., "issue", "page", "comment")
            operation: Operation to perform
            identifier: Resource identifier for get/update/delete operations
            data: Data payload for create/update/add operations
            options: Additional parameters (fields, expand, etc.)

        Returns:
            JSON string containing operation result

        Raises:
            MetaToolError: If operation fails with structured error information
        """
        try:
            # Validate inputs
            self._validate_operation_inputs(
                service, resource, operation, identifier, data
            )

            # Get appropriate service client
            if service == "jira":
                client = await get_jira_fetcher(ctx)
                operations_map = self.JIRA_RESOURCE_OPERATIONS
            else:  # confluence
                client = await get_confluence_fetcher(ctx)
                operations_map = self.CONFLUENCE_RESOURCE_OPERATIONS

            # Find and execute the operation
            if resource not in operations_map:
                raise MetaToolError(
                    error_code=f"{service.upper()}_RESOURCE_NOT_SUPPORTED",
                    user_message=f"Resource type '{resource}' is not supported for {service}",
                    suggestions=[
                        f"Supported {service} resources: {', '.join(operations_map.keys())}"
                    ],
                    context={"service": service, "resource": resource},
                )

            resource_ops = operations_map[resource]
            if operation not in resource_ops:
                raise MetaToolError(
                    error_code=f"{service.upper()}_OPERATION_NOT_SUPPORTED",
                    user_message=f"Operation '{operation}' is not supported for {service} {resource}",
                    suggestions=[
                        f"Supported operations for {resource}: {', '.join(resource_ops.keys())}"
                    ],
                    context={
                        "service": service,
                        "resource": resource,
                        "operation": operation,
                    },
                )

            # Execute the operation
            method_name = resource_ops[operation]
            method = getattr(self, method_name)
            result = await method(client, identifier, data, options)

            return json.dumps(
                {
                    "success": True,
                    "operation": f"{service}_{resource}_{operation}",
                    "result": result,
                },
                indent=2,
                ensure_ascii=False,
            )

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in resource_manager: {e}", exc_info=True)

            # Provide specific error messages based on the underlying error
            error_message = str(e).lower()
            specific_suggestions = []

            if "oauth authentication requires a valid cloud_id" in error_message:
                specific_suggestions = [
                    "Add 'cloud_id' to your service configuration",
                    "For Cloud instances, set ATLASSIAN_CLOUD_ID environment variable",
                    "Example: ATLASSIAN_CLOUD_ID=your-site-id (found in your Atlassian URL)",
                    "OAuth authentication requires both valid credentials and cloud_id"
                ]
            elif "authentication" in error_message and "failed" in error_message:
                specific_suggestions = [
                    "Verify your API token or OAuth credentials are correct",
                    "Check that the token has not expired",
                    "Ensure the token has required permissions for this operation",
                    f"For {service.title()}, check your authentication configuration"
                ]
            elif "permission" in error_message or "forbidden" in error_message:
                specific_suggestions = [
                    f"Your account lacks permission to {operation} {resource} in {service.title()}",
                    "Contact your administrator to grant the required permissions",
                    f"Verify you have {operation} access to the target {resource}"
                ]
            elif "not found" in error_message or "does not exist" in error_message:
                if identifier:
                    specific_suggestions = [
                        f"The {resource} '{identifier}' was not found",
                        f"Verify the {resource} identifier is correct",
                        f"Check that you have permission to view this {resource}"
                    ]
                else:
                    specific_suggestions = [
                        f"Required {resource} not found",
                        "Check the service configuration and resource parameters"
                    ]
            elif "connection" in error_message or "timeout" in error_message:
                specific_suggestions = [
                    f"Unable to connect to {service.title()} service",
                    "Check your internet connection",
                    "Verify the service URL is correct",
                    "The service may be temporarily unavailable"
                ]
            else:
                # Fallback to more generic but still helpful suggestions
                specific_suggestions = [
                    f"Check your {service.title()} service configuration",
                    "Verify authentication credentials are valid",
                    "Ensure you have permission for this operation",
                    "Check the get_resource_schema tool for parameter validation"
                ]

            raise MetaToolError.from_exception(
                error=e,
                error_code="RESOURCE_MANAGER_ERROR",
                user_message=f"Failed to {operation} {service} {resource}",
                suggestions=specific_suggestions,
                context={
                    "service": service,
                    "resource": resource,
                    "operation": operation,
                    "identifier": identifier,
                    "has_data": data is not None,
                    "underlying_error": str(e),
                },
            )

    def _validate_operation_inputs(
        self,
        service: str,
        resource: str,
        operation: str,
        identifier: str | None,
        data: dict[str, Any] | None,
    ) -> None:
        """Validate operation inputs."""
        if service not in ["jira", "confluence"]:
            raise MetaToolError(
                error_code="INVALID_SERVICE",
                user_message=f"Service must be 'jira' or 'confluence', got '{service}'",
                suggestions=[
                    "Use 'jira' for Jira operations or 'confluence' for Confluence operations"
                ],
                context={"provided_service": service},
            )

        # Operations that require an identifier
        identifier_required_ops = ["get", "update", "delete"]
        if operation in identifier_required_ops and not identifier:
            raise MetaToolError(
                error_code="MISSING_IDENTIFIER",
                user_message=f"Operation '{operation}' requires an identifier (e.g., issue key, page ID)",
                suggestions=[
                    "Provide the resource identifier (issue key for Jira, page ID for Confluence)",
                ],
                context={"operation": operation, "resource": resource},
            )

        # Operations that require data
        data_required_ops = ["create", "update", "add"]
        if operation in data_required_ops and not data:
            # Get schema hints for better error message
            schema_hint = "Use get_resource_schema() to see required fields"
            try:
                schema = schema_discovery.get_resource_schema(
                    service, resource, operation
                )
                if schema.required:
                    required_fields = ", ".join(schema.required)
                    schema_hint = f"Required fields: {required_fields}"

                # Add example hint
                if "minimal" in schema.examples:
                    example_data = json.dumps(schema.examples["minimal"], indent=2)
                    schema_hint += f"\n\nMinimal example:\n{example_data}"
            except Exception:
                pass

            raise MetaToolError(
                error_code="MISSING_DATA",
                user_message=f"Operation '{operation}' requires data payload",
                suggestions=[
                    "Provide the data dictionary with required fields for this operation",
                    schema_hint,
                ],
                context={"operation": operation, "resource": resource},
            )


    def _get_required_fields(
        self, service: str, resource: str, operation: str
    ) -> list[str]:
        """Get required fields for a specific operation using schema discovery."""
        try:
            schema = schema_discovery.get_resource_schema(service, resource, operation)
            return schema.required
        except Exception as e:
            logger.warning(f"Failed to get required fields from schema discovery: {e}")
            # Fallback to basic required fields
            fallback_requirements = {
                "jira": {
                    "issue": {"create": ["project_key", "summary", "issue_type"]},
                    "comment": {"add": ["body"], "update": ["body"]},
                    "worklog": {"add": ["time_spent"]},
                },
                "confluence": {
                    "page": {
                        "create": ["space_id", "title", "body"],
                        "update": ["title", "body"],
                    },
                    "comment": {"add": ["body"], "update": ["body"]},
                },
            }
            return (
                fallback_requirements.get(service, {})
                .get(resource, {})
                .get(operation, [])
            )

    # Jira operation implementations
    async def _get_jira_issue(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira issue by key."""
        try:
            if not identifier:
                raise ValueError("Issue key is required")

            # Extract parameters from options
            expand_fields = options.get("expand") if options else None
            fields = options.get("fields") if options else None
            comment_limit = options.get("comment_limit", 10) if options else 10
            properties = options.get("properties") if options else None
            update_history = options.get("update_history", True) if options else True

            # Call with correct parameter names
            issue = client.get_issue(
                issue_key=identifier,
                expand=expand_fields,
                fields=fields,
                comment_limit=comment_limit,
                properties=properties,
                update_history=update_history,
            )
            return issue.to_simplified_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_ISSUE_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}",
                suggestions=[
                    "Verify the issue key exists and you have permission to view it",
                ],
                context={"issue_key": identifier},
            )

    async def _create_jira_issue(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create Jira issue.
        
        Automatically converts markdown content in the description field to the appropriate
        format for the target Jira instance:
        - Cloud instances: Converts to ADF (Atlassian Document Format)
        - Server/DC instances: Converts to wiki markup
        
        Args:
            client: JiraFetcher instance
            identifier: Not used for creation
            data: Issue data dictionary containing project_key, summary, issue_type, 
                  description (markdown), and other fields
            options: Optional parameters
            
        Returns:
            Dictionary representation of the created issue
        """
        try:
            if not data:
                raise ValueError("Issue data is required")

            # Extract required fields
            project_key = data.get("project_key")
            summary = data.get("summary")
            issue_type = data.get("issue_type")

            if not all([project_key, summary, issue_type]):
                missing = [
                    f
                    for f, v in [
                        ("project_key", project_key),
                        ("summary", summary),
                        ("issue_type", issue_type),
                    ]
                    if not v
                ]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            # Create issue using consistency-aware implementation
            wait_for_indexing = (options or {}).get("wait_for_indexing", True)
            issue = client.create_issue_with_consistency(
                project_key=project_key,
                summary=summary,
                issue_type=issue_type,
                description=data.get("description", ""),
                assignee=data.get("assignee"),
                components=data.get("components"),
                wait_for_indexing=wait_for_indexing,
                **{
                    k: v
                    for k, v in data.items()
                    if k
                    not in [
                        "project_key",
                        "summary",
                        "issue_type",
                        "description",
                        "assignee",
                        "components",
                    ]
                },
            )
            return issue.to_simplified_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_CREATE_ISSUE_FAILED",
                api_endpoint="/rest/api/3/issue",
                suggestions=[
                    "Verify project key, issue type, and required fields are correct",
                    "Check that you have permission to create issues in this project",
                ],
                context={"project_key": data.get("project_key") if data else None},
            )

    async def _update_jira_issue(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Jira issue."""
        try:
            if not identifier or not data:
                raise ValueError("Issue key and update data are required")

            # Use correct parameter name
            issue = client.update_issue(issue_key=identifier, fields=data)
            return issue.to_simplified_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_UPDATE_ISSUE_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}",
                suggestions=[
                    "Verify the issue key exists and you have permission to edit it",
                    "Check that the field values are valid for this issue type",
                ],
                context={"issue_key": identifier},
            )

    async def _delete_jira_issue(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira issue."""
        try:
            if not identifier:
                raise ValueError("Issue key is required")

            # Use correct parameter name
            success = client.delete_issue(issue_key=identifier)
            return {"deleted": success, "issue_key": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_ISSUE_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}",
                suggestions=[
                    "Verify the issue key exists and you have permission to delete it",
                ],
                context={"issue_key": identifier},
            )

    # Placeholder implementations for other Jira operations
    async def _get_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira comment by ID."""
        try:
            if not identifier:
                raise ValueError("Comment ID is required")

            comment = client.get_comment(identifier)
            return self._serialize_result(comment)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_COMMENT_FAILED",
                api_endpoint=f"/rest/api/3/comment/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to view it",
                ],
                context={"comment_id": identifier},
            )

    async def _add_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add comment to Jira issue."""
        try:
            if not identifier or not data:
                raise ValueError("Issue key and comment data are required")

            body = data.get("body")
            if not body:
                raise ValueError("Comment body is required")

            comment = client.add_comment(identifier, body)
            return self._serialize_result(comment)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_ADD_COMMENT_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}/comment",
                suggestions=[
                    "Verify the issue key exists and you have permission to comment",
                    "Check that the comment body is not empty",
                ],
                context={"issue_key": identifier},
            )

    async def _update_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Jira comment."""
        try:
            if not identifier or not data:
                raise ValueError("Comment ID and update data are required")

            body = data.get("body")
            if not body:
                raise ValueError("Comment body is required")

            comment = client.update_comment(
                comment_id=identifier,
                body=body,
                visibility=data.get("visibility")
            )
            return self._serialize_result(comment)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_UPDATE_COMMENT_FAILED",
                api_endpoint=f"/rest/api/3/comment/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to edit it",
                    "Check that the comment body is not empty",
                ],
                context={"comment_id": identifier},
            )

    async def _delete_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira comment."""
        try:
            if not identifier:
                raise ValueError("Comment ID is required")

            success = client.delete_comment(identifier)
            return {"deleted": success, "comment_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_COMMENT_FAILED",
                api_endpoint=f"/rest/api/3/comment/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to delete it",
                ],
                context={"comment_id": identifier},
            )

    async def _get_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira worklog by ID."""
        try:
            if not identifier:
                raise ValueError("Worklog ID is required")

            worklog = client.get_worklog(identifier)
            return self._serialize_result(worklog)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_WORKLOG_FAILED",
                api_endpoint=f"/rest/api/3/worklog/{identifier}",
                suggestions=[
                    "Verify the worklog ID exists and you have permission to view it",
                ],
                context={"worklog_id": identifier},
            )

    async def _add_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add worklog to Jira issue."""
        try:
            if not identifier or not data:
                raise ValueError("Issue key and worklog data are required")

            time_spent = data.get("time_spent")
            if not time_spent:
                raise ValueError("Time spent is required")

            worklog = client.add_worklog(
                issue_key=identifier,
                time_spent=time_spent,
                comment=data.get("comment"),
                started=data.get("started"),
                visibility=data.get("visibility")
            )
            return self._serialize_result(worklog)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_ADD_WORKLOG_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}/worklog",
                suggestions=[
                    "Verify the issue key exists and you have permission to log work",
                    "Check that time_spent is in valid format (e.g., '2h 30m')",
                ],
                context={"issue_key": identifier},
            )

    async def _update_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Jira worklog."""
        try:
            if not identifier or not data:
                raise ValueError("Worklog ID and update data are required")

            worklog = client.update_worklog(
                worklog_id=identifier,
                time_spent=data.get("time_spent"),
                comment=data.get("comment"),
                started=data.get("started"),
                visibility=data.get("visibility")
            )
            return worklog.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_UPDATE_WORKLOG_FAILED",
                api_endpoint=f"/rest/api/3/worklog/{identifier}",
                suggestions=[
                    "Verify the worklog ID exists and you have permission to edit it",
                    "Check that time_spent is in valid format if provided",
                ],
                context={"worklog_id": identifier},
            )

    async def _delete_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira worklog."""
        try:
            if not identifier:
                raise ValueError("Worklog ID is required")

            success = client.delete_worklog(identifier)
            return {"deleted": success, "worklog_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_WORKLOG_FAILED",
                api_endpoint=f"/rest/api/3/worklog/{identifier}",
                suggestions=[
                    "Verify the worklog ID exists and you have permission to delete it",
                ],
                context={"worklog_id": identifier},
            )

    async def _get_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira attachment by ID."""
        try:
            if not identifier:
                raise ValueError("Attachment ID is required")

            attachment = client.get_attachment(identifier)
            return attachment.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_ATTACHMENT_FAILED",
                api_endpoint=f"/rest/api/3/attachment/{identifier}",
                suggestions=[
                    "Verify the attachment ID exists and you have permission to view it",
                ],
                context={"attachment_id": identifier},
            )

    async def _add_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add attachment to Jira issue."""
        try:
            if not identifier or not data:
                raise ValueError("Issue key and attachment data are required")

            filename = data.get("filename")
            content = data.get("content")
            if not filename or not content:
                raise ValueError("Filename and content are required")

            attachment = client.add_attachment(
                issue_key=identifier,
                filename=filename,
                content=content
            )
            return attachment.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_ADD_ATTACHMENT_FAILED",
                api_endpoint=f"/rest/api/3/issue/{identifier}/attachments",
                suggestions=[
                    "Verify the issue key exists and you have permission to attach files",
                    "Check that filename and content are provided",
                ],
                context={"issue_key": identifier},
            )

    async def _delete_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira attachment."""
        try:
            if not identifier:
                raise ValueError("Attachment ID is required")

            success = client.delete_attachment(identifier)
            return {"deleted": success, "attachment_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_ATTACHMENT_FAILED",
                api_endpoint=f"/rest/api/3/attachment/{identifier}",
                suggestions=[
                    "Verify the attachment ID exists and you have permission to delete it",
                ],
                context={"attachment_id": identifier},
            )

    async def _create_jira_issue_link(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create link between Jira issues."""
        try:
            if not data:
                raise ValueError("Link data is required")

            from_issue = data.get("from_issue")
            to_issue = data.get("to_issue")
            link_type = data.get("link_type")

            if not all([from_issue, to_issue, link_type]):
                missing = [
                    f for f, v in [
                        ("from_issue", from_issue),
                        ("to_issue", to_issue),
                        ("link_type", link_type)
                    ] if not v
                ]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            link = client.create_issue_link(
                from_issue=from_issue,
                to_issue=to_issue,
                link_type=link_type,
                comment=data.get("comment")
            )
            return link.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_CREATE_LINK_FAILED",
                api_endpoint="/rest/api/3/issueLink",
                suggestions=[
                    "Verify both issue keys exist and you have permission to link them",
                    "Check that the link type is valid for this Jira instance",
                ],
                context={"from_issue": data.get("from_issue") if data else None},
            )

    async def _delete_jira_issue_link(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira issue link."""
        try:
            if not identifier:
                raise ValueError("Link ID is required")

            success = client.delete_issue_link(identifier)
            return {"deleted": success, "link_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_LINK_FAILED",
                api_endpoint=f"/rest/api/3/issueLink/{identifier}",
                suggestions=[
                    "Verify the link ID exists and you have permission to delete it",
                ],
                context={"link_id": identifier},
            )

    async def _get_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira sprint by ID."""
        try:
            if not identifier:
                raise ValueError("Sprint ID is required")

            sprint = client.get_sprint(identifier)
            return sprint.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_SPRINT_FAILED",
                api_endpoint=f"/rest/agile/1.0/sprint/{identifier}",
                suggestions=[
                    "Verify the sprint ID exists and you have permission to view it",
                ],
                context={"sprint_id": identifier},
            )

    async def _create_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create Jira sprint."""
        try:
            if not data:
                raise ValueError("Sprint data is required")

            name = data.get("name")
            board_id = data.get("board_id")
            if not all([name, board_id]):
                missing = [f for f, v in [("name", name), ("board_id", board_id)] if not v]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            sprint = client.create_sprint(
                name=name,
                board_id=board_id,
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                goal=data.get("goal")
            )
            return sprint.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_CREATE_SPRINT_FAILED",
                api_endpoint="/rest/agile/1.0/sprint",
                suggestions=[
                    "Verify the board ID exists and you have permission to create sprints",
                    "Check that the sprint name is unique",
                ],
                context={"board_id": data.get("board_id") if data else None},
            )

    async def _update_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Jira sprint."""
        try:
            if not identifier or not data:
                raise ValueError("Sprint ID and update data are required")

            sprint = client.update_sprint(
                sprint_id=identifier,
                name=data.get("name"),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                goal=data.get("goal"),
                state=data.get("state")
            )
            return sprint.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_UPDATE_SPRINT_FAILED",
                api_endpoint=f"/rest/agile/1.0/sprint/{identifier}",
                suggestions=[
                    "Verify the sprint ID exists and you have permission to edit it",
                    "Check that state values are valid (future, active, closed)",
                ],
                context={"sprint_id": identifier},
            )

    async def _get_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Jira version by ID."""
        try:
            if not identifier:
                raise ValueError("Version ID is required")

            version = client.get_version(identifier)
            return version.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_GET_VERSION_FAILED",
                api_endpoint=f"/rest/api/3/version/{identifier}",
                suggestions=[
                    "Verify the version ID exists and you have permission to view it",
                ],
                context={"version_id": identifier},
            )

    async def _create_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create Jira version."""
        try:
            if not data:
                raise ValueError("Version data is required")

            name = data.get("name")
            project_key = data.get("project_key")
            if not all([name, project_key]):
                missing = [f for f, v in [("name", name), ("project_key", project_key)] if not v]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            version = client.create_version(
                name=name,
                project_key=project_key,
                description=data.get("description"),
                archived=data.get("archived", False),
                released=data.get("released", False),
                release_date=data.get("release_date")
            )
            return version.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_CREATE_VERSION_FAILED",
                api_endpoint="/rest/api/3/version",
                suggestions=[
                    "Verify the project key exists and you have permission to create versions",
                    "Check that the version name is unique within the project",
                ],
                context={"project_key": data.get("project_key") if data else None},
            )

    async def _update_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Jira version."""
        try:
            if not identifier or not data:
                raise ValueError("Version ID and update data are required")

            version = client.update_version(
                version_id=identifier,
                name=data.get("name"),
                description=data.get("description"),
                archived=data.get("archived"),
                released=data.get("released"),
                release_date=data.get("release_date")
            )
            return version.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_UPDATE_VERSION_FAILED",
                api_endpoint=f"/rest/api/3/version/{identifier}",
                suggestions=[
                    "Verify the version ID exists and you have permission to edit it",
                    "Check that the version name is unique if changing it",
                ],
                context={"version_id": identifier},
            )

    async def _delete_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Jira version."""
        try:
            if not identifier:
                raise ValueError("Version ID is required")

            success = client.delete_version(identifier)
            return {"deleted": success, "version_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="JIRA_DELETE_VERSION_FAILED",
                api_endpoint=f"/rest/api/3/version/{identifier}",
                suggestions=[
                    "Verify the version ID exists and you have permission to delete it",
                    "Check that the version is not referenced by any issues",
                ],
                context={"version_id": identifier},
            )

    # Confluence operation implementations
    async def _get_confluence_page(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Confluence page by ID."""
        try:
            if not identifier:
                raise ValueError("Page ID is required")

            convert_to_markdown = options.get("convert_to_markdown", True) if options else True
            page = client.get_page_content(page_id=identifier, convert_to_markdown=convert_to_markdown)
            return page.to_simplified_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_GET_PAGE_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}",
                suggestions=[
                    "Verify the page ID exists and you have permission to view it",
                ],
                context={"page_id": identifier},
            )

    async def _create_confluence_page(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create Confluence page.

        Automatically converts markdown content in the body field to the appropriate
        format for the target Confluence instance:
        - Cloud instances: Converts to ADF (Atlassian Document Format)
        - Server/DC instances: Converts to Confluence storage format (XHTML)

        Supports ADF-specific markdown extensions like panels, status badges, dates,
        mentions, and expandable sections.

        Args:
            client: ConfluenceFetcher instance
            identifier: Not used for creation
            data: Page data dictionary containing space_key (or space_id), title, body (markdown),
                  and optional parent_id
            options: Optional parameters

        Returns:
            Dictionary representation of the created page
        """
        try:
            if not data:
                raise MetaToolError(
                    error_code="CONFLUENCE_MISSING_DATA",
                    user_message="Page data is required",
                    suggestions=[
                        "Provide a data dictionary with required fields",
                        "Example: data={'space_key': '~911651470', 'title': 'My Page', 'body': '# Content'}"
                    ],
                    context={"provided_data": None}
                )

            # Extract required fields - support both space_key and space_id for compatibility
            space_key = data.get("space_key") or data.get("space_id")
            title = data.get("title")
            body = data.get("body")

            # Validate required fields with helpful error messages
            if not space_key:
                raise MetaToolError(
                    error_code="CONFLUENCE_MISSING_SPACE",
                    user_message="Missing required field: 'space_key'",
                    suggestions=[
                        "Add 'space_key' to your data object",
                        "For personal space use: \"space_key\": \"~911651470\"",
                        "For team space use: \"space_key\": \"TEAMSPACE\"",
                        "You can also use 'space_id' if you have the numeric ID"
                    ],
                    context={"provided_fields": list(data.keys())}
                )

            if not title:
                raise MetaToolError(
                    error_code="CONFLUENCE_MISSING_TITLE",
                    user_message="Missing required field: 'title'",
                    suggestions=[
                        "Add 'title' to your data object",
                        "Example: \"title\": \"My Page Title\"",
                        "Page titles must be unique within the space"
                    ],
                    context={"provided_fields": list(data.keys())}
                )

            if not body:
                raise MetaToolError(
                    error_code="CONFLUENCE_MISSING_BODY",
                    user_message="Missing required field: 'body'",
                    suggestions=[
                        "Add 'body' to your data object",
                        "Example: \"body\": \"# My Page\\n\\nContent with **markdown** formatting\"",
                        "Body content supports full markdown syntax"
                    ],
                    context={"provided_fields": list(data.keys())}
                )

            # Create page using existing implementation
            page = client.create_page(
                space_id=space_key,  # The create_page method handles both space_key and space_id
                title=title,
                body=body,
                parent_id=data.get("parent_id"),
                is_markdown=data.get("is_markdown", True),
                enable_heading_anchors=data.get("enable_heading_anchors", False),
                content_representation=data.get("content_representation"),
            )
            return page.model_dump()
        except MetaToolError:
            # Re-raise MetaToolError as-is to preserve structured error information
            raise
        except Exception as e:
            # Enhanced error handling with more specific guidance
            error_message = str(e).lower()

            if "space" in error_message and ("not found" in error_message or "does not exist" in error_message):
                raise MetaToolError.from_exception(
                    error=e,
                    error_code="CONFLUENCE_SPACE_NOT_FOUND",
                    api_endpoint="/wiki/api/v2/pages",
                    suggestions=[
                        f"Space '{space_key}' was not found or you don't have access to it",
                        "Verify the space key is correct (e.g., '~911651470' for personal space)",
                        "Check that you have permission to view and create pages in this space",
                        "For personal spaces, use format: ~<account_id>",
                        "For team spaces, use the space key from the URL"
                    ],
                    context={
                        "space_key": space_key,
                        "title": title,
                        "provided_fields": list(data.keys())
                    }
                )
            elif "title" in error_message and ("duplicate" in error_message or "already exists" in error_message):
                raise MetaToolError.from_exception(
                    error=e,
                    error_code="CONFLUENCE_DUPLICATE_TITLE",
                    api_endpoint="/wiki/api/v2/pages",
                    suggestions=[
                        f"A page with title '{title}' already exists in space '{space_key}'",
                        "Choose a different page title",
                        "Or update the existing page instead of creating a new one",
                        "Page titles must be unique within each space"
                    ],
                    context={
                        "space_key": space_key,
                        "title": title,
                        "provided_fields": list(data.keys())
                    }
                )
            elif "permission" in error_message or "forbidden" in error_message or "401" in error_message or "403" in error_message:
                raise MetaToolError.from_exception(
                    error=e,
                    error_code="CONFLUENCE_PERMISSION_DENIED",
                    api_endpoint="/wiki/api/v2/pages",
                    suggestions=[
                        "You don't have permission to create pages in this space",
                        "Check that your API token has the required scopes",
                        "Verify you have 'Add Page' permission in the space",
                        "Contact your Confluence administrator for access"
                    ],
                    context={
                        "space_key": space_key,
                        "title": title,
                        "provided_fields": list(data.keys())
                    }
                )
            else:
                # Generic error with helpful context
                raise MetaToolError.from_exception(
                    error=e,
                    error_code="CONFLUENCE_CREATE_PAGE_FAILED",
                    api_endpoint="/wiki/api/v2/pages",
                    suggestions=[
                        "Check that all field values are valid",
                        "Verify the space exists and you have access to it",
                        "Ensure the page title is unique within the space",
                        "Check the get_resource_schema tool for field validation"
                    ],
                    context={
                        "space_key": space_key,
                        "title": title,
                        "provided_fields": list(data.keys()),
                        "error_details": str(e)
                    }
                )

    async def _update_confluence_page(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Confluence page."""
        try:
            if not identifier or not data:
                raise ValueError("Page ID and update data are required")

            # Extract required fields
            title = data.get("title")
            body = data.get("body")

            if not all([title, body]):
                missing = [f for f, v in [("title", title), ("body", body)] if not v]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            page = client.update_page(
                page_id=identifier,
                title=title,
                body=body,
                is_markdown=data.get("is_markdown", True),
                enable_heading_anchors=data.get("enable_heading_anchors", False),
                content_representation=data.get("content_representation"),
            )
            return page.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_UPDATE_PAGE_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}",
                suggestions=[
                    "Verify the page ID exists and you have permission to edit it",
                ],
                context={"page_id": identifier},
            )

    async def _delete_confluence_page(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Confluence page."""
        try:
            if not identifier:
                raise ValueError("Page ID is required")

            success = client.delete_page(page_id=identifier)
            return {"deleted": success, "page_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_DELETE_PAGE_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}",
                suggestions=[
                    "Verify the page ID exists and you have permission to delete it",
                ],
                context={"page_id": identifier},
            )

    # Placeholder implementations for other Confluence operations
    async def _get_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Confluence comment by ID."""
        try:
            if not identifier:
                raise ValueError("Comment ID is required")

            comment = client.get_comment(identifier)
            return self._serialize_result(comment)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_GET_COMMENT_FAILED",
                api_endpoint=f"/wiki/api/v2/comments/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to view it",
                ],
                context={"comment_id": identifier},
            )

    async def _add_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add comment to Confluence page."""
        try:
            if not identifier or not data:
                raise ValueError("Page ID and comment data are required")

            body = data.get("body")
            if not body:
                raise ValueError("Comment body is required")

            comment = client.add_comment(
                page_id=identifier,
                content=body
            )
            return self._serialize_result(comment) if comment else {"error": "Failed to create comment"}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_ADD_COMMENT_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}/comments",
                suggestions=[
                    "Verify the page ID exists and you have permission to comment",
                    "Check that the comment body is not empty",
                ],
                context={"page_id": identifier},
            )

    async def _update_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Confluence comment."""
        try:
            if not identifier or not data:
                raise ValueError("Comment ID and update data are required")

            body = data.get("body")
            if not body:
                raise ValueError("Comment body is required")

            comment = client.update_comment(
                comment_id=identifier,
                body=body,
                is_markdown=data.get("is_markdown", True)
            )
            return self._serialize_result(comment)
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_UPDATE_COMMENT_FAILED",
                api_endpoint=f"/wiki/api/v2/comments/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to edit it",
                    "Check that the comment body is not empty",
                ],
                context={"comment_id": identifier},
            )

    async def _delete_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Confluence comment."""
        try:
            if not identifier:
                raise ValueError("Comment ID is required")

            success = client.delete_comment(identifier)
            return {"deleted": success, "comment_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_DELETE_COMMENT_FAILED",
                api_endpoint=f"/wiki/api/v2/comments/{identifier}",
                suggestions=[
                    "Verify the comment ID exists and you have permission to delete it",
                ],
                context={"comment_id": identifier},
            )

    async def _add_confluence_label(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Add label to Confluence page."""
        try:
            if not identifier or not data:
                raise ValueError("Page ID and label data are required")

            label_name = data.get("name")
            if not label_name:
                raise ValueError("Label name is required")

            labels = client.add_page_label(
                page_id=identifier,
                name=label_name
            )
            return [label.to_simplified_dict() for label in labels]
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_ADD_LABEL_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}/labels",
                suggestions=[
                    "Verify the page ID exists and you have permission to add labels",
                    "Check that the label name is valid",
                ],
                context={"page_id": identifier},
            )

    async def _delete_confluence_label(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete label from Confluence page."""
        try:
            if not identifier or not data:
                raise ValueError("Page ID and label data are required")

            label_name = data.get("name")
            if not label_name:
                raise ValueError("Label name is required")

            success = client.remove_label(
                page_id=identifier,
                label_name=label_name
            )
            return {"deleted": success, "page_id": identifier, "label_name": label_name}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_DELETE_LABEL_FAILED",
                api_endpoint=f"/wiki/api/v2/pages/{identifier}/labels",
                suggestions=[
                    "Verify the page ID and label name exist",
                    "Check that you have permission to remove labels",
                ],
                context={"page_id": identifier, "label_name": data.get("name") if data else None},
            )

    async def _get_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Get Confluence space by ID."""
        try:
            if not identifier:
                raise ValueError("Space ID is required")

            space = client.get_space(identifier)
            return space.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_GET_SPACE_FAILED",
                api_endpoint=f"/wiki/api/v2/spaces/{identifier}",
                suggestions=[
                    "Verify the space ID exists and you have permission to view it",
                ],
                context={"space_id": identifier},
            )

    async def _create_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create Confluence space."""
        try:
            if not data:
                raise ValueError("Space data is required")

            name = data.get("name")
            key = data.get("key")
            if not all([name, key]):
                missing = [f for f, v in [("name", name), ("key", key)] if not v]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            space = client.create_space(
                name=name,
                key=key,
                description=data.get("description"),
                type=data.get("type", "global")
            )
            return space.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_CREATE_SPACE_FAILED",
                api_endpoint="/wiki/api/v2/spaces",
                suggestions=[
                    "Check that the space key is unique and follows naming conventions",
                    "Verify you have permission to create spaces",
                ],
                context={"space_key": data.get("key") if data else None},
            )

    async def _update_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update Confluence space."""
        try:
            if not identifier or not data:
                raise ValueError("Space ID and update data are required")

            space = client.update_space(
                space_id=identifier,
                name=data.get("name"),
                description=data.get("description")
            )
            return space.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_UPDATE_SPACE_FAILED",
                api_endpoint=f"/wiki/api/v2/spaces/{identifier}",
                suggestions=[
                    "Verify the space ID exists and you have permission to edit it",
                ],
                context={"space_id": identifier},
            )

    async def _delete_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Delete Confluence space."""
        try:
            if not identifier:
                raise ValueError("Space ID is required")

            success = client.delete_space(identifier)
            return {"deleted": success, "space_id": identifier}
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_DELETE_SPACE_FAILED",
                api_endpoint=f"/wiki/api/v2/spaces/{identifier}",
                suggestions=[
                    "Verify the space ID exists and you have permission to delete it",
                    "Check that the space is not referenced by other content",
                ],
                context={"space_id": identifier},
            )
