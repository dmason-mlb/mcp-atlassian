"""Main FastMCP server setup for Atlassian integration."""

import json
import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal, Optional

from cachetools import TTLCache
from fastmcp import FastMCP, Context
from fastmcp.tools import Tool as FastMCPTool
from mcp.types import Tool as MCPTool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.utils.environment import get_available_services
from mcp_atlassian.utils.io import is_read_only_mode
from mcp_atlassian.utils.logging import mask_sensitive
from mcp_atlassian.utils.tools import get_enabled_tools, should_include_tool

from .context import MainAppContext
from .dependencies import get_confluence_fetcher, get_jira_fetcher

logger = logging.getLogger("mcp-atlassian.server.main")


def get_tool_context(server: "AtlassianMCP") -> Any:
    """Get proper context for tool execution with lifespan_context access.

    This function creates a context object that provides access to the
    lifespan_context required by meta-tools and dependency functions.

    This fixes the P0 error: "'Server' object has no attribute 'lifespan_context'"
    that was causing all tool operations to fail.

    Args:
        server: The AtlassianMCP server instance (can be None)

    Returns:
        Context-like object with direct lifespan_context access
    """
    # Create a context object where lifespan_context is directly accessible
    # The dependencies.py functions expect ctx.lifespan_context to work
    class ToolContext:
        def __init__(self, lifespan_context):
            self.lifespan_context = lifespan_context

    try:
        # Handle None server
        if server is None:
            return ToolContext({})

        # Handle missing _mcp_server
        if not hasattr(server, '_mcp_server') or server._mcp_server is None:
            return ToolContext({})

        # Handle missing request_context
        req_context = getattr(server._mcp_server, 'request_context', None)
        if req_context is None:
            return ToolContext({})

        # Handle missing lifespan_context
        if hasattr(req_context, 'lifespan_context'):
            lifespan_context = req_context.lifespan_context
            # Return a copy of the lifespan_context for immutability (if it's a dict)
            if isinstance(lifespan_context, dict):
                return ToolContext(lifespan_context.copy())
            else:
                # Return the lifespan_context as-is for non-dict values (None, strings, etc.)
                return ToolContext(lifespan_context)
        else:
            return ToolContext({})

    except (AttributeError, TypeError, RuntimeError):
        # Handle any unexpected errors during attribute access
        return ToolContext({})


async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@asynccontextmanager
async def main_lifespan(app: FastMCP[MainAppContext]) -> AsyncIterator[dict]:
    logger.info("Main Atlassian MCP server lifespan starting...")
    services = get_available_services()
    read_only = is_read_only_mode()
    enabled_tools = get_enabled_tools()

    # Only meta-tools are available (legacy tools have been removed)
    logger.info("Using meta-tools (legacy tools removed)")

    loaded_jira_config: JiraConfig | None = None
    loaded_confluence_config: ConfluenceConfig | None = None

    if services.get("jira"):
        try:
            jira_config = JiraConfig.from_env()
            if jira_config.is_auth_configured():
                loaded_jira_config = jira_config
                logger.info(
                    "Jira configuration loaded and authentication is configured."
                )
            else:
                logger.warning(
                    "Jira URL found, but authentication is not fully configured. Jira tools will be unavailable."
                )
        except Exception as e:
            logger.error(f"Failed to load Jira configuration: {e}", exc_info=True)

    if services.get("confluence"):
        try:
            confluence_config = ConfluenceConfig.from_env()
            if confluence_config.is_auth_configured():
                loaded_confluence_config = confluence_config
                logger.info(
                    "Confluence configuration loaded and authentication is configured."
                )
            else:
                logger.warning(
                    "Confluence URL found, but authentication is not fully configured. Confluence tools will be unavailable."
                )
        except Exception as e:
            logger.error(f"Failed to load Confluence configuration: {e}", exc_info=True)

    app_context = MainAppContext(
        full_jira_config=loaded_jira_config,
        full_confluence_config=loaded_confluence_config,
        read_only=read_only,
        enabled_tools=enabled_tools,
    )
    logger.info(f"Read-only mode: {'ENABLED' if read_only else 'DISABLED'}")
    logger.info(f"Enabled tools filter: {enabled_tools or 'All tools enabled'}")

    try:
        yield {"app_lifespan_context": app_context}
    except Exception as e:
        logger.error(f"Error during lifespan: {e}", exc_info=True)
        raise
    finally:
        logger.info("Main Atlassian MCP server lifespan shutting down...")
        # Perform any necessary cleanup here
        try:
            # Close any open connections if needed
            if loaded_jira_config:
                logger.debug("Cleaning up Jira resources...")
            if loaded_confluence_config:
                logger.debug("Cleaning up Confluence resources...")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        logger.info("Main Atlassian MCP server lifespan shutdown complete.")


class AtlassianMCP(FastMCP[MainAppContext]):
    """Custom FastMCP server class for Atlassian integration with tool filtering."""

    async def _mcp_list_tools(self) -> list[MCPTool]:
        # Filter tools based on enabled_tools, read_only mode, and service configuration from the lifespan context.
        req_context = self._mcp_server.request_context
        if req_context is None or req_context.lifespan_context is None:
            logger.warning(
                "Lifespan context not available during _main_mcp_list_tools call."
            )
            return []

        lifespan_ctx_dict = req_context.lifespan_context
        app_lifespan_state: MainAppContext | None = (
            lifespan_ctx_dict.get("app_lifespan_context")
            if isinstance(lifespan_ctx_dict, dict)
            else None
        )
        read_only = (
            getattr(app_lifespan_state, "read_only", False)
            if app_lifespan_state
            else False
        )
        enabled_tools_filter = (
            getattr(app_lifespan_state, "enabled_tools", None)
            if app_lifespan_state
            else None
        )
        logger.debug(
            f"_main_mcp_list_tools: read_only={read_only}, enabled_tools_filter={enabled_tools_filter}"
        )

        # Register v2 meta-tools if not already registered
        if not hasattr(self, "_tools_registered"):
            logger.info("Registering v2 (meta) tools")
            register_v2_tools(self)
            self._tools_registered = True

        all_tools: dict[str, FastMCPTool] = await self.get_tools()
        logger.debug(
            f"Aggregated {len(all_tools)} tools before filtering: {list(all_tools.keys())}"
        )

        filtered_tools: list[MCPTool] = []
        for registered_name, tool_obj in all_tools.items():
            tool_tags = tool_obj.tags


            if not should_include_tool(registered_name, enabled_tools_filter):
                logger.debug(f"Excluding tool '{registered_name}' (not enabled)")
                continue

            if tool_obj and read_only and "write" in tool_tags:
                logger.debug(
                    f"Excluding tool '{registered_name}' due to read-only mode and 'write' tag"
                )
                continue

            # Exclude Jira/Confluence tools if config is not fully authenticated
            is_jira_tool = "jira" in tool_tags
            is_confluence_tool = "confluence" in tool_tags
            service_configured_and_available = True
            if app_lifespan_state:
                if is_jira_tool and not app_lifespan_state.full_jira_config:
                    logger.debug(
                        f"Excluding Jira tool '{registered_name}' as Jira configuration/authentication is incomplete."
                    )
                    service_configured_and_available = False
                if is_confluence_tool and not app_lifespan_state.full_confluence_config:
                    logger.debug(
                        f"Excluding Confluence tool '{registered_name}' as Confluence configuration/authentication is incomplete."
                    )
                    service_configured_and_available = False
            elif is_jira_tool or is_confluence_tool:
                logger.warning(
                    f"Excluding tool '{registered_name}' as application context is unavailable to verify service configuration."
                )
                service_configured_and_available = False

            if not service_configured_and_available:
                continue

            filtered_tools.append(tool_obj.to_mcp_tool(name=registered_name))

        logger.debug(
            f"_main_mcp_list_tools: Total tools after filtering: {len(filtered_tools)}"
        )
        return filtered_tools

    def http_app(
        self,
        path: str | None = None,
        middleware: list[Middleware] | None = None,
        transport: Literal["streamable-http", "sse"] = "streamable-http",
    ) -> "Starlette":
        user_token_mw = Middleware(UserTokenMiddleware, mcp_server_ref=self)
        final_middleware_list = [user_token_mw]
        if middleware:
            final_middleware_list.extend(middleware)
        app = super().http_app(
            path=path, middleware=final_middleware_list, transport=transport
        )
        return app


# Thread-safe token validation cache
token_validation_cache: TTLCache[
    int, tuple[bool, str | None, JiraFetcher | None, ConfluenceFetcher | None]
] = TTLCache(maxsize=100, ttl=300)
token_cache_lock = threading.Lock()


class UserTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Atlassian user tokens/credentials from Authorization headers."""

    def __init__(
        self, app: Any, mcp_server_ref: Optional["AtlassianMCP"] = None
    ) -> None:
        super().__init__(app)
        self.mcp_server_ref = mcp_server_ref
        if not self.mcp_server_ref:
            logger.warning(
                "UserTokenMiddleware initialized without mcp_server_ref. Path matching for MCP endpoint might fail if settings are needed."
            )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        logger.debug(
            f"UserTokenMiddleware.dispatch: ENTERED for request path='{request.url.path}', method='{request.method}'"
        )
        mcp_server_instance = self.mcp_server_ref
        if mcp_server_instance is None:
            logger.debug(
                "UserTokenMiddleware.dispatch: self.mcp_server_ref is None. Skipping MCP auth logic."
            )
            return await call_next(request)

        mcp_path = mcp_server_instance.settings.streamable_http_path.rstrip("/")
        request_path = request.url.path.rstrip("/")
        logger.debug(
            f"UserTokenMiddleware.dispatch: Comparing request_path='{request_path}' with mcp_path='{mcp_path}'. Request method='{request.method}'"
        )
        if request_path == mcp_path and request.method == "POST":
            auth_header = request.headers.get("Authorization")
            cloud_id_header = request.headers.get("X-Atlassian-Cloud-Id")

            token_for_log = mask_sensitive(
                auth_header.split(" ", 1)[1].strip()
                if auth_header and " " in auth_header
                else auth_header
            )
            logger.debug(
                f"UserTokenMiddleware: Path='{request.url.path}', AuthHeader='{mask_sensitive(auth_header)}', ParsedToken(masked)='{token_for_log}', CloudId='{cloud_id_header}'"
            )

            # Extract and save cloudId if provided
            if cloud_id_header and cloud_id_header.strip():
                request.state.user_atlassian_cloud_id = cloud_id_header.strip()
                logger.debug(
                    f"UserTokenMiddleware: Extracted cloudId from header: {cloud_id_header.strip()}"
                )
            else:
                request.state.user_atlassian_cloud_id = None
                logger.debug(
                    "UserTokenMiddleware: No cloudId header provided, will use global config"
                )

            # Check for mcp-session-id header for debugging
            mcp_session_id = request.headers.get("mcp-session-id")
            if mcp_session_id:
                logger.debug(
                    f"UserTokenMiddleware: MCP-Session-ID header found: {mcp_session_id}"
                )
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Bearer token"},
                        status_code=401,
                    )
                logger.debug(
                    f"UserTokenMiddleware.dispatch: Bearer token extracted (masked): ...{mask_sensitive(token, 8)}"
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "oauth"
                request.state.user_atlassian_email = None
                logger.debug(
                    f"UserTokenMiddleware.dispatch: Set request.state (pre-validation): "
                    f"auth_type='{getattr(request.state, 'user_atlassian_auth_type', 'N/A')}', "
                    f"token_present={bool(getattr(request.state, 'user_atlassian_token', None))}"
                )
            elif auth_header and auth_header.startswith("Token "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Token (PAT)"},
                        status_code=401,
                    )
                logger.debug(
                    f"UserTokenMiddleware.dispatch: PAT (Token scheme) extracted (masked): ...{mask_sensitive(token, 8)}"
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "pat"
                request.state.user_atlassian_email = (
                    None  # PATs don't carry email in the token itself
                )
                logger.debug(
                    "UserTokenMiddleware.dispatch: Set request.state for PAT auth."
                )
            elif auth_header:
                logger.warning(
                    f"Unsupported Authorization type for {request.url.path}: {auth_header.split(' ', 1)[0] if ' ' in auth_header else 'UnknownType'}"
                )
                return JSONResponse(
                    {
                        "error": "Unauthorized: Only 'Bearer <OAuthToken>' or 'Token <PAT>' types are supported."
                    },
                    status_code=401,
                )
            else:
                logger.debug(
                    f"No Authorization header provided for {request.url.path}. Will proceed with global/fallback server configuration if applicable."
                )
        response = await call_next(request)
        logger.debug(
            f"UserTokenMiddleware.dispatch: EXITED for request path='{request.url.path}'"
        )
        return response


def _format_error_response(
    exception: Exception,
    service: str | None = None,
    resource: str | None = None,
    operation: str | None = None,
    data: dict | None = None
) -> str:
    """Format exception into structured JSON response for AI agents.

    This helper function converts exceptions (especially MetaToolError) into
    structured JSON responses that AI agents can understand and act upon.

    Args:
        exception: The exception that occurred
        service: Service name (jira/confluence) for context
        resource: Resource type for context
        operation: Operation type for context
        data: Original data for context

    Returns:
        JSON string with structured error information
    """
    from ..meta_tools.errors import MetaToolError
    import traceback

    if isinstance(exception, MetaToolError):
        # Use the structured error information from MetaToolError
        error_response = {
            "error": True,
            "error_code": exception.error_code,
            "message": exception.user_message,
            "suggestions": exception.suggestions,
            "context": exception.context,
            "api_endpoint": exception.api_endpoint
        }

        # Add working example for the operation if possible
        if service and resource and operation:
            error_response["working_example"] = _get_working_example(service, resource, operation)

    else:
        # Handle generic exceptions with helpful context
        error_message = str(exception)

        # Create structured error response
        error_response = {
            "error": True,
            "error_code": "GENERIC_ERROR",
            "message": error_message,
            "suggestions": [
                "Check the error message for specific details",
                "Verify all required fields are provided correctly",
                "Check the tool documentation for required field formats"
            ],
            "context": {
                "service": service,
                "resource": resource,
                "operation": operation,
                "provided_data_keys": list(data.keys()) if data else [],
                "exception_type": type(exception).__name__
            }
        }

        # Add working example if we have enough context
        if service and resource and operation:
            error_response["working_example"] = _get_working_example(service, resource, operation)

        # Include traceback in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            error_response["traceback"] = traceback.format_exc()

    return json.dumps(error_response, indent=2)


def _get_working_example(service: str, resource: str, operation: str) -> dict[str, Any]:
    """Get a working example for the given service/resource/operation combination."""
    examples = {
        ("confluence", "page", "create"): {
            "service": "confluence",
            "resource": "page",
            "operation": "create",
            "data": {
                "space_key": "~911651470",
                "title": "My Test Page",
                "body": "# Welcome\\n\\nThis is a test page with **markdown** content."
            }
        },
        ("jira", "issue", "create"): {
            "service": "jira",
            "resource": "issue",
            "operation": "create",
            "data": {
                "project_key": "FTEST",
                "summary": "Example issue summary",
                "issue_type": "Task",
                "description": "Detailed description of the issue"
            }
        },
        ("jira", "comment", "add"): {
            "service": "jira",
            "resource": "comment",
            "operation": "add",
            "identifier": "FTEST-123",
            "data": {
                "body": "This is a comment on the issue"
            }
        }
    }

    key = (service, resource, operation)
    return examples.get(key, {
        "service": service,
        "resource": resource,
        "operation": operation,
        "data": {"field": "example_value"}
    })


def register_v2_tools(server: AtlassianMCP) -> None:
    """Register v2 (meta) tools for token optimization."""
    # Import meta-tools modules here to avoid circular imports
    from ..meta_tools.attachment_handler import AttachmentHandler
    from ..meta_tools.batch_processor import BatchProcessor
    from ..meta_tools.relationship_manager import RelationshipManager
    from ..meta_tools.resource_manager import ResourceManager
    from ..meta_tools.schema_discovery import SchemaDiscovery
    from ..meta_tools.search_engine import SearchEngine
    from ..meta_tools.workflow_engine import WorkflowEngine
    import json

    @server.tool(tags={"debug", "diagnostics"})
    async def debug_context_info(ctx: Context | None = None) -> str:
        """Debug tool to inspect Context object and diagnose MCP issues."""
        import traceback

        try:
            debug_info = {
                "timestamp": "2025-09-20",
                "context_analysis": {},
                "diagnostics": []
            }

            # Check if context exists
            if ctx is None:
                debug_info["context_analysis"]["has_context"] = False
                debug_info["diagnostics"].append("❌ No Context object provided")
                return json.dumps(debug_info, indent=2)

            debug_info["context_analysis"]["has_context"] = True
            debug_info["context_analysis"]["context_type"] = str(type(ctx))
            debug_info["context_analysis"]["context_attrs"] = [attr for attr in dir(ctx) if not attr.startswith('_')]

            # Check request_context
            if hasattr(ctx, 'request_context'):
                debug_info["context_analysis"]["has_request_context"] = True
                if ctx.request_context:
                    debug_info["context_analysis"]["request_context_type"] = str(type(ctx.request_context))
                    debug_info["context_analysis"]["request_context_attrs"] = [attr for attr in dir(ctx.request_context) if not attr.startswith('_')]

                    # Check lifespan_context
                    if hasattr(ctx.request_context, 'lifespan_context'):
                        debug_info["context_analysis"]["has_lifespan_context"] = True
                        if ctx.request_context.lifespan_context:
                            debug_info["context_analysis"]["lifespan_context_type"] = str(type(ctx.request_context.lifespan_context))
                            debug_info["context_analysis"]["lifespan_keys"] = list(ctx.request_context.lifespan_context.keys()) if isinstance(ctx.request_context.lifespan_context, dict) else "Not a dict"
                        else:
                            debug_info["context_analysis"]["lifespan_context"] = "None"
                    else:
                        debug_info["context_analysis"]["has_lifespan_context"] = False
                        debug_info["diagnostics"].append("❌ request_context has no lifespan_context")
                else:
                    debug_info["context_analysis"]["request_context"] = "None"
                    debug_info["diagnostics"].append("❌ request_context is None")
            else:
                debug_info["context_analysis"]["has_request_context"] = False
                debug_info["diagnostics"].append("❌ Context has no request_context attribute")

            # Success message
            if not debug_info["diagnostics"]:
                debug_info["diagnostics"].append("✅ Context structure looks good")

            return json.dumps(debug_info, indent=2)

        except Exception as e:
            return json.dumps({
                "error": True,
                "exception": str(e),
                "traceback": traceback.format_exc()
            }, indent=2)

    # Create meta-tool instances
    resource_manager = ResourceManager()
    schema_discovery = SchemaDiscovery()
    batch_processor = BatchProcessor()
    search_engine = SearchEngine()
    workflow_engine = WorkflowEngine()
    relationship_manager = RelationshipManager()
    attachment_handler = AttachmentHandler()

    @server.tool(tags={"v2", "meta", "crud"})
    async def resource_manager_tool(
        ctx: Context,
        service: str,
        resource: str,
        operation: str,
        identifier: str | None = None,
        data: dict | None = None,
        options: dict | None = None
    ) -> str:
        """Universal CRUD operations for all Jira/Confluence resources.

        This is the primary tool for creating, reading, updating, and deleting resources
        in both Jira and Confluence. Use this tool for all basic operations.

        Parameters:
        - service: "jira" or "confluence"
        - resource: Type of resource (see Available Resources below)
        - operation: Action to perform (see Operations below)
        - identifier: Resource ID/key (required for get/update/delete operations)
        - data: Resource data payload (required for create/update/add operations)
        - options: Additional parameters like fields, expand, etc.

        Available Resources:

        Jira Resources:
        - issue: Jira issues/tickets
        - comment: Comments on issues
        - worklog: Time tracking entries
        - attachment: File attachments
        - link: Issue links between issues
        - sprint: Agile sprint management
        - version: Project versions/releases

        Confluence Resources:
        - page: Wiki pages and documents
        - comment: Comments on pages
        - label: Tags/labels on content
        - space: Confluence spaces

        Operations by Resource:
        - create: Create new resource (requires data parameter)
        - get: Retrieve resource by identifier (requires identifier parameter)
        - update: Modify existing resource (requires identifier and data parameters)
        - delete: Remove resource (requires identifier parameter)
        - add: Add sub-resource like comment/worklog (requires identifier and data parameters)

        Required Fields by Operation:

        Confluence Page (create):
        - space_key: "~911651470" (personal space) or "TEAMSPACE" (team space)
        - title: "Page Title"
        - body: "Page content with **markdown** support"
        Optional: parent_id, labels

        Confluence Page (update):
        - title: "Updated Page Title" (if changing title)
        - body: "Updated content" (if changing content)
        - version: Current page version number (auto-incremented if not provided)

        Jira Issue (create):
        - project_key: "FTEST" (from environment configuration)
        - summary: "Issue title/summary"
        - issue_type: "Task", "Bug", "Story", etc.
        Optional: description, assignee, priority, labels, components

        Jira Issue (update):
        - Any field that exists on the issue type
        Common: summary, description, assignee, priority, status

        Comment (add) - both Jira and Confluence:
        - body: "Comment text content"

        Worklog (add) - Jira only:
        - time_spent: "2h 30m" or "1d 4h" (Jira time format)
        Optional: comment, started (datetime)

        Common Usage Examples:

        1. Create Confluence Page in Personal Space:
        await resource_manager_tool(
            service="confluence",
            resource="page",
            operation="create",
            data={
                "space_key": "~911651470",
                "title": "My Test Page",
                "body": "This is a test page with **bold** text and *italic* text."
            }
        )

        2. Create Jira Issue:
        await resource_manager_tool(
            service="jira",
            resource="issue",
            operation="create",
            data={
                "project_key": "FTEST",
                "summary": "Fix login bug",
                "issue_type": "Bug",
                "description": "Users cannot log in with special characters in password"
            }
        )

        3. Add Comment to Jira Issue:
        await resource_manager_tool(
            service="jira",
            resource="comment",
            operation="add",
            identifier="FTEST-123",
            data={
                "body": "I've reproduced this issue and working on a fix."
            }
        )

        4. Get Confluence Page:
        await resource_manager_tool(
            service="confluence",
            resource="page",
            operation="get",
            identifier="123456789",
            options={"expand": "body.storage,version"}
        )

        5. Update Jira Issue:
        await resource_manager_tool(
            service="jira",
            resource="issue",
            operation="update",
            identifier="FTEST-123",
            data={
                "summary": "Updated issue title",
                "priority": "High"
            }
        )

        Error Handling:
        - Invalid service/resource combinations return helpful error messages
        - Missing required fields are identified with examples

        For more specific examples, use the get_resource_schema tool with your
        specific service, resource, and operation combination."""
        try:
            result = await resource_manager.execute_operation(
                ctx=ctx,
                service=service,
                resource=resource,
                operation=operation,
                identifier=identifier,
                data=data,
                options=options
            )
            return result
        except Exception as e:
            logger.error(f"Error in resource_manager_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, service, resource, operation, data)

    @server.tool(tags={"v2", "meta", "discovery"})
    async def get_resource_schema(
        service: str,
        resource: str,
        operation: str = "create"
    ) -> str:
        """Get detailed schema information for specific resource operations.

        This tool provides detailed field requirements, types, and examples
        for any resource operation. Use this when you need to understand
        exactly what fields are required for a specific operation.

        Parameters:
        - service: "jira" or "confluence"
        - resource: Resource type (issue, page, comment, etc.)
        - operation: Operation type (create, update, get, delete, add)

        Usage Examples:

        1. Get Confluence Page Creation Schema:
        await get_resource_schema(
            service="confluence",
            resource="page",
            operation="create"
        )

        2. Get Jira Issue Update Schema:
        await get_resource_schema(
            service="jira",
            resource="issue",
            operation="update"
        )

        Returns detailed information including:
        - Required vs optional fields
        - Field types and formats
        - Example values
        - Common usage patterns"""
        try:
            schema_info = schema_discovery.get_resource_schema(
                service=service,
                resource=resource,
                operation=operation
            )
            return schema_info.model_dump_json()
        except Exception as e:
            logger.error(f"Error in get_resource_schema: {e}", exc_info=True)
            raise

    @server.tool(tags={"v2", "meta", "discovery"})
    async def get_capabilities(
        service: str | None = None
    ) -> str:
        """Get comprehensive capabilities overview for all available services and operations.

        This tool provides a high-level overview of what resources and operations
        are available in the MCP server. Use this to discover what's possible.

        Parameters:
        - service: Optional service filter ("jira" or "confluence")
                  If not provided, returns capabilities for both services

        Usage Examples:

        1. Get All Capabilities:
        await get_capabilities()

        2. Get Jira-Only Capabilities:
        await get_capabilities(service="jira")

        3. Get Confluence-Only Capabilities:
        await get_capabilities(service="confluence")

        Returns information about:
        - Available resources per service
        - Supported operations per resource
        - Common usage patterns
        - Example tool calls"""
        try:
            capabilities = schema_discovery.get_capabilities(service=service)
            return json.dumps(capabilities, indent=2)
        except Exception as e:
            logger.error(f"Error in get_capabilities: {e}", exc_info=True)
            raise

    @server.tool(tags={"v2", "meta", "examples"})
    async def get_tool_examples(
        operation_type: str | None = None,
        service: str | None = None
    ) -> str:
        """Get practical examples for common operations.

        This tool provides copy-paste ready examples for the most common
        operations you'll want to perform. Perfect for getting started quickly.

        Parameters:
        - operation_type: Filter by operation ("create", "search", "update", etc.)
        - service: Filter by service ("jira", "confluence", or both)

        Usage Examples:

        1. Get All Examples:
        await get_tool_examples()

        2. Get Creation Examples:
        await get_tool_examples(operation_type="create")

        3. Get Jira Examples:
        await get_tool_examples(service="jira")

        4. Get Confluence Creation Examples:
        await get_tool_examples(operation_type="create", service="confluence")
        """
        try:
            examples = {
                "confluence_page_create": {
                    "description": "Create a Confluence page in personal space",
                    "tool": "resource_manager_tool",
                    "example": {
                        "service": "confluence",
                        "resource": "page",
                        "operation": "create",
                        "data": {
                            "space_key": "~911651470",
                            "title": "My Test Page with Rich Formatting",
                            "body": """# Welcome to My Test Page

This page demonstrates various formatting options:

## Text Formatting
- **Bold text** for emphasis
- *Italic text* for subtle emphasis
- ~~Strikethrough text~~ for corrections
- `Inline code` for technical terms

## Lists
1. Numbered list item 1
2. Numbered list item 2
   - Nested bullet point
   - Another nested item

## Code Block
```python
def hello_world():
    print("Hello from Confluence!")
```

## Links and References
Visit [Atlassian Documentation](https://www.atlassian.com/software/confluence) for more info.

## Tables
| Feature | Status | Notes |
|---------|---------|-------|
| Page Creation | ✅ Complete | Working perfectly |
| Rich Formatting | ✅ Complete | All markdown supported |
| ADF Conversion | ✅ Complete | Automatic for Cloud |

This page was created via the MCP Atlassian server!"""
                        }
                    }
                },
                "jira_issue_create": {
                    "description": "Create a Jira issue",
                    "tool": "resource_manager_tool",
                    "example": {
                        "service": "jira",
                        "resource": "issue",
                        "operation": "create",
                        "data": {
                            "project_key": "FTEST",
                            "summary": "Implement user authentication system",
                            "issue_type": "Task",
                            "description": """## Overview
Need to implement a secure user authentication system.

## Requirements
- [ ] User login/logout functionality
- [ ] Password strength validation
- [ ] Session management
- [ ] Multi-factor authentication support

## Acceptance Criteria
- Users can log in with email/password
- Sessions expire after 24 hours of inactivity
- Failed login attempts are rate limited
- All authentication events are logged""",
                            "priority": "High",
                            "labels": ["security", "authentication", "user-management"]
                        }
                    }
                },
                "confluence_search": {
                    "description": "Search Confluence pages",
                    "tool": "search_engine_tool",
                    "example": {
                        "service": "confluence",
                        "query_type": "cql",
                        "query": "space = '~911651470' AND type = page AND title ~ 'test'",
                        "options": {"limit": 25}
                    }
                },
                "jira_search": {
                    "description": "Search Jira issues",
                    "tool": "search_engine_tool",
                    "example": {
                        "service": "jira",
                        "query_type": "jql",
                        "query": "project = FTEST AND status = 'In Progress' ORDER BY updated DESC",
                        "options": {"limit": 20}
                    }
                },
                "add_comment": {
                    "description": "Add comment to Jira issue",
                    "tool": "resource_manager_tool",
                    "example": {
                        "service": "jira",
                        "resource": "comment",
                        "operation": "add",
                        "identifier": "FTEST-123",
                        "data": {
                            "body": "Updated the implementation based on code review feedback. Ready for testing."
                        }
                    }
                },
                "transition_issue": {
                    "description": "Move Jira issue to next status",
                    "tool": "workflow_engine_tool",
                    "example": {
                        "operation": "transition",
                        "issue_key": "FTEST-123",
                        "transition_name": "In Progress",
                        "fields": {
                            "assignee": {"name": "john.doe@example.com"},
                            "comment": "Starting work on this issue"
                        }
                    }
                }
            }

            # Filter examples based on parameters
            filtered_examples = {}

            for key, example in examples.items():
                include = True

                if service:
                    example_service = example["example"].get("service")
                    if example_service and example_service != service:
                        include = False

                if operation_type:
                    example_op = example["example"].get("operation")
                    example_tool = example["tool"]

                    # Map operation types to relevant examples
                    if operation_type == "create" and example_op != "create":
                        include = False
                    elif operation_type == "search" and "search" not in example_tool:
                        include = False
                    elif operation_type == "update" and example_op not in ["update", "transition"]:
                        include = False

                if include:
                    filtered_examples[key] = example

            result = {
                "description": "Practical examples for common MCP Atlassian operations",
                "usage_note": "Copy these examples and modify the data fields as needed",
                "environment_values": {
                    "confluence_space": "~911651470",
                    "jira_project": "FTEST"
                },
                "examples": filtered_examples
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in get_tool_examples: {e}", exc_info=True)
            raise

    @server.tool(tags={"v2", "meta", "search"})
    async def search_engine_tool(
        ctx: Context,
        service: str,
        query_type: str,
        query: str | dict | None = None,
        options: dict | None = None
    ) -> str:
        """Universal search engine for Jira/Confluence.

        This tool provides comprehensive search capabilities across both Jira and Confluence,
        supporting multiple query types and advanced search options.

        Parameters:
        - service: "jira" or "confluence"
        - query_type: Type of search to perform (see Query Types below)
        - query: Search query string or structured query object
        - options: Additional search parameters (limit, start, expand, etc.)

        Jira Query Types:
        - jql: JQL (Jira Query Language) search
        - text: Simple text search across issues
        - issues_in_project: Find issues in specific project
        - issues_by_assignee: Find issues assigned to user
        - recent_issues: Get recently updated issues

        Confluence Query Types:
        - cql: CQL (Confluence Query Language) search
        - text: Simple text search across pages
        - pages_in_space: Find pages in specific space
        - pages_by_title: Search pages by title
        - recent_pages: Get recently updated pages

        Query Examples:

        Jira JQL Search:
        query = "project = FTEST AND status = 'In Progress' ORDER BY updated DESC"

        Jira Text Search:
        query = "login bug authentication"

        Confluence CQL Search:
        query = "space = '~911651470' AND type = page AND title ~ 'test'"

        Confluence Text Search:
        query = "API documentation tutorial"

        Common Options:
        - limit: Maximum results to return (default: 50, max: 1000)
        - start: Starting index for pagination (default: 0)
        - expand: Additional fields to include in results
        - fields: Specific fields to return

        Usage Examples:

        1. Search Jira Issues with JQL:
        await search_engine_tool(
            service="jira",
            query_type="jql",
            query="project = FTEST AND assignee = currentUser()",
            options={"limit": 20, "expand": "names"}
        )

        2. Simple Text Search in Jira:
        await search_engine_tool(
            service="jira",
            query_type="text",
            query="authentication bug",
            options={"limit": 10}
        )

        3. Search Confluence Pages with CQL:
        await search_engine_tool(
            service="confluence",
            query_type="cql",
            query="space = '~911651470' AND type = page",
            options={"limit": 25, "expand": "body.storage"}
        )

        4. Find Pages in Personal Space:
        await search_engine_tool(
            service="confluence",
            query_type="pages_in_space",
            query="~911651470",
            options={"limit": 50}
        )

        5. Recent Issues in Project:
        await search_engine_tool(
            service="jira",
            query_type="recent_issues",
            options={"limit": 15, "project": "FTEST"}
        )

        Advanced Query Patterns:

        Jira JQL Examples:
        - Find bugs: "project = FTEST AND issuetype = Bug"
        - Open issues: "project = FTEST AND status != Done"
        - My issues: "assignee = currentUser() AND status != Done"
        - Recent activity: "updated >= -7d ORDER BY updated DESC"

        Confluence CQL Examples:
        - Personal pages: "space = '~911651470' AND type = page"
        - Recent pages: "lastModified >= '2024-01-01' ORDER BY lastModified DESC"
        - Pages with label: "label = 'documentation' AND type = page"
        - Title search: "title ~ 'API' AND space = 'DEV'"

        Error Handling:
        - Invalid JQL/CQL syntax returns detailed error messages
        - Permission errors include guidance on required access
"""
        try:
            result = await search_engine.execute_search(
                ctx=ctx,
                service=service,
                query_type=query_type,
                query=query,
                options=options
            )
            return result
        except Exception as e:
            logger.error(f"Error in search_engine_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, service, "search", query_type, {"query": query, "options": options})

    @server.tool(tags={"v2", "meta", "batch"})
    async def batch_processor_tool(
        ctx: Context,
        service: str,
        operation: str,
        resource: str,
        items: list[dict],
        concurrency: int = 5
    ) -> str:
        """Process multiple operations in parallel.

        Efficiently process multiple create, update, or delete operations
        in parallel to improve performance for bulk operations.

        Parameters:
        - service: "jira" or "confluence"
        - operation: "create", "update", or "delete"
        - resource: Resource type (issue, page, comment, etc.)
        - items: List of data objects for the operations
        - concurrency: Number of parallel operations (default: 5, max: 10)

        Usage Examples:

        1. Create Multiple Jira Issues:
        await batch_processor_tool(
            service="jira",
            operation="create",
            resource="issue",
            items=[
                {
                    "project_key": "FTEST",
                    "summary": "Bug 1",
                    "issue_type": "Bug"
                },
                {
                    "project_key": "FTEST",
                    "summary": "Bug 2",
                    "issue_type": "Bug"
                }
            ],
            concurrency=3
        )

        2. Update Multiple Confluence Pages:
        await batch_processor_tool(
            service="confluence",
            operation="update",
            resource="page",
            items=[
                {
                    "id": "123456",
                    "title": "Updated Page 1",
                    "body": "New content"
                },
                {
                    "id": "789012",
                    "title": "Updated Page 2",
                    "body": "Different content"
                }
            ]
        )"""
        try:
            # Clamp concurrency to valid range
            clamped_concurrency = max(1, min(concurrency, 10))
            
            result = await batch_processor.execute_batch_operation(
                ctx=ctx,
                service=service,
                operation=operation,
                resource_type=resource,
                items=items,
                options={"concurrency": clamped_concurrency}  # FIX: Pass concurrency in options
            )
            return result
        except Exception as e:
            logger.error(f"Error in batch_processor_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, service, resource, operation, {"items": items, "concurrency": concurrency})


    @server.tool(tags={"v2", "meta", "workflow"})
    async def workflow_engine_tool(
        ctx: Context,
        operation: str,
        issue_key: str | None = None,
        transition_id: str | None = None,
        transition_name: str | None = None,
        fields: dict | None = None,
        project_key: str | None = None,
        issue_type: str | None = None,
        options: dict | None = None
    ) -> str:
        """Universal workflow engine for Jira.

        This tool manages Jira issue workflows, transitions, and status changes.
        Use this for moving issues through their lifecycle and managing workflow states.

        Parameters:
        - operation: Workflow operation to perform (see Operations below)
        - issue_key: Jira issue key (required for most operations)
        - transition_id: Numeric ID of transition (alternative to transition_name)
        - transition_name: Human-readable name of transition (e.g., "In Progress", "Done")
        - fields: Additional field updates during transition
        - project_key: Project key (required for workflow discovery operations)
        - issue_type: Issue type (required for some discovery operations)
        - options: Additional parameters

        Available Operations:
        - transition: Move issue through workflow transition
        - get_transitions: Get available transitions for an issue
        - get_workflow: Get workflow information for project/issue type
        - get_statuses: Get all possible statuses for project
        - get_status: Get current status of an issue

        Common Workflow Operations:

        1. Transition Issue (by name):
        await workflow_engine_tool(
            operation="transition",
            issue_key="FTEST-123",
            transition_name="In Progress",
            fields={
                "assignee": {"name": "john.doe@example.com"},
                "comment": "Starting work on this issue"
            }
        )

        2. Transition Issue (by ID):
        await workflow_engine_tool(
            operation="transition",
            issue_key="FTEST-123",
            transition_id="21",
            fields={"resolution": {"name": "Fixed"}}
        )

        3. Get Available Transitions:
        await workflow_engine_tool(
            operation="get_transitions",
            issue_key="FTEST-123"
        )

        4. Get Project Workflow:
        await workflow_engine_tool(
            operation="get_workflow",
            project_key="FTEST",
            issue_type="Task"
        )

        5. Get All Project Statuses:
        await workflow_engine_tool(
            operation="get_statuses",
            project_key="FTEST"
        )

        Common Transition Names:
        - "To Do" → "In Progress" → "Done"
        - "Open" → "In Progress" → "Resolved" → "Closed"
        - "Backlog" → "Selected for Development" → "In Progress" → "Done"

        Field Updates During Transitions:
        You can update fields while transitioning:
        - assignee: {"name": "user@example.com"}
        - resolution: {"name": "Fixed"} or {"name": "Won't Fix"}
        - comment: "Transition comment"
        - customfield_xxxxx: Custom field values

        Error Handling:
        - Invalid transitions return available options
        - Missing permissions include required roles
        - Field validation errors show required format

        Tips:
        - Use get_transitions first to see what's available
        - Transition names are case-sensitive
        - Some transitions require specific fields (e.g., resolution for "Done")
"""
        try:
            result = await workflow_engine.execute_workflow_operation(
                ctx=ctx,
                operation=operation,
                issue_key=issue_key,
                transition_id=transition_id,
                transition_name=transition_name,
                fields=fields,
                project_key=project_key,
                issue_type=issue_type,
                options=options
            )
            return result
        except Exception as e:
            logger.error(f"Error in workflow_engine_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, "jira", "workflow", operation, {
                "issue_key": issue_key,
                "transition_id": transition_id,
                "transition_name": transition_name,
                "fields": fields
            })

    @server.tool(tags={"v2", "meta", "relationships"})
    async def relationship_manager_tool(
        ctx: Context,
        operation: str,
        issue_key: str,
        target_issue_key: str | None = None,
        link_type: str | None = None,
        epic_key: str | None = None,
        parent_key: str | None = None,
        comment: str | None = None,
        link_id: str | None = None,
        options: dict | None = None
    ) -> str:
        """Universal relationship manager for Jira.

        Manage relationships between Jira issues including links, epic assignments,
        and parent-child hierarchies.

        Parameters:
        - operation: Relationship operation (link, unlink, add_to_epic, etc.)
        - issue_key: Source issue key (e.g., "FTEST-123")
        - target_issue_key: Target issue for linking operations
        - link_type: Type of link ("Blocks", "Duplicates", "Relates", etc.)
        - epic_key: Epic issue key for epic operations
        - parent_key: Parent issue key for sub-task operations
        - comment: Optional comment for the relationship
        - link_id: Existing link ID for unlink operations

        Common Operations:
        - link: Create link between two issues
        - unlink: Remove link between issues
        - add_to_epic: Add issue to epic
        - remove_from_epic: Remove issue from epic
        - get_links: Get all links for an issue

        Usage Examples:

        1. Link Issues:
        await relationship_manager_tool(
            operation="link",
            issue_key="FTEST-123",
            target_issue_key="FTEST-456",
            link_type="Blocks",
            comment="This issue blocks the other"
        )

        2. Add Issue to Epic:
        await relationship_manager_tool(
            operation="add_to_epic",
            issue_key="FTEST-123",
            epic_key="FTEST-100"
        )

        3. Get Issue Links:
        await relationship_manager_tool(
            operation="get_links",
            issue_key="FTEST-123"
        )"""
        try:
            result = await relationship_manager.execute_relationship_operation(
                ctx=ctx,
                operation=operation,
                issue_key=issue_key,
                target_issue_key=target_issue_key,
                link_type=link_type,
                epic_key=epic_key,
                parent_key=parent_key,
                comment=comment,
                link_id=link_id,
                options=options
            )
            return result
        except Exception as e:
            logger.error(f"Error in relationship_manager_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, "jira", "relationship", operation, {
                "issue_key": issue_key,
                "target_issue_key": target_issue_key,
                "link_type": link_type,
                "epic_key": epic_key
            })

    @server.tool(tags={"v2", "meta", "attachments"})
    async def attachment_handler_tool(
        ctx: Context,
        service: str,
        operation: str,
        issue_key: str | None = None,
        page_id: str | None = None,
        attachment_id: str | None = None,
        file_path: str | None = None,
        file_name: str | None = None,
        file_content: bytes | None = None,
        download_path: str | None = None,
        options: dict | None = None
    ) -> str:
        """Universal attachment handler for Jira/Confluence.

        Upload, download, and manage file attachments for issues and pages.

        Parameters:
        - service: "jira" or "confluence"
        - operation: "upload", "download", "list", "delete"
        - issue_key: Jira issue key (for Jira attachments)
        - page_id: Confluence page ID (for Confluence attachments)
        - attachment_id: Existing attachment ID (for download/delete)
        - file_path: Local file path for upload/download
        - file_name: Name for uploaded file
        - file_content: Raw file content (alternative to file_path)
        - download_path: Where to save downloaded files

        Usage Examples:

        1. Upload File to Jira Issue:
        await attachment_handler_tool(
            service="jira",
            operation="upload",
            issue_key="FTEST-123",
            file_path="/path/to/screenshot.png",
            file_name="bug_screenshot.png"
        )

        2. Upload to Confluence Page:
        await attachment_handler_tool(
            service="confluence",
            operation="upload",
            page_id="123456789",
            file_path="/path/to/document.pdf"
        )

        3. List Attachments:
        await attachment_handler_tool(
            service="jira",
            operation="list",
            issue_key="FTEST-123"
        )

        4. Download Attachment:
        await attachment_handler_tool(
            service="jira",
            operation="download",
            attachment_id="987654",
            download_path="/downloads/file.pdf"
        )"""
        try:
            result = await attachment_handler.execute_attachment_operation(
                ctx=ctx,
                service=service,
                operation=operation,
                issue_key=issue_key,
                page_id=page_id,
                attachment_id=attachment_id,
                file_path=file_path,
                file_name=file_name,
                file_content=file_content,
                download_path=download_path,
                options=options
            )
            return result
        except Exception as e:
            logger.error(f"Error in attachment_handler_tool: {e}", exc_info=True)
            # Return structured error information instead of re-raising
            return _format_error_response(e, service, "attachment", operation, {
                "issue_key": issue_key,
                "page_id": page_id,
                "attachment_id": attachment_id,
                "file_path": file_path,
                "file_name": file_name
            })

    @server.tool(tags={"v2", "meta", "health"})
    async def connection_health_check(
        ctx: Context,
        service: str | None = None
    ) -> str:
        """Check connection health for Atlassian services.

        Validates connectivity and authentication for Jira and/or Confluence.

        Parameters:
        - service: "jira", "confluence", or None for both

        Returns:
        JSON string with health check results including:
        - Configuration status
        - Authentication status
        - API connectivity status
        - Error details if any issues found
        """
        try:
            health_results = {"timestamp": "2025-01-01T00:00:00Z", "checks": {}}

            services_to_check = ["jira", "confluence"] if service is None else [service]

            for svc in services_to_check:
                health_results["checks"][svc] = await _check_service_health(ctx, svc)

            # Overall status
            all_healthy = all(
                check.get("status") == "healthy"
                for check in health_results["checks"].values()
            )
            health_results["overall_status"] = "healthy" if all_healthy else "unhealthy"

            return json.dumps(health_results, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error in connection_health_check: {e}", exc_info=True)
            return _format_error_response(e, service, "health", "check", {})


async def _check_service_health(ctx: Any, service: str) -> dict[str, Any]:
    """Check health of a specific service."""
    health_check = {
        "service": service,
        "status": "unknown",
        "configuration": "unknown",
        "authentication": "unknown",
        "connectivity": "unknown",
        "errors": [],
        "diagnostics": {
            "environment_vars_checked": [],
            "config_present": False,
            "auth_type": "unknown",
            "is_cloud": None,
        }
    }

    try:
        # Check environment variables and configuration
        import os

        if service == "jira":
            # Check relevant environment variables
            env_vars = ["JIRA_URL", "ATLASSIAN_URL", "JIRA_USERNAME", "ATLASSIAN_EMAIL",
                       "JIRA_API_TOKEN", "ATLASSIAN_API_TOKEN", "ATLASSIAN_OAUTH_ACCESS_TOKEN",
                       "ATLASSIAN_OAUTH_CLOUD_ID"]
            for var in env_vars:
                if os.getenv(var):
                    health_check["diagnostics"]["environment_vars_checked"].append(f"{var}=present")
                else:
                    health_check["diagnostics"]["environment_vars_checked"].append(f"{var}=absent")

            try:
                fetcher = await get_jira_fetcher(ctx)
                health_check["configuration"] = "valid"
                health_check["diagnostics"]["config_present"] = True
                health_check["diagnostics"]["auth_type"] = fetcher.config.auth_type
                health_check["diagnostics"]["is_cloud"] = fetcher.config.is_cloud
                if hasattr(fetcher.config, 'oauth_config') and fetcher.config.oauth_config:
                    health_check["diagnostics"]["oauth_cloud_id"] = fetcher.config.oauth_config.cloud_id
            except Exception as e:
                health_check["configuration"] = "invalid"
                health_check["errors"].append(f"Jira configuration error: {str(e)}")
                health_check["status"] = "unhealthy"
                health_check["verification_method"] = "configuration_validation_failed_before_api_testing"
                health_check["note"] = "Cannot perform operational API tests due to configuration issues"
                health_check["diagnostics"]["config_error"] = str(e)
                return health_check

        elif service == "confluence":
            # Check relevant environment variables
            env_vars = ["CONFLUENCE_URL", "ATLASSIAN_URL", "CONFLUENCE_USERNAME", "ATLASSIAN_EMAIL",
                       "CONFLUENCE_API_TOKEN", "ATLASSIAN_API_TOKEN", "ATLASSIAN_OAUTH_ACCESS_TOKEN",
                       "ATLASSIAN_OAUTH_CLOUD_ID"]
            for var in env_vars:
                if os.getenv(var):
                    health_check["diagnostics"]["environment_vars_checked"].append(f"{var}=present")
                else:
                    health_check["diagnostics"]["environment_vars_checked"].append(f"{var}=absent")

            try:
                fetcher = await get_confluence_fetcher(ctx)
                health_check["configuration"] = "valid"
                health_check["diagnostics"]["config_present"] = True
                health_check["diagnostics"]["auth_type"] = fetcher.config.auth_type
                health_check["diagnostics"]["is_cloud"] = fetcher.config.is_cloud
                if hasattr(fetcher.config, 'oauth_config') and fetcher.config.oauth_config:
                    health_check["diagnostics"]["oauth_cloud_id"] = fetcher.config.oauth_config.cloud_id
            except Exception as e:
                health_check["configuration"] = "invalid"
                health_check["errors"].append(f"Confluence configuration error: {str(e)}")
                health_check["status"] = "unhealthy"
                health_check["verification_method"] = "configuration_validation_failed_before_api_testing"
                health_check["note"] = "Cannot perform operational API tests due to configuration issues"
                health_check["diagnostics"]["config_error"] = str(e)
                return health_check


        # Test authentication and connectivity with actual API operations
        try:
            if service == "jira":
                # Execute actual API call to test operational capability
                user = fetcher.get_current_user_account_id()
                health_check["authentication"] = "verified_via_api_call"
                health_check["connectivity"] = "tested_successfully"
                health_check["operations_tested"] = ["get_current_user_account_id"]
                health_check["api_functionality"] = "working"
            elif service == "confluence":
                # Execute actual API call to test operational capability
                user = fetcher.get_current_user()
                health_check["authentication"] = "verified_via_api_call"
                health_check["connectivity"] = "tested_successfully"
                health_check["operations_tested"] = ["get_current_user"]
                health_check["api_functionality"] = "working"

            health_check["status"] = "healthy"
            health_check["verification_method"] = "actual_api_operations_performed"

        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "unauthorized" in error_str:
                health_check["authentication"] = "failed_during_api_call"
                health_check["errors"].append(f"Authentication failed during operational test: {str(e)}")
            else:
                health_check["connectivity"] = "failed_during_api_call"
                health_check["errors"].append(f"API operation failed: {str(e)}")
            health_check["status"] = "unhealthy"
            health_check["verification_method"] = "actual_api_operations_attempted_but_failed"

    except Exception as e:
        health_check["status"] = "unhealthy"
        health_check["errors"].append(f"Unexpected error: {str(e)}")

    return health_check


main_mcp = AtlassianMCP(name="Atlassian MCP", lifespan=main_lifespan)

# Version-aware tool registration will happen dynamically based on context


@main_mcp.resource("confluence://troubleshooting")
async def confluence_troubleshooting_guide() -> str:
    """Confluence page creation troubleshooting guide for AI agents."""
    import os
    from pathlib import Path

    guide_path = Path(__file__).parent.parent / "resources" / "confluence_troubleshooting.md"
    if guide_path.exists():
        return guide_path.read_text(encoding="utf-8")
    else:
        return "# Troubleshooting guide not found\n\nThe confluence troubleshooting guide is not available."


@main_mcp.resource("atlassian://field-mappings")
async def field_mappings() -> str:
    """Field mappings and examples for all MCP Atlassian operations."""
    import os
    from pathlib import Path

    mappings_path = Path(__file__).parent.parent / "resources" / "field_mappings.json"
    if mappings_path.exists():
        return mappings_path.read_text(encoding="utf-8")
    else:
        return '{"error": "Field mappings file not found"}'


@main_mcp.resource("atlassian://help")
async def help_resource() -> str:
    """Quick help resource for common MCP Atlassian operations."""
    return """# MCP Atlassian Quick Help

## Most Common Operations

### Create Confluence Page
```json
{
  "service": "confluence",
  "resource": "page",
  "operation": "create",
  "data": {
    "space_key": "~911651470",
    "title": "My Page Title",
    "body": "# Content\\n\\nMarkdown content here"
  }
}
```

### Create Jira Issue
```json
{
  "service": "jira",
  "resource": "issue",
  "operation": "create",
  "data": {
    "project_key": "FTEST",
    "summary": "Issue title",
    "issue_type": "Task",
    "description": "Issue description"
  }
}
```

## Error Handling
- Always check error messages for specific guidance
- Check the confluence://troubleshooting resource for detailed help
- Reference atlassian://field-mappings for correct field names

## Getting More Help
- Query confluence://troubleshooting for Confluence issues
- Query atlassian://field-mappings for field reference
- Use get_resource_schema tool for operation-specific schemas
- Use get_tool_examples tool for copy-paste examples
"""


@main_mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
async def _health_check_route(request: Request) -> JSONResponse:
    return await health_check(request)


logger.info("Added /healthz endpoint for Kubernetes probes")
