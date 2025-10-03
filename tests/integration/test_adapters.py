"""Test adapters for meta-tools that bypass FastMCP context requirements.

These adapters allow testing meta-tools with real APIs without needing
FastMCP context dependency injection.
"""

import logging
from typing import Any, Dict, Optional

from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig
from src.mcp_atlassian.jira import JiraFetcher
from src.mcp_atlassian.confluence import ConfluenceFetcher

logger = logging.getLogger(__name__)


class TestJiraFetcher(JiraFetcher):
    """Test adapter for JiraFetcher that doesn't require FastMCP context."""

    def __init__(self, config: JiraConfig):
        """Initialize with JiraConfig."""
        # Initialize the fetcher directly with the config
        super().__init__(config=config)


class TestConfluenceFetcher(ConfluenceFetcher):
    """Test adapter for ConfluenceFetcher that doesn't require FastMCP context."""

    def __init__(self, config: ConfluenceConfig):
        """Initialize with ConfluenceConfig."""
        # Initialize the fetcher directly with the config
        super().__init__(config=config)


class SearchEngineTestAdapter:
    """Test adapter for SearchEngine that uses direct fetcher instances."""

    # Copy the supported query types from the original SearchEngine
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

    def __init__(self, jira_fetcher: TestJiraFetcher, confluence_fetcher: TestConfluenceFetcher, execution_mode: str = "dry_run"):
        """Initialize with pre-configured fetchers.

        Args:
            jira_fetcher: TestJiraFetcher instance
            confluence_fetcher: TestConfluenceFetcher instance
            execution_mode: "dry_run", "real", or "hybrid" (default: "dry_run")
        """
        self.jira_fetcher = jira_fetcher
        self.confluence_fetcher = confluence_fetcher
        self.execution_mode = execution_mode

    async def execute_search(
        self,
        service: str,
        query_type: str,
        query: str | dict | None = None,
        options: dict[str, Any] | None = None,
        dry_run: bool | None = None,
    ) -> str:
        """Execute a search operation - simplified version of the original."""
        import json

        # Validate inputs
        if service not in ["jira", "confluence"]:
            raise ValueError(f"Service must be 'jira' or 'confluence', got '{service}'")

        # Check if query type is supported for the service
        supported_types = (
            self.JIRA_QUERY_TYPES if service == "jira" else self.CONFLUENCE_QUERY_TYPES
        )

        if query_type not in supported_types:
            raise ValueError(f"Query type '{query_type}' is not supported for {service}")

        # Determine execution mode
        effective_dry_run = self._determine_execution_mode(dry_run)

        # Perform dry run validation if requested
        if effective_dry_run:
            return json.dumps({
                "dry_run": True,
                "service": service,
                "query_type": query_type,
                "validation": "PASSED",
                "query_format": type(query).__name__ if query else "None",
                "execution_mode": self.execution_mode,
            }, indent=2)

        # Get appropriate fetcher
        fetcher = self.jira_fetcher if service == "jira" else self.confluence_fetcher

        try:
            if service == "jira":
                result = await self._execute_jira_search(fetcher, query_type, query, options)
            else:
                result = await self._execute_confluence_search(fetcher, query_type, query, options)

            return result

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise ValueError(f"Failed to execute {service} {query_type} search: {e}")

    async def _execute_jira_search(
        self,
        fetcher: TestJiraFetcher,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Jira search operations."""
        import json

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

            results = fetcher.search_issues(
                jql=jql,
                limit=opts.get("limit", 50),
                start_at=opts.get("start_at", 0),
                fields=opts.get("fields"),
                expand=opts.get("expand"),
                validate_query=opts.get("validate_query", True)
            )

        elif query_type == "fields":
            results = fetcher.get_fields()

        elif query_type == "users":
            results = fetcher.search_users(
                query=str(query) if query else "",
                start_at=opts.get("start_at", 0),
                max_results=opts.get("limit", 50)
            )

        elif query_type == "projects":
            results = fetcher.get_all_projects(
                include_archived=opts.get("include_archived", False)
            )

        elif query_type == "issue_types":
            results = fetcher.get_issue_types()

        elif query_type == "statuses":
            results = fetcher.get_issue_statuses()

        elif query_type == "priorities":
            results = fetcher.get_issue_priorities()

        else:
            raise ValueError(f"Unsupported Jira query type: {query_type}")

        # Convert results to JSON format
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

    async def _execute_confluence_search(
        self,
        fetcher: TestConfluenceFetcher,
        query_type: str,
        query: str | dict | None,
        options: dict[str, Any] | None,
    ) -> str:
        """Execute Confluence search operations."""
        import json

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

            results = fetcher.search_pages(
                cql=cql,
                limit=opts.get("limit", 25),
                start=opts.get("start_at", 0),
                expand=opts.get("expand")
            )

        elif query_type == "spaces":
            results = fetcher.get_all_spaces(
                limit=opts.get("limit", 25),
                start=opts.get("start", 0),
                expand=opts.get("expand"),
                status=opts.get("status"),
                type=opts.get("type")
            )

        elif query_type == "users":
            results = fetcher.search_users(
                query=str(query) if query else "",
                limit=opts.get("limit", 50)
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
            else:
                # Generic field handling
                clauses.append(f'{field} = "{value}"')

        return " AND ".join(clauses)

    def _determine_execution_mode(self, dry_run_override: bool | None) -> bool:
        """Determine whether to run in dry-run mode.

        Args:
            dry_run_override: Explicit override for this call

        Returns:
            True if should run in dry-run mode, False for real execution
        """
        # Explicit override takes precedence
        if dry_run_override is not None:
            return dry_run_override

        # Check execution mode setting
        if self.execution_mode == "real":
            return False
        elif self.execution_mode == "dry_run":
            return True
        elif self.execution_mode == "hybrid":
            # In hybrid mode, default to dry_run for safety
            return True
        else:
            # Unknown mode, default to dry_run for safety
            return True


class BatchProcessorTestAdapter:
    """Test adapter for BatchProcessor that uses direct fetcher instances."""

    def __init__(self, jira_fetcher: TestJiraFetcher, confluence_fetcher: TestConfluenceFetcher, execution_mode: str = "dry_run"):
        """Initialize with pre-configured fetchers."""
        # Import BatchProcessor here to avoid circular imports
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor

        self.jira_fetcher = jira_fetcher
        self.confluence_fetcher = confluence_fetcher
        self.batch_processor = BatchProcessor()
        self.execution_mode = execution_mode

    async def execute_batch_operation(
        self,
        service: str,
        operation: str,
        batch_data: list[dict],
        options: dict | None = None,
        dry_run: bool | None = None
    ) -> str:
        """Execute a batch operation - adapted version that patches the imports."""
        import json
        import sys
        from unittest.mock import MagicMock

        # Create a mock module for the context
        mock_context_module = MagicMock()
        mock_context_module.get_jira_client = lambda: self.jira_fetcher
        mock_context_module.get_confluence_client = lambda: self.confluence_fetcher

        # Store the original module if it exists
        original_module = sys.modules.get('src.mcp_atlassian.servers.context')

        # Monkey-patch the module
        sys.modules['src.mcp_atlassian.servers.context'] = mock_context_module

        try:
            # Import after patching to make sure the BatchProcessor uses our mock
            from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor

            # Create a fresh BatchProcessor instance
            batch_processor = BatchProcessor()

            # Determine execution mode
            effective_dry_run = self._determine_execution_mode(dry_run)

            # Now the correct signature from looking at the source - needs resource_type and items
            result = await batch_processor.execute_batch_operation(
                service=service,
                operation=operation,
                resource_type="issue" if service == "jira" else "page",
                items=batch_data,
                options=options or {},
                dry_run=effective_dry_run
            )
            return result
        finally:
            # Restore original module
            if original_module is not None:
                sys.modules['src.mcp_atlassian.servers.context'] = original_module
            else:
                sys.modules.pop('src.mcp_atlassian.servers.context', None)

    def _determine_execution_mode(self, dry_run_override: bool | None) -> bool:
        """Determine whether to run in dry-run mode."""
        if dry_run_override is not None:
            return dry_run_override
        return self.execution_mode != "real"


class WorkflowEngineTestAdapter:
    """Test adapter for WorkflowEngine that uses direct fetcher instances."""

    def __init__(self, jira_fetcher: TestJiraFetcher, execution_mode: str = "dry_run"):
        """Initialize with pre-configured Jira fetcher."""
        # Import WorkflowEngine here to avoid circular imports
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine

        self.jira_fetcher = jira_fetcher
        self.workflow_engine = WorkflowEngine()
        self.execution_mode = execution_mode

    async def execute_workflow_operation(
        self,
        operation: str,
        issue_key: str | None = None,
        transition_id: str | None = None,
        transition_name: str | None = None,
        fields: dict | None = None,
        project_key: str | None = None,
        issue_type: str | None = None,
        options: dict | None = None,
        dry_run: bool = False
    ) -> str:
        """Execute a workflow operation - adapted version that patches the imports."""
        import sys
        from unittest.mock import MagicMock

        # Create a mock module for the context
        mock_context_module = MagicMock()
        mock_context_module.get_jira_client = lambda: self.jira_fetcher

        # Store the original module if it exists
        original_module = sys.modules.get('src.mcp_atlassian.servers.context')

        # Monkey-patch the module
        sys.modules['src.mcp_atlassian.servers.context'] = mock_context_module

        try:
            # Import after patching to make sure the WorkflowEngine uses our mock
            from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine

            # Create a fresh WorkflowEngine instance
            workflow_engine = WorkflowEngine()

            # Execute the workflow operation
            result = await workflow_engine.execute_workflow_operation(
                operation=operation,
                issue_key=issue_key,
                transition_id=transition_id,
                transition_name=transition_name,
                fields=fields,
                project_key=project_key,
                issue_type=issue_type,
                options=options or {},
                dry_run=dry_run
            )
            return result
        finally:
            # Restore original module
            if original_module is not None:
                sys.modules['src.mcp_atlassian.servers.context'] = original_module
            else:
                sys.modules.pop('src.mcp_atlassian.servers.context', None)

class RelationshipManagerTestAdapter:
    """Test adapter for RelationshipManager that uses direct fetcher instances."""

    def __init__(self, jira_fetcher: TestJiraFetcher):
        """Initialize with pre-configured Jira fetcher."""
        # Import RelationshipManager here to avoid circular imports
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager

        self.jira_fetcher = jira_fetcher
        self.relationship_manager = RelationshipManager()

    async def execute_relationship_operation(
        self,
        operation: str,
        issue_key: str,
        target_issue_key: str | None = None,
        link_type: str | None = None,
        epic_key: str | None = None,
        parent_key: str | None = None,
        comment: str | None = None,
        link_id: str | None = None,
        options: dict | None = None,
        dry_run: bool = False
    ) -> str:
        """Execute a relationship operation - adapted version that patches the imports."""
        import sys
        from unittest.mock import MagicMock

        # Create a mock module for the context
        mock_context_module = MagicMock()
        mock_context_module.get_jira_client = lambda: self.jira_fetcher

        # Store the original module if it exists
        original_module = sys.modules.get('src.mcp_atlassian.servers.context')

        # Monkey-patch the module
        sys.modules['src.mcp_atlassian.servers.context'] = mock_context_module

        try:
            # Import after patching to make sure the RelationshipManager uses our mock
            from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager

            # Create a fresh RelationshipManager instance
            relationship_manager = RelationshipManager()

            # Execute the relationship operation
            result = await relationship_manager.execute_relationship_operation(
                operation=operation,
                issue_key=issue_key,
                target_issue_key=target_issue_key,
                link_type=link_type,
                epic_key=epic_key,
                parent_key=parent_key,
                comment=comment,
                link_id=link_id,
                options=options or {},
                dry_run=dry_run
            )
            return result
        finally:
            # Restore original module
            if original_module is not None:
                sys.modules['src.mcp_atlassian.servers.context'] = original_module
            else:
                sys.modules.pop('src.mcp_atlassian.servers.context', None)


class AttachmentHandlerTestAdapter:
    """Test adapter for AttachmentHandler that uses direct fetcher instances."""

    def __init__(self, jira_fetcher: TestJiraFetcher, confluence_fetcher: TestConfluenceFetcher):
        """Initialize with pre-configured fetchers."""
        # Import AttachmentHandler here to avoid circular imports
        from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

        self.jira_fetcher = jira_fetcher
        self.confluence_fetcher = confluence_fetcher
        self.attachment_handler = AttachmentHandler()

    async def execute_attachment_operation(
        self,
        service: str,
        operation: str,
        issue_key: str | None = None,
        page_id: str | None = None,
        attachment_id: str | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        file_content: bytes | None = None,
        download_path: str | None = None,
        options: dict | None = None,
        dry_run: bool = False
    ) -> str:
        """Execute an attachment operation - adapted version that patches the imports."""
        import sys
        from unittest.mock import MagicMock

        # Create a mock module for the context
        mock_context_module = MagicMock()
        mock_context_module.get_jira_client = lambda: self.jira_fetcher
        mock_context_module.get_confluence_client = lambda: self.confluence_fetcher

        # Store the original module if it exists
        original_module = sys.modules.get('src.mcp_atlassian.servers.context')

        # Monkey-patch the module
        sys.modules['src.mcp_atlassian.servers.context'] = mock_context_module

        try:
            # Import after patching to make sure the AttachmentHandler uses our mock
            from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

            # Create a fresh AttachmentHandler instance
            attachment_handler = AttachmentHandler()

            # Execute the attachment operation
            result = await attachment_handler.execute_attachment_operation(
                service=service,
                operation=operation,
                issue_key=issue_key,
                page_id=page_id,
                attachment_id=attachment_id,
                file_path=file_path,
                file_name=file_name,
                file_content=file_content,
                download_path=download_path,
                options=options or {},
                dry_run=dry_run
            )
            return result
        finally:
            # Restore original module
            if original_module is not None:
                sys.modules['src.mcp_atlassian.servers.context'] = original_module
            else:
                sys.modules.pop('src.mcp_atlassian.servers.context', None)


class ResourceManagerTestAdapter:
    """Test adapter for ResourceManager that uses direct fetcher instances."""

    def __init__(self, jira_fetcher: TestJiraFetcher | None, confluence_fetcher: TestConfluenceFetcher | None):
        """Initialize with pre-configured fetchers."""
        self.jira_fetcher = jira_fetcher
        self.confluence_fetcher = confluence_fetcher

    async def execute_operation(
        self,
        service: str,
        operation: str,
        resource_type: str,
        resource_id: str | None = None,
        resource_data: dict | None = None,
        options: dict | None = None,
        dry_run: bool = False
    ) -> str:
        """Execute a resource operation - adapted version that patches the dependencies."""
        from unittest.mock import patch, AsyncMock

        # Create mock fetcher functions
        async def mock_get_jira_fetcher(ctx):
            return self.jira_fetcher

        async def mock_get_confluence_fetcher(ctx):
            return self.confluence_fetcher

        # Patch the dependency injection functions
        with patch('src.mcp_atlassian.meta_tools.resource_manager.get_jira_fetcher', mock_get_jira_fetcher), \
             patch('src.mcp_atlassian.meta_tools.resource_manager.get_confluence_fetcher', mock_get_confluence_fetcher):

            # Import after patching
            from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager

            # Create a fresh ResourceManager instance
            resource_manager = ResourceManager()

            # Create a mock context
            mock_ctx = AsyncMock()

            # Execute the resource operation (map adapter params to ResourceManager params)
            result = await resource_manager.execute_operation(
                ctx=mock_ctx,
                service=service,
                operation=operation,
                resource=resource_type,   # Map resource_type to resource
                identifier=resource_id,   # Map resource_id to identifier
                data=resource_data or {},  # Map resource_data to data
                options=options or {}
            )
            return result
