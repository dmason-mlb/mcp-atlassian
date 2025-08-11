"""Issue batch operations mixin for Jira client."""

import logging
from collections import defaultdict
from typing import Any

from ...models.jira import JiraChangelog, JiraIssue
from ..client import JiraClient
from ..protocols import (
    IssueOperationsProto,
    UsersOperationsProto,
)

logger = logging.getLogger("mcp-jira")


class IssueBatchMixin(
    JiraClient,
    IssueOperationsProto,
    UsersOperationsProto,
):
    """Mixin for Jira issue batch operations."""

    def batch_create_issues(
        self,
        issues: list[dict[str, Any]],
        validate_only: bool = False,
    ) -> list[JiraIssue]:
        """Create multiple Jira issues in a batch.

        Args:
            issues: List of issue dictionaries, each containing:
                - project_key (str): Key of the project
                - summary (str): Issue summary
                - issue_type (str): Type of issue
                - description (str, optional): Issue description
                - assignee (str, optional): Username of assignee
                - components (list[str], optional): List of component names
                - **kwargs: Additional fields specific to your Jira instance
            validate_only: If True, only validates the issues without creating them

        Returns:
            List of created JiraIssue objects

        Raises:
            ValueError: If any required fields are missing or invalid
            MCPAtlassianAuthenticationError: If authentication fails
        """
        if not issues:
            return []

        # Prepare issues for bulk creation
        issue_updates = []
        for issue_data in issues:
            try:
                # Extract and validate required fields
                project_key = issue_data.pop("project_key", None)
                summary = issue_data.pop("summary", None)
                issue_type = issue_data.pop("issue_type", None)
                description = issue_data.pop("description", "")
                assignee = issue_data.pop("assignee", None)
                components = issue_data.pop("components", None)

                # Validate required fields
                if not all([project_key, summary, issue_type]):
                    raise ValueError(
                        f"Missing required fields for issue: {project_key=}, {summary=}, {issue_type=}"
                    )

                # Prepare fields dictionary
                fields = {
                    "project": {"key": project_key},
                    "summary": summary,
                    "issuetype": {"name": issue_type},
                }

                # Add optional fields
                if description:
                    # Convert description from Markdown to Jira format (ADF or wiki markup)
                    description_content = self.markdown_to_jira(description)
                    fields["description"] = description_content

                # Add assignee if provided
                if assignee:
                    try:
                        # _get_account_id now returns the correct identifier (accountId for cloud, name for server)
                        assignee_identifier = self._get_account_id(assignee)
                        self._add_assignee_to_fields(fields, assignee_identifier)
                    except ValueError as e:
                        logger.warning(f"Could not assign issue: {str(e)}")

                # Add components if provided
                if components:
                    if isinstance(components, list):
                        valid_components = [
                            comp_name.strip()
                            for comp_name in components
                            if isinstance(comp_name, str) and comp_name.strip()
                        ]
                        if valid_components:
                            fields["components"] = [
                                {"name": comp_name} for comp_name in valid_components
                            ]

                # Add any remaining custom fields
                self._process_additional_fields(fields, issue_data)

                if validate_only:
                    # For validation, just log the issue that would be created
                    logger.info(
                        f"Validated issue creation: {project_key} - {summary} ({issue_type})"
                    )
                    continue

                # Add to bulk creation list
                issue_updates.append({"fields": fields})

            except Exception as e:
                logger.error(f"Failed to prepare issue for creation: {str(e)}")
                if not issue_updates:
                    raise

        if validate_only:
            return []

        try:
            # Call Jira's bulk create endpoint
            response = self.jira.create_issues(issue_updates)
            if not isinstance(response, dict):
                msg = f"Unexpected return value type from `jira.create_issues`: {type(response)}"
                logger.error(msg)
                raise TypeError(msg)

            # Process results
            created_issues = []
            for issue_info in response.get("issues", []):
                issue_key = issue_info.get("key")
                if issue_key:
                    try:
                        # Fetch the full issue data
                        issue_data = self.jira.get_issue(issue_key)
                        if not isinstance(issue_data, dict):
                            msg = f"Unexpected return value type from `jira.get_issue`: {type(issue_data)}"
                            logger.error(msg)
                            raise TypeError(msg)

                        created_issues.append(
                            JiraIssue.from_api_response(
                                issue_data,
                                base_url=self.config.url
                                if hasattr(self, "config")
                                else None,
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Error fetching created issue {issue_key}: {str(e)}"
                        )

            # Log any errors from the bulk creation
            errors = response.get("errors", [])
            if errors:
                for error in errors:
                    logger.error(f"Bulk creation error: {error}")

            return created_issues

        except Exception as e:
            logger.error(f"Error in bulk issue creation: {str(e)}")
            raise

    def batch_get_changelogs(
        self, issue_ids_or_keys: list[str], fields: list[str] | None = None
    ) -> list[JiraIssue]:
        """
        Get changelogs for multiple issues in a batch. Repeatly fetch data if necessary.

        Warning:
            This function is only avaiable on Jira Cloud.

        Args:
            issue_ids_or_keys: List of issue IDs or keys
            fields: Filter the changelogs by fields, e.g. ['status', 'assignee']. Default to None for all fields.

        Returns:
            List of JiraIssue objects that only contain changelogs and id
        """

        if not self.config.is_cloud:
            error_msg = "Batch get issue changelogs is only available on Jira Cloud."
            logger.error(error_msg)
            raise NotImplementedError(error_msg)

        # Get paged api results
        paged_api_results = self.get_paged(
            method="post",
            url=self.jira.resource_url("changelog/bulkfetch"),
            params_or_json={
                "fieldIds": fields,
                "issueIdsOrKeys": issue_ids_or_keys,
            },
        )

        # Save (issue_id, changelogs)
        issue_changelog_results: defaultdict[str, list[JiraChangelog]] = defaultdict(
            list
        )

        for api_result in paged_api_results:
            for data in api_result.get("issueChangeLogs", []):
                issue_id = data.get("issueId", "")
                changelogs = [
                    JiraChangelog.from_api_response(changelog_data)
                    for changelog_data in data.get("changeHistories", [])
                ]

                issue_changelog_results[issue_id].extend(changelogs)

        issues = [
            JiraIssue(id=issue_id, changelogs=changelogs)
            for issue_id, changelogs in issue_changelog_results.items()
        ]

        return issues
