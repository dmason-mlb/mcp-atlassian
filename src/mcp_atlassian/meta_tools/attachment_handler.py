"""Attachment Handler Meta-Tool for MCP Atlassian.

This module handles all attachment operations including upload, download,
and management of files in Jira and Confluence.
"""

import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Literal

from .errors import MetaToolError
from ..jira.client import JiraClient
from ..confluence.client import ConfluenceClient

logger = logging.getLogger(__name__)


class AttachmentHandler:
    """Universal attachment handler for Jira and Confluence attachment operations.

    Consolidates attachment-related tools:
    - upload_attachment
    - download_attachment
    - get_attachments
    - delete_attachment
    - get_attachment_metadata
    """

    # Supported attachment operations
    ATTACHMENT_OPERATIONS = {
        "upload": "Upload file as attachment",
        "download": "Download attachment file",
        "get_attachments": "Get list of attachments",
        "delete": "Delete attachment",
        "get_metadata": "Get attachment metadata",
        "validate_file": "Validate file before upload",
    }

    # Common file type restrictions
    COMMON_MIME_TYPES = {
        "images": ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"],
        "documents": [
            "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ],
        "text": ["text/plain", "text/csv", "text/html", "text/xml"],
        "archives": ["application/zip", "application/x-rar-compressed", "application/x-7z-compressed"],
    }

    # File size limits (in bytes)
    DEFAULT_SIZE_LIMITS = {
        "jira": 10 * 1024 * 1024,  # 10MB
        "confluence": 100 * 1024 * 1024,  # 100MB
    }

    def __init__(self) -> None:
        """Initialize the AttachmentHandler."""
        pass

    async def execute_attachment_operation(
        self,
        ctx: Any,  # FastMCP Context
        service: Literal["jira", "confluence"],
        operation: str,
        issue_key: str | None = None,
        page_id: str | None = None,
        attachment_id: str | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        file_content: bytes | None = None,
        download_path: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> str:
        """Execute an attachment operation.

        Args:
            ctx: The FastMCP context
            service: Target service (jira or confluence)
            operation: Type of attachment operation to perform
            issue_key: Jira issue key for attachments
            page_id: Confluence page ID for attachments
            attachment_id: ID of attachment for get/delete operations
            file_path: Path to file for upload operations
            file_name: Name for the uploaded file
            file_content: Raw file content for upload (alternative to file_path)
            download_path: Path to save downloaded file
            options: Additional operation options

        Returns:
            JSON string with operation results
        """
        try:
            # Validate inputs
            self._validate_attachment_inputs(
                service, operation, issue_key, page_id, attachment_id,
                file_path, file_name, file_content, download_path, options
            )

            # Get appropriate fetcher based on service
            if service == "jira":
                from ..servers.dependencies import get_jira_fetcher
                client = await get_jira_fetcher(ctx)
                return await self._execute_jira_attachment_operation(
                    client, operation, issue_key, attachment_id, file_path,
                    file_name, file_content, download_path, options
                )
            else:
                from ..servers.dependencies import get_confluence_fetcher
                client = await get_confluence_fetcher(ctx)
                return await self._execute_confluence_attachment_operation(
                    client, operation, page_id, attachment_id, file_path,
                    file_name, file_content, download_path, options
                )

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in attachment_handler: {e}", exc_info=True)
            raise MetaToolError.from_exception(
                error=e,
                error_code="ATTACHMENT_HANDLER_ERROR",
                user_message=f"Failed to execute {operation} attachment operation",
                suggestions=["Check the service configuration and try again"],
                context={
                    "service": service,
                    "operation": operation,
                    "issue_key": issue_key,
                    "page_id": page_id,
                    "attachment_id": attachment_id,
                },
            )

    def _validate_attachment_inputs(
        self,
        service: str,
        operation: str,
        issue_key: str | None,
        page_id: str | None,
        attachment_id: str | None,
        file_path: str | None,
        file_name: str | None,
        file_content: bytes | None,
        download_path: str | None,
        options: dict[str, Any] | None,
    ) -> None:
        """Validate attachment operation inputs."""
        if service not in ["jira", "confluence"]:
            raise MetaToolError(
                error_code="INVALID_SERVICE",
                user_message=f"Service must be 'jira' or 'confluence', got '{service}'",
                suggestions=[
                    "Use 'jira' for Jira attachments or 'confluence' for Confluence attachments"
                ],
                context={"provided_service": service},
            )

        if operation not in self.ATTACHMENT_OPERATIONS:
            raise MetaToolError(
                error_code="INVALID_ATTACHMENT_OPERATION",
                user_message=f"Operation '{operation}' is not supported",
                suggestions=[
                    f"Supported attachment operations: {', '.join(self.ATTACHMENT_OPERATIONS.keys())}"
                ],
                context={
                    "provided_operation": operation,
                    "supported_operations": list(self.ATTACHMENT_OPERATIONS.keys()),
                },
            )

        # Validate service-specific context
        if service == "jira" and not issue_key:
            raise MetaToolError(
                error_code="MISSING_ISSUE_KEY",
                user_message="Jira attachment operations require an issue_key",
                suggestions=["Provide a valid Jira issue key (e.g., 'PROJ-123')"],
                context={"service": service, "operation": operation},
            )

        if service == "confluence" and not page_id:
            raise MetaToolError(
                error_code="MISSING_PAGE_ID",
                user_message="Confluence attachment operations require a page_id",
                suggestions=["Provide a valid Confluence page ID (e.g., '123456')"],
                context={"service": service, "operation": operation},
            )

        # Validate operation-specific requirements
        if operation == "upload":
            if not file_path and not file_content:
                raise MetaToolError(
                    error_code="MISSING_FILE_SOURCE",
                    user_message="Upload operation requires either file_path or file_content",
                    suggestions=[
                        "Provide file_path to upload from disk",
                        "Provide file_content as bytes for in-memory upload"
                    ],
                    context={"operation": operation},
                )

            if file_content and not file_name:
                raise MetaToolError(
                    error_code="MISSING_FILE_NAME",
                    user_message="Upload with file_content requires a file_name",
                    suggestions=["Provide file_name when uploading from bytes"],
                    context={"operation": operation},
                )

        elif operation in ["download", "delete", "get_metadata"]:
            if not attachment_id:
                raise MetaToolError(
                    error_code="MISSING_ATTACHMENT_ID",
                    user_message=f"Operation '{operation}' requires an attachment_id",
                    suggestions=[
                        "Use get_attachments to find the attachment ID first",
                        "Provide the numeric attachment ID"
                    ],
                    context={"operation": operation},
                )


    def _validate_file_for_upload(self, file_path: str, service: str) -> dict[str, Any]:
        """Validate file for upload operation."""
        validation = {
            "file_exists": False,
            "file_readable": False,
            "file_size": 0,
            "mime_type": None,
            "size_within_limits": False,
            "type_allowed": True,
        }

        try:
            path = Path(file_path)
            validation["file_exists"] = path.exists()
            validation["file_readable"] = path.is_file() and os.access(path, os.R_OK)

            if validation["file_exists"]:
                validation["file_size"] = path.stat().st_size
                validation["mime_type"] = mimetypes.guess_type(str(path))[0]

                # Check size limits
                size_limit = self.DEFAULT_SIZE_LIMITS.get(service, 10 * 1024 * 1024)
                validation["size_within_limits"] = validation["file_size"] <= size_limit
                validation["size_limit"] = size_limit

        except Exception as e:
            validation["error"] = str(e)

        return validation

    def _validate_content_for_upload(
        self, file_content: bytes, file_name: str, service: str
    ) -> dict[str, Any]:
        """Validate file content for upload operation."""
        validation = {
            "content_size": len(file_content),
            "mime_type": mimetypes.guess_type(file_name)[0],
            "size_within_limits": False,
            "type_allowed": True,
        }

        # Check size limits
        size_limit = self.DEFAULT_SIZE_LIMITS.get(service, 10 * 1024 * 1024)
        validation["size_within_limits"] = validation["content_size"] <= size_limit
        validation["size_limit"] = size_limit

        return validation

    async def _execute_jira_attachment_operation(
        self,
        client: JiraClient,
        operation: str,
        issue_key: str,
        attachment_id: str | None,
        file_path: str | None,
        file_name: str | None,
        file_content: bytes | None,
        download_path: str | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Jira attachment operations."""
        try:
            if operation == "upload":
                if file_path:
                    result = client.upload_attachment(
                        issue_key=issue_key,
                        file_path=file_path
                    )
                else:
                    # Upload from content - not directly available, raise error
                    raise MetaToolError(
                        error_code="CONTENT_UPLOAD_NOT_SUPPORTED",
                        user_message="Upload from file content not supported, use file_path instead",
                        suggestions=["Save content to a temporary file and use file_path parameter"],
                        context={"operation": operation}
                    )

            elif operation == "get_attachments":
                issue = client.get_issue(
                    issue_key=issue_key,
                    fields="attachment",
                    expand="attachment"
                )
                result = getattr(issue, 'attachment', [])

            elif operation == "download":
                if not download_path:
                    raise MetaToolError(
                        error_code="MISSING_DOWNLOAD_PATH",
                        user_message="Download operation requires download_path parameter",
                        suggestions=["Provide a valid download path"],
                        context={"operation": operation}
                    )
                # download_attachment needs URL, but we only have attachment_id
                # This would require getting the attachment metadata first to get the URL
                raise MetaToolError(
                    error_code="DOWNLOAD_NOT_IMPLEMENTED",
                    user_message="Individual attachment download not implemented - use download_issue_attachments instead",
                    suggestions=["Use download operation with full issue download"],
                    context={"operation": operation}
                )

            elif operation == "delete":
                # Delete attachment not available in current API
                raise MetaToolError(
                    error_code="DELETE_NOT_SUPPORTED",
                    user_message="Individual attachment deletion not available in current API",
                    suggestions=["Delete attachments through Jira web interface"],
                    context={"operation": operation}
                )

            elif operation == "get_metadata":
                # Get attachment metadata not available in current API
                raise MetaToolError(
                    error_code="METADATA_NOT_SUPPORTED",
                    user_message="Individual attachment metadata not available in current API",
                    suggestions=["Get attachments through issue fields"],
                    context={"operation": operation}
                )

            elif operation == "validate_file":
                if file_path:
                    result = self._validate_file_for_upload(file_path, "jira")
                else:
                    result = self._validate_content_for_upload(file_content, file_name, "jira")

            else:
                raise ValueError(f"Unsupported Jira attachment operation: {operation}")

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
                    "service": "jira",
                    "operation": operation,
                    "issue_key": issue_key,
                    "attachment_id": attachment_id,
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"JIRA_ATTACHMENT_{operation.upper()}_FAILED",
                api_endpoint=self._get_api_endpoint("jira", operation),
                suggestions=self._get_error_suggestions("jira", operation, e),
                context={
                    "operation": operation,
                    "issue_key": issue_key,
                    "attachment_id": attachment_id,
                    "file_path": file_path,
                },
            )

    async def _execute_confluence_attachment_operation(
        self,
        client: ConfluenceClient,
        operation: str,
        page_id: str,
        attachment_id: str | None,
        file_path: str | None,
        file_name: str | None,
        file_content: bytes | None,
        download_path: str | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Confluence attachment operations."""
        try:
            if operation == "upload":
                # Confluence attachment methods not implemented in current API
                raise MetaToolError(
                    error_code="CONFLUENCE_UPLOAD_NOT_SUPPORTED",
                    user_message="Confluence attachment upload not available in current API",
                    suggestions=["Use Confluence web interface to attach files to pages"],
                    context={"operation": operation, "service": "confluence"}
                )

            elif operation == "get_attachments":
                # Get attachments through page content
                page = client.get_page_content(page_id=page_id, convert_to_markdown=False)
                # Extract attachment info from page if available
                result = getattr(page, 'attachments', [])

            elif operation == "download":
                # Confluence download not implemented in current API
                raise MetaToolError(
                    error_code="CONFLUENCE_DOWNLOAD_NOT_SUPPORTED",
                    user_message="Confluence attachment download not available in current API",
                    suggestions=["Access attachments through Confluence web interface"],
                    context={"operation": operation, "service": "confluence"}
                )

            elif operation == "delete":
                # Confluence delete not implemented in current API
                raise MetaToolError(
                    error_code="CONFLUENCE_DELETE_NOT_SUPPORTED",
                    user_message="Confluence attachment deletion not available in current API",
                    suggestions=["Delete attachments through Confluence web interface"],
                    context={"operation": operation, "service": "confluence"}
                )

            elif operation == "get_metadata":
                # Confluence metadata not implemented in current API
                raise MetaToolError(
                    error_code="CONFLUENCE_METADATA_NOT_SUPPORTED",
                    user_message="Confluence attachment metadata not available in current API",
                    suggestions=["Get attachment info through page content"],
                    context={"operation": operation, "service": "confluence"}
                )

            elif operation == "validate_file":
                if file_path:
                    result = self._validate_file_for_upload(file_path, "confluence")
                else:
                    result = self._validate_content_for_upload(file_content, file_name, "confluence")

            else:
                raise ValueError(f"Unsupported Confluence attachment operation: {operation}")

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
                    "service": "confluence",
                    "operation": operation,
                    "page_id": page_id,
                    "attachment_id": attachment_id,
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"CONFLUENCE_ATTACHMENT_{operation.upper()}_FAILED",
                api_endpoint=self._get_api_endpoint("confluence", operation),
                suggestions=self._get_error_suggestions("confluence", operation, e),
                context={
                    "operation": operation,
                    "page_id": page_id,
                    "attachment_id": attachment_id,
                    "file_path": file_path,
                },
            )

    def _get_api_endpoint(self, service: str, operation: str) -> str:
        """Get the API endpoint for error reporting."""
        if service == "jira":
            endpoints = {
                "upload": "/rest/api/3/issue/{issueIdOrKey}/attachments",
                "get_attachments": "/rest/api/3/issue/{issueIdOrKey}",
                "download": "/rest/api/3/attachment/{id}",
                "delete": "/rest/api/3/attachment/{id}",
                "get_metadata": "/rest/api/3/attachment/{id}",
            }
        else:  # confluence
            endpoints = {
                "upload": "/wiki/api/v2/pages/{pageId}/attachments",
                "get_attachments": "/wiki/api/v2/pages/{pageId}/attachments",
                "download": "/wiki/api/v2/attachments/{attachmentId}/data",
                "delete": "/wiki/api/v2/attachments/{attachmentId}",
                "get_metadata": "/wiki/api/v2/attachments/{attachmentId}",
            }

        return endpoints.get(operation, f"/rest/api/3/{operation}")

    def _get_error_suggestions(
        self, service: str, operation: str, error: Exception
    ) -> list[str]:
        """Get error-specific suggestions."""
        suggestions = [
            f"Verify the {service} configuration and permissions",
        ]

        error_str = str(error).lower()

        if "authentication" in error_str or "unauthorized" in error_str:
            suggestions.append("Check your authentication credentials")
        elif "not found" in error_str:
            if operation in ["download", "delete", "get_metadata"]:
                suggestions.append("Verify the attachment ID exists and is accessible")
            elif service == "jira":
                suggestions.append("Verify the issue key exists and is accessible")
            else:
                suggestions.append("Verify the page ID exists and is accessible")
        elif "file not found" in error_str or "no such file" in error_str:
            suggestions.append("Check that the file path exists and is readable")
        elif "file too large" in error_str or "size" in error_str:
            size_limit = self.DEFAULT_SIZE_LIMITS.get(service, 10 * 1024 * 1024)
            suggestions.append(f"Check file size limit ({size_limit // (1024*1024)}MB for {service})")
        elif "permission" in error_str:
            suggestions.append(f"Ensure you have permission to perform {operation} operations")
            if operation == "upload":
                suggestions.append("Check if you can edit the issue/page and add attachments")

        return suggestions


# Export the main class
__all__ = ["AttachmentHandler"]