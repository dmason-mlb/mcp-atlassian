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

    def __init__(self, dry_run: bool = False) -> None:
        """Initialize ResourceManager.

        Args:
            dry_run: If True, validate operations without executing them
        """
        self.dry_run = dry_run

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
                    "fallback": "Use the dry_run parameter to validate your data structure",
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

            if self.dry_run:
                return self._perform_dry_run_validation(
                    service, resource, operation, data
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
            raise MetaToolError.from_exception(
                error=e,
                error_code="RESOURCE_MANAGER_ERROR",
                user_message=f"Failed to {operation} {service} {resource}",
                suggestions=["Check the service configuration and try again"],
                context={
                    "service": service,
                    "resource": resource,
                    "operation": operation,
                    "identifier": identifier,
                    "has_data": data is not None,
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

    def _perform_dry_run_validation(
        self,
        service: str,
        resource: str,
        operation: str,
        data: dict[str, Any] | None,
    ) -> str:
        """Perform dry run validation without executing the operation."""
        validation_result = {
            "dry_run": True,
            "service": service,
            "resource": resource,
            "operation": operation,
            "validation": "PASSED",
            "required_fields": self._get_required_fields(service, resource, operation),
            "provided_fields": list(data.keys()) if data else [],
        }

        if data:
            required_fields = validation_result["required_fields"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                validation_result["validation"] = "FAILED"
                validation_result["missing_fields"] = missing_fields

        return json.dumps(validation_result, indent=2, ensure_ascii=False)

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

            expand_fields = options.get("expand") if options else None
            issue = client.get_issue(identifier, expand=expand_fields)
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

            # Create issue using existing implementation
            issue = client.create_issue(
                project_key=project_key,
                summary=summary,
                issue_type=issue_type,
                description=data.get("description", ""),
                assignee=data.get("assignee"),
                components=data.get("components"),
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

            issue = client.update_issue(identifier, fields=data)
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

            success = client.delete_issue(identifier)
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
        raise MetaToolError(
            "JIRA_COMMENT_GET_NOT_IMPLEMENTED",
            "Jira comment get operation not yet implemented",
        )

    async def _add_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_COMMENT_ADD_NOT_IMPLEMENTED",
            "Jira comment add operation not yet implemented",
        )

    async def _update_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_COMMENT_UPDATE_NOT_IMPLEMENTED",
            "Jira comment update operation not yet implemented",
        )

    async def _delete_jira_comment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_COMMENT_DELETE_NOT_IMPLEMENTED",
            "Jira comment delete operation not yet implemented",
        )

    async def _get_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_WORKLOG_GET_NOT_IMPLEMENTED",
            "Jira worklog get operation not yet implemented",
        )

    async def _add_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_WORKLOG_ADD_NOT_IMPLEMENTED",
            "Jira worklog add operation not yet implemented",
        )

    async def _update_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_WORKLOG_UPDATE_NOT_IMPLEMENTED",
            "Jira worklog update operation not yet implemented",
        )

    async def _delete_jira_worklog(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_WORKLOG_DELETE_NOT_IMPLEMENTED",
            "Jira worklog delete operation not yet implemented",
        )

    async def _get_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_ATTACHMENT_GET_NOT_IMPLEMENTED",
            "Jira attachment get operation not yet implemented",
        )

    async def _add_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_ATTACHMENT_ADD_NOT_IMPLEMENTED",
            "Jira attachment add operation not yet implemented",
        )

    async def _delete_jira_attachment(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_ATTACHMENT_DELETE_NOT_IMPLEMENTED",
            "Jira attachment delete operation not yet implemented",
        )

    async def _create_jira_issue_link(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_LINK_CREATE_NOT_IMPLEMENTED",
            "Jira link create operation not yet implemented",
        )

    async def _delete_jira_issue_link(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_LINK_DELETE_NOT_IMPLEMENTED",
            "Jira link delete operation not yet implemented",
        )

    async def _get_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_SPRINT_GET_NOT_IMPLEMENTED",
            "Jira sprint get operation not yet implemented",
        )

    async def _create_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_SPRINT_CREATE_NOT_IMPLEMENTED",
            "Jira sprint create operation not yet implemented",
        )

    async def _update_jira_sprint(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_SPRINT_UPDATE_NOT_IMPLEMENTED",
            "Jira sprint update operation not yet implemented",
        )

    async def _get_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_VERSION_GET_NOT_IMPLEMENTED",
            "Jira version get operation not yet implemented",
        )

    async def _create_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_VERSION_CREATE_NOT_IMPLEMENTED",
            "Jira version create operation not yet implemented",
        )

    async def _update_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_VERSION_UPDATE_NOT_IMPLEMENTED",
            "Jira version update operation not yet implemented",
        )

    async def _delete_jira_version(
        self,
        client: JiraFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "JIRA_VERSION_DELETE_NOT_IMPLEMENTED",
            "Jira version delete operation not yet implemented",
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

            expand_fields = options.get("expand") if options else None
            page = client.get_page_content(identifier, expand=expand_fields)
            return page.to_dict()
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
            data: Page data dictionary containing space_id, title, body (markdown),
                  and optional parent_id
            options: Optional parameters
            
        Returns:
            Dictionary representation of the created page
        """
        try:
            if not data:
                raise ValueError("Page data is required")

            # Extract required fields
            space_id = data.get("space_id")
            title = data.get("title")
            body = data.get("body")

            if not all([space_id, title, body]):
                missing = [
                    f
                    for f, v in [
                        ("space_id", space_id),
                        ("title", title),
                        ("body", body),
                    ]
                    if not v
                ]
                raise ValueError(f"Missing required fields: {', '.join(missing)}")

            # Create page using existing implementation
            page = client.create_page(
                space_id=space_id,
                title=title,
                body=body,
                parent_id=data.get("parent_id"),
                is_markdown=data.get("is_markdown", True),
                enable_heading_anchors=data.get("enable_heading_anchors", False),
                content_representation=data.get("content_representation"),
            )
            return page.to_dict()
        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code="CONFLUENCE_CREATE_PAGE_FAILED",
                api_endpoint="/wiki/api/v2/pages",
                suggestions=[
                    "Verify space ID exists and you have permission to create pages",
                    "Check that the page title is unique within the space",
                ],
                context={"space_id": data.get("space_id") if data else None},
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

            success = client.delete_page(identifier)
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
        raise MetaToolError(
            "CONFLUENCE_COMMENT_GET_NOT_IMPLEMENTED",
            "Confluence comment get operation not yet implemented",
        )

    async def _add_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_COMMENT_ADD_NOT_IMPLEMENTED",
            "Confluence comment add operation not yet implemented",
        )

    async def _update_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_COMMENT_UPDATE_NOT_IMPLEMENTED",
            "Confluence comment update operation not yet implemented",
        )

    async def _delete_confluence_comment(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_COMMENT_DELETE_NOT_IMPLEMENTED",
            "Confluence comment delete operation not yet implemented",
        )

    async def _add_confluence_label(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_LABEL_ADD_NOT_IMPLEMENTED",
            "Confluence label add operation not yet implemented",
        )

    async def _delete_confluence_label(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_LABEL_DELETE_NOT_IMPLEMENTED",
            "Confluence label delete operation not yet implemented",
        )

    async def _get_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_SPACE_GET_NOT_IMPLEMENTED",
            "Confluence space get operation not yet implemented",
        )

    async def _create_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_SPACE_CREATE_NOT_IMPLEMENTED",
            "Confluence space create operation not yet implemented",
        )

    async def _update_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_SPACE_UPDATE_NOT_IMPLEMENTED",
            "Confluence space update operation not yet implemented",
        )

    async def _delete_confluence_space(
        self,
        client: ConfluenceFetcher,
        identifier: str | None,
        data: dict[str, Any] | None,
        options: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise MetaToolError(
            "CONFLUENCE_SPACE_DELETE_NOT_IMPLEMENTED",
            "Confluence space delete operation not yet implemented",
        )
