"""Tests for Jira Issues mixin - Import consolidation for backward compatibility.

This file provides backward compatibility by importing all test classes from
their specialized functional modules. The original monolithic test file was
split into focused test files to improve maintainability and reduce context
window usage while preserving all test coverage.

Test file organization:
- test_issues_retrieval.py: Issue retrieval functionality (13 tests)
- test_issues_creation.py: Issue creation functionality (9 tests) 
- test_issues_updates.py: Issue update operations (3 tests)
- test_issues_deletion.py: Issue deletion operations (2 tests)
- test_issues_batch.py: Batch operations functionality (10 tests)
- test_issues_fields.py: Field processing and utility functions (9 tests)

Total: 46 comprehensive test methods covering all IssuesMixin functionality
"""

# Import all test classes from their specialized modules
# This preserves backward compatibility for test discovery and execution
from tests.unit.jira.test_issues_batch import TestIssuesBatchMixin
from tests.unit.jira.test_issues_creation import TestIssuesCreationMixin
from tests.unit.jira.test_issues_deletion import TestIssuesDeletionMixin
from tests.unit.jira.test_issues_fields import TestIssuesFieldsMixin
from tests.unit.jira.test_issues_retrieval import TestIssuesRetrievalMixin
from tests.unit.jira.test_issues_updates import TestIssuesUpdatesMixin

# Re-export all test classes to maintain pytest discovery
__all__ = [
    "TestIssuesRetrievalMixin",
    "TestIssuesCreationMixin", 
    "TestIssuesUpdatesMixin",
    "TestIssuesDeletionMixin",
    "TestIssuesBatchMixin",
    "TestIssuesFieldsMixin",
]