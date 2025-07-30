"""Utility functions related to environment checking."""

import logging
import os

from .urls import is_atlassian_cloud_url

logger = logging.getLogger("mcp-atlassian.utils.environment")


def get_available_services() -> dict[str, bool | None]:
    """Determine which services are available based on environment variables."""
    # Support both individual service URLs and shared Atlassian URL
    confluence_url = os.getenv("CONFLUENCE_URL")
    if not confluence_url:
        # Try to derive from shared ATLASSIAN_URL
        atlassian_url = os.getenv("ATLASSIAN_URL")
        if atlassian_url:
            # For Cloud instances, CONFLUENCE_URL is ATLASSIAN_URL + /wiki
            base_url = atlassian_url.rstrip('/')
            if base_url.endswith('/wiki'):
                confluence_url = base_url
            else:
                confluence_url = base_url + '/wiki'
    
    confluence_is_setup = False
    if confluence_url:
        is_cloud = is_atlassian_cloud_url(confluence_url)

        # OAuth check (highest precedence, applies to Cloud)
        if all(
            [
                os.getenv("ATLASSIAN_OAUTH_CLIENT_ID"),
                os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET"),
                os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI"),
                os.getenv("ATLASSIAN_OAUTH_SCOPE"),
                os.getenv(
                    "ATLASSIAN_OAUTH_CLOUD_ID"
                ),  # CLOUD_ID is essential for OAuth client init
            ]
        ):
            confluence_is_setup = True
            logger.info(
                "Using Confluence OAuth 2.0 (3LO) authentication (Cloud-only features)"
            )
        elif all(
            [
                os.getenv("ATLASSIAN_OAUTH_ACCESS_TOKEN"),
                os.getenv("ATLASSIAN_OAUTH_CLOUD_ID"),
            ]
        ):
            confluence_is_setup = True
            logger.info(
                "Using Confluence OAuth 2.0 (3LO) authentication (Cloud-only features) "
                "with provided access token"
            )
        elif is_cloud:  # Cloud non-OAuth
            # Support both service-specific and shared credentials
            username = (
                os.getenv("CONFLUENCE_USERNAME") or 
                os.getenv("ATLASSIAN_EMAIL") or 
                os.getenv("ATLASSIAN_USERNAME")
            )
            api_token = (
                os.getenv("CONFLUENCE_API_TOKEN") or 
                os.getenv("ATLASSIAN_API_TOKEN")
            )
            if username and api_token:
                confluence_is_setup = True
                logger.info("Using Confluence Cloud Basic Authentication (API Token)")
        else:  # Server/Data Center non-OAuth
            # Support both service-specific and shared credentials
            personal_token = (
                os.getenv("CONFLUENCE_PERSONAL_TOKEN") or 
                os.getenv("ATLASSIAN_PERSONAL_TOKEN") or 
                os.getenv("ATLASSIAN_PAT")
            )
            username = (
                os.getenv("CONFLUENCE_USERNAME") or 
                os.getenv("ATLASSIAN_EMAIL") or 
                os.getenv("ATLASSIAN_USERNAME")
            )
            api_token = (
                os.getenv("CONFLUENCE_API_TOKEN") or 
                os.getenv("ATLASSIAN_API_TOKEN")
            )
            if personal_token or (username and api_token):
                confluence_is_setup = True
                logger.info(
                    "Using Confluence Server/Data Center authentication (PAT or Basic Auth)"
                )
    elif os.getenv("ATLASSIAN_OAUTH_ENABLE", "").lower() in ("true", "1", "yes"):
        confluence_is_setup = True
        logger.info(
            "Using Confluence minimal OAuth configuration - expecting user-provided tokens via headers"
        )

    # Support both individual service URLs and shared Atlassian URL
    jira_url = os.getenv("JIRA_URL")
    if not jira_url:
        # Try to derive from shared ATLASSIAN_URL
        atlassian_url = os.getenv("ATLASSIAN_URL")
        if atlassian_url:
            # For Cloud instances, JIRA_URL is the same as ATLASSIAN_URL
            jira_url = atlassian_url.rstrip('/')
    
    jira_is_setup = False
    if jira_url:
        is_cloud = is_atlassian_cloud_url(jira_url)

        # OAuth check (highest precedence, applies to Cloud)
        if all(
            [
                os.getenv("ATLASSIAN_OAUTH_CLIENT_ID"),
                os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET"),
                os.getenv("ATLASSIAN_OAUTH_REDIRECT_URI"),
                os.getenv("ATLASSIAN_OAUTH_SCOPE"),
                os.getenv("ATLASSIAN_OAUTH_CLOUD_ID"),
            ]
        ):
            jira_is_setup = True
            logger.info(
                "Using Jira OAuth 2.0 (3LO) authentication (Cloud-only features)"
            )
        elif all(
            [
                os.getenv("ATLASSIAN_OAUTH_ACCESS_TOKEN"),
                os.getenv("ATLASSIAN_OAUTH_CLOUD_ID"),
            ]
        ):
            jira_is_setup = True
            logger.info(
                "Using Jira OAuth 2.0 (3LO) authentication (Cloud-only features) "
                "with provided access token"
            )
        elif is_cloud:  # Cloud non-OAuth
            # Support both service-specific and shared credentials
            username = (
                os.getenv("JIRA_USERNAME") or 
                os.getenv("ATLASSIAN_EMAIL") or 
                os.getenv("ATLASSIAN_USERNAME")
            )
            api_token = (
                os.getenv("JIRA_API_TOKEN") or 
                os.getenv("ATLASSIAN_API_TOKEN")
            )
            if username and api_token:
                jira_is_setup = True
                logger.info("Using Jira Cloud Basic Authentication (API Token)")
        else:  # Server/Data Center non-OAuth
            # Support both service-specific and shared credentials
            personal_token = (
                os.getenv("JIRA_PERSONAL_TOKEN") or 
                os.getenv("ATLASSIAN_PERSONAL_TOKEN") or 
                os.getenv("ATLASSIAN_PAT")
            )
            username = (
                os.getenv("JIRA_USERNAME") or 
                os.getenv("ATLASSIAN_EMAIL") or 
                os.getenv("ATLASSIAN_USERNAME")
            )
            api_token = (
                os.getenv("JIRA_API_TOKEN") or 
                os.getenv("ATLASSIAN_API_TOKEN")
            )
            if personal_token or (username and api_token):
                jira_is_setup = True
                logger.info(
                    "Using Jira Server/Data Center authentication (PAT or Basic Auth)"
                )
    elif os.getenv("ATLASSIAN_OAUTH_ENABLE", "").lower() in ("true", "1", "yes"):
        jira_is_setup = True
        logger.info(
            "Using Jira minimal OAuth configuration - expecting user-provided tokens via headers"
        )

    if not confluence_is_setup:
        logger.info(
            "Confluence is not configured or required environment variables are missing."
        )
    if not jira_is_setup:
        logger.info(
            "Jira is not configured or required environment variables are missing."
        )

    return {"confluence": confluence_is_setup, "jira": jira_is_setup}
