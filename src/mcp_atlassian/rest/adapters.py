"""Adapter classes to provide backward compatibility during migration."""

import logging
import os
from typing import Any

from requests import Session

from .confluence_v2 import ConfluenceV2Client
from .jira_v3 import JiraV3Client

logger = logging.getLogger(__name__)


class JiraAdapter:
    """Adapter to provide atlassian-python-api compatible interface using JiraV3Client."""

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        session: Session | None = None,
        cloud: bool = True,
        verify_ssl: bool = True,
    ):
        """Initialize JIRA adapter.

        Args:
            url: JIRA URL
            username: Username for basic auth
            password: Password/API token for basic auth
            token: Personal access token
            session: Pre-configured session (for OAuth)
            cloud: Whether this is a cloud instance
            verify_ssl: Whether to verify SSL
        """
        self.url = url.rstrip("/")
        self.cloud = cloud
        self._session = session or Session()

        # Determine auth type and create client
        if session and "Authorization" in session.headers:
            # OAuth session
            self.client = JiraV3Client(
                base_url=url,
                auth_type="oauth",
                oauth_session=session,
                verify_ssl=verify_ssl,
            )
        elif token:
            # PAT auth
            self.client = JiraV3Client(
                base_url=url,
                auth_type="pat",
                token=token,
                verify_ssl=verify_ssl,
            )
        else:
            # Basic auth
            self.client = JiraV3Client(
                base_url=url,
                auth_type="basic",
                username=username,
                password=password,
                verify_ssl=verify_ssl,
            )

        # Store session reference for compatibility
        self._session = self.client.session

    # === Core Methods ===

    def myself(self) -> dict[str, Any]:
        """Get current user info."""
        return self.client.get_myself()

    def get_issue(
        self,
        issue_key: str,
        expand: str | None = None,
        fields: str | None = None,
        properties: str | None = None,
        update_history: bool = True,
    ) -> dict[str, Any]:
        """Get issue details."""
        expand_list = expand.split(",") if expand else None
        fields_list = fields.split(",") if fields else None
        properties_list = properties.split(",") if properties else None
        return self.client.get_issue(
            issue_key,
            expand=expand_list,
            fields=fields_list,
            properties=properties_list,
            update_history=update_history,
        )

    def create_issue(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Create issue."""
        return self.client.create_issue(fields)

    def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
        notify_users: bool = True,
        **kwargs,
    ) -> None:
        """Update issue."""
        self.client.update_issue(
            issue_key=issue_key,
            fields=fields,
            update=update,
            notify_users=notify_users,
        )

    def delete_issue(self, issue_key: str) -> None:
        """Delete issue."""
        self.client.delete_issue(issue_key)

    def create_issues(self, issue_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk create issues."""
        # Convert to new format
        issues = []
        for issue_data in issue_list:
            issue = {}
            if "fields" in issue_data:
                issue["fields"] = issue_data["fields"]
            if "update" in issue_data:
                issue["update"] = issue_data["update"]
            issues.append(issue)

        return self.client.create_issues(issues)

    # === Comments ===

    def issue_get_comments(self, issue_key: str) -> list[dict[str, Any]]:
        """Get issue comments."""
        result = self.client.get_comments(issue_key, max_results=100)
        return result.get("comments", [])

    def issue_add_comment(
        self,
        issue_key: str,
        comment: str | dict[str, Any],
        visibility: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Add comment to issue."""
        return self.client.add_comment(issue_key, comment, visibility)

    # === Transitions ===

    def get_issue_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """Get available transitions."""
        result = self.client.get_transitions(issue_key)
        return result.get("transitions", [])

    def set_issue_status_by_transition_id(
        self,
        issue_key: str,
        transition_id: str,
        fields: dict[str, Any] | None = None,
        comment: str | None = None,
    ) -> None:
        """Transition issue by ID."""
        comment_data = None
        if comment:
            comment_data = {"body": comment}

        self.client.transition_issue(
            issue_key=issue_key,
            transition_id=transition_id,
            fields=fields,
            comment=comment_data,
        )

    def set_issue_status(
        self,
        issue_key: str,
        status_name: str,
        fields: dict[str, Any] | None = None,
        comment: str | None = None,
    ) -> None:
        """Transition issue by status name."""
        # Get transitions and find matching one
        transitions = self.get_issue_transitions(issue_key)
        for transition in transitions:
            if transition.get("to", {}).get("name") == status_name:
                self.set_issue_status_by_transition_id(
                    issue_key,
                    transition["id"],
                    fields,
                    comment,
                )
                return

        raise ValueError(f"No transition found to status '{status_name}'")

    # === Search ===

    def jql(
        self,
        jql: str,
        start_at: int = 0,
        limit: int = 50,
        fields: str | list[str] | None = None,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Search using JQL."""
        if isinstance(fields, str):
            fields = fields.split(",") if fields else None

        expand_list = expand.split(",") if expand else None

        return self.client.search_issues(
            jql=jql,
            start_at=start_at,
            max_results=limit,
            fields=fields,
            expand=expand_list,
        )

    def enhanced_jql_get_list_of_tickets(
        self,
        jql: str,
        fields: str | list[str] | None = None,
        limit: int = 100,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Enhanced JQL search for cloud instances that returns just issues list.
        
        This method is used specifically for Jira Cloud instances and returns
        only the issues array without pagination metadata.
        
        Args:
            jql: JQL query string
            fields: Fields to return (comma-separated string or list)
            limit: Maximum number of issues to return
            expand: Fields to expand
            
        Returns:
            List of issue dictionaries
        """
        # Use the standard jql method but extract just the issues
        result = self.jql(
            jql=jql,
            start_at=0,
            limit=limit,
            fields=fields,
            expand=expand,
        )
        
        # Return just the issues array
        return result.get("issues", [])

    # === Projects ===

    def projects(self, included_archived: bool = False) -> list[dict[str, Any]]:
        """Get all projects."""
        result = self.client.get_projects(max_results=1000)
        projects = result.get("values", [])

        if not included_archived:
            projects = [p for p in projects if not p.get("archived", False)]

        return projects

    def get_all_project_issues(
        self,
        project: str,
        start_at: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get all issues in a project."""
        jql = f"project = {project}"
        return self.jql(jql, start_at=start_at, limit=limit)

    def get_project_versions(
        self,
        project: str,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get project versions."""
        expand_list = expand.split(",") if expand else None
        return self.client.get_project_versions(project, expand=expand_list)

    # === Fields ===

    def get_all_fields(self) -> list[dict[str, Any]]:
        """Get all fields."""
        return self.client.get_fields()

    # === Worklogs ===

    def get_issue_worklog(self, issue_key: str) -> dict[str, Any]:
        """Get issue worklogs."""
        result = self.client.get_worklogs(issue_key, max_results=100)
        return {
            "worklogs": result.get("worklogs", []),
            "total": result.get("total", 0),
        }

    def issue_add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        started: str | None = None,
        comment: str | None = None,
        adjust_estimate: str = "auto",
        new_estimate: str | None = None,
        reduce_by: str | None = None,
    ) -> dict[str, Any]:
        """Add worklog to issue."""
        # Default to current time if not provided
        if not started:
            from datetime import datetime

            started = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        return self.client.add_worklog(
            issue_key=issue_key,
            time_spent=time_spent,
            started=started,
            comment=comment,
            adjust_estimate=adjust_estimate,
            new_estimate=new_estimate,
            reduce_by=reduce_by,
        )

    # === Links ===

    def get_issue_link_types(self) -> list[dict[str, Any]]:
        """Get issue link types."""
        result = self.client.get_issue_link_types()
        return result.get("issueLinkTypes", [])

    def create_issue_link(
        self,
        link_data: dict[str, Any],
    ) -> None:
        """Create issue link."""
        self.client.create_issue_link(
            inward_issue_key=link_data["inwardIssue"]["key"],
            outward_issue_key=link_data["outwardIssue"]["key"],
            link_type=link_data["type"]["name"],
            comment=link_data.get("comment"),
        )

    def delete_issue_link(self, link_id: str) -> None:
        """Delete issue link."""
        self.client.delete_issue_link(link_id)

    def create_or_update_issue_remote_links(
        self,
        issue_key: str,
        link_url: str,
        title: str,
        global_id: str | None = None,
        relationship: str | None = None,
        summary: str | None = None,
        icon_url: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create remote issue link."""
        return self.client.create_remote_issue_link(
            issue_key=issue_key,
            url=link_url,
            title=title,
            summary=summary,
            icon_url=icon_url,
            relationship=relationship,
            global_id=global_id,
        )

    # === Users ===

    def user(
        self,
        username: str | None = None,
        account_id: str | None = None,
        key: str | None = None,
    ) -> dict[str, Any]:
        """Get user details."""
        return self.client.get_user(
            account_id=account_id,
            username=username,
            key=key,
        )

    def user_find_by_user_string(
        self,
        query: str,
        start_at: int = 0,
        max_results: int = 50,
        include_active: bool = True,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """Search users."""
        return self.client.search_users(query, start_at, max_results)

    # === Attachments ===

    def download_attachments_from_issue(
        self,
        issue_key: str,
        path: str | None = None,
        attachment_ids: list[str] | None = None,
    ) -> list[str]:
        """Download issue attachments."""
        # Get issue with attachment details
        issue = self.get_issue(issue_key, expand="attachment")
        attachments = issue.get("fields", {}).get("attachment", [])

        if not attachments:
            return []

        # Filter by IDs if provided
        if attachment_ids:
            attachments = [a for a in attachments if a.get("id") in attachment_ids]

        # Create download directory
        if not path:
            path = os.getcwd()
        os.makedirs(path, exist_ok=True)

        downloaded = []
        for attachment in attachments:
            att_id = attachment.get("id")
            filename = attachment.get("filename", f"attachment_{att_id}")
            filepath = os.path.join(path, filename)

            # Download content
            content = self.client.download_attachment(att_id, redirect=True)

            # Save to file
            with open(filepath, "wb") as f:
                f.write(content)

            downloaded.append(filepath)

        return downloaded

    # === Agile/Sprint Operations ===

    def get_all_agile_boards(
        self,
        board_name: str | None = None,
        project_key: str | None = None,
        board_type: str | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Get agile boards."""
        # Use Agile API endpoint
        endpoint = "/rest/agile/1.0/board"
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if board_name:
            params["name"] = board_name
        if project_key:
            params["projectKeyOrId"] = project_key
        if board_type:
            params["type"] = board_type

        return self.client.get(endpoint, params=params)

    def get_board(self, board_id: int) -> dict[str, Any]:
        """Get board details."""
        return self.client.get(f"/rest/agile/1.0/board/{board_id}")

    def get_board_by_filter_id(self, filter_id: int) -> dict[str, Any]:
        """Get board by filter ID."""
        boards = self.get_all_agile_boards(max_results=100)
        for board in boards.get("values", []):
            if board.get("filter", {}).get("id") == str(filter_id):
                return board
        raise ValueError(f"No board found with filter ID {filter_id}")

    def get_board_by_name(self, board_name: str) -> dict[str, Any]:
        """Get board by name."""
        boards = self.get_all_agile_boards(board_name=board_name, max_results=1)
        values = boards.get("values", [])
        if not values:
            raise ValueError(f"No board found with name '{board_name}'")
        return values[0]

    def get_board_issues(
        self,
        board_id: int,
        start_at: int = 0,
        max_results: int = 50,
        jql: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get board issues."""
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = fields

        return self.client.get(
            f"/rest/agile/1.0/board/{board_id}/issue",
            params=params,
        )

    def get_all_sprint(
        self,
        board_id: int,
        state: str | None = None,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Get board sprints."""
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if state:
            params["state"] = state

        return self.client.get(
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params=params,
        )

    def get_sprint_issues(
        self,
        sprint_id: int,
        start_at: int = 0,
        max_results: int = 50,
        jql: str | None = None,
        fields: str | None = None,
    ) -> dict[str, Any]:
        """Get sprint issues."""
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = fields

        return self.client.get(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            params=params,
        )

    def create_sprint(
        self,
        name: str,
        board_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> dict[str, Any]:
        """Create sprint."""
        data = {
            "name": name,
            "originBoardId": board_id,
        }
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        if goal:
            data["goal"] = goal

        return self.client.post("/rest/agile/1.0/sprint", json_data=data)

    def update_sprint(
        self,
        sprint_id: int,
        name: str | None = None,
        state: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        goal: str | None = None,
    ) -> dict[str, Any]:
        """Update sprint."""
        data = {}
        if name:
            data["name"] = name
        if state:
            data["state"] = state
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        if goal:
            data["goal"] = goal

        return self.client.put(
            f"/rest/agile/1.0/sprint/{sprint_id}",
            json_data=data,
        )

    def get_issues_for_sprint(
        self,
        sprint_id: int,
        start_at: int = 0,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Get issues in sprint."""
        result = self.get_sprint_issues(sprint_id, start_at, max_results)
        return result.get("issues", [])

    # === Generic Methods ===

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> Any:
        """Generic GET request."""
        return self.client.get(path, params=params, absolute=absolute)

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> Any:
        """Generic POST request."""
        return self.client.post(
            path,
            json_data=json,
            data=data,
            params=params,
            absolute=absolute,
        )

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> Any:
        """Generic PUT request."""
        return self.client.put(
            path,
            json_data=json,
            data=data,
            params=params,
            absolute=absolute,
        )

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        absolute: bool = False,
    ) -> Any:
        """Generic DELETE request."""
        return self.client.delete(path, params=params, absolute=absolute)

    def resource_url(self, resource: str) -> str:
        """Build resource URL."""
        return f"{self.url}/rest/api/3/{resource.lstrip('/')}"


class ConfluenceAdapter:
    """Adapter to provide atlassian-python-api compatible interface using ConfluenceV2Client."""

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        session: Session | None = None,
        cloud: bool = True,
        verify_ssl: bool = True,
    ):
        """Initialize Confluence adapter.

        Args:
            url: Confluence URL
            username: Username for basic auth
            password: Password/API token for basic auth
            token: Personal access token
            session: Pre-configured session (for OAuth)
            cloud: Whether this is a cloud instance
            verify_ssl: Whether to verify SSL
        """
        self.url = url.rstrip("/")
        self.cloud = cloud
        self._session = session or Session()

        # Determine auth type and create client
        if session and "Authorization" in session.headers:
            # OAuth session
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="oauth",
                oauth_session=session,
                verify_ssl=verify_ssl,
            )
        elif token:
            # PAT auth
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="pat",
                token=token,
                verify_ssl=verify_ssl,
            )
        else:
            # Basic auth
            self.client = ConfluenceV2Client(
                base_url=url,
                auth_type="basic",
                username=username,
                password=password,
                verify_ssl=verify_ssl,
            )

        # Store session reference for compatibility
        self._session = self.client.session

    # === User Operations ===

    def get_user_details_by_username(self, username: str) -> dict[str, Any]:
        """Get user details by username."""
        if self.cloud:
            # Cloud uses account ID
            return self.client.get_user(username=username)
        else:
            # Server/DC
            return self.client.get_user(username=username)

    # === Page Operations ===

    def get_page_by_id(
        self,
        page_id: str,
        expand: str | None = None,
        status: str | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Get page by ID."""
        expand_list = expand.split(",") if expand else None
        return self.client.get_page_by_id(
            page_id=page_id,
            version=version,
            include=expand_list,
        )

    def get_page_by_title(
        self,
        space: str,
        title: str,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Get page by title."""
        expand_list = expand.split(",") if expand else None
        return self.client.get_page_by_title(space, title, expand=expand_list)

    def get_all_pages_from_space(
        self,
        space: str,
        start: int = 0,
        limit: int = 100,
        status: str | None = None,
        expand: str | None = None,
        content_type: str = "page",
    ) -> list[dict[str, Any]]:
        """Get all pages from space."""
        # Get space details first
        spaces = self.client.get_spaces(keys=[space], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space}' not found")

        space_id = space_data[0]["id"]

        # Get pages
        result = self.client.get_pages(
            space_id=space_id,
            status=status,
            limit=limit,
        )

        return result.get("results", [])

    def create_page(
        self,
        space: str,
        title: str,
        body: str | dict[str, Any],
        parent_id: int | None = None,
        type: str = "page",
        representation: str = "storage",
        editor: str | None = None,
        full_width: bool = False,
    ) -> dict[str, Any]:
        """Create page."""
        # Get space ID
        spaces = self.client.get_spaces(keys=[space], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space}' not found")

        space_id = space_data[0]["id"]

        # Handle body format
        if isinstance(body, str):
            # Legacy wiki markup - convert to ADF if cloud
            if self.cloud:
                # For now, wrap in a basic ADF structure
                body_adf = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": body,
                                }
                            ],
                        }
                    ],
                }
            else:
                # Server/DC - keep as string
                body_adf = body
        else:
            # Already ADF
            body_adf = body

        return self.client.create_page(
            space_id=space_id,
            title=title,
            body=body_adf,
            parent_id=str(parent_id) if parent_id else None,
        )

    def update_page(
        self,
        page_id: int | str,
        title: str,
        body: str | dict[str, Any],
        parent_id: int | None = None,
        type: str = "page",
        representation: str = "storage",
        minor_edit: bool = False,
        full_width: bool = False,
    ) -> dict[str, Any]:
        """Update page."""
        # Get current page to get version
        page = self.get_page_by_id(str(page_id))
        current_version = page.get("version", {}).get("number", 0)

        # Handle body format
        if isinstance(body, str):
            # Legacy wiki markup - convert to ADF if cloud
            if self.cloud:
                # For now, wrap in a basic ADF structure
                body_adf = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": body,
                                }
                            ],
                        }
                    ],
                }
            else:
                # Server/DC - keep as string
                body_adf = body
        else:
            # Already ADF
            body_adf = body

        return self.client.update_page(
            page_id=str(page_id),
            title=title,
            body=body_adf,
            version_number=current_version,
            parent_id=str(parent_id) if parent_id else None,
        )

    def get_page_ancestors(self, page_id: str) -> list[dict[str, Any]]:
        """Get page ancestors."""
        return self.client.get_page_ancestors(page_id)

    def get_page_child_by_type(
        self,
        page_id: str,
        type: str = "page",
        start: int = 0,
        limit: int = 100,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get page children."""
        result = self.client.get_page_children(
            page_id=page_id,
            limit=limit,
        )
        return result.get("results", [])

    def remove_page(self, page_id: str) -> None:
        """Delete page."""
        self.client.delete_page(page_id)

    # === Comment Operations ===

    def get_page_comments(
        self,
        page_id: str,
        expand: str | None = None,
        depth: str | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get page comments."""
        result = self.client.get_comments(
            page_id=page_id,
            limit=limit,
        )
        return result.get("results", [])

    def add_comment(
        self,
        page_id: str,
        text: str | dict[str, Any],
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Add comment to page."""
        # Handle body format
        if isinstance(text, str):
            # Convert to ADF
            body = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": text,
                            }
                        ],
                    }
                ],
            }
        else:
            body = text

        return self.client.create_comment(page_id=page_id, body=body)

    # === Search Operations ===

    def cql(
        self,
        cql: str,
        start: int = 0,
        limit: int = 100,
        include_archived_spaces: bool = False,
    ) -> dict[str, Any]:
        """Search using CQL."""
        result = self.client.search(
            cql=cql,
            limit=limit,
            include_archived_spaces=include_archived_spaces,
        )

        # Convert to legacy format
        return {
            "results": result.get("results", []),
            "start": start,
            "limit": limit,
            "size": len(result.get("results", [])),
            "_links": result.get("_links", {}),
        }

    # === Space Operations ===

    def get_all_spaces(
        self,
        start: int = 0,
        limit: int = 100,
        space_type: str | None = None,
        status: str | None = None,
        label: str | None = None,
        favourite: bool | None = None,
        expand: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all spaces."""
        result = self.client.get_spaces(
            type=space_type,
            status=status,
            limit=limit,
        )
        return result.get("results", [])

    def get_space(
        self,
        space_key: str,
        expand: str | None = None,
    ) -> dict[str, Any]:
        """Get space details."""
        # First try to get by key
        spaces = self.client.get_spaces(keys=[space_key], limit=1)
        space_data = spaces.get("results", [])
        if not space_data:
            raise ValueError(f"Space '{space_key}' not found")

        space_id = space_data[0]["id"]
        expand_list = expand.split(",") if expand else None

        return self.client.get_space_by_id(space_id, include=expand_list)

    # === Label Operations ===

    def get_page_labels(
        self,
        page_id: str,
        prefix: str | None = None,
        start: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get page labels."""
        result = self.client.get_labels(
            page_id=page_id,
            prefix=prefix,
            limit=limit,
        )
        return result.get("results", [])

    def set_page_label(self, page_id: str, label: str) -> dict[str, Any]:
        """Add label to page."""
        result = self.client.add_labels(page_id=page_id, labels=[label])
        return result
