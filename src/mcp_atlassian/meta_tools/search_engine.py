"""Search Engine Meta-Tool for MCP Atlassian.

This module consolidates all search and query operations into a single meta-tool
to reduce token usage while maintaining full functionality.
"""

import json
import logging
from typing import Any, Literal

from ..exceptions import MetaToolError
from ..jira.client import JiraFetcher
from ..confluence.client import ConfluenceFetcher

logger = logging.getLogger(__name__)


class SearchEngine:
    """Universal search engine for Jira and Confluence operations.

    Consolidates 8+ individual search tools into a single meta-tool:
    - search (JQL/CQL queries)
    - search_fields (field discovery)
    - search_user (user lookup)
    - get_project_issues (project-scoped search)
    - get_all_projects (project listing)
    - get_agile_boards (board discovery)
    """

    # Supported query types for each service
    JIRA_QUERY_TYPES = {
        "issues": "Search issues using JQL",
        "fields": "Discover available fields",
        "users": "Search for users",
        "projects": "List all projects",
        "boards": "List agile boards",
        "sprints": "Search sprints",
        "versions": "Search project versions",
        "components": "Search project components",
        "issue_types": "List issue types",
        "statuses": "List issue statuses",
        "priorities": "List issue priorities",
        "resolutions": "List issue resolutions",
    }

    CONFLUENCE_QUERY_TYPES = {
        "pages": "Search pages using CQL",
        "spaces": "List all spaces",
        "users": "Search for users",
        "content": "Search all content types",
        "labels": "Search labels",
        "attachments": "Search attachments",
    }

    def __init__(self):
        """Initialize the SearchEngine."""
        pass

    async def execute_search(
        self,
        service: Literal["jira", "confluence"],
        query_type: str,
        query: str | dict | None = None,
        options: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> str:
        """Execute a search operation.

        Args:
            service: Target service (jira or confluence)
            query_type: Type of search to perform
            query: Search query (JQL/CQL string or structured query)
            options: Additional search options (limit, fields, expand, etc.)
            dry_run: If True, validate without executing

        Returns:
            JSON string with search results
        """
        try:
            # Validate inputs
            self._validate_search_inputs(service, query_type, query, options)

            # Perform dry run validation if requested
            if dry_run:
                return self._perform_dry_run_validation(service, query_type, query, options)

            # Get appropriate client based on service
            if service == "jira":
                from ..servers.context import get_jira_client
                client = get_jira_client()
                return await self._execute_jira_search(client, query_type, query, options)
            else:
                from ..servers.context import get_confluence_client
                client = get_confluence_client()
                return await self._execute_confluence_search(client, query_type, query, options)

        except MetaToolError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in search_engine: {e}", exc_info=True)
            raise MetaToolError.from_exception(
                error=e,
                error_code="SEARCH_ENGINE_ERROR",
                user_message=f"Failed to execute {service} {query_type} search",
                suggestions=["Check the service configuration and try again"],
                context={
                    "service": service,
                    "query_type": query_type,
                    "has_query": query is not None,
                    "has_options": options is not None,
                },
            )

    def _validate_search_inputs(
        self,
        service: str,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> None:
        """Validate search inputs."""
        if service not in ["jira", "confluence"]:
            raise MetaToolError(
                error_code="INVALID_SERVICE",
                user_message=f"Service must be 'jira' or 'confluence', got '{service}'",
                suggestions=[
                    "Use 'jira' for Jira searches or 'confluence' for Confluence searches"
                ],
                context={"provided_service": service},
            )

        # Check if query type is supported for the service
        supported_types = (
            self.JIRA_QUERY_TYPES if service == "jira" else self.CONFLUENCE_QUERY_TYPES
        )

        if query_type not in supported_types:
            raise MetaToolError(
                error_code=f"{service.upper()}_QUERY_TYPE_NOT_SUPPORTED",
                user_message=f"Query type '{query_type}' is not supported for {service}",
                suggestions=[
                    f"Supported {service} query types: {', '.join(supported_types.keys())}"
                ],
                context={
                    "service": service,
                    "query_type": query_type,
                    "supported_types": list(supported_types.keys()),
                },
            )

        # Some query types require a query parameter
        query_required_types = {
            "jira": ["issues", "users", "sprints", "versions", "components"],
            "confluence": ["pages", "content", "labels", "attachments", "users"],
        }

        if (query_type in query_required_types.get(service, []) and
            not query and query != ""):
            raise MetaToolError(
                error_code="MISSING_QUERY",
                user_message=f"Query type '{query_type}' requires a query parameter",
                suggestions=[
                    f"Provide a query string or structured query for {query_type} search",
                    f"For JQL: 'project = PROJ AND status = Open'",
                    f"For CQL: 'type = page AND space = SPACE'",
                ],
                context={
                    "service": service,
                    "query_type": query_type,
                },
            )

    def _perform_dry_run_validation(
        self,
        service: str,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Perform dry run validation without executing the search."""
        validation_result = {
            "dry_run": True,
            "service": service,
            "query_type": query_type,
            "validation": "PASSED",
            "query_format": type(query).__name__ if query else "None",
            "supported_options": self._get_supported_options(service, query_type),
            "provided_options": list(options.keys()) if options else [],
        }

        # Add query-specific validation
        if query_type in ["issues", "pages"] and query:
            if isinstance(query, str):
                validation_result["query_syntax"] = (
                    "JQL" if service == "jira" else "CQL"
                )
            elif isinstance(query, dict):
                validation_result["query_syntax"] = "Structured"
                validation_result["query_fields"] = list(query.keys())

        return json.dumps(validation_result, indent=2, ensure_ascii=False)

    def _get_supported_options(self, service: str, query_type: str) -> list[str]:
        """Get supported options for a specific search type."""
        common_options = ["limit", "start_at", "fields", "expand"]

        if service == "jira":
            if query_type == "issues":
                return common_options + ["jql", "validate_query", "properties"]
            elif query_type == "projects":
                return ["expand", "recent", "properties"]
            elif query_type == "boards":
                return ["start_at", "max_results", "type", "name", "project_key_or_id"]
            else:
                return common_options
        else:  # confluence
            if query_type == "pages":
                return common_options + ["cql", "space_key", "title", "type"]
            elif query_type == "spaces":
                return ["limit", "start", "expand", "status", "type"]
            else:
                return common_options

    async def _execute_jira_search(
        self,
        client: JiraFetcher,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Jira search operations."""
        try:
            # Apply default options
            opts = options or {}

            if query_type == "issues":
                # Handle both string JQL and structured queries
                if isinstance(query, str):
                    jql = query
                elif isinstance(query, dict):
                    # Convert structured query to JQL
                    jql = self._dict_to_jql(query)
                else:
                    jql = str(query) if query else ""

                results = client.search_issues(
                    jql=jql,
                    limit=opts.get("limit", 50),
                    start_at=opts.get("start_at", 0),
                    fields=opts.get("fields"),
                    expand=opts.get("expand"),
                    validate_query=opts.get("validate_query", True)
                )

            elif query_type == "fields":
                results = client.get_fields()

            elif query_type == "users":
                results = client.search_users(
                    query=str(query) if query else "",
                    start_at=opts.get("start_at", 0),
                    max_results=opts.get("limit", 50)
                )

            elif query_type == "projects":
                results = client.get_all_projects(
                    expand=opts.get("expand"),
                    recent=opts.get("recent")
                )

            elif query_type == "boards":
                results = client.get_agile_boards(
                    start_at=opts.get("start_at", 0),
                    max_results=opts.get("limit", 50),
                    board_type=opts.get("type"),
                    name=opts.get("name"),
                    project_key_or_id=opts.get("project_key_or_id")
                )

            elif query_type == "sprints":
                board_id = opts.get("board_id")
                if not board_id:
                    raise ValueError("board_id is required for sprint search")
                results = client.get_sprints(
                    board_id=board_id,
                    start_at=opts.get("start_at", 0),
                    max_results=opts.get("limit", 50),
                    state=opts.get("state")
                )

            elif query_type == "versions":
                project_key = opts.get("project_key")
                if not project_key:
                    raise ValueError("project_key is required for version search")
                results = client.get_project_versions(project_key)

            elif query_type == "components":
                project_key = opts.get("project_key")
                if not project_key:
                    raise ValueError("project_key is required for component search")
                results = client.get_project_components(project_key)

            elif query_type == "issue_types":
                results = client.get_issue_types()

            elif query_type == "statuses":
                results = client.get_issue_statuses()

            elif query_type == "priorities":
                results = client.get_issue_priorities()

            elif query_type == "resolutions":
                results = client.get_issue_resolutions()

            else:
                raise ValueError(f"Unsupported Jira query type: {query_type}")

            # Convert results to JSON
            if hasattr(results, 'to_dict'):
                result_data = results.to_dict()
            elif hasattr(results, 'to_simplified_dict'):
                result_data = results.to_simplified_dict()
            elif isinstance(results, list):
                result_data = [
                    item.to_dict() if hasattr(item, 'to_dict') else item
                    for item in results
                ]
            else:
                result_data = results

            return json.dumps(
                {
                    "success": True,
                    "service": "jira",
                    "query_type": query_type,
                    "query": query,
                    "result_count": (
                        len(result_data) if isinstance(result_data, list)
                        else result_data.get("total") if isinstance(result_data, dict)
                        else 1
                    ),
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"JIRA_{query_type.upper()}_SEARCH_FAILED",
                api_endpoint=self._get_api_endpoint("jira", query_type),
                suggestions=self._get_error_suggestions("jira", query_type, e),
                context={
                    "query_type": query_type,
                    "query": str(query) if query else None,
                    "options": options,
                },
            )

    async def _execute_confluence_search(
        self,
        client: ConfluenceFetcher,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Confluence search operations."""
        try:
            # Apply default options
            opts = options or {}

            if query_type == "pages":
                # Handle both string CQL and structured queries
                if isinstance(query, str):
                    cql = query
                elif isinstance(query, dict):
                    # Convert structured query to CQL
                    cql = self._dict_to_cql(query)
                else:
                    cql = str(query) if query else ""

                results = client.search_pages(
                    cql=cql,
                    limit=opts.get("limit", 25),
                    start=opts.get("start_at", 0),
                    expand=opts.get("expand")
                )

            elif query_type == "content":
                # General content search
                if isinstance(query, str):
                    cql = query
                elif isinstance(query, dict):
                    cql = self._dict_to_cql(query)
                else:
                    cql = str(query) if query else ""

                results = client.search_content(
                    cql=cql,
                    limit=opts.get("limit", 25),
                    start=opts.get("start_at", 0),
                    expand=opts.get("expand")
                )

            elif query_type == "spaces":
                results = client.get_all_spaces(
                    limit=opts.get("limit", 25),
                    start=opts.get("start", 0),
                    expand=opts.get("expand"),
                    status=opts.get("status"),
                    type=opts.get("type")
                )

            elif query_type == "users":
                results = client.search_users(
                    query=str(query) if query else "",
                    limit=opts.get("limit", 50)
                )

            elif query_type == "labels":
                results = client.search_labels(
                    query=str(query) if query else "",
                    limit=opts.get("limit", 200)
                )

            elif query_type == "attachments":
                space_key = opts.get("space_key")
                results = client.search_attachments(
                    filename=str(query) if query else "",
                    space_key=space_key,
                    limit=opts.get("limit", 25)
                )

            else:
                raise ValueError(f"Unsupported Confluence query type: {query_type}")

            # Convert results to JSON
            if hasattr(results, 'to_dict'):
                result_data = results.to_dict()
            elif hasattr(results, 'to_simplified_dict'):
                result_data = results.to_simplified_dict()
            elif isinstance(results, list):
                result_data = [
                    item.to_dict() if hasattr(item, 'to_dict') else item
                    for item in results
                ]
            else:
                result_data = results

            return json.dumps(
                {
                    "success": True,
                    "service": "confluence",
                    "query_type": query_type,
                    "query": query,
                    "result_count": (
                        len(result_data) if isinstance(result_data, list)
                        else result_data.get("size") if isinstance(result_data, dict)
                        else 1
                    ),
                    "results": result_data,
                },
                indent=2,
                ensure_ascii=False,
            )

        except Exception as e:
            raise MetaToolError.from_exception(
                error=e,
                error_code=f"CONFLUENCE_{query_type.upper()}_SEARCH_FAILED",
                api_endpoint=self._get_api_endpoint("confluence", query_type),
                suggestions=self._get_error_suggestions("confluence", query_type, e),
                context={
                    "query_type": query_type,
                    "query": str(query) if query else None,
                    "options": options,
                },
            )

    def _dict_to_jql(self, query_dict: dict) -> str:
        """Convert structured query dictionary to JQL string."""
        clauses = []

        for field, value in query_dict.items():
            if field == "project":
                clauses.append(f"project = {value}")
            elif field == "status":
                if isinstance(value, list):
                    statuses = ", ".join(f'"{s}"' for s in value)
                    clauses.append(f"status IN ({statuses})")
                else:
                    clauses.append(f'status = "{value}"')
            elif field == "assignee":
                if value == "currentUser()":
                    clauses.append("assignee = currentUser()")
                elif value == "unassigned":
                    clauses.append("assignee is EMPTY")
                else:
                    clauses.append(f'assignee = "{value}"')
            elif field == "reporter":
                clauses.append(f'reporter = "{value}"')
            elif field == "priority":
                if isinstance(value, list):
                    priorities = ", ".join(f'"{p}"' for p in value)
                    clauses.append(f"priority IN ({priorities})")
                else:
                    clauses.append(f'priority = "{value}"')
            elif field == "created":
                clauses.append(f"created {value}")
            elif field == "updated":
                clauses.append(f"updated {value}")
            else:
                # Generic field handling
                clauses.append(f'{field} = "{value}"')

        return " AND ".join(clauses)

    def _dict_to_cql(self, query_dict: dict) -> str:
        """Convert structured query dictionary to CQL string."""
        clauses = []

        for field, value in query_dict.items():
            if field == "space":
                clauses.append(f"space = {value}")
            elif field == "type":
                clauses.append(f"type = {value}")
            elif field == "title":
                clauses.append(f'title ~ "{value}"')
            elif field == "text":
                clauses.append(f'text ~ "{value}"')
            elif field == "label":
                if isinstance(value, list):
                    for label in value:
                        clauses.append(f'label = "{label}"')
                else:
                    clauses.append(f'label = "{value}"')
            elif field == "creator":
                clauses.append(f'creator = "{value}"')
            elif field == "created":
                clauses.append(f"created {value}")
            elif field == "lastModified":
                clauses.append(f"lastModified {value}")
            else:
                # Generic field handling
                clauses.append(f'{field} = "{value}"')

        return " AND ".join(clauses)

    def _get_api_endpoint(self, service: str, query_type: str) -> str:
        """Get the API endpoint for error reporting."""
        if service == "jira":
            endpoints = {
                "issues": "/rest/api/3/search",
                "fields": "/rest/api/3/field",
                "users": "/rest/api/3/user/search",
                "projects": "/rest/api/3/project",
                "boards": "/rest/agile/1.0/board",
                "sprints": "/rest/agile/1.0/board/{boardId}/sprint",
                "versions": "/rest/api/3/project/{projectKey}/version",
                "components": "/rest/api/3/project/{projectKey}/component",
                "issue_types": "/rest/api/3/issuetype",
                "statuses": "/rest/api/3/status",
                "priorities": "/rest/api/3/priority",
                "resolutions": "/rest/api/3/resolution",
            }
        else:  # confluence
            endpoints = {
                "pages": "/wiki/api/v2/pages",
                "content": "/wiki/api/v2/content/search",
                "spaces": "/wiki/api/v2/spaces",
                "users": "/wiki/rest/api/user",
                "labels": "/wiki/rest/api/label",
                "attachments": "/wiki/api/v2/attachments",
            }

        return endpoints.get(query_type, f"/rest/api/3/{query_type}")

    def _get_error_suggestions(
        self, service: str, query_type: str, error: Exception
    ) -> list[str]:
        """Get error-specific suggestions."""
        suggestions = [
            f"Verify the {service} configuration and permissions",
        ]

        error_str = str(error).lower()

        if "authentication" in error_str or "unauthorized" in error_str:
            suggestions.append("Check your authentication credentials")
        elif "not found" in error_str:
            suggestions.append(f"Verify the {query_type} exists and is accessible")
        elif "syntax" in error_str or "invalid" in error_str:
            if query_type in ["issues", "pages", "content"]:
                query_lang = "JQL" if service == "jira" else "CQL"
                suggestions.append(f"Check your {query_lang} syntax")
        elif "permission" in error_str:
            suggestions.append(f"Ensure you have permission to search {query_type}")

        return suggestions