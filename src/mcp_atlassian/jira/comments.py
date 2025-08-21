"""Module for Jira comment operations."""

import logging
from typing import Any

from ..preprocessing.jira import JiraPreprocessor
from ..utils import parse_date
from .client import JiraClient

logger = logging.getLogger("mcp-jira")


class CommentsMixin(JiraClient):
    """Mixin for Jira comment operations."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the CommentsMixin.

        Args:
            *args: Positional arguments for the JiraClient
            **kwargs: Keyword arguments for the JiraClient
        """
        super().__init__(*args, **kwargs)

        # Initialize preprocessor if not already set
        if not hasattr(self, "preprocessor") or not self.preprocessor:
            base_url = ""
            if hasattr(self, "config") and hasattr(self.config, "url"):
                base_url = self.config.url
            self.preprocessor = JiraPreprocessor(base_url=base_url)

    def get_issue_comments(
        self, issue_key: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get comments for a specific issue.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            limit: Maximum number of comments to return

        Returns:
            List of comments with author, creation date, and content

        Raises:
            Exception: If there is an error getting comments
        """
        try:
            comments = self.jira.issue_get_comments(issue_key)

            if not isinstance(comments, dict):
                msg = (
                    "Unexpected return value type from "
                    f"`jira.issue_get_comments`: {type(comments)}"
                )
                logger.error(msg)
                raise TypeError(msg)

            processed_comments = []
            for comment in comments.get("comments", [])[:limit]:
                processed_comment = {
                    "id": comment.get("id"),
                    "body": self._clean_text(comment.get("body", "")),
                    "created": str(parse_date(comment.get("created"))),
                    "updated": str(parse_date(comment.get("updated"))),
                    "author": comment.get("author", {}).get("displayName", "Unknown"),
                }
                processed_comments.append(processed_comment)

            return processed_comments
        except Exception as e:
            error_msg = f"Error getting comments for issue {issue_key}: {str(e)}"
            logger.error(error_msg)
            raise_msg = f"Error getting comments: {str(e)}"
            raise Exception(raise_msg) from e

    def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            comment: Comment text to add (in Markdown format)

        Returns:
            The created comment details

        Raises:
            Exception: If there is an error adding the comment
        """
        try:
            # Convert markdown using helper which returns string (JSON for ADF or wiki markup)
            jira_formatted_comment = self._markdown_to_jira(comment)

            result = self.jira.issue_add_comment(issue_key, jira_formatted_comment)
            if not isinstance(result, dict):
                msg = (
                    "Unexpected return value type from "
                    f"`jira.issue_add_comment`: {type(result)}"
                )
                logger.error(msg)
                raise TypeError(msg)

            # Handle ADF response where body is a dict
            body = result.get("body", "")
            if isinstance(body, dict):
                # For ADF format, return the dict as-is or convert to string
                body_text = str(body)  # Simple string representation
            else:
                body_text = self._clean_text(body)

            return {
                "id": result.get("id"),
                "body": body_text,
                "created": str(parse_date(result.get("created"))),
                "author": result.get("author", {}).get("displayName", "Unknown"),
            }
        except Exception as e:
            error_msg = f"Error adding comment to issue {issue_key}: {str(e)}"
            logger.error(error_msg)
            raise_msg = f"Error adding comment: {str(e)}"
            raise Exception(raise_msg) from e

    def _markdown_to_jira(self, markdown_text: str) -> str | dict[str, Any]:
        """
        Convert Markdown syntax to Jira markup syntax.

        This method uses the preprocessor for consistent conversion between
        Markdown and Jira markup. Returns raw ADF dict for Cloud instances
        rather than JSON string to maintain API compatibility.

        Args:
            markdown_text: Text in Markdown format

        Returns:
            For Cloud instances: Dictionary containing ADF JSON structure
            For Server/DC instances: String in Jira wiki markup format
        """
        # Use the preprocessor directly for conversion
        if not markdown_text:
            return ""

        try:
            # Use the preprocessor - return raw dict/string without JSON conversion
            result = self.preprocessor.markdown_to_jira(markdown_text)
            return result

        except Exception:  # noqa: BLE001
            logger.warning(
                "Error converting markdown to Jira format for text: %s",
                markdown_text[:50] + "..."
                if len(markdown_text) > 50
                else markdown_text,
            )
            # Return the original text if conversion fails
            return markdown_text
