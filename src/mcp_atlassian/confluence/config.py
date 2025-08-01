"""Configuration module for the Confluence client."""

import logging
import os
from dataclasses import dataclass
from typing import Literal

from ..utils.env import get_custom_headers, is_env_ssl_verify
from ..utils.oauth import (
    BYOAccessTokenOAuthConfig,
    OAuthConfig,
    get_oauth_config_from_env,
)
from ..utils.urls import is_atlassian_cloud_url


@dataclass
class ConfluenceConfig:
    """Confluence API configuration.

    Handles authentication for Confluence Cloud and Server/Data Center:
    - Cloud: username/API token (basic auth) or OAuth 2.0 (3LO)
    - Server/DC: personal access token or basic auth
    """

    url: str  # Base URL for Confluence
    auth_type: Literal["basic", "pat", "oauth"]  # Authentication type
    username: str | None = None  # Email or username
    api_token: str | None = None  # API token used as password
    personal_token: str | None = None  # Personal access token (Server/DC)
    oauth_config: OAuthConfig | BYOAccessTokenOAuthConfig | None = None
    ssl_verify: bool = True  # Whether to verify SSL certificates
    spaces_filter: str | None = None  # List of space keys to filter searches
    http_proxy: str | None = None  # HTTP proxy URL
    https_proxy: str | None = None  # HTTPS proxy URL
    no_proxy: str | None = None  # Comma-separated list of hosts to bypass proxy
    socks_proxy: str | None = None  # SOCKS proxy URL (optional)
    custom_headers: dict[str, str] | None = None  # Custom HTTP headers

    # ADF and formatting configuration
    enable_adf: bool | None = (
        None  # Enable ADF format (None = auto-detect based on deployment)
    )
    force_wiki_markup: bool = False  # Force wiki markup even for Cloud instances
    deployment_type_override: str | None = (
        None  # Override deployment detection ('cloud', 'server', 'datacenter')
    )

    @property
    def is_cloud(self) -> bool:
        """Check if this is a cloud instance.

        Returns:
            True if this is a cloud instance (atlassian.net), False otherwise.
            Localhost URLs are always considered non-cloud (Server/Data Center).
        """
        # Multi-Cloud OAuth mode: URL might be None, but we use api.atlassian.com
        if (
            self.auth_type == "oauth"
            and self.oauth_config
            and self.oauth_config.cloud_id
        ):
            # OAuth with cloud_id uses api.atlassian.com which is always Cloud
            return True

        # For other auth types, check the URL
        return is_atlassian_cloud_url(self.url) if self.url else False

    @property
    def verify_ssl(self) -> bool:
        """Compatibility property for old code.

        Returns:
            The ssl_verify value
        """
        return self.ssl_verify

    @classmethod
    def from_env(cls) -> "ConfluenceConfig":
        """Create configuration from environment variables.

        Returns:
            ConfluenceConfig with values from environment variables

        Raises:
            ValueError: If any required environment variable is missing
        """
        # Support both individual service URLs and shared Atlassian URL
        url = os.getenv("CONFLUENCE_URL")
        if not url:
            # Try to derive from shared ATLASSIAN_URL
            atlassian_url = os.getenv("ATLASSIAN_URL")
            if atlassian_url:
                # For Cloud instances, CONFLUENCE_URL is ATLASSIAN_URL + /wiki
                base_url = atlassian_url.rstrip("/")
                if base_url.endswith("/wiki"):
                    url = base_url
                else:
                    url = base_url + "/wiki"
            elif not os.getenv("ATLASSIAN_OAUTH_ENABLE"):
                error_msg = "Missing required CONFLUENCE_URL or ATLASSIAN_URL environment variable"
                raise ValueError(error_msg)

        # Support both service-specific and shared credentials
        username = (
            os.getenv("CONFLUENCE_USERNAME")
            or os.getenv("ATLASSIAN_EMAIL")
            or os.getenv("ATLASSIAN_USERNAME")
        )
        api_token = os.getenv("CONFLUENCE_API_TOKEN") or os.getenv(
            "ATLASSIAN_API_TOKEN"
        )
        personal_token = (
            os.getenv("CONFLUENCE_PERSONAL_TOKEN")
            or os.getenv("ATLASSIAN_PERSONAL_TOKEN")
            or os.getenv("ATLASSIAN_PAT")
        )

        # Check for OAuth configuration
        oauth_config = get_oauth_config_from_env()
        auth_type = None

        # Use the shared utility function directly
        is_cloud = is_atlassian_cloud_url(url) if url else False

        if oauth_config:
            # OAuth is available - could be full config or minimal config for user-provided tokens
            auth_type = "oauth"
        elif is_cloud:
            if username and api_token:
                auth_type = "basic"
            else:
                error_msg = "Cloud authentication requires CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN (or ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN), or OAuth configuration (set ATLASSIAN_OAUTH_ENABLE=true for user-provided tokens)"
                raise ValueError(error_msg)
        else:  # Server/Data Center
            if personal_token:
                auth_type = "pat"
            elif username and api_token:
                # Allow basic auth for Server/DC too
                auth_type = "basic"
            else:
                error_msg = "Server/Data Center authentication requires CONFLUENCE_PERSONAL_TOKEN (or ATLASSIAN_PAT) or CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN (or ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN)"
                raise ValueError(error_msg)

        # SSL verification (for Server/DC)
        ssl_verify = is_env_ssl_verify("CONFLUENCE_SSL_VERIFY")

        # Get the spaces filter if provided
        spaces_filter = os.getenv("CONFLUENCE_SPACES_FILTER")

        # Proxy settings
        http_proxy = os.getenv("CONFLUENCE_HTTP_PROXY", os.getenv("HTTP_PROXY"))
        https_proxy = os.getenv("CONFLUENCE_HTTPS_PROXY", os.getenv("HTTPS_PROXY"))
        no_proxy = os.getenv("CONFLUENCE_NO_PROXY", os.getenv("NO_PROXY"))
        socks_proxy = os.getenv("CONFLUENCE_SOCKS_PROXY", os.getenv("SOCKS_PROXY"))

        # Custom headers - service-specific only
        custom_headers = get_custom_headers("CONFLUENCE_CUSTOM_HEADERS")

        # ADF and formatting configuration from environment
        enable_adf = None
        if os.getenv("ATLASSIAN_ENABLE_ADF"):
            enable_adf = os.getenv("ATLASSIAN_ENABLE_ADF", "").lower() in (
                "true",
                "1",
                "yes",
            )
        elif os.getenv("ATLASSIAN_DISABLE_ADF"):
            enable_adf = os.getenv("ATLASSIAN_DISABLE_ADF", "").lower() not in (
                "true",
                "1",
                "yes",
            )
        elif os.getenv("CONFLUENCE_ENABLE_ADF"):
            enable_adf = os.getenv("CONFLUENCE_ENABLE_ADF", "").lower() in (
                "true",
                "1",
                "yes",
            )

        force_wiki_markup = os.getenv("ATLASSIAN_FORCE_WIKI_MARKUP", "").lower() in (
            "true",
            "1",
            "yes",
        )
        deployment_type_override = os.getenv("ATLASSIAN_DEPLOYMENT_TYPE")

        # Ensure url is not None for the dataclass
        if not url:
            raise ValueError(
                "URL configuration resulted in None - check CONFLUENCE_URL or ATLASSIAN_URL"
            )

        # Ensure auth_type is properly typed
        if auth_type not in ("basic", "pat", "oauth"):
            error_msg = f"Invalid auth_type: {auth_type}"
            raise ValueError(error_msg)

        return cls(
            url=url,
            auth_type=auth_type,  # type: ignore[arg-type]
            username=username,
            api_token=api_token,
            personal_token=personal_token,
            oauth_config=oauth_config,
            ssl_verify=ssl_verify,
            spaces_filter=spaces_filter,
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
            socks_proxy=socks_proxy,
            custom_headers=custom_headers,
            enable_adf=enable_adf,
            force_wiki_markup=force_wiki_markup,
            deployment_type_override=deployment_type_override,
        )

    def is_auth_configured(self) -> bool:
        """Check if the current authentication configuration is complete and valid for making API calls.

        Returns:
            bool: True if authentication is fully configured, False otherwise.
        """
        logger = logging.getLogger("mcp-atlassian.confluence.config")
        if self.auth_type == "oauth":
            # Handle different OAuth configuration types
            if self.oauth_config:
                # Full OAuth configuration (traditional mode)
                if isinstance(self.oauth_config, OAuthConfig):
                    if (
                        self.oauth_config.client_id
                        and self.oauth_config.client_secret
                        and self.oauth_config.redirect_uri
                        and self.oauth_config.scope
                        and self.oauth_config.cloud_id
                    ):
                        return True
                    # Minimal OAuth configuration (user-provided tokens mode)
                    # This is valid if we have oauth_config but missing client credentials
                    # In this case, we expect authentication to come from user-provided headers
                    elif (
                        not self.oauth_config.client_id
                        and not self.oauth_config.client_secret
                    ):
                        logger.debug(
                            "Minimal OAuth config detected - expecting user-provided tokens via headers"
                        )
                        return True
                # Bring Your Own Access Token mode
                elif isinstance(self.oauth_config, BYOAccessTokenOAuthConfig):
                    if self.oauth_config.cloud_id and self.oauth_config.access_token:
                        return True

            # Partial configuration is invalid
            logger.warning("Incomplete OAuth configuration detected")
            return False
        elif self.auth_type == "pat":
            return bool(self.personal_token)
        elif self.auth_type == "basic":
            return bool(self.username and self.api_token)
        else:
            # Due to validation in from_env, auth_type can only be basic, pat, or oauth
            # This should never happen, but we raise an exception to be explicit
            error_msg = f"Unknown auth_type: {self.auth_type}"
            raise ValueError(error_msg)
