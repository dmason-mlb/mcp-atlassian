"""Confluence v2 REST API client implementation."""

import logging
from typing import Any
from urllib.parse import quote

from mcp_atlassian.exceptions import MCPAtlassianNotFoundError

from .base import BaseRESTClient

logger = logging.getLogger(__name__)


class ConfluenceV2Client(BaseRESTClient):
    """Confluence v2 REST API client with native ADF support."""

    def __init__(self, *args, **kwargs):
        """Initialize Confluence v2 client."""
        super().__init__(*args, **kwargs)

        # Confluence-specific headers
        self.session.headers.update(
            {
                "X-Atlassian-Token": "no-check",  # Disable XSRF check
            }
        )

    # === Page Operations ===

    def get_page_by_id(
        self,
        page_id: str,
        body_format: str = "atlas_doc_format",
        get_draft: bool = False,
        version: int | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a page by ID.

        Args:
            page_id: Page ID
            body_format: Body format (atlas_doc_format, storage, view)
            get_draft: Whether to get draft version
            version: Specific version number
            include: Additional data to include

        Returns:
            Page data
        """
        params = {
            "body-format": body_format,
            "get-draft": get_draft,
        }
        if version is not None:
            params["version"] = version
        if include:
            params["include"] = ",".join(include)

        return self.get(f"/wiki/api/v2/pages/{page_id}", params=params)

    def get_pages(
        self,
        space_id: str | None = None,
        status: str | None = None,
        title: str | None = None,
        body_format: str = "atlas_doc_format",
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get pages with optional filters.

        Args:
            space_id: Filter by space ID
            status: Filter by status (current, draft, archived)
            title: Filter by title
            body_format: Body format
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Pages data with pagination
        """
        params = {
            "body-format": body_format,
            "limit": limit,
        }
        if space_id:
            params["space-id"] = space_id
        if status:
            params["status"] = status
        if title:
            params["title"] = title
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get("/wiki/api/v2/pages", params=params)

    def create_page(
        self,
        space_id: str,
        title: str,
        body: dict[str, Any],
        status: str = "current",
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new page.

        Args:
            space_id: Space ID
            title: Page title
            body: Page body in ADF format
            status: Page status
            parent_id: Parent page ID

        Returns:
            Created page data
        """
        data = {
            "spaceId": space_id,
            "status": status,
            "title": title,
            "body": {
                "representation": "atlas_doc_format",
                "value": body,
            },
        }
        if parent_id:
            data["parentId"] = parent_id

        return self.post("/wiki/api/v2/pages", json_data=data)

    def update_page(
        self,
        page_id: str,
        title: str,
        body: dict[str, Any],
        version_number: int,
        status: str | None = None,
        parent_id: str | None = None,
        version_message: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing page.

        Args:
            page_id: Page ID
            title: New title
            body: New body in ADF format
            version_number: Current version number
            status: New status
            parent_id: New parent ID
            version_message: Version message

        Returns:
            Updated page data
        """
        data = {
            "title": title,
            "body": {
                "representation": "atlas_doc_format",
                "value": body,
            },
            "version": {
                "number": version_number + 1,
            },
        }
        if status:
            data["status"] = status
        if parent_id:
            data["parentId"] = parent_id
        if version_message:
            data["version"]["message"] = version_message

        return self.put(f"/wiki/api/v2/pages/{page_id}", json_data=data)

    def delete_page(self, page_id: str) -> None:
        """Delete a page.

        Args:
            page_id: Page ID
        """
        self.delete(f"/wiki/api/v2/pages/{page_id}")

    def get_page_children(
        self,
        page_id: str,
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get child pages.

        Args:
            page_id: Parent page ID
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Child pages with pagination
        """
        params = {
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get(f"/wiki/api/v2/pages/{page_id}/children", params=params)

    # === Space Operations ===

    def get_spaces(
        self,
        keys: list[str] | None = None,
        ids: list[str] | None = None,
        type: str | None = None,
        status: str | None = None,
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get spaces.

        Args:
            keys: Filter by space keys
            ids: Filter by space IDs
            type: Filter by type (global, personal)
            status: Filter by status (current, archived)
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Spaces data with pagination
        """
        params = {
            "limit": limit,
        }
        if keys:
            params["keys"] = ",".join(keys)
        if ids:
            params["ids"] = ",".join(ids)
        if type:
            params["type"] = type
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get("/wiki/api/v2/spaces", params=params)

    def get_space_by_id(
        self,
        space_id: str,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a space by ID.

        Args:
            space_id: Space ID
            include: Additional data to include

        Returns:
            Space data
        """
        params = {}
        if include:
            params["include"] = ",".join(include)

        return self.get(f"/wiki/api/v2/spaces/{space_id}", params=params)

    # === Search Operations ===

    def search(
        self,
        cql: str,
        cursor: str | None = None,
        limit: int = 25,
        include_archived_spaces: bool = False,
    ) -> dict[str, Any]:
        """Search content using CQL.

        Args:
            cql: CQL query string
            cursor: Pagination cursor
            limit: Results per page
            include_archived_spaces: Include archived spaces

        Returns:
            Search results with pagination
        """
        params = {
            "cql": cql,
            "limit": limit,
            "includeArchivedSpaces": include_archived_spaces,
        }
        if cursor:
            params["cursor"] = cursor

        return self.get("/wiki/api/v2/search", params=params)

    # === Comment Operations ===

    def get_comments(
        self,
        page_id: str,
        body_format: str = "atlas_doc_format",
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get page comments.

        Args:
            page_id: Page ID
            body_format: Body format
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Comments data with pagination
        """
        params = {
            "body-format": body_format,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get(f"/wiki/api/v2/pages/{page_id}/comments", params=params)

    def create_comment(
        self,
        page_id: str,
        body: dict[str, Any],
        inline_position: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a comment on a page.

        Args:
            page_id: Page ID
            body: Comment body in ADF format
            inline_position: Inline comment position

        Returns:
            Created comment data
        """
        data = {
            "pageId": page_id,
            "body": {
                "representation": "atlas_doc_format",
                "value": body,
            },
        }
        if inline_position:
            data["inlinePosition"] = inline_position

        return self.post("/wiki/api/v2/comments", json_data=data)

    def get_comment(
        self,
        comment_id: str,
        body_format: str = "atlas_doc_format",
    ) -> dict[str, Any]:
        """Get a comment by ID.

        Args:
            comment_id: Comment ID
            body_format: Body format

        Returns:
            Comment data
        """
        params = {"body-format": body_format}
        return self.get(f"/wiki/api/v2/comments/{comment_id}", params=params)

    def update_comment(
        self,
        comment_id: str,
        body: dict[str, Any],
        version_number: int,
        version_message: str | None = None,
    ) -> dict[str, Any]:
        """Update a comment.

        Args:
            comment_id: Comment ID
            body: New body in ADF format
            version_number: Current version number
            version_message: Version message

        Returns:
            Updated comment data
        """
        data = {
            "body": {
                "representation": "atlas_doc_format",
                "value": body,
            },
            "version": {
                "number": version_number + 1,
            },
        }
        if version_message:
            data["version"]["message"] = version_message

        return self.put(f"/wiki/api/v2/comments/{comment_id}", json_data=data)

    def delete_comment(self, comment_id: str) -> None:
        """Delete a comment.

        Args:
            comment_id: Comment ID
        """
        self.delete(f"/wiki/api/v2/comments/{comment_id}")

    # === Label Operations ===

    def get_labels(
        self,
        page_id: str,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get page labels.

        Args:
            page_id: Page ID
            prefix: Filter by prefix
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Labels data with pagination
        """
        params = {
            "limit": limit,
        }
        if prefix:
            params["prefix"] = prefix
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get(f"/wiki/api/v2/pages/{page_id}/labels", params=params)

    def add_labels(
        self,
        page_id: str,
        labels: list[str],
    ) -> dict[str, Any]:
        """Add labels to a page.

        Args:
            page_id: Page ID
            labels: List of label names

        Returns:
            Added labels data
        """
        data = [{"name": label} for label in labels]
        return self.post(f"/wiki/api/v2/pages/{page_id}/labels", json_data=data)

    def remove_label(
        self,
        page_id: str,
        label_name: str,
    ) -> None:
        """Remove a label from a page.

        Args:
            page_id: Page ID
            label_name: Label name
        """
        self.delete(f"/wiki/api/v2/pages/{page_id}/labels/{quote(label_name)}")

    # === User Operations ===

    def get_current_user(self) -> dict[str, Any]:
        """Get current user information.

        Returns:
            Current user data
        """
        return self.get("/wiki/rest/api/user/current")

    def get_user(
        self,
        account_id: str | None = None,
        username: str | None = None,
        key: str | None = None,
    ) -> dict[str, Any]:
        """Get user details.

        Args:
            account_id: User account ID (Cloud)
            username: Username (Server/DC)
            key: User key (Server/DC)

        Returns:
            User data
        """
        params = {}
        if account_id:
            params["accountId"] = account_id
        if username:
            params["username"] = username
        if key:
            params["key"] = key

        return self.get("/wiki/rest/api/user", params=params)

    # === Attachment Operations ===

    def get_attachments(
        self,
        page_id: str,
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
        mediaType: str | None = None,
        filename: str | None = None,
    ) -> dict[str, Any]:
        """Get page attachments.

        Args:
            page_id: Page ID
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order
            mediaType: Filter by media type
            filename: Filter by filename

        Returns:
            Attachments data with pagination
        """
        params = {
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort
        if mediaType:
            params["mediaType"] = mediaType
        if filename:
            params["filename"] = filename

        return self.get(f"/wiki/api/v2/pages/{page_id}/attachments", params=params)

    def download_attachment(
        self,
        attachment_id: str,
        version: int | None = None,
    ) -> bytes:
        """Download attachment content.

        Args:
            attachment_id: Attachment ID
            version: Specific version

        Returns:
            Attachment content
        """
        params = {}
        if version is not None:
            params["version"] = version

        response = self.get(
            f"/wiki/api/v2/attachments/{attachment_id}/download",
            params=params,
            raw_response=True,
        )
        return response.content

    # === Version Operations ===

    def get_page_versions(
        self,
        page_id: str,
        cursor: str | None = None,
        limit: int = 25,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Get page versions.

        Args:
            page_id: Page ID
            cursor: Pagination cursor
            limit: Results per page
            sort: Sort order

        Returns:
            Versions data with pagination
        """
        params = {
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        if sort:
            params["sort"] = sort

        return self.get(f"/wiki/api/v2/pages/{page_id}/versions", params=params)

    def get_page_version(
        self,
        page_id: str,
        version_number: int,
    ) -> dict[str, Any]:
        """Get a specific page version.

        Args:
            page_id: Page ID
            version_number: Version number

        Returns:
            Version data
        """
        return self.get(f"/wiki/api/v2/pages/{page_id}/versions/{version_number}")

    # === Ancestors Operations ===

    def get_page_ancestors(
        self,
        page_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get page ancestors.

        Args:
            page_id: Page ID
            limit: Maximum number of ancestors

        Returns:
            List of ancestor pages
        """
        params = {}
        if limit is not None:
            params["limit"] = limit

        result = self.get(f"/wiki/api/v2/pages/{page_id}/ancestors", params=params)
        return result.get("results", [])

    # === Permissions Operations ===

    def check_permissions(
        self,
        page_id: str,
        operations: list[str],
    ) -> dict[str, bool]:
        """Check permissions for operations on a page.

        Args:
            page_id: Page ID
            operations: List of operations to check

        Returns:
            Dict of operation -> boolean
        """
        data = {"operations": operations}
        result = self.post(
            f"/wiki/api/v2/pages/{page_id}/permissions/check",
            json_data=data,
        )
        return result.get("hasPermission", {})

    # === Legacy API Support ===

    def get_page_by_title(
        self,
        space_key: str,
        title: str,
        expand: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get page by space key and title (legacy API).

        Args:
            space_key: Space key
            title: Page title
            expand: Fields to expand

        Returns:
            Page data
        """
        # Use v2 search API to find page by title
        cql = f'space.key="{space_key}" AND title="{title}"'
        results = self.search(cql, limit=1)

        pages = results.get("results", [])
        if not pages:
            raise MCPAtlassianNotFoundError(
                f"Page '{title}' not found in space '{space_key}'"
            )

        # Get full page details
        return self.get_page_by_id(
            pages[0]["id"],
            include=expand,
        )
