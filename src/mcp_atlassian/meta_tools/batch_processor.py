"""Batch Processor Meta-Tool for MCP Atlassian.

This module consolidates all batch operations into a single meta-tool
to reduce token usage while maintaining full functionality.
"""

import json
import logging
import asyncio
from typing import Any, Literal

from ..exceptions import MetaToolError
from ..jira.client import JiraFetcher
from ..confluence.client import ConfluenceFetcher

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Universal batch processor for Jira and Confluence operations.

    Consolidates 3+ individual batch tools into a single meta-tool:
    - batch_create_issues
    - batch_create_versions
    - batch_get_changelogs
    """

    # Supported batch operations for each service
    JIRA_BATCH_OPERATIONS = {
        "create": {
            "issue": "Batch create multiple issues",
            "version": "Batch create multiple project versions",
            "sprint": "Batch create multiple sprints",
            "component": "Batch create multiple project components",
        },
        "update": {
            "issue": "Batch update multiple issues",
            "version": "Batch update multiple versions",
            "sprint": "Batch update multiple sprints",
        },
        "get": {
            "changelog": "Batch get changelogs for multiple issues",
            "issue": "Batch get multiple issues",
            "worklog": "Batch get worklogs for multiple issues",
        },
        "delete": {
            "issue": "Batch delete multiple issues",
            "version": "Batch delete multiple versions",
            "attachment": "Batch delete multiple attachments",
        }
    }

    CONFLUENCE_BATCH_OPERATIONS = {
        "create": {
            "page": "Batch create multiple pages",
            "space": "Batch create multiple spaces",
        },
        "update": {
            "page": "Batch update multiple pages",
        },
        "get": {
            "page": "Batch get multiple pages",
            "content": "Batch get multiple content items",
        },
        "delete": {
            "page": "Batch delete multiple pages",
            "attachment": "Batch delete multiple attachments",
        }
    }

    def __init__(self):
        """Initialize the BatchProcessor."""
        pass

    async def execute_batch_operation(
        self,
        service: Literal["jira", "confluence"],
        operation: Literal["create", "update", "get", "delete"],
        resource_type: str,
        items: list[dict],
        options: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> str:
        """Execute a batch operation.

        Args:
            service: Target service (jira or confluence)
            operation: Operation type (create, update, get, delete)
            resource_type: Type of resource (issue, page, version, etc.)
            items: Array of items to process
            options: Additional options (validation, parallel processing, etc.)
            dry_run: If True, validate without executing

        Returns:
            JSON string with batch operation results
        """
        try:
            # Validate inputs
            self._validate_batch_inputs(service, operation, resource_type, items, options)

            # Perform dry run validation if requested
            if dry_run:
                return self._perform_dry_run_validation(
                    service, operation, resource_type, items, options
                )

            # Get appropriate client based on service
            if service == "jira":
                from ..servers.context import get_jira_client
                client = get_jira_client()
                return await self._execute_jira_batch(
                    client, operation, resource_type, items, options
                )
            else:
                from ..servers.context import get_confluence_client
                client = get_confluence_client()
                return await self._execute_confluence_batch(
                    client, operation, resource_type, items, options
                )

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in batch_processor: {e}", exc_info=True)
            raise MetaToolError.from_exception(
                error=e,
                error_code="BATCH_PROCESSOR_ERROR",
                user_message=f"Failed to execute {service} {operation} {resource_type} batch",
                suggestions=["Check the service configuration and try again"],
                context={
                    "service": service,
                    "operation": operation,
                    "resource_type": resource_type,
                    "item_count": len(items) if items else 0,
                    "has_options": options is not None,
                },
            )

    def _validate_batch_inputs(
        self,
        service: str,
        operation: str,
        resource_type: str,
        items: list[dict],
        options: dict[str, Any] | None,
    ) -> None:
        """Validate batch operation inputs."""
        if service not in ["jira", "confluence"]:
            raise MetaToolError(
                error_code="INVALID_SERVICE",
                user_message=f"Service must be 'jira' or 'confluence', got '{service}'",
                suggestions=[
                    "Use 'jira' for Jira operations or 'confluence' for Confluence operations"
                ],
                context={"provided_service": service},
            )

        if operation not in ["create", "update", "get", "delete"]:
            raise MetaToolError(
                error_code="INVALID_OPERATION",
                user_message=f"Operation must be 'create', 'update', 'get', or 'delete', got '{operation}'",
                suggestions=[
                    "Use one of the supported batch operations: create, update, get, delete"
                ],
                context={"provided_operation": operation},
            )

        # Check if operation and resource type combination is supported
        supported_ops = (
            self.JIRA_BATCH_OPERATIONS if service == "jira"
            else self.CONFLUENCE_BATCH_OPERATIONS
        )

        if operation not in supported_ops or resource_type not in supported_ops[operation]:
            supported_resources = (
                list(supported_ops.get(operation, {}).keys())
                if operation in supported_ops else []
            )
            raise MetaToolError(
                error_code=f"{service.upper()}_BATCH_OPERATION_NOT_SUPPORTED",
                user_message=f"Batch {operation} for {resource_type} is not supported for {service}",
                suggestions=[
                    f"Supported {operation} resources for {service}: {', '.join(supported_resources)}"
                    if supported_resources else
                    f"Operation '{operation}' is not supported for {service}"
                ],
                context={
                    "service": service,
                    "operation": operation,
                    "resource_type": resource_type,
                    "supported_resources": supported_resources,
                },
            )

        # Validate items array
        if not items or not isinstance(items, list):
            raise MetaToolError(
                error_code="INVALID_ITEMS_ARRAY",
                user_message="Items must be a non-empty array of objects",
                suggestions=[
                    "Provide an array of items to process",
                    "Each item should be a dictionary with required fields",
                ],
                context={
                    "items_type": type(items).__name__,
                    "items_length": len(items) if isinstance(items, list) else 0,
                },
            )

        # Check batch size limits
        max_batch_size = options.get("max_batch_size", 100) if options else 100
        if len(items) > max_batch_size:
            raise MetaToolError(
                error_code="BATCH_SIZE_EXCEEDED",
                user_message=f"Batch size {len(items)} exceeds maximum of {max_batch_size}",
                suggestions=[
                    f"Split the batch into smaller chunks of {max_batch_size} items or less",
                    "Increase max_batch_size in options if needed",
                ],
                context={
                    "batch_size": len(items),
                    "max_batch_size": max_batch_size,
                },
            )

    def _perform_dry_run_validation(
        self,
        service: str,
        operation: str,
        resource_type: str,
        items: list[dict],
        options: dict[str, Any] | None,
    ) -> str:
        """Perform dry run validation without executing the batch operation."""
        validation_result = {
            "dry_run": True,
            "service": service,
            "operation": operation,
            "resource_type": resource_type,
            "validation": "PASSED",
            "item_count": len(items),
            "required_fields": self._get_required_fields(service, operation, resource_type),
            "estimated_duration": self._estimate_batch_duration(len(items), options),
            "parallel_processing": options.get("parallel", False) if options else False,
        }

        # Validate each item has required fields
        missing_fields_items = []
        required_fields = validation_result["required_fields"]

        for i, item in enumerate(items):
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                missing_fields_items.append({
                    "item_index": i,
                    "missing_fields": missing_fields,
                    "provided_fields": list(item.keys()),
                })

        if missing_fields_items:
            validation_result["validation"] = "FAILED"
            validation_result["validation_errors"] = missing_fields_items[:5]  # Show first 5 errors
            validation_result["total_errors"] = len(missing_fields_items)

        return json.dumps(validation_result, indent=2, ensure_ascii=False)

    def _get_required_fields(self, service: str, operation: str, resource_type: str) -> list[str]:
        """Get required fields for a specific batch operation."""
        field_mappings = {
            "jira": {
                "create": {
                    "issue": ["project_key", "summary", "issue_type"],
                    "version": ["name", "project_key"],
                    "sprint": ["name", "board_id"],
                    "component": ["name", "project_key"],
                },
                "update": {
                    "issue": ["key"],
                    "version": ["id"],
                    "sprint": ["id"],
                },
                "get": {
                    "changelog": ["issue_key"],
                    "issue": ["key"],
                    "worklog": ["issue_key"],
                },
                "delete": {
                    "issue": ["key"],
                    "version": ["id"],
                    "attachment": ["id"],
                },
            },
            "confluence": {
                "create": {
                    "page": ["space_id", "title", "body"],
                    "space": ["name", "key"],
                },
                "update": {
                    "page": ["id", "title", "body"],
                },
                "get": {
                    "page": ["id"],
                    "content": ["id"],
                },
                "delete": {
                    "page": ["id"],
                    "attachment": ["id"],
                },
            },
        }

        return (
            field_mappings.get(service, {})
            .get(operation, {})
            .get(resource_type, [])
        )

    def _estimate_batch_duration(self, item_count: int, options: dict[str, Any] | None) -> str:
        """Estimate batch operation duration."""
        # Base time per item (in seconds)
        base_time_per_item = 0.5

        # Adjust for parallel processing
        parallel = options.get("parallel", False) if options else False
        max_concurrent = options.get("max_concurrent", 5) if options else 5

        if parallel:
            # Parallel processing reduces time but has overhead
            estimated_seconds = (item_count / max_concurrent) * base_time_per_item + 2
        else:
            # Sequential processing
            estimated_seconds = item_count * base_time_per_item

        # Format duration
        if estimated_seconds < 60:
            return f"{estimated_seconds:.1f} seconds"
        else:
            minutes = estimated_seconds / 60
            return f"{minutes:.1f} minutes"

    async def _execute_jira_batch(
        self,
        client: JiraFetcher,
        operation: str,
        resource_type: str,
        items: list[dict],
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Jira batch operations."""
        try:
            opts = options or {}
            parallel = opts.get("parallel", False)
            max_concurrent = opts.get("max_concurrent", 5)

            results = []
            errors = []

            if parallel and len(items) > 1:
                # Parallel processing with semaphore for concurrency control
                semaphore = asyncio.Semaphore(max_concurrent)
                tasks = [
                    self._execute_single_jira_operation(
                        semaphore, client, operation, resource_type, item, i
                    )
                    for i, item in enumerate(items)
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        errors.append({
                            "item_index": i,
                            "item": items[i],
                            "error": str(result),
                        })
                    else:
                        results.append(result)
            else:
                # Sequential processing
                for i, item in enumerate(items):
                    try:
                        result = await self._execute_single_jira_operation(
                            None, client, operation, resource_type, item, i
                        )
                        results.append(result)
                    except Exception as e:
                        errors.append({
                            "item_index": i,
                            "item": item,
                            "error": str(e),
                        })

            return json.dumps(
                {
                    "success": True,
                    "service": "jira",
                    "operation": operation,
                    "resource_type": resource_type,
                    "total_items": len(items),
                    "successful_items": len(results),
                    "failed_items": len(errors),
                    "parallel_processing": parallel,
                    "results": results,
                    "errors": errors,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"JIRA_BATCH_{operation.upper()}_{resource_type.upper()}_FAILED",
                api_endpoint=self._get_batch_api_endpoint("jira", operation, resource_type),
                suggestions=[
                    f"Verify all items have required fields for {resource_type} {operation}",
                    "Check that you have permission for batch operations",
                    "Consider reducing batch size if encountering timeouts",
                ],
                context={
                    "operation": operation,
                    "resource_type": resource_type,
                    "item_count": len(items),
                },
            )

    async def _execute_single_jira_operation(
        self,
        semaphore: asyncio.Semaphore | None,
        client: JiraFetcher,
        operation: str,
        resource_type: str,
        item: dict,
        index: int,
    ) -> dict:
        """Execute a single Jira operation with optional semaphore for concurrency."""
        async def _do_operation():
            if operation == "create":
                if resource_type == "issue":
                    result = client.create_issue(
                        project_key=item["project_key"],
                        summary=item["summary"],
                        issue_type=item["issue_type"],
                        description=item.get("description", ""),
                        assignee=item.get("assignee"),
                        **{k: v for k, v in item.items() if k not in
                           ["project_key", "summary", "issue_type", "description", "assignee"]}
                    )
                elif resource_type == "version":
                    result = client.create_version(
                        name=item["name"],
                        project_key=item["project_key"],
                        description=item.get("description"),
                        released=item.get("released", False),
                        archived=item.get("archived", False),
                        release_date=item.get("release_date")
                    )
                elif resource_type == "sprint":
                    result = client.create_sprint(
                        name=item["name"],
                        board_id=item["board_id"],
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        goal=item.get("goal")
                    )
                elif resource_type == "component":
                    result = client.create_component(
                        name=item["name"],
                        project_key=item["project_key"],
                        description=item.get("description"),
                        lead=item.get("lead")
                    )
                else:
                    raise ValueError(f"Unsupported create operation for {resource_type}")

            elif operation == "update":
                if resource_type == "issue":
                    result = client.update_issue(
                        issue_key=item["key"],
                        fields={k: v for k, v in item.items() if k != "key"}
                    )
                elif resource_type == "version":
                    result = client.update_version(
                        version_id=item["id"],
                        name=item.get("name"),
                        description=item.get("description"),
                        released=item.get("released"),
                        archived=item.get("archived"),
                        release_date=item.get("release_date")
                    )
                elif resource_type == "sprint":
                    result = client.update_sprint(
                        sprint_id=item["id"],
                        name=item.get("name"),
                        start_date=item.get("start_date"),
                        end_date=item.get("end_date"),
                        goal=item.get("goal"),
                        state=item.get("state")
                    )
                else:
                    raise ValueError(f"Unsupported update operation for {resource_type}")

            elif operation == "get":
                if resource_type == "changelog":
                    result = client.get_issue_changelog(item["issue_key"])
                elif resource_type == "issue":
                    result = client.get_issue(
                        item["key"],
                        expand=item.get("expand"),
                        fields=item.get("fields")
                    )
                elif resource_type == "worklog":
                    result = client.get_issue_worklogs(item["issue_key"])
                else:
                    raise ValueError(f"Unsupported get operation for {resource_type}")

            elif operation == "delete":
                if resource_type == "issue":
                    result = {"deleted": client.delete_issue(item["key"]), "key": item["key"]}
                elif resource_type == "version":
                    result = {"deleted": client.delete_version(item["id"]), "id": item["id"]}
                elif resource_type == "attachment":
                    result = {"deleted": client.delete_attachment(item["id"]), "id": item["id"]}
                else:
                    raise ValueError(f"Unsupported delete operation for {resource_type}")

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            # Convert result to dict
            if hasattr(result, 'to_dict'):
                result_data = result.to_dict()
            elif hasattr(result, 'to_simplified_dict'):
                result_data = result.to_simplified_dict()
            else:
                result_data = result

            return {
                "item_index": index,
                "operation": f"{operation}_{resource_type}",
                "result": result_data,
            }

        if semaphore:
            async with semaphore:
                return await _do_operation()
        else:
            return await _do_operation()

    async def _execute_confluence_batch(
        self,
        client: ConfluenceFetcher,
        operation: str,
        resource_type: str,
        items: list[dict],
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Confluence batch operations."""
        try:
            opts = options or {}
            parallel = opts.get("parallel", False)
            max_concurrent = opts.get("max_concurrent", 5)

            results = []
            errors = []

            if parallel and len(items) > 1:
                # Parallel processing with semaphore for concurrency control
                semaphore = asyncio.Semaphore(max_concurrent)
                tasks = [
                    self._execute_single_confluence_operation(
                        semaphore, client, operation, resource_type, item, i
                    )
                    for i, item in enumerate(items)
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        errors.append({
                            "item_index": i,
                            "item": items[i],
                            "error": str(result),
                        })
                    else:
                        results.append(result)
            else:
                # Sequential processing
                for i, item in enumerate(items):
                    try:
                        result = await self._execute_single_confluence_operation(
                            None, client, operation, resource_type, item, i
                        )
                        results.append(result)
                    except Exception as e:
                        errors.append({
                            "item_index": i,
                            "item": item,
                            "error": str(e),
                        })

            return json.dumps(
                {
                    "success": True,
                    "service": "confluence",
                    "operation": operation,
                    "resource_type": resource_type,
                    "total_items": len(items),
                    "successful_items": len(results),
                    "failed_items": len(errors),
                    "parallel_processing": parallel,
                    "results": results,
                    "errors": errors,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"CONFLUENCE_BATCH_{operation.upper()}_{resource_type.upper()}_FAILED",
                api_endpoint=self._get_batch_api_endpoint("confluence", operation, resource_type),
                suggestions=[
                    f"Verify all items have required fields for {resource_type} {operation}",
                    "Check that you have permission for batch operations",
                    "Consider reducing batch size if encountering timeouts",
                ],
                context={
                    "operation": operation,
                    "resource_type": resource_type,
                    "item_count": len(items),
                },
            )

    async def _execute_single_confluence_operation(
        self,
        semaphore: asyncio.Semaphore | None,
        client: ConfluenceFetcher,
        operation: str,
        resource_type: str,
        item: dict,
        index: int,
    ) -> dict:
        """Execute a single Confluence operation with optional semaphore for concurrency."""
        async def _do_operation():
            if operation == "create":
                if resource_type == "page":
                    result = client.create_page(
                        space_id=item["space_id"],
                        title=item["title"],
                        body=item["body"],
                        parent_id=item.get("parent_id"),
                        is_markdown=item.get("is_markdown", True)
                    )
                elif resource_type == "space":
                    result = client.create_space(
                        name=item["name"],
                        key=item["key"],
                        description=item.get("description"),
                        type=item.get("type", "global")
                    )
                else:
                    raise ValueError(f"Unsupported create operation for {resource_type}")

            elif operation == "update":
                if resource_type == "page":
                    result = client.update_page(
                        page_id=item["id"],
                        title=item["title"],
                        body=item["body"],
                        is_markdown=item.get("is_markdown", True)
                    )
                else:
                    raise ValueError(f"Unsupported update operation for {resource_type}")

            elif operation == "get":
                if resource_type == "page":
                    result = client.get_page_content(
                        item["id"],
                        expand=item.get("expand")
                    )
                elif resource_type == "content":
                    result = client.get_content_by_id(
                        item["id"],
                        expand=item.get("expand")
                    )
                else:
                    raise ValueError(f"Unsupported get operation for {resource_type}")

            elif operation == "delete":
                if resource_type == "page":
                    result = {"deleted": client.delete_page(item["id"]), "id": item["id"]}
                elif resource_type == "attachment":
                    result = {"deleted": client.delete_attachment(item["id"]), "id": item["id"]}
                else:
                    raise ValueError(f"Unsupported delete operation for {resource_type}")

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            # Convert result to dict
            if hasattr(result, 'to_dict'):
                result_data = result.to_dict()
            elif hasattr(result, 'to_simplified_dict'):
                result_data = result.to_simplified_dict()
            else:
                result_data = result

            return {
                "item_index": index,
                "operation": f"{operation}_{resource_type}",
                "result": result_data,
            }

        if semaphore:
            async with semaphore:
                return await _do_operation()
        else:
            return await _do_operation()

    def _get_batch_api_endpoint(self, service: str, operation: str, resource_type: str) -> str:
        """Get the API endpoint for error reporting."""
        if service == "jira":
            base_endpoints = {
                "issue": "/rest/api/3/issue",
                "version": "/rest/api/3/version",
                "sprint": "/rest/agile/1.0/sprint",
                "component": "/rest/api/3/component",
                "changelog": "/rest/api/3/issue/{issueKey}/changelog",
                "worklog": "/rest/api/3/issue/{issueKey}/worklog",
                "attachment": "/rest/api/3/attachment",
            }
        else:  # confluence
            base_endpoints = {
                "page": "/wiki/api/v2/pages",
                "space": "/wiki/api/v2/spaces",
                "content": "/wiki/api/v2/content",
                "attachment": "/wiki/api/v2/attachments",
            }

        endpoint = base_endpoints.get(resource_type, f"/rest/api/3/{resource_type}")
        return f"{endpoint} (batch {operation})"