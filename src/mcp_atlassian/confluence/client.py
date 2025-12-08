"""Base client module for Confluence API interactions."""

import logging
import os

from requests import Session

from mcp_atlassian.rest.adapters import ConfluenceAdapter

from ..exceptions import MCPAtlassianAuthenticationError
from ..utils.logging import get_masked_session_headers, log_config_param, mask_sensitive
from ..utils.oauth import configure_oauth_session
from ..utils.ssl import configure_ssl_verification
from .config import ConfluenceConfig

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceClient:
    """Base client for Confluence API interactions."""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        """Initialize the Confluence client with given or environment config.

        Args:
            config: Configuration for Confluence client. If None, will load from
                environment.

        Raises:
            ValueError: If configuration is invalid or environment variables are missing
            MCPAtlassianAuthenticationError: If OAuth authentication fails
        """
        self.config = config or ConfluenceConfig.from_env()

        # Initialize the Confluence client based on auth type
        if self.config.auth_type == "oauth":
            if not self.config.oauth_config or not self.config.oauth_config.cloud_id:
                error_msg = "OAuth authentication requires a valid cloud_id"
                raise ValueError(error_msg)

            # Create a session for OAuth
            session = Session()

            # Configure the session with OAuth authentication
            oauth_result = configure_oauth_session(session, self.config.oauth_config)
            if not oauth_result:
                # Provide specific error message based on OAuth configuration state
                if not self.config.oauth_config.access_token:
                    error_msg = (
                        "OAuth authentication failed: No access token available. "
                        "To fix this:\n"
                        "1. Set ATLASSIAN_OAUTH_ACCESS_TOKEN environment variable, or\n"
                        "2. Complete OAuth setup wizard with: uv run mcp-atlassian --oauth-setup, or\n"
                        "3. Use API token authentication instead (CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN)"
                    )
                elif not self.config.oauth_config.refresh_token:
                    error_msg = (
                        "OAuth authentication failed: Access token expired and no refresh token available. "
                        "To fix this:\n"
                        "1. Provide a fresh access token via ATLASSIAN_OAUTH_ACCESS_TOKEN, or\n"
                        "2. Run OAuth setup wizard: uv run mcp-atlassian --oauth-setup, or\n"
                        "3. Use API token authentication instead (CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN)"
                    )
                else:
                    error_msg = (
                        "OAuth authentication failed: Unable to refresh access token. "
                        "To fix this:\n"
                        "1. Verify OAuth configuration is correct\n"
                        "2. Run OAuth setup wizard: uv run mcp-atlassian --oauth-setup, or\n"
                        "3. Use API token authentication instead (CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN)"
                    )
                raise MCPAtlassianAuthenticationError(error_msg)

            # The Confluence API URL with OAuth is different
            api_url = f"https://api.atlassian.com/ex/confluence/{self.config.oauth_config.cloud_id}"

            # Initialize Confluence with the session
            self.confluence = ConfluenceAdapter(
                url=api_url,
                session=session,
                cloud=True,  # OAuth is only for Cloud
                verify_ssl=self.config.ssl_verify,
                enable_adf=self.config.enable_adf,
                adf_validation_level=self.config.adf_validation_level,
            )
        elif self.config.auth_type == "pat":
            logger.debug(
                f"Initializing Confluence client with Token (PAT) auth. "
                f"URL: {self.config.url}, "
                f"Token (masked): {mask_sensitive(str(self.config.personal_token))}"
            )
            self.confluence = ConfluenceAdapter(
                url=self.config.url,
                token=self.config.personal_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                enable_adf=self.config.enable_adf,
                adf_validation_level=self.config.adf_validation_level,
            )
        else:  # basic auth
            logger.debug(
                f"Initializing Confluence client with Basic auth. "
                f"URL: {self.config.url}, Username: {self.config.username}, "
                f"API Token present: {bool(self.config.api_token)}, "
                f"Is Cloud: {self.config.is_cloud}"
            )
            self.confluence = ConfluenceAdapter(
                url=self.config.url,
                username=self.config.username,
                password=self.config.api_token,  # API token is used as password
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
                enable_adf=self.config.enable_adf,
                adf_validation_level=self.config.adf_validation_level,
            )
            logger.debug(
                f"Confluence client initialized. "
                f"Session headers (Authorization masked): "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )

        # Configure SSL verification using the shared utility
        configure_ssl_verification(
            service_name="Confluence",
            url=self.config.url,
            session=self.confluence._session,
            ssl_verify=self.config.ssl_verify,
        )

        # Proxy configuration
        proxies = {}
        if self.config.http_proxy:
            proxies["http"] = self.config.http_proxy
        if self.config.https_proxy:
            proxies["https"] = self.config.https_proxy
        if self.config.socks_proxy:
            proxies["socks"] = self.config.socks_proxy
        if proxies:
            self.confluence._session.proxies.update(proxies)
            for k, v in proxies.items():
                log_config_param(
                    logger, "Confluence", f"{k.upper()}_PROXY", v, sensitive=True
                )
        if self.config.no_proxy and isinstance(self.config.no_proxy, str):
            os.environ["NO_PROXY"] = self.config.no_proxy
            log_config_param(logger, "Confluence", "NO_PROXY", self.config.no_proxy)

        # Apply custom headers if configured
        if self.config.custom_headers:
            self._apply_custom_headers()

        # Import here to avoid circular imports
        from ..preprocessing.confluence import ConfluencePreprocessor

        self.preprocessor = ConfluencePreprocessor(base_url=self.config.url)

        # Test authentication during initialization (in debug mode only)
        if logger.isEnabledFor(logging.DEBUG):
            try:
                self._validate_authentication()
            except MCPAtlassianAuthenticationError:
                logger.warning(
                    "Authentication validation failed during client initialization - "
                    "continuing anyway"
                )

    def _validate_authentication(self) -> None:
        """Validate authentication by making a simple API call."""
        try:
            logger.debug(
                "Testing Confluence authentication by making a simple API call..."
            )
            # Make a simple API call to test authentication
            spaces = self.confluence.get_all_spaces(start=0, limit=1)
            if spaces is not None:
                logger.info(
                    f"Confluence authentication successful. "
                    f"API call returned {len(spaces.get('results', []))} spaces."
                )
            else:
                logger.warning(
                    "Confluence authentication test returned None - "
                    "this may indicate an issue"
                )
        except Exception as e:
            error_msg = f"Confluence authentication validation failed: {e}"
            logger.error(error_msg)
            logger.debug(
                f"Authentication headers during failure: "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )
            raise MCPAtlassianAuthenticationError(error_msg) from e

    def _apply_custom_headers(self) -> None:
        """Apply custom headers to the Confluence session."""
        if not self.config.custom_headers:
            return

        logger.debug(
            f"Applying {len(self.config.custom_headers)} custom headers to Confluence session"
        )
        for header_name, header_value in self.config.custom_headers.items():
            self.confluence._session.headers[header_name] = header_value
            logger.debug(f"Applied custom header: {header_name}")

    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        """Process HTML content into both HTML and markdown formats.

        Args:
            html_content: Raw HTML content from Confluence
            space_key: The key of the space containing the content

        Returns:
            Tuple of (processed_html, processed_markdown)
        """
        return self.preprocessor.process_html_content(
            html_content, space_key, self.confluence
        )

    # Search methods
    def search_pages(
        self,
        cql: str,
        limit: int = 25,
        start: int = 0,
    ) -> dict:
        """Search for Confluence pages using CQL.

        Note: The Confluence v2 API does not support the expand parameter for search
        operations. This is a deliberate design decision to improve performance.
        If you need additional fields, retrieve them with separate get_page_by_id() calls.

        Args:
            cql: Confluence Query Language (CQL) query string
            limit: Maximum number of results to return (default: 25)
            start: Starting index for pagination (default: 0)

        Returns:
            Dictionary containing search results

        Examples:
            >>> client.search_pages("space = DEV AND type = page")
            >>> client.search_pages("title ~ 'API' AND space = '~123456'", limit=50)
        """
        return self.confluence.cql(cql=cql, limit=limit, start=start)

    def search_content(
        self,
        cql: str,
        limit: int = 25,
        start: int = 0,
    ) -> dict:
        """Search for Confluence content (pages, blogposts, attachments) using CQL.

        Note: The Confluence v2 API does not support the expand parameter for search
        operations. This is a deliberate design decision to improve performance.
        If you need additional fields, retrieve them with separate API calls.

        Args:
            cql: Confluence Query Language (CQL) query string
            limit: Maximum number of results to return (default: 25)
            start: Starting index for pagination (default: 0)

        Returns:
            Dictionary containing search results

        Examples:
            >>> client.search_content("type in (page, blogpost) AND space = DEV")
            >>> client.search_content("lastModified >= '2024-01-01'")
        """
        return self.confluence.cql(cql=cql, limit=limit, start=start)

    def search_users(
        self,
        query: str,
        limit: int = 50,
    ) -> list:
        """Search for Confluence users.

        Args:
            query: Search query string (username, email, or display name)
            limit: Maximum number of results to return (default: 50)

        Returns:
            List of user dictionaries

        Examples:
            >>> client.search_users("john.doe")
            >>> client.search_users("john.doe@example.com", limit=10)
        """
        # Use CQL to search for users
        cql = f"user.fullname ~ '{query}' OR user ~ '{query}'"
        try:
            # Try user search via CQL first
            results = self.confluence.cql(cql=cql, limit=limit)

            # Extract unique users from results
            users_dict = {}
            if results and "results" in results:
                for item in results["results"]:
                    # Extract user information from various fields
                    if "lastModified" in item and "by" in item["lastModified"]:
                        user = item["lastModified"]["by"]
                        if "accountId" in user:
                            users_dict[user["accountId"]] = user
                    if "history" in item and "createdBy" in item["history"]:
                        user = item["history"]["createdBy"]
                        if "accountId" in user:
                            users_dict[user["accountId"]] = user

            return list(users_dict.values())[:limit]
        except Exception as e:
            logger.warning(f"CQL user search failed: {e}, returning empty list")
            return []

    def search_labels(
        self,
        query: str,
        limit: int = 200,
    ) -> list:
        """Search for Confluence labels.

        Args:
            query: Search query for label names
            limit: Maximum number of results to return (default: 200)

        Returns:
            List of label dictionaries

        Examples:
            >>> client.search_labels("documentation")
            >>> client.search_labels("api-*", limit=50)
        """
        # Use CQL to find content with labels matching the query
        cql = f"label = '{query}' OR label ~ '{query}'"
        try:
            results = self.confluence.cql(cql=cql, limit=limit)

            # Extract unique labels from results
            labels_dict = {}
            if results and "results" in results:
                for item in results["results"]:
                    if "metadata" in item and "labels" in item["metadata"]:
                        for label in item["metadata"]["labels"]["results"]:
                            label_name = label.get("name") or label.get("label")
                            if label_name and label_name not in labels_dict:
                                labels_dict[label_name] = label

            return list(labels_dict.values())[:limit]
        except Exception as e:
            logger.warning(f"Label search failed: {e}, returning empty list")
            return []

    def search_attachments(
        self,
        filename: str,
        space_key: str | None = None,
        limit: int = 25,
    ) -> list:
        """Search for Confluence attachments.

        Args:
            filename: Filename or pattern to search for
            space_key: Optional space key to restrict search
            limit: Maximum number of results to return (default: 25)

        Returns:
            List of attachment dictionaries

        Examples:
            >>> client.search_attachments("diagram.png")
            >>> client.search_attachments("*.pdf", space_key="DEV", limit=100)
        """
        # Build CQL query for attachments
        cql_parts = ["type = attachment"]

        if filename:
            # Use title for filename search
            cql_parts.append(f"title ~ '{filename}'")

        if space_key:
            cql_parts.append(f"space = '{space_key}'")

        cql = " AND ".join(cql_parts)

        try:
            results = self.confluence.cql(cql=cql, limit=limit)

            attachments = []
            if results and "results" in results:
                for item in results["results"]:
                    if item.get("type") == "attachment":
                        attachments.append(item)

            return attachments[:limit]
        except Exception as e:
            logger.warning(f"Attachment search failed: {e}, returning empty list")
            return []
