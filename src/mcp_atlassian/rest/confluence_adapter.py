"""Confluence adapter to provide backward compatibility during migration."""

import logging
from typing import Any

from requests import Session

from ..formatting.router import FormatRouter
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
        enable_adf: bool | None = None,
        adf_validation_level: str | None = None,
    ):
        """Initialize Confluence adapter.

        Args:
            url: Confluence URL
            username: Username for basic auth
            password: Password for basic auth
            token: Personal access token
            session: Existing session
            cloud: Whether this is a cloud instance
            verify_ssl: Whether to verify SSL
            enable_adf: Whether to enable ADF format (None = auto-detect)
            adf_validation_level: ADF validation level (None = environment default)
        """
        self.url = url
        self.cloud = cloud
        self.enable_adf = enable_adf

        # Initialize FormatRouter for deployment detection and format conversion
        self.format_router = FormatRouter(adf_validation_level=adf_validation_level)

        # Determine effective ADF usage
        self.should_use_adf = self._determine_adf_usage()

        # Store original URL for client initialization
        original_url = url.rstrip("/")
        self._session = session or Session()

        # Determine auth type and create client
        if (
            session
            and hasattr(session, "headers")
            and ("Authorization" in session.headers)
        ):
            # OAuth session
            self.client = ConfluenceV2Client(
                base_url=original_url,
                auth_type="oauth",
                oauth_session=session,
                verify_ssl=verify_ssl,
            )
        elif token:
            # PAT auth
            self.client = ConfluenceV2Client(
                base_url=original_url,
                auth_type="pat",
                token=token,
                verify_ssl=verify_ssl,
            )
        else:
            # Basic auth
            self.client = ConfluenceV2Client(
                base_url=original_url,
                auth_type="basic",
                username=username,
                password=password,
                verify_ssl=verify_ssl,
            )

        # Store session reference for compatibility
        self._session = self.client.session

    def _determine_adf_usage(self) -> bool:
        """Determine whether to use ADF format based on configuration and deployment type.

        Returns:
            True if ADF should be used, False for storage/wiki markup
        """
        # Explicit configuration overrides auto-detection
        if self.enable_adf is not None:
            return self.enable_adf

        # Use FormatRouter to determine deployment type and format
        try:
            result = self.format_router.detect_deployment_type(self.url)
            return result.name == "CLOUD"
        except Exception as e:
            logger.warning(f"Failed to determine deployment type for {self.url}: {e}")
            # Fall back to the cloud parameter
            return self.cloud

    def _get_representation(self) -> str:
        """Get the representation format to use for API calls.

        Returns:
            "atlas_doc_format" for ADF, "storage" for wiki markup
        """
        return "atlas_doc_format" if self.should_use_adf else "storage"

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Generic GET request method for API endpoints.

        Args:
            endpoint: The API endpoint path (e.g., "rest/api/search/user")
            params: Query parameters for the request

        Returns:
            The JSON response from the API
        """
        url = f"{self.url}/{endpoint.lstrip('/')}"
        response = self._session.get(url, params=params)
        response.raise_for_status()
        return response.json()

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
        representation: str | None = None,
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

        # Determine representation format based on FormatRouter or explicit override
        effective_representation = representation or self._get_representation()

        # Handle body format based on effective representation
        if effective_representation == "atlas_doc_format":
            # ADF format
            if isinstance(body, dict):
                # Already ADF format, use as-is
                body_adf = body
            else:
                # String content - convert to ADF using FormatRouter
                try:
                    conversion_result = self.format_router.convert_markdown(
                        str(body), self.url
                    )
                    body_adf = conversion_result["content"]

                    # Log validation feedback if available
                    if hasattr(self.format_router, "adf_generator") and hasattr(
                        self.format_router.adf_generator, "validator"
                    ):
                        validator = self.format_router.adf_generator.validator
                        is_valid, errors = validator.validate(body_adf)
                        if not is_valid and errors:
                            if validator.validation_level == "error":
                                logger.error(
                                    f"ADF validation errors: {'; '.join(errors)}"
                                )
                            elif validator.validation_level == "warn":
                                logger.warning(
                                    f"ADF validation warnings: {'; '.join(errors)}"
                                )

                except Exception as e:
                    logger.warning(
                        f"ADF conversion failed, falling back to simple structure: {e}"
                    )
                    # Fallback to basic ADF structure
                    body_adf = {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": str(body)}],
                            }
                        ],
                    }
        else:
            # Storage format - string content that needs format-specific handling
            if isinstance(body, str):
                # For storage format, keep string as-is for wiki markup
                body_adf = body
            else:
                # Already ADF (dict format) - should not happen with storage format but handle gracefully
                body_adf = body

        return self.client.create_page(
            space_id=space_id,
            title=title,
            body=body_adf,
            parent_id=str(parent_id) if parent_id else None,
            representation=effective_representation,
        )

    def update_page(
        self,
        page_id: int | str,
        title: str,
        body: str | dict[str, Any],
        parent_id: int | None = None,
        type: str = "page",
        representation: str | None = None,
        minor_edit: bool = False,
        full_width: bool = False,
    ) -> dict[str, Any]:
        """Update page."""
        # Get current page to get version
        page = self.get_page_by_id(str(page_id))
        current_version = page.get("version", {}).get("number", 0)

        # Determine representation format based on FormatRouter or explicit override
        effective_representation = representation or self._get_representation()

        # Handle body format based on effective representation
        if effective_representation == "atlas_doc_format":
            # ADF format
            if isinstance(body, dict):
                # Already ADF format, use as-is
                body_adf = body
            else:
                # String content - convert to ADF using FormatRouter
                try:
                    conversion_result = self.format_router.convert_markdown(
                        str(body), self.url
                    )
                    body_adf = conversion_result["content"]

                    # Log validation feedback if available
                    if hasattr(self.format_router, "adf_generator") and hasattr(
                        self.format_router.adf_generator, "validator"
                    ):
                        validator = self.format_router.adf_generator.validator
                        is_valid, errors = validator.validate(body_adf)
                        if not is_valid and errors:
                            if validator.validation_level == "error":
                                logger.error(
                                    f"ADF validation errors: {'; '.join(errors)}"
                                )
                            elif validator.validation_level == "warn":
                                logger.warning(
                                    f"ADF validation warnings: {'; '.join(errors)}"
                                )

                except Exception as e:
                    logger.warning(
                        f"ADF conversion failed, falling back to simple structure: {e}"
                    )
                    # Fallback to basic ADF structure
                    body_adf = {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": str(body)}],
                            }
                        ],
                    }
        else:
            # Storage format - string content that needs format-specific handling
            if isinstance(body, str):
                # For storage format, keep string as-is for wiki markup
                body_adf = body
            else:
                # Already ADF (dict format) - should not happen with storage format but handle gracefully
                body_adf = body

        return self.client.update_page(
            page_id=str(page_id),
            title=title,
            body=body_adf,
            version_number=current_version,
            parent_id=str(parent_id) if parent_id else None,
            representation=effective_representation,
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
