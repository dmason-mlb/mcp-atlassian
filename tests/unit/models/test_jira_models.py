"""Consolidated test imports for all Jira model tests.

This file provides backward compatibility by importing all test classes
from the modular test files organized by functional area.

The original monolithic test file has been split into focused modules:
- test_jira_user.py: JiraUser model tests
- test_jira_status.py: JiraStatus and JiraStatusCategory tests
- test_jira_issue_types.py: JiraIssueType and JiraPriority tests
- test_jira_comments_timetracking.py: JiraComment and JiraTimetracking tests
- test_jira_issue_core.py: Core JiraIssue model functionality tests
- test_jira_search_projects.py: JiraSearchResult and JiraProject tests
- test_jira_transitions_links.py: Transition and link model tests
- test_jira_worklog.py: JiraWorklog and real API validation tests
"""

# Import all test classes from modular files
from .test_jira_comments_timetracking import TestJiraComment, TestJiraTimetracking
from .test_jira_issue_core import TestJiraIssue
from .test_jira_issue_types import TestJiraIssueType, TestJiraPriority
from .test_jira_search_projects import TestJiraProject, TestJiraSearchResult
from .test_jira_status import TestJiraStatus, TestJiraStatusCategory
from .test_jira_transitions_links import (
    TestJiraIssueLink,
    TestJiraIssueLinkType,
    TestJiraLinkedIssue,
    TestJiraLinkedIssueFields,
    TestJiraTransition,
)
from .test_jira_user import TestJiraUser
from .test_jira_worklog import TestJiraWorklog, TestRealJiraData

# Export all test classes for backward compatibility
__all__ = [
    "TestJiraUser",
    "TestJiraStatus",
    "TestJiraStatusCategory",
    "TestJiraIssueType",
    "TestJiraPriority",
    "TestJiraComment",
    "TestJiraTimetracking",
    "TestJiraIssue",
    "TestJiraSearchResult",
    "TestJiraProject",
    "TestJiraTransition",
    "TestJiraIssueLinkType",
    "TestJiraLinkedIssueFields",
    "TestJiraLinkedIssue",
    "TestJiraIssueLink",
    "TestJiraWorklog",
    "TestRealJiraData",
]
