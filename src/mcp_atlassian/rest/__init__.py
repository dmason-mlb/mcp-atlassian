"""REST API clients for direct Atlassian API access."""

from .base import BaseRESTClient
from .jira_v3 import JiraV3Client
from .confluence_v2 import ConfluenceV2Client

__all__ = [
    "BaseRESTClient",
    "JiraV3Client", 
    "ConfluenceV2Client",
]