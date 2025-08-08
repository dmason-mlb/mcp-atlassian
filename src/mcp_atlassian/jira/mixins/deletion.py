"""Issue deletion operations mixin for Jira client."""

import logging

from ..client import JiraClient
from ..protocols import IssueOperationsProto

logger = logging.getLogger("mcp-jira")


class IssueDeletionMixin(
    JiraClient,
    IssueOperationsProto,
):
    """Mixin for Jira issue deletion operations."""

    def delete_issue(self, issue_key: str) -> bool:
        """
        Delete a Jira issue.

        Args:
            issue_key: The key of the issue to delete

        Returns:
            True if the issue was deleted successfully

        Raises:
            Exception: If there is an error deleting the issue
        """
        try:
            self.jira.delete_issue(issue_key)
            return True
        except Exception as e:
            msg = f"Error deleting issue {issue_key}: {str(e)}"
            logger.error(msg)
            raise Exception(msg) from e
