"""URL-related utility functions for MCP Atlassian."""

import re
from urllib.parse import urlparse


def is_atlassian_cloud_url(url: str) -> bool:
    """Determine if a URL belongs to Atlassian Cloud or Server/Data Center.

    Args:
        url: The URL to check

    Returns:
        True if the URL is for an Atlassian Cloud instance, False for Server/Data Center
    """
    # Localhost and IP-based URLs are always Server/Data Center
    if url is None or not url:
        return False

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""

    # Check for localhost or IP address
    if (
        hostname == "localhost"
        or re.match(r"^127\.", hostname)
        or re.match(r"^192\.168\.", hostname)
        or re.match(r"^10\.", hostname)
        or re.match(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.", hostname)
    ):
        return False

    # The standard check for Atlassian cloud domains
    return (
        ".atlassian.net" in hostname
        or ".jira.com" in hostname
        or ".jira-dev.com" in hostname
        or "api.atlassian.com" in hostname
    )


def extract_cloud_id_from_url(url: str) -> str | None:
    """Extract cloud_id from an Atlassian Cloud URL.

    For URLs like https://mycompany.atlassian.net, the cloud_id is 'mycompany'.
    This is essential for OAuth authentication with Atlassian Cloud.

    Args:
        url: The Atlassian Cloud URL

    Returns:
        The cloud_id if extractable, None otherwise

    Examples:
        >>> extract_cloud_id_from_url("https://baseball.atlassian.net")
        'baseball'
        >>> extract_cloud_id_from_url("https://mycompany.atlassian.net/secure/Dashboard.jspa")
        'mycompany'
        >>> extract_cloud_id_from_url("https://localhost:8080")
        None
    """
    if not url or not is_atlassian_cloud_url(url):
        return None

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""

    # Extract cloud_id from standard Atlassian Cloud domains
    if ".atlassian.net" in hostname:
        # Format: {cloud_id}.atlassian.net
        cloud_id = hostname.split(".atlassian.net")[0]
        # Handle potential subdomain prefixes (e.g., wiki.mycompany.atlassian.net)
        if "." in cloud_id:
            cloud_id = cloud_id.split(".")[-1]
        return cloud_id if cloud_id else None

    # For other cloud domains, cloud_id extraction might be different
    # but these are less common, so return None for now
    return None
