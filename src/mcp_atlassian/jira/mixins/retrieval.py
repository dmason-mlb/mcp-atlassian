"""Issue retrieval operations mixin for Jira client."""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ...exceptions import MCPAtlassianAuthenticationError
from ...models.jira import JiraIssue
from ...utils import parse_date
from ..client import JiraClient
from ..constants import DEFAULT_READ_JIRA_FIELDS
from ..protocols import (
    AttachmentsOperationsProto,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    ProjectsOperationsProto,
    UsersOperationsProto,
)

logger = logging.getLogger("mcp-jira")


class IssueRetrievalMixin(
    JiraClient,
    AttachmentsOperationsProto,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    ProjectsOperationsProto,
    UsersOperationsProto,
):
    """Mixin for Jira issue retrieval operations."""

    def _markdown_to_jira(self, markdown_text: str) -> str | dict[str, Any]:
        """Helper method to convert markdown to Jira format.

        This wraps the FormattingMixin method for convenience.

        Args:
            markdown_text: Text in Markdown format

        Returns:
            For Cloud instances: Dictionary containing ADF JSON structure
            For Server/DC instances: String in Jira wiki markup format
        """
        return self.markdown_to_jira(markdown_text, return_raw_adf=True)

    def get_issue(
        self,
        issue_key: str,
        expand: str | None = None,
        comment_limit: int | str | None = 10,
        fields: str | list[str] | tuple[str, ...] | set[str] | None = None,
        properties: str | list[str] | None = None,
        update_history: bool = True,
    ) -> JiraIssue:
        """
        Get a Jira issue by key.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            expand: Fields to expand in the response
            comment_limit: Maximum number of comments to include, or "all"
            fields: Fields to return (comma-separated string, list, tuple, set, or "*all")
            properties: Issue properties to return (comma-separated string or list)
            update_history: Whether to update the issue view history

        Returns:
            JiraIssue model with issue data and metadata

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Jira API (401/403)
            Exception: If there is an error retrieving the issue
        """
        try:
            # Obtain the projects filter from the config.
            # These should NOT be overridden by the request.
            filter_to_use = self.config.projects_filter

            # Apply projects filter if present
            if filter_to_use:
                # Split projects filter by commas and handle possible whitespace
                projects = [p.strip() for p in filter_to_use.split(",")]

                # Obtain the project key from issue_key
                issue_key_project = issue_key.split("-")[0]

                if issue_key_project not in projects:
                    # If the project key not in the filter, return an empty issue
                    msg = (
                        "Issue with project prefix "
                        f"'{issue_key_project}' are restricted by configuration"
                    )
                    raise ValueError(msg)

            # Determine fields_param: use provided fields or default from constant
            fields_param = fields
            if fields_param is None:
                fields_param = ",".join(DEFAULT_READ_JIRA_FIELDS)
            elif isinstance(fields_param, list | tuple | set):
                fields_param = ",".join(fields_param)

            # Ensure necessary fields are included based on special parameters
            if (
                fields_param == ",".join(DEFAULT_READ_JIRA_FIELDS)
                or fields_param == "*all"
            ):
                # Default fields are being used - preserve the order
                default_fields_list = (
                    fields_param.split(",")
                    if fields_param != "*all"
                    else list(DEFAULT_READ_JIRA_FIELDS)
                )
                additional_fields = []

                # Add appropriate fields based on expand parameter
                if expand:
                    expand_params = expand.split(",")
                    if (
                        "changelog" in expand_params
                        and "changelog" not in default_fields_list
                        and "changelog" not in additional_fields
                    ):
                        additional_fields.append("changelog")
                    if (
                        "renderedFields" in expand_params
                        and "rendered" not in default_fields_list
                        and "rendered" not in additional_fields
                    ):
                        additional_fields.append("rendered")

                # Add appropriate fields based on properties parameter
                if (
                    properties
                    and "properties" not in default_fields_list
                    and "properties" not in additional_fields
                ):
                    additional_fields.append("properties")

                # Combine default fields with additional fields, preserving order
                if additional_fields:
                    fields_param = ",".join(default_fields_list + additional_fields)
            # Handle non-default fields string

            # Build expand parameter if provided
            expand_param = expand

            # Convert properties to proper format if it's a list
            properties_param = properties
            if properties and isinstance(properties, list | tuple | set):
                properties_param = ",".join(properties)

            # Get the issue data with all parameters
            issue = self.jira.get_issue(
                issue_key,
                expand=expand_param,
                fields=fields_param,
                properties=properties_param,
                update_history=update_history,
            )
            if not issue:
                msg = f"Issue {issue_key} not found"
                raise ValueError(msg)
            if not isinstance(issue, dict):
                msg = (
                    f"Unexpected return value type from `jira.get_issue`: {type(issue)}"
                )
                logger.error(msg)
                raise TypeError(msg)

            # Extract fields data, safely handling None
            fields_data = issue.get("fields", {}) or {}

            # Get comments if needed
            if "comment" in fields_data:
                comment_limit_int = self._normalize_comment_limit(comment_limit)
                comments = self._get_issue_comments_if_needed(
                    issue_key, comment_limit_int
                )
                # Add comments to the issue data for processing by the model
                fields_data["comment"]["comments"] = comments

            # Extract epic information
            try:
                epic_info = self._extract_epic_information(issue)
            except Exception as e:
                logger.warning(f"Error extracting epic information: {str(e)}")
                epic_info = {"epic_key": None, "epic_name": None}

            # If this is linked to an epic, add the epic information to the fields
            if epic_info.get("epic_key"):
                try:
                    # Get field IDs for epic fields
                    field_ids = self.get_field_ids_to_epic()

                    # Add epic link field if it doesn't exist
                    if (
                        "epic_link" in field_ids
                        and field_ids["epic_link"] not in fields_data
                    ):
                        fields_data[field_ids["epic_link"]] = epic_info["epic_key"]

                    # Add epic name field if it doesn't exist
                    if (
                        epic_info.get("epic_name")
                        and "epic_name" in field_ids
                        and field_ids["epic_name"] not in fields_data
                    ):
                        fields_data[field_ids["epic_name"]] = epic_info["epic_name"]
                except Exception as e:
                    logger.warning(f"Error setting epic fields: {str(e)}")

            # Update the issue data with the fields
            issue["fields"] = fields_data

            # Create and return the JiraIssue model, passing requested_fields
            return JiraIssue.from_api_response(
                issue,
                base_url=self.config.url if hasattr(self, "config") else None,
                requested_fields=fields,
            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Jira API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error retrieving issue {issue_key}: {error_msg}")
            raise Exception(f"Error retrieving issue {issue_key}: {error_msg}") from e

    def _normalize_comment_limit(self, comment_limit: int | str | None) -> int | None:
        """
        Normalize the comment limit to an integer or None.

        Args:
            comment_limit: The comment limit as int, string, or None

        Returns:
            Normalized comment limit as int or None
        """
        if comment_limit is None:
            return None

        if isinstance(comment_limit, int):
            return comment_limit

        if comment_limit == "all":
            return None  # No limit

        # Try to convert to int
        try:
            return int(comment_limit)
        except ValueError:
            # If conversion fails, default to 10
            return 10

    def _get_issue_comments_if_needed(
        self, issue_key: str, comment_limit: int | None
    ) -> list[dict]:
        """
        Get comments for an issue if needed.

        Args:
            issue_key: The issue key
            comment_limit: Maximum number of comments to include

        Returns:
            List of comments
        """
        if comment_limit is None or comment_limit > 0:
            try:
                response = self.jira.issue_get_comments(issue_key)
                if not isinstance(response, dict):
                    msg = f"Unexpected return value type from `jira.issue_get_comments`: {type(response)}"
                    logger.error(msg)
                    raise TypeError(msg)

                comments = response["comments"]

                # Limit comments if needed
                if comment_limit is not None:
                    comments = comments[:comment_limit]

                return comments
            except Exception as e:
                logger.warning(f"Error getting comments for {issue_key}: {str(e)}")
                return []
        return []

    def _extract_epic_information(self, issue: dict) -> dict[str, str | None]:
        """
        Extract epic information from an issue.

        Args:
            issue: The issue data

        Returns:
            Dictionary with epic information
        """
        # Initialize with default values
        epic_info = {
            "epic_key": None,
            "epic_name": None,
            "epic_summary": None,
            "is_epic": False,
        }

        try:
            fields = issue.get("fields", {}) or {}
            issue_type = fields.get("issuetype", {}).get("name", "").lower()

            # Get field IDs for epic fields
            try:
                field_ids = self.get_field_ids_to_epic()
            except Exception as e:
                logger.warning(f"Error getting Jira fields: {str(e)}")
                field_ids = {}

            # Check if this is an epic
            if issue_type == "epic":
                epic_info["is_epic"] = True

                # Use the discovered field ID for epic name
                if "epic_name" in field_ids and field_ids["epic_name"] in fields:
                    epic_info["epic_name"] = fields.get(field_ids["epic_name"], "")

            # If not an epic, check for epic link
            elif "epic_link" in field_ids:
                epic_link_field = field_ids["epic_link"]

                if epic_link_field in fields and fields[epic_link_field]:
                    epic_key = fields[epic_link_field]
                    epic_info["epic_key"] = epic_key

                    # Try to get epic details
                    try:
                        epic = self.jira.get_issue(
                            epic_key,
                            expand=None,
                            fields=None,
                            properties=None,
                            update_history=True,
                        )
                        if not isinstance(epic, dict):
                            msg = f"Unexpected return value type from `jira.get_issue`: {type(epic)}"
                            logger.error(msg)
                            raise TypeError(msg)

                        epic_fields = epic.get("fields", {}) or {}

                        # Get epic name using the discovered field ID
                        if "epic_name" in field_ids:
                            epic_info["epic_name"] = epic_fields.get(
                                field_ids["epic_name"], ""
                            )

                        epic_info["epic_summary"] = epic_fields.get("summary", "")
                    except Exception as e:
                        logger.warning(
                            f"Error getting epic details for {epic_key}: {str(e)}"
                        )
        except Exception as e:
            logger.warning(f"Error extracting epic information: {str(e)}")

        return epic_info

    def _format_issue_content(
        self,
        issue_key: str,
        issue: dict,
        description: str,
        comments: list[dict],
        created_date: str,
        epic_info: dict[str, str | None],
    ) -> str:
        """
        Format issue content for display.

        Args:
            issue_key: The issue key
            issue: The issue data
            description: The issue description
            comments: The issue comments
            created_date: The formatted creation date
            epic_info: Epic information

        Returns:
            Formatted issue content
        """
        fields = issue.get("fields", {})

        # Basic issue information
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        issue_type = fields.get("issuetype", {}).get("name", "")

        # Format content
        content = [f"# {issue_key}: {summary}"]
        content.append(f"**Type**: {issue_type}")
        content.append(f"**Status**: {status}")
        content.append(f"**Created**: {created_date}")

        # Add reporter
        reporter = fields.get("reporter", {})
        reporter_name = reporter.get("displayName", "") or reporter.get("name", "")
        if reporter_name:
            content.append(f"**Reporter**: {reporter_name}")

        # Add assignee
        assignee = fields.get("assignee", {})
        assignee_name = assignee.get("displayName", "") or assignee.get("name", "")
        if assignee_name:
            content.append(f"**Assignee**: {assignee_name}")

        # Add epic information
        if epic_info["is_epic"]:
            content.append(f"**Epic Name**: {epic_info['epic_name']}")
        elif epic_info["epic_key"]:
            content.append(
                f"**Epic**: [{epic_info['epic_key']}] {epic_info['epic_summary']}"
            )

        # Add description
        if description:
            content.append("\n## Description\n")
            content.append(description)

        # Add comments
        if comments:
            content.append("\n## Comments\n")
            for comment in comments:
                author = comment.get("author", {})
                author_name = author.get("displayName", "") or author.get("name", "")
                comment_body = self._clean_text(comment.get("body", ""))

                if author_name and comment_body:
                    comment_date = comment.get("created", "")
                    if comment_date:
                        comment_date = parse_date(comment_date)
                        content.append(f"**{author_name}** ({comment_date}):")
                    else:
                        content.append(f"**{author_name}**:")

                    content.append(f"{comment_body}\n")

        return "\n".join(content)

    def _create_issue_metadata(
        self,
        issue_key: str,
        issue: dict,
        comments: list[dict],
        created_date: str,
        epic_info: dict[str, str | None],
    ) -> dict[str, Any]:
        """
        Create metadata for a Jira issue.

        Args:
            issue_key: The issue key
            issue: The issue data
            comments: The issue comments
            created_date: The formatted creation date
            epic_info: Epic information

        Returns:
            Metadata dictionary
        """
        fields = issue.get("fields", {})

        # Initialize metadata
        metadata = {
            "key": issue_key,
            "title": fields.get("summary", ""),
            "status": fields.get("status", {}).get("name", ""),
            "type": fields.get("issuetype", {}).get("name", ""),
            "created": created_date,
            "url": f"{self.config.url}/browse/{issue_key}",
        }

        # Add assignee if available
        assignee = fields.get("assignee", {})
        if assignee:
            metadata["assignee"] = assignee.get("displayName", "") or assignee.get(
                "name", ""
            )

        # Add epic information
        if epic_info["is_epic"]:
            metadata["is_epic"] = True
            metadata["epic_name"] = epic_info["epic_name"]
        elif epic_info["epic_key"]:
            metadata["epic_key"] = epic_info["epic_key"]
            metadata["epic_name"] = epic_info["epic_name"]
            metadata["epic_summary"] = epic_info["epic_summary"]

        # Add comment count
        metadata["comment_count"] = len(comments)

        return metadata
