"""
Jira worklog models.

This module provides Pydantic models for Jira worklogs (time tracking entries).
"""

import logging
from typing import Any

from ..base import ApiModel, TimestampMixin
from ..constants import (
    EMPTY_STRING,
    JIRA_DEFAULT_ID,
    UNKNOWN,
)
from .common import JiraUser

logger = logging.getLogger(__name__)


class JiraWorklog(ApiModel, TimestampMixin):
    """
    Model representing a Jira worklog entry.

    This model contains information about time spent on an issue,
    including the author, time spent, and related metadata.
    """

    id: str = JIRA_DEFAULT_ID
    author: JiraUser | None = None
    update_author: JiraUser | None = None
    comment: dict | str | None = None
    issue_id: str = EMPTY_STRING
    created: str = EMPTY_STRING
    updated: str = EMPTY_STRING
    started: str = EMPTY_STRING
    time_spent: str = EMPTY_STRING
    time_spent_seconds: int = 0

    @classmethod
    def from_api_response(cls, data: dict[str, Any], **kwargs: Any) -> "JiraWorklog":
        """
        Create a JiraWorklog from a Jira API response.

        Args:
            data: The worklog data from the Jira API

        Returns:
            A JiraWorklog instance
        """
        if not data:
            return cls()

        # Handle non-dictionary data by returning a default instance
        if not isinstance(data, dict):
            logger.debug("Received non-dictionary data, returning default instance")
            return cls()

        # Extract author data
        author_data = data.get("author")
        author = JiraUser.from_api_response(author_data or {})

        # Extract update author data
        update_author_data = data.get("updateAuthor")
        update_author = JiraUser.from_api_response(update_author_data or {})

        # Ensure ID is a string
        worklog_id = data.get("id", JIRA_DEFAULT_ID)
        if worklog_id is not None:
            worklog_id = str(worklog_id)

        # Parse time spent seconds with type safety
        time_spent_seconds = data.get("timeSpentSeconds", 0)
        try:
            time_spent_seconds = (
                int(time_spent_seconds) if time_spent_seconds is not None else 0
            )
        except (ValueError, TypeError):
            time_spent_seconds = 0

        # Normalize comment: some APIs return ADF dict; convert to string
        raw_comment = data.get("comment")
        if isinstance(raw_comment, dict):
            safe_comment: dict | str | None = raw_comment
        elif raw_comment is None:
            safe_comment = {}
        else:
            safe_comment = str(raw_comment)

        return cls(
            id=worklog_id,
            author=author,
            update_author=update_author,
            comment=safe_comment,
            created=str(data.get("created") or EMPTY_STRING),
            updated=str(data.get("updated") or EMPTY_STRING),
            started=str(data.get("started") or EMPTY_STRING),
            time_spent=str(data.get("timeSpent", EMPTY_STRING)),
            time_spent_seconds=time_spent_seconds,
            issue_id=str(data.get("issueId", EMPTY_STRING) or EMPTY_STRING),
        )

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result = {
            "time_spent": self.time_spent,
            "time_spent_seconds": self.time_spent_seconds,
        }

        if self.author:
            result["author"] = self.author.to_simplified_dict()

        if self.comment:
            result["comment"] = self.comment

        if self.started:
            result["started"] = self.started

        if self.created:
            result["created"] = self.created

        if self.updated:
            result["updated"] = self.updated

        return result
