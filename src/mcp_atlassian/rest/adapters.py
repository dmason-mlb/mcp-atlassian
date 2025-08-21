"""Adapter classes to provide backward compatibility during migration."""

from .confluence_adapter import ConfluenceAdapter
from .jira_adapter import JiraAdapter

__all__ = ["JiraAdapter", "ConfluenceAdapter"]
