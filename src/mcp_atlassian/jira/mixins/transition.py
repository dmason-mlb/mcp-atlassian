"""Issue transition operations mixin for Jira client."""

import logging

from ...models.jira import JiraIssue
from ..client import JiraClient
from ..protocols import IssueOperationsProto

logger = logging.getLogger("mcp-jira")


class IssueTransitionMixin(
    JiraClient,
    IssueOperationsProto,
):
    """Mixin for Jira issue transition operations."""

    def _get_raw_transitions(self, issue_key: str) -> list[dict]:
        """
        Get raw transition data from the Jira API.

        This is an internal method that returns unprocessed transition data.
        For normalized transitions with proper structure, use get_available_transitions()
        from TransitionsMixin instead.

        Args:
            issue_key: The key of the issue

        Returns:
            List of raw transition data from the API

        Raises:
            Exception: If there is an error getting transitions
        """
        try:
            transitions = self.jira.get_issue_transitions(issue_key)
            return transitions
        except Exception as e:
            logger.error(f"Error getting transitions for issue {issue_key}: {str(e)}")
            raise Exception(
                f"Error getting transitions for issue {issue_key}: {str(e)}"
            ) from e

    def transition_issue(self, issue_key: str, transition_id: str) -> JiraIssue:
        """
        Transition an issue to a new status.

        Args:
            issue_key: The key of the issue
            transition_id: The ID of the transition to perform

        Returns:
            JiraIssue model with the updated issue data

        Raises:
            Exception: If there is an error transitioning the issue
        """
        try:
            self.jira.set_issue_status(
                issue_key=issue_key,
                status_name=transition_id,
                fields=None,
                comment=None,
            )
            return self.get_issue(issue_key)
        except Exception as e:
            logger.error(f"Error transitioning issue {issue_key}: {str(e)}")
            raise