"""JIRA v3 REST API client implementation."""

import logging
from typing import Any
from urllib.parse import quote

from .base import BaseRESTClient

logger = logging.getLogger(__name__)


class JiraV3Client(BaseRESTClient):
    """JIRA v3 REST API client with native ADF support."""

    def __init__(self, *args, **kwargs):
        """Initialize JIRA v3 client."""
        super().__init__(*args, **kwargs)

        # JIRA-specific headers
        self.session.headers.update(
            {
                "X-Atlassian-Token": "no-check",  # Disable XSRF check
            }
        )

    # === User Operations ===

    def get_myself(self) -> dict[str, Any]:
        """Get information about the current user.

        Returns:
            User information
        """
        return self.get("/rest/api/3/myself")

    def get_user(
        self,
        account_id: str | None = None,
        username: str | None = None,
        key: str | None = None,
    ) -> dict[str, Any]:
        """Get user details.

        Args:
            account_id: User account ID (Cloud)
            username: Username (Server/DC)
            key: User key (Server/DC)

        Returns:
            User information
        """
        params = {}
        if account_id:
            params["accountId"] = account_id
        if username:
            params["username"] = username
        if key:
            params["key"] = key

        return self.get("/rest/api/3/user", params=params)

    def search_users(
        self,
        query: str,
        start_at: int = 0,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Search for users.

        Args:
            query: Search query
            start_at: Starting index
            max_results: Maximum results

        Returns:
            List of users
        """
        params = {
            "query": query,
            "startAt": start_at,
            "maxResults": max_results,
        }
        return self.get("/rest/api/3/user/search", params=params)

    # === Issue Operations ===

    def get_issue(
        self,
        issue_key: str,
        fields: list[str] | None = None,
        expand: list[str] | None = None,
        properties: list[str] | None = None,
        update_history: bool = True,
    ) -> dict[str, Any]:
        """Get issue details.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            fields: List of fields to return
            expand: List of fields to expand
            properties: List of properties to return
            update_history: Whether to update the user's issue view history

        Returns:
            Issue data
        """
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        if expand:
            params["expand"] = ",".join(expand)
        if properties:
            params["properties"] = ",".join(properties)
        if not update_history:
            params["updateHistory"] = "false"

        return self.get(f"/rest/api/3/issue/{quote(issue_key)}", params=params)

    def create_issue(
        self,
        fields: dict[str, Any],
        update: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new issue.

        Args:
            fields: Issue fields (includes project, issuetype, summary, etc.)
            update: Update operations

        Returns:
            Created issue data
        """
        data = {"fields": fields}
        if update:
            data["update"] = update

        return self.post("/rest/api/3/issue", json_data=data)

    def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
        notify_users: bool = True,
        override_screen_security: bool = False,
        override_editable_flag: bool = False,
    ) -> None:
        """Update an issue.

        Args:
            issue_key: Issue key
            fields: Fields to update
            update: Update operations
            notify_users: Whether to notify users
            override_screen_security: Override screen security
            override_editable_flag: Override editable flag
        """
        data = {}
        if fields:
            data["fields"] = fields
        if update:
            data["update"] = update

        params = {
            "notifyUsers": notify_users,
            "overrideScreenSecurity": override_screen_security,
            "overrideEditableFlag": override_editable_flag,
        }

        self.put(
            f"/rest/api/3/issue/{quote(issue_key)}",
            json_data=data,
            params=params,
        )

    def delete_issue(
        self,
        issue_key: str,
        delete_subtasks: bool = True,
    ) -> None:
        """Delete an issue.

        Args:
            issue_key: Issue key
            delete_subtasks: Whether to delete subtasks
        """
        params = {"deleteSubtasks": delete_subtasks}
        self.delete(f"/rest/api/3/issue/{quote(issue_key)}", params=params)

    def create_issues(
        self,
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create multiple issues in bulk.

        Args:
            issues: List of issue data (each with fields and optional update)

        Returns:
            Bulk creation result
        """
        data = {"issueUpdates": issues}
        return self.post("/rest/api/3/issue/bulk", json_data=data)

    # === Comments ===

    def get_comments(
        self,
        issue_key: str,
        start_at: int = 0,
        max_results: int = 50,
        order_by: str | None = None,
        expand: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get issue comments.

        Args:
            issue_key: Issue key
            start_at: Starting index
            max_results: Maximum results
            order_by: Sort order
            expand: Fields to expand

        Returns:
            Comments data with pagination
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if order_by:
            params["orderBy"] = order_by
        if expand:
            params["expand"] = ",".join(expand)

        return self.get(
            f"/rest/api/3/issue/{quote(issue_key)}/comment",
            params=params,
        )

    def add_comment(
        self,
        issue_key: str,
        body: str | dict[str, Any],
        visibility: dict[str, str] | None = None,
        properties: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_key: Issue key
            body: Comment body (string for wiki markup, dict for ADF)
            visibility: Visibility restrictions
            properties: Comment properties

        Returns:
            Created comment data
        """
        data = {"body": body}
        if visibility:
            data["visibility"] = visibility
        if properties:
            data["properties"] = properties

        return self.post(
            f"/rest/api/3/issue/{quote(issue_key)}/comment",
            json_data=data,
        )

    # === Transitions ===

    def get_transitions(self, issue_key: str) -> dict[str, Any]:
        """Get available transitions for an issue.

        Args:
            issue_key: Issue key

        Returns:
            Available transitions
        """
        return self.get(f"/rest/api/3/issue/{quote(issue_key)}/transitions")

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        fields: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
        comment: dict[str, Any] | None = None,
        history_metadata: dict[str, Any] | None = None,
        properties: list[dict[str, Any]] | None = None,
    ) -> None:
        """Transition an issue to a new status.

        Args:
            issue_key: Issue key
            transition_id: Transition ID
            fields: Fields to update during transition
            update: Update operations
            comment: Comment to add
            history_metadata: History metadata
            properties: Transition properties
        """
        data = {"transition": {"id": transition_id}}
        if fields:
            data["fields"] = fields
        if update:
            data["update"] = update
        if comment:
            data["comment"] = comment
        if history_metadata:
            data["historyMetadata"] = history_metadata
        if properties:
            data["properties"] = properties

        self.post(
            f"/rest/api/3/issue/{quote(issue_key)}/transitions",
            json_data=data,
        )

    # === Search ===

    def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: list[str] | None = None,
        properties: list[str] | None = None,
        fields_by_keys: bool = False,
        validate_query: bool = True,
    ) -> dict[str, Any]:
        """Search for issues using JQL.

        Args:
            jql: JQL query string
            start_at: Starting index
            max_results: Maximum results
            fields: Fields to return
            expand: Fields to expand
            properties: Properties to return
            fields_by_keys: Return fields by keys
            validate_query: Validate the JQL query

        Returns:
            Search results with pagination
        """
        data = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fieldsByKeys": fields_by_keys,
            "validateQuery": validate_query,
        }
        if fields:
            data["fields"] = fields
        if expand:
            data["expand"] = expand
        if properties:
            data["properties"] = properties

        return self.post("/rest/api/3/search", json_data=data)

    # === Projects ===

    def get_projects(
        self,
        start_at: int = 0,
        max_results: int = 50,
        order_by: str | None = None,
        expand: list[str] | None = None,
        recent: int | None = None,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get all projects.

        Args:
            start_at: Starting index
            max_results: Maximum results
            order_by: Sort order
            expand: Fields to expand
            recent: Number of recent projects
            properties: Properties to return

        Returns:
            Projects data with pagination
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if order_by:
            params["orderBy"] = order_by
        if expand:
            params["expand"] = ",".join(expand)
        if recent is not None:
            params["recent"] = recent
        if properties:
            params["properties"] = ",".join(properties)

        return self.get("/rest/api/3/project", params=params)

    def get_project(
        self,
        project_key: str,
        expand: list[str] | None = None,
        properties: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get project details.

        Args:
            project_key: Project key
            expand: Fields to expand
            properties: Properties to return

        Returns:
            Project data
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)
        if properties:
            params["properties"] = ",".join(properties)

        return self.get(f"/rest/api/3/project/{quote(project_key)}", params=params)

    # === Fields ===

    def get_fields(self) -> list[dict[str, Any]]:
        """Get all fields.

        Returns:
            List of field definitions
        """
        return self.get("/rest/api/3/field")

    # === Worklogs ===

    def get_worklogs(
        self,
        issue_key: str,
        start_at: int = 0,
        max_results: int = 50,
        expand: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get issue worklogs.

        Args:
            issue_key: Issue key
            start_at: Starting index
            max_results: Maximum results
            expand: Fields to expand

        Returns:
            Worklogs data with pagination
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if expand:
            params["expand"] = ",".join(expand)

        return self.get(
            f"/rest/api/3/issue/{quote(issue_key)}/worklog",
            params=params,
        )

    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        started: str,
        comment: str | dict[str, Any] | None = None,
        visibility: dict[str, str] | None = None,
        author: dict[str, str] | None = None,
        update_author: dict[str, str] | None = None,
        properties: list[dict[str, Any]] | None = None,
        notify_users: bool = True,
        adjust_estimate: str = "auto",
        new_estimate: str | None = None,
        reduce_by: str | None = None,
        expand: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add a worklog to an issue.

        Args:
            issue_key: Issue key
            time_spent: Time spent (e.g., "3h 30m")
            started: Start time (ISO 8601)
            comment: Worklog comment
            visibility: Visibility restrictions
            author: Author details
            update_author: Update author details
            properties: Worklog properties
            notify_users: Whether to notify users
            adjust_estimate: How to adjust estimate
            new_estimate: New estimate
            reduce_by: Reduce estimate by
            expand: Fields to expand

        Returns:
            Created worklog data
        """
        data = {
            "timeSpent": time_spent,
            "started": started,
        }
        if comment:
            data["comment"] = comment
        if visibility:
            data["visibility"] = visibility
        if author:
            data["author"] = author
        if update_author:
            data["updateAuthor"] = update_author
        if properties:
            data["properties"] = properties

        params = {
            "notifyUsers": notify_users,
            "adjustEstimate": adjust_estimate,
        }
        if new_estimate:
            params["newEstimate"] = new_estimate
        if reduce_by:
            params["reduceBy"] = reduce_by
        if expand:
            params["expand"] = ",".join(expand)

        return self.post(
            f"/rest/api/3/issue/{quote(issue_key)}/worklog",
            json_data=data,
            params=params,
        )

    # === Links ===

    def get_issue_link_types(self) -> dict[str, Any]:
        """Get all issue link types.

        Returns:
            Issue link types
        """
        return self.get("/rest/api/3/issueLinkType")

    def create_issue_link(
        self,
        inward_issue_key: str,
        outward_issue_key: str,
        link_type: str,
        comment: dict[str, Any] | None = None,
    ) -> None:
        """Create a link between two issues.

        Args:
            inward_issue_key: Inward issue key
            outward_issue_key: Outward issue key
            link_type: Link type name
            comment: Optional comment
        """
        data = {
            "inwardIssue": {"key": inward_issue_key},
            "outwardIssue": {"key": outward_issue_key},
            "type": {"name": link_type},
        }
        if comment:
            data["comment"] = comment

        self.post("/rest/api/3/issueLink", json_data=data)

    def delete_issue_link(self, link_id: str) -> None:
        """Delete an issue link.

        Args:
            link_id: Link ID
        """
        self.delete(f"/rest/api/3/issueLink/{link_id}")

    def create_remote_issue_link(
        self,
        issue_key: str,
        url: str,
        title: str,
        summary: str | None = None,
        icon_url: str | None = None,
        relationship: str | None = None,
        global_id: str | None = None,
        application: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a remote issue link.

        Args:
            issue_key: Issue key
            url: Remote URL
            title: Link title
            summary: Link summary
            icon_url: Icon URL
            relationship: Relationship type
            global_id: Global ID
            application: Application details

        Returns:
            Created remote link data
        """
        data = {
            "object": {
                "url": url,
                "title": title,
            }
        }
        if summary:
            data["object"]["summary"] = summary
        if icon_url:
            data["object"]["icon"] = {"url16x16": icon_url}
        if relationship:
            data["relationship"] = relationship
        if global_id:
            data["globalId"] = global_id
        if application:
            data["application"] = application

        return self.post(
            f"/rest/api/3/issue/{quote(issue_key)}/remotelink",
            json_data=data,
        )

    # === Versions ===

    def get_project_versions(
        self,
        project_key: str,
        expand: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get project versions.

        Args:
            project_key: Project key
            expand: Fields to expand

        Returns:
            List of versions
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        return self.get(
            f"/rest/api/3/project/{quote(project_key)}/versions",
            params=params,
        )

    def create_version(
        self,
        project_key: str,
        name: str,
        description: str | None = None,
        archived: bool = False,
        released: bool = False,
        start_date: str | None = None,
        release_date: str | None = None,
    ) -> dict[str, Any]:
        """Create a project version.

        Args:
            project_key: Project key
            name: Version name
            description: Version description
            archived: Whether archived
            released: Whether released
            start_date: Start date (YYYY-MM-DD)
            release_date: Release date (YYYY-MM-DD)

        Returns:
            Created version data
        """
        data = {
            "project": project_key,
            "name": name,
            "archived": archived,
            "released": released,
        }
        if description:
            data["description"] = description
        if start_date:
            data["startDate"] = start_date
        if release_date:
            data["releaseDate"] = release_date

        return self.post("/rest/api/3/version", json_data=data)

    # === Attachments ===

    def get_attachment(self, attachment_id: str) -> dict[str, Any]:
        """Get attachment metadata.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment metadata
        """
        return self.get(f"/rest/api/3/attachment/{attachment_id}")

    def download_attachment(
        self,
        attachment_id: str,
        redirect: bool = True,
    ) -> bytes | str:
        """Download attachment content.

        Args:
            attachment_id: Attachment ID
            redirect: Follow redirect

        Returns:
            Attachment content or redirect URL
        """
        params = {"redirect": redirect}
        response = self.get(
            f"/rest/api/3/attachment/content/{attachment_id}",
            params=params,
            raw_response=True,
        )

        if redirect:
            return response.content
        else:
            # Return the redirect URL from Location header
            return response.headers.get("Location", "")

    # === Bulk Operations ===

    def get_issues_by_keys(
        self,
        issue_keys: list[str],
        fields: list[str] | None = None,
        expand: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get multiple issues by their keys.

        Args:
            issue_keys: List of issue keys
            fields: Fields to return
            expand: Fields to expand

        Returns:
            List of issues
        """
        # Use JQL to fetch multiple issues
        jql = f"key IN ({','.join(issue_keys)})"
        result = self.search_issues(
            jql=jql,
            max_results=len(issue_keys),
            fields=fields,
            expand=expand,
        )
        return result.get("issues", [])
