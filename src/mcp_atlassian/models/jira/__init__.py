"""
Jira data models for the MCP Atlassian integration.

This package provides Pydantic models for Jira API data structures,
organized by entity type for better maintainability and clarity.
"""

from .agile import JiraBoard, JiraSprint
from .comment import JiraComment
from .common import (
    JiraAttachment,
    JiraChangelog,
    JiraChangelogItem,
    JiraIssueType,
    JiraPriority,
    JiraResolution,
    JiraStatus,
    JiraStatusCategory,
    JiraTimetracking,
    JiraUser,
)
from .issue import JiraIssue
from .link import (
    JiraIssueLink,
    JiraIssueLinkType,
    JiraLinkedIssue,
    JiraLinkedIssueFields,
)
from .project import JiraProject
from .search import JiraSearchResult
from .workflow import JiraTransition
from .worklog import JiraWorklog

__all__ = [
    # Common models
    "JiraUser",
    "JiraStatusCategory",
    "JiraStatus",
    "JiraIssueType",
    "JiraPriority",
    "JiraAttachment",
    "JiraResolution",
    "JiraTimetracking",
    "JiraChangelog",
    "JiraChangelogItem",
    # Entity-specific models
    "JiraComment",
    "JiraWorklog",
    "JiraProject",
    "JiraTransition",
    "JiraBoard",
    "JiraSprint",
    "JiraIssue",
    "JiraSearchResult",
    "JiraIssueLinkType",
    "JiraIssueLink",
    "JiraLinkedIssue",
    "JiraLinkedIssueFields",
]
