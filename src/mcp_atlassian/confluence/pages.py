"""Module for Confluence page operations."""

import logging

import requests
from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAuthenticationError
from ..models.confluence import ConfluencePage
from .client import ConfluenceClient
from .v2_adapter import ConfluenceV2Adapter

logger = logging.getLogger("mcp-atlassian")


class PagesMixin(ConfluenceClient):
    """Mixin for Confluence page operations."""

    @property
    def _v2_adapter(self) -> ConfluenceV2Adapter | None:
        """Get v2 API adapter for OAuth authentication.

        Returns:
            ConfluenceV2Adapter instance if OAuth is configured, None otherwise
        """
        if self.config.auth_type == "oauth" and self.config.is_cloud:
            return ConfluenceV2Adapter(
                session=self.confluence._session, base_url=self.confluence.url
            )
        return None

    def get_page_content(
        self, page_id: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage:
        """
        Get content of a specific page.

        Args:
            page_id: The ID of the page to retrieve
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            ConfluencePage model containing the page content and metadata

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error retrieving the page
        """
        try:
            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to get page '{page_id}'"
                )
                page = v2_adapter.get_page(
                    page_id=page_id,
                    expand="body.storage,version,space,children.attachment",
                )
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to get page '{page_id}'"
                )
                page = self.confluence.get_page_by_id(
                    page_id=page_id,
                    expand="body.storage,version,space,children.attachment",
                )

            space_key = page.get("space", {}).get("key", "")
            content = page["body"]["storage"]["value"]
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content, space_key=space_key, confluence_client=self.confluence
            )

            # Use the appropriate content format based on the convert_to_markdown flag
            page_content = processed_markdown if convert_to_markdown else processed_html

            # Create and return the ConfluencePage model
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # Override content with our processed version
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                is_cloud=self.config.is_cloud,
            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(
                f"Error retrieving page content for page ID {page_id}: {str(e)}"
            )
            raise Exception(f"Error retrieving page content: {str(e)}") from e

    def get_page_ancestors(self, page_id: str) -> list[ConfluencePage]:
        """
        Get ancestors (parent pages) of a specific page.

        Args:
            page_id: The ID of the page to get ancestors for

        Returns:
            List of ConfluencePage models representing the ancestors in hierarchical order
                (immediate parent first, root ancestor last)

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
        """
        try:
            # Use the Atlassian Python API to get ancestors
            ancestors = self.confluence.get_page_ancestors(page_id)

            # Process each ancestor
            ancestor_models = []
            for ancestor in ancestors:
                # Create the page model without fetching content
                page_model = ConfluencePage.from_api_response(
                    ancestor,
                    base_url=self.config.url,
                    include_body=False,
                )
                ancestor_models.append(page_model)

            return ancestor_models
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"Error fetching ancestors for page {page_id}: {str(e)}")
            logger.debug("Full exception details:", exc_info=True)
            return []

    def get_page_by_title(
        self, space_key: str, title: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage | None:
        """
        Get a specific page by its title from a Confluence space.

        Args:
            space_key: The key of the space containing the page
            title: The title of the page to retrieve
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            ConfluencePage model containing the page content and metadata, or None if not found
        """
        try:
            # Directly try to find the page by title
            page = self.confluence.get_page_by_title(
                space=space_key, title=title, expand="body.storage,version"
            )

            if not page:
                logger.warning(
                    f"Page '{title}' not found in space '{space_key}'. "
                    f"The space may be invalid, the page may not exist, or permissions may be insufficient."
                )
                return None

            content = page["body"]["storage"]["value"]
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content, space_key=space_key, confluence_client=self.confluence
            )

            # Use the appropriate content format based on the convert_to_markdown flag
            page_content = processed_markdown if convert_to_markdown else processed_html

            # Create and return the ConfluencePage model
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # Override content with our processed version
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                is_cloud=self.config.is_cloud,
            )

        except KeyError as e:
            logger.error(f"Missing key in page data: {str(e)}")
            return None
        except requests.RequestException as e:
            logger.error(f"Network error when fetching page: {str(e)}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing page data: {str(e)}")
            return None
        except Exception as e:  # noqa: BLE001 - Intentional fallback with full logging
            logger.error(f"Unexpected error fetching page: {str(e)}")
            # Log the full traceback at debug level for troubleshooting
            logger.debug("Full exception details:", exc_info=True)
            return None

    def get_space_pages(
        self,
        space_key: str,
        start: int = 0,
        limit: int = 10,
        *,
        convert_to_markdown: bool = True,
    ) -> list[ConfluencePage]:
        """
        Get all pages from a specific space.

        Args:
            space_key: The key of the space to get pages from
            start: The starting index for pagination
            limit: Maximum number of pages to return
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            List of ConfluencePage models containing page content and metadata
        """
        pages = self.confluence.get_all_pages_from_space(
            space=space_key, start=start, limit=limit, expand="body.storage"
        )

        page_models = []
        for page in pages:
            content = page["body"]["storage"]["value"]
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content, space_key=space_key, confluence_client=self.confluence
            )

            # Use the appropriate content format based on the convert_to_markdown flag
            page_content = processed_markdown if convert_to_markdown else processed_html

            # Ensure space information is included
            if "space" not in page:
                page["space"] = {
                    "key": space_key,
                    "name": space_key,  # Use space_key as name if not available
                }

            # Create the ConfluencePage model
            page_model = ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # Override content with our processed version
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                is_cloud=self.config.is_cloud,
            )

            page_models.append(page_model)

        return page_models

    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
        *,
        is_markdown: bool = True,
        enable_heading_anchors: bool = False,
        content_representation: str | None = None,
    ) -> ConfluencePage:
        """
        Create a new page in a Confluence space.

        Args:
            space_key: The key of the space to create the page in
            title: The title of the new page
            body: The content of the page (markdown, wiki markup, or storage format)
            parent_id: Optional ID of a parent page
            is_markdown: Whether the body content is in markdown format (default: True, keyword-only)
            enable_heading_anchors: Whether to enable automatic heading anchor generation (default: False, keyword-only)
            content_representation: Content format when is_markdown=False ('wiki' or 'storage', keyword-only)

        Returns:
            ConfluencePage model containing the new page's data

        Raises:
            Exception: If there is an error creating the page
        """
        try:
            # Determine body and representation based on content type
            if is_markdown:
                # Convert markdown to appropriate Confluence format (ADF for Cloud, storage for Server/DC)
                converted_body = self.preprocessor.markdown_to_confluence(
                    body, enable_heading_anchors=enable_heading_anchors
                )
                if isinstance(converted_body, dict):
                    # ADF format for Cloud instances
                    final_body = converted_body
                    representation = "atlas_doc_format"
                else:
                    # Storage format for Server/DC instances
                    final_body = converted_body
                    representation = "storage"
            else:
                # Use body as-is with specified representation
                final_body = body
                representation = content_representation or "storage"

            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to create page '{title}'"
                )
                result = v2_adapter.create_page(
                    space_key=space_key,
                    title=title,
                    body=final_body,
                    parent_id=parent_id,
                    representation=representation,
                )
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to create page '{title}'"
                )
                result = self.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=final_body,
                    parent_id=parent_id,
                    representation=representation,
                )

            # Get the new page content
            page_id = result.get("id")
            if not page_id:
                raise ValueError("Create page response did not contain an ID")

            return self.get_page_content(page_id)
        except Exception as e:
            logger.error(
                f"Error creating page '{title}' in space {space_key}: {str(e)}"
            )
            raise Exception(
                f"Failed to create page '{title}' in space {space_key}: {str(e)}"
            ) from e

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        is_minor_edit: bool = False,
        version_comment: str = "",
        is_markdown: bool = True,
        parent_id: str | None = None,
        enable_heading_anchors: bool = False,
        content_representation: str | None = None,
    ) -> ConfluencePage:
        """
        Update an existing page in Confluence.

        Args:
            page_id: The ID of the page to update
            title: The new title of the page
            body: The new content of the page (markdown, wiki markup, or storage format)
            is_minor_edit: Whether this is a minor edit (keyword-only)
            version_comment: Optional comment for this version (keyword-only)
            is_markdown: Whether the body content is in markdown format (default: True, keyword-only)
            parent_id: Optional new parent page ID (keyword-only)
            enable_heading_anchors: Whether to enable automatic heading anchor generation (default: False, keyword-only)
            content_representation: Content format when is_markdown=False ('wiki' or 'storage', keyword-only)

        Returns:
            ConfluencePage model containing the updated page's data

        Raises:
            Exception: If there is an error updating the page
        """
        try:
            # Determine body and representation based on content type
            if is_markdown:
                # Convert markdown to appropriate Confluence format (ADF for Cloud, storage for Server/DC)
                converted_body = self.preprocessor.markdown_to_confluence(
                    body, enable_heading_anchors=enable_heading_anchors
                )
                if isinstance(converted_body, dict):
                    # ADF format for Cloud instances
                    final_body = converted_body
                    representation = "atlas_doc_format"
                else:
                    # Storage format for Server/DC instances
                    final_body = converted_body
                    representation = "storage"
            else:
                # Use body as-is with specified representation
                final_body = body
                representation = content_representation or "storage"

            logger.debug(f"Updating page {page_id} with title '{title}'")

            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to update page '{page_id}'"
                )
                response = v2_adapter.update_page(
                    page_id=page_id,
                    title=title,
                    body=final_body,
                    representation=representation,
                    version_comment=version_comment,
                )
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to update page '{page_id}'"
                )
                update_kwargs = {
                    "page_id": page_id,
                    "title": title,
                    "body": final_body,
                    "type": "page",
                    "representation": representation,
                    "minor_edit": is_minor_edit,
                    "version_comment": version_comment,
                    "always_update": True,
                }
                if parent_id:
                    update_kwargs["parent_id"] = parent_id

                self.confluence.update_page(**update_kwargs)

            # After update, refresh the page data
            return self.get_page_content(page_id)
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {str(e)}")
            raise Exception(f"Failed to update page {page_id}: {str(e)}") from e

    def get_page_children(
        self,
        page_id: str,
        start: int = 0,
        limit: int = 25,
        expand: str = "version",
        *,
        convert_to_markdown: bool = True,
    ) -> list[ConfluencePage]:
        """
        Get child pages of a specific Confluence page.

        Args:
            page_id: The ID of the parent page
            start: The starting index for pagination
            limit: Maximum number of child pages to return
            expand: Fields to expand in the response
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            List of ConfluencePage models containing the child pages
        """
        try:
            # Use the Atlassian Python API's get_page_child_by_type method
            results = self.confluence.get_page_child_by_type(
                page_id=page_id, type="page", start=start, limit=limit, expand=expand
            )

            # Process results
            page_models = []

            # Handle both pagination modes
            if isinstance(results, dict) and "results" in results:
                child_pages = results.get("results", [])
            else:
                child_pages = results or []

            space_key = ""

            # Get space key from the first result if available
            if child_pages and "space" in child_pages[0]:
                space_key = child_pages[0].get("space", {}).get("key", "")

            # Process each child page
            for page in child_pages:
                # Only process content if we have "body" expanded
                content_override = None
                if "body" in page and convert_to_markdown:
                    content = page.get("body", {}).get("storage", {}).get("value", "")
                    if content:
                        _, processed_markdown = self.preprocessor.process_html_content(
                            content,
                            space_key=space_key,
                            confluence_client=self.confluence,
                        )
                        content_override = processed_markdown

                # Create the page model
                page_model = ConfluencePage.from_api_response(
                    page,
                    base_url=self.config.url,
                    include_body=True,
                    content_override=content_override,
                    content_format="markdown" if convert_to_markdown else "storage",
                )

                page_models.append(page_model)

            return page_models

        except Exception as e:
            logger.error(f"Error fetching child pages for page {page_id}: {str(e)}")
            logger.debug("Full exception details:", exc_info=True)
            return []

    def delete_page(self, page_id: str) -> bool:
        """
        Delete a Confluence page by its ID.

        Args:
            page_id: The ID of the page to delete

        Returns:
            Boolean indicating success (True) or failure (False)

        Raises:
            Exception: If there is an error deleting the page
        """
        try:
            logger.debug(f"Deleting page {page_id}")

            # Use v2 API for OAuth authentication, v1 API for token/basic auth
            v2_adapter = self._v2_adapter
            if v2_adapter:
                logger.debug(
                    f"Using v2 API for OAuth authentication to delete page '{page_id}'"
                )
                return v2_adapter.delete_page(page_id=page_id)
            else:
                logger.debug(
                    f"Using v1 API for token/basic authentication to delete page '{page_id}'"
                )
                response = self.confluence.remove_page(page_id=page_id)

                # The Atlassian library's remove_page returns the raw response from
                # the REST API call. For a successful deletion, we should get a
                # response object, but it might be empty (HTTP 204 No Content).
                # For REST DELETE operations, a success typically returns 204 or 200

                # Check if we got a response object
                if isinstance(response, requests.Response):
                    # Check if status code indicates success (2xx)
                    success = 200 <= response.status_code < 300
                    logger.debug(
                        f"Delete page {page_id} returned status code {response.status_code}"
                    )
                    return success
                # If it's not a response object but truthy (like True), consider it a success
                elif response:
                    return True
                # Default to true since no exception was raised
                # This is safer than returning false when we don't know what happened
                return True

        except Exception as e:
            logger.error(f"Error deleting page {page_id}: {str(e)}")
            raise Exception(f"Failed to delete page {page_id}: {str(e)}") from e
