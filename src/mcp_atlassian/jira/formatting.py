"""Module for Jira content formatting utilities."""

import html
import logging
import re
from typing import Any, Literal, overload

from ..preprocessing.jira import JiraPreprocessor
from .client import JiraClient
from .protocols import (
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    UsersOperationsProto,
)

logger = logging.getLogger("mcp-jira")


class FormattingMixin(
    JiraClient,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    UsersOperationsProto,
):
    """Mixin for Jira content formatting operations.

    This mixin provides utilities for converting between different formats,
    formatting issue content for display, parsing dates, and sanitizing content.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the FormattingMixin.

        Args:
            *args: Positional arguments for the JiraClient
            **kwargs: Keyword arguments for the JiraClient
        """
        super().__init__(*args, **kwargs)

        # Use the JiraPreprocessor with the base URL from the client
        base_url = ""
        if hasattr(self, "config") and hasattr(self.config, "url"):
            base_url = self.config.url
        self.preprocessor = JiraPreprocessor(base_url=base_url)

    def _convert_adf_to_json(self, adf_dict: dict[str, Any]) -> str:
        """Convert ADF dict to JSON string for API compatibility.

        Args:
            adf_dict: ADF dictionary object

        Returns:
            JSON string representation of the ADF dict
        """
        import json
        return json.dumps(adf_dict)

    @overload
    def markdown_to_jira(
        self, markdown_text: str, *, return_raw_adf: Literal[False] = ...
    ) -> str:
        """When return_raw_adf=False (default), always returns string."""
        ...

    @overload
    def markdown_to_jira(
        self, markdown_text: str, *, return_raw_adf: Literal[True]
    ) -> str | dict[str, Any]:
        """When return_raw_adf=True, returns dict for ADF or str for wiki."""
        ...

    def markdown_to_jira(
        self, markdown_text: str, *, return_raw_adf: bool = False
    ) -> str | dict[str, Any]:
        """
        Convert Markdown syntax to Jira markup syntax.

        This method uses the TextPreprocessor implementation for consistent
        conversion between Markdown and Jira markup.

        Args:
            markdown_text: Text in Markdown format
            return_raw_adf: If True, returns raw ADF dict for Cloud instances.
                If False, returns JSON string for API compatibility.

        Returns:
            For Cloud instances: ADF dict (if return_raw_adf=True) or JSON string
            For Server/DC instances: String in Jira wiki markup format
        """
        if not markdown_text:
            return ""

        try:
            # Use the existing preprocessor
            result = self.preprocessor.markdown_to_jira(markdown_text)

            # Handle ADF dict objects for Cloud instances
            if isinstance(result, dict):
                if return_raw_adf:
                    return result  # Return raw dict for internal use
                else:
                    # Return JSON string for API compatibility
                    return self._convert_adf_to_json(result)

            # Return string result for Server/DC instances
            return str(result)

        except Exception:  # noqa: BLE001
            logger.warning(
                "Error converting markdown to Jira format for text: %s",
                markdown_text[:50] + "..." if len(markdown_text) > 50 else markdown_text
            )
            # Return the original text if conversion fails
            return markdown_text

    def format_issue_content(
        self,
        issue_key: str,
        issue: dict[str, Any],
        description: str,
        comments: list[dict[str, Any]],
        created_date: str,
        epic_info: dict[str, str | None],
    ) -> str:
        """
        Format the issue content for display.

        Args:
            issue_key: The issue key
            issue: The issue data from Jira
            description: Processed description text
            comments: List of comment dictionaries
            created_date: Formatted created date
            epic_info: Dictionary with epic_key and epic_name

        Returns:
            Formatted content string
        """
        # Basic issue information
        content = f"""Issue: {issue_key}
Title: {issue["fields"].get("summary", "")}
Type: {issue["fields"]["issuetype"]["name"]}
Status: {issue["fields"]["status"]["name"]}
Created: {created_date}
"""

        # Add Epic information if available
        if epic_info.get("epic_key"):
            content += f"Epic: {epic_info['epic_key']}"
            if epic_info.get("epic_name"):
                content += f" - {epic_info['epic_name']}"
            content += "\n"

        content += f"""
Description:
{description}
"""
        # Add comments if present
        if comments:
            content += "\nComments:\n" + "\n".join(
                [f"{c['created']} - {c['author']}: {c['body']}" for c in comments]
            )

        return content

    def create_issue_metadata(
        self,
        issue_key: str,
        issue: dict[str, Any],
        comments: list[dict[str, Any]],
        created_date: str,
        epic_info: dict[str, str | None],
    ) -> dict[str, Any]:
        """
        Create metadata for the issue document.

        Args:
            issue_key: The issue key
            issue: The issue data from Jira
            comments: List of comment dictionaries
            created_date: Formatted created date
            epic_info: Dictionary with epic_key and epic_name

        Returns:
            Metadata dictionary
        """
        # Extract fields
        fields = issue.get("fields", {})

        # Basic metadata
        metadata = {
            "key": issue_key,
            "summary": fields.get("summary", ""),
            "type": fields.get("issuetype", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", ""),
            "created": created_date,
            "source": "jira",
        }

        # Add assignee if present
        if fields.get("assignee"):
            metadata["assignee"] = fields["assignee"].get(
                "displayName", fields["assignee"].get("name", "")
            )

        # Add reporter if present
        if fields.get("reporter"):
            metadata["reporter"] = fields["reporter"].get(
                "displayName", fields["reporter"].get("name", "")
            )

        # Add priority if present
        if fields.get("priority"):
            metadata["priority"] = fields["priority"].get("name", "")

        # Add Epic information to metadata if available
        if epic_info.get("epic_key"):
            metadata["epic_key"] = epic_info["epic_key"]
            if epic_info.get("epic_name"):
                metadata["epic_name"] = epic_info["epic_name"]

        # Add project information
        if fields.get("project"):
            metadata["project"] = fields["project"].get("key", "")
            metadata["project_name"] = fields["project"].get("name", "")

        # Add comment count
        metadata["comment_count"] = len(comments)

        return metadata

    def extract_epic_information(
        self, issue: dict[str, Any]
    ) -> dict[str, None] | dict[str, str]:
        """
        Extract epic information from issue data.

        Args:
            issue: Issue data dictionary

        Returns:
            Dictionary containing epic_key and epic_name (or None if not found)
        """
        epic_info = {"epic_key": None, "epic_name": None}

        # Check if the issue has fields
        if "fields" not in issue:
            return epic_info

        fields = issue["fields"]

        # Try to get the epic link from issue
        # (requires the correct field ID which varies across instances)
        # Use the field discovery mechanism if available
        try:
            field_ids = self.get_field_ids_to_epic()

            # Get the epic link field ID
            epic_link_field = field_ids.get("Epic Link")
            if epic_link_field and epic_link_field in fields:
                epic_value = fields[epic_link_field]
                if epic_value:
                    epic_info["epic_key"] = epic_value

                    # If the issue is linked to an epic, try to get the epic name
                    if hasattr(self, "get_issue") and epic_info["epic_key"]:  # type: ignore[unreachable]
                        try:  # type: ignore[unreachable]
                            epic_issue = self.get_issue(epic_info["epic_key"])
                            epic_fields = epic_issue.get("fields", {})

                            # Get the epic name field ID
                            epic_name_field = field_ids.get("Epic Name")
                            if epic_name_field and epic_name_field in epic_fields:
                                epic_info["epic_name"] = epic_fields[epic_name_field]

                        except Exception:  # noqa: BLE001
                            logger.warning(
                                "Error getting epic details for epic key: %s",
                                epic_info["epic_key"]
                            )

        except Exception:  # noqa: BLE001
            logger.warning("Error extracting epic information from issue")

        return epic_info

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content by removing HTML tags.

        Args:
            html_content: HTML content to sanitize

        Returns:
            Plaintext content with HTML tags removed
        """
        if not html_content:
            return ""

        try:
            # Remove HTML tags
            plain_text = re.sub(r"<[^>]+>", "", html_content)
            # Decode HTML entities
            plain_text = html.unescape(plain_text)
            # Normalize whitespace
            plain_text = re.sub(r"\s+", " ", plain_text).strip()

            return plain_text

        except Exception:  # noqa: BLE001
            logger.warning("Error sanitizing HTML content")
            return html_content

    def sanitize_transition_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize fields to ensure they're valid for the Jira API.

        This is used for transition data to properly format field values.

        Args:
            fields: Dictionary of fields to sanitize

        Returns:
            Dictionary of sanitized fields
        """
        sanitized_fields = {}

        for key, value in fields.items():
            # Skip empty values
            if value is None:
                continue

            # Handle assignee field specially
            if key in ["assignee", "reporter"]:
                # If the value is already a dictionary, use it as is
                if isinstance(value, dict) and "accountId" in value:
                    sanitized_fields[key] = value
                else:
                    # Otherwise, look up the account ID
                    if not isinstance(value, str):
                        logger.warning(f"Invalid assignee value: {value}")
                        continue

                    try:
                        account_id = self._get_account_id(value)
                        if account_id:
                            sanitized_fields[key] = {"accountId": account_id}
                    except Exception:  # noqa: BLE001
                        logger.warning(
                            "Error getting account ID for user: %s", value
                        )
            # All other fields pass through as is
            else:
                sanitized_fields[key] = value

        return sanitized_fields

    def add_comment_to_transition_data(
        self, transition_data: dict[str, Any], comment: str | None
    ) -> dict[str, Any]:
        """
        Add a comment to transition data.

        Args:
            transition_data: Transition data dictionary
            comment: Comment text (in Markdown format) or None

        Returns:
            Updated transition data
        """
        if not comment:
            return transition_data

        # Convert markdown to Jira format (return ADF dict for transitions)
        jira_formatted_comment = self.markdown_to_jira(comment, return_raw_adf=True)

        # Add the comment to the transition data
        transition_data["update"] = {
            "comment": [{"add": {"body": jira_formatted_comment}}]
        }

        return transition_data
