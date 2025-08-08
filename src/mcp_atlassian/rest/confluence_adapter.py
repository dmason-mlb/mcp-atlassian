"""Confluence adapter to provide backward compatibility during migration."""

import logging
from typing import Any

from requests import Session

from .confluence_v2 import ConfluenceV2Client

logger = logging.getLogger(__name__)


class ConfluenceAdapter:
    """Adapter to provide atlassian-python-api compatible interface using ConfluenceV2Client."""

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        session: Session | None = None,
        cloud: bool = True,
        verify_ssl: bool = True,
    ):
        """Initialize Confluence adapter.

        Args:
            url: Confluence URL
            username: Username for basic auth
            password: Password/API token for basic auth
            token: Personal access token
            session: Pre-configured session (for OAuth)
            cloud: Whether this is a cloud instance
            verify_ssl: Whether to verify SSL
        """
        self.url = url.rstrip("/")
        self.cloud = cloud
        self._session = session or Session()

        # Determine auth type and create client
        if session and hasattr(session, "headers") and (
            "Authorization" in session.headers or True
        ):
            # OAuth session
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="oauth",
                oauth_session=session,
                verify_ssl=verify_ssl,
            )
        elif token:
            # PAT auth
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="pat",
                token=token,
                verify_ssl=verify_ssl,
            )
        else:
            # Basic auth
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="basic",
                username=username,
                password=password,
                verify_ssl=verify_ssl,
            )

        # Store session reference for compatibility
        self._session = self.client.session

    # === User Operations ===

    def get_user_details_by_username(self, username: str) -> dict[str, Any]:
        """Get user details by username."""
        if self.cloud:
            # Cloud uses account ID
            return self.client.get_user(username=username)
        else:
            # Server/DC
            return self.client.get_user(username=username)

    def get_user_details_by_accountid(
        self, account_id: str, expand: str | None = None
    ) -> dict[str, Any]:
        """Get user details by account ID."""
        if self.cloud:
            # Cloud primarily uses account ID
            return self.client.get_user(account_id=account_id)
        else:
            # Server/DC - account ID might be treated as username
            return self.client.get_user(username=account_id)

    # === Page Operations ===

    def get_page_by_id(
        self,
        page_id: str,
        expand: str | None = None,
        status: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Get page by ID."""
        expand_list = expand.split(",") if expand else None
        return self.client.get_page_by_id(
            page_id=page_id,
            version=version,
            include=expand_list,
        )

    def get_page_by_title(
        self,
        space: str,
        title: str,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Get page by title."""
        expand_list = expand.split(",") if expand else None
        return self.client.get_page_by_title(space, title, expand=expand_list)

    def get_all_pages_from_space(
        self,
        space: str,
        start: int = 0,
        limit: int = 100,
        status: str | None = None,
        expand: str | None = None,
        content_type: str = "page",
    ) -> list[dict[str, Any]]:
        """Get all pages from space."""
        # Get space details first
        spaces = self.client.get_spaces(keys=[space], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space}' not found")

        space_id = space_data[0]["id"]

        # Get pages
        result = self.client.get_pages(
            space_id=space_id,
            status=status,
            limit=limit,
        )

        return result.get("results", [])

    def create_page(
        self,
        space: str,
        title: str,
        body: str | dict[str, Any],
        parent_id: int | None = None,
        type: str = "page",
        representation: str = "storage",
        editor: str | None = None,
        full_width: bool = False,
    ) -> dict[str, Any]:
        """Create page."""
        # Get space ID
        spaces = self.client.get_spaces(keys=[space], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space}' not found")

        space_id = space_data[0]["id"]

        # Handle body format based on representation parameter
        if representation == "atlas_doc_format":
            # When representation is atlas_doc_format, the body should already be ADF
            # Don't wrap it again
            if isinstance(body, dict):
                # Already ADF format, use as-is
                body_adf = body
            else:
                # String content with atlas_doc_format representation shouldn't happen
                # but if it does, log a warning and try to use it as-is
                logger.warning(
                    f"Received string body with atlas_doc_format representation: {body[:100]}"
                )
                body_adf = body
        elif isinstance(body, str):
            # Legacy wiki markup - convert to ADF if cloud
            if self.cloud:
                # For now, wrap in a basic ADF structure
                body_adf = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": body,
                                }
                            ],
                        }
                    ],
                }
            else:
                # Server/DC - keep as string
                body_adf = body
        else:
            # Already ADF (dict format)
            body_adf = body

        return self.client.create_page(
            space_id=space_id,
            title=title,
            body=body_adf,
            parent_id=str(parent_id) if parent_id else None,
        )

    def update_page(
        self,
        page_id: int | str,
        title: str,
        body: str | dict[str, Any],
        parent_id: int | None = None,
        type: str = "page",
        representation: str = "storage",
        minor_edit: bool = False,
        full_width: bool = False,
    ) -> dict[str, Any]:
        """Update page."""
        # Get current page to get version
        page = self.get_page_by_id(str(page_id))
        current_version = page.get("version", {}).get("number", 0)

        # Handle body format based on representation parameter
        if representation == "atlas_doc_format":
            # When representation is atlas_doc_format, the body should already be ADF
            # Don't wrap it again
            if isinstance(body, dict):
                # Already ADF format, use as-is
                body_adf = body
            else:
                # String content with atlas_doc_format representation shouldn't happen
                # but if it does, log a warning and try to use it as-is
                logger.warning(
                    f"Received string body with atlas_doc_format representation: {body[:100]}"
                )
                body_adf = body
        elif isinstance(body, str):
            # Legacy wiki markup - convert to ADF if cloud
            if self.cloud:
                # For now, wrap in a basic ADF structure
                body_adf = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": body,
                                }
                            ],
                        }
                    ],
                }
            else:
                # Server/DC - keep as string
                body_adf = body
        else:
            # Already ADF (dict format)
            body_adf = body

        return self.client.update_page(
            page_id=str(page_id),
            title=title,
            body=body_adf,
            version_number=current_version,
            parent_id=str(parent_id) if parent_id else None,
        )

    def get_page_ancestors(self, page_id: str) -> list[dict[str, Any]]:
        """Get page ancestors."""
        return self.client.get_page_ancestors(page_id)

    def get_page_child_by_type(
        self,
        page_id: str,
        type: str = "page",
        start: int = 0,
        limit: int = 100,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get page children."""
        result = self.client.get_page_children(
            page_id=page_id,
            limit=limit,
        )
        return result.get("results", [])

    def remove_page(self, page_id: str) -> None:
        """Delete page."""
        self.client.delete_page(page_id)

    # === Comment Operations ===

    def get_page_comments(
        self,
        page_id: str,
        expand: str | None = None,
        depth: str | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get page comments."""
        result = self.client.get_comments(
            page_id=page_id,
            limit=limit,
        )
        return result.get("results", [])

    def add_comment(
        self,
        page_id: str,
        text: str | dict[str, Any],
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Add comment to page."""
        # Handle body format
        if isinstance(text, str):
            # Convert to ADF
            body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": text,
                            }
                        ],
                    }
                ],
            }
        else:
            body = text

        return self.client.create_comment(page_id=page_id, body=body)

    # === Search Operations ===

    def cql(
        self,
        cql: str,
        start: int = 0,
        limit: int = 100,
        include_archived_spaces: bool = False,
    ) -> dict[str, Any]:
        """Search using CQL."""
        result = self.client.search(
            cql=cql,
            limit=limit,
            include_archived_spaces=include_archived_spaces,
        )

        # Convert to legacy format
        return {
            "results": result.get("results", []),
            "start": start,
            "limit": limit,
            "size": len(result.get("results", [])),
            "_links": result.get("_links", {}),
        }

    # === Space Operations ===

    def get_all_spaces(
        self,
        start: int = 0,
        limit: int = 100,
        space_type: str | None = None,
        status: str | None = None,
        label: str | None = None,
        favourite: bool | None = None,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all spaces."""
        result = self.client.get_spaces(
            type=space_type,
            status=status,
            limit=limit,
        )
        return result.get("results", [])

    def get_space(
        self,
        space_key: str,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Get space details."""
        # First try to get by key
        spaces = self.client.get_spaces(keys=[space_key], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space_key}' not found")

        space_id = space_data[0]["id"]
        expand_list = expand.split(",") if expand else None

        return self.client.get_space_by_id(space_id, include=expand_list)

    # === Label Operations ===

    def get_page_labels(
        self,
        page_id: str,
        prefix: str | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get page labels."""
        result = self.client.get_labels(
            page_id=page_id,
            prefix=prefix,
            limit=limit,
        )
        return result.get("results", [])

    def set_page_label(self, page_id: str, label: str) -> dict[str, Any]:
        """Add label to page."""
        result = self.client.add_labels(page_id=page_id, labels=[label])
        return result