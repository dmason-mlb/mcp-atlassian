"""Confluence page management tools."""

import json
import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import BeforeValidator, Field

from mcp_atlassian.servers.dependencies import get_confluence_fetcher
from mcp_atlassian.utils.decorators import check_write_access

logger = logging.getLogger(__name__)

# Create FastMCP instance for pages
pages_mcp = FastMCP(
    name="Confluence Pages Service",
    description="Provides tools for Confluence page management.",
)


class PagesServer:
    """Container for Confluence page management tools."""

    def __init__(self):
        self.mcp = pages_mcp

    def get_tools(self):
        """Get all page management tools."""
        return self.mcp.tools


@pages_mcp.tool(tags={"confluence", "read"})
async def get_page(
    ctx: Context,
    page_id: Annotated[
        str | None,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be found in the page URL). "
                "For example, in the URL 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title', "
                "the page ID is '123456789'. "
                "Provide this OR both 'title' and 'space_key'. If page_id is provided, title and space_key will be ignored."
            ),
            default=None,
        ),
    ] = None,
    title: Annotated[
        str | None,
        Field(
            description=(
                "The exact title of the Confluence page. Use this with 'space_key' if 'page_id' is not known."
            ),
            default=None,
        ),
    ] = None,
    space_key: Annotated[
        str | None,
        Field(
            description=(
                "The key of the Confluence space where the page resides (e.g., 'DEV', 'TEAM'). Required if using 'title'."
            ),
            default=None,
        ),
    ] = None,
    include_metadata: Annotated[
        bool,
        Field(
            description="Whether to include page metadata such as creation date, last update, version, and labels.",
            default=True,
        ),
    ] = True,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description=(
                "Whether to convert page to markdown (true) or keep it in raw HTML format (false). "
                "Raw HTML can reveal macros (like dates) not visible in markdown, but CAUTION: "
                "using HTML significantly increases token usage in AI responses."
            ),
            default=True,
        ),
    ] = True,
) -> str:
    """Get content of a specific Confluence page by its ID, or by its title and space key.

    Args:
        ctx: The FastMCP context.
        page_id: Confluence page ID. If provided, 'title' and 'space_key' are ignored.
        title: The exact title of the page. Must be used with 'space_key'.
        space_key: The key of the space. Must be used with 'title'.
        include_metadata: Whether to include page metadata.
        convert_to_markdown: Convert content to markdown (true) or keep raw HTML (false).

    Returns:
        JSON string representing the page content and/or metadata, or an error if not found or parameters are invalid.
    """
    from . import get_confluence_fetcher  # lazy import to allow test patching

    confluence_fetcher = await get_confluence_fetcher(ctx)
    page_object = None

    if page_id:
        if title or space_key:
            logger.warning(
                "page_id was provided; title and space_key parameters will be ignored."
            )
        try:
            page_object = confluence_fetcher.get_page_content(
                page_id, convert_to_markdown=convert_to_markdown
            )
        except Exception as e:
            logger.error(f"Error fetching page by ID '{page_id}': {e}")
            return json.dumps(
                {"error": f"Failed to retrieve page by ID '{page_id}': {e}"},
                indent=2,
                ensure_ascii=False,
            )
    elif title and space_key:
        page_object = confluence_fetcher.get_page_by_title(
            space_key, title, convert_to_markdown=convert_to_markdown
        )
        if not page_object:
            return json.dumps(
                {
                    "error": f"Page with title '{title}' not found in space '{space_key}'."
                },
                indent=2,
                ensure_ascii=False,
            )
    else:
        raise ValueError(
            "Either 'page_id' OR both 'title' and 'space_key' must be provided."
        )

    if not page_object:
        return json.dumps(
            {"error": "Page not found with the provided identifiers."},
            indent=2,
            ensure_ascii=False,
        )

    if include_metadata:
        result = {"metadata": page_object.to_simplified_dict()}
    else:
        result = {"content": {"value": page_object.content}}

    return json.dumps(result, indent=2, ensure_ascii=False)


@pages_mcp.tool(tags={"confluence", "read"})
async def get_page_children(
    ctx: Context,
    parent_id: Annotated[
        str,
        Field(
            description="The ID of the parent page whose children you want to retrieve"
        ),
    ],
    expand: Annotated[
        str,
        Field(
            description="Fields to expand in the response (e.g., 'version', 'body.storage')",
            default="version",
        ),
    ] = "version",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of child pages to return (1-50)",
            default=25,
            ge=1,
            le=50,
        ),
    ] = 25,
    include_content: Annotated[
        bool,
        Field(
            description="Whether to include the page content in the response",
            default=False,
        ),
    ] = False,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description="Whether to convert page content to markdown (true) or keep it in raw HTML format (false). Only relevant if include_content is true.",
            default=True,
        ),
    ] = True,
    start: Annotated[
        int,
        Field(description="Starting index for pagination (0-based)", default=0, ge=0),
    ] = 0,
) -> str:
    """Get child pages of a specific Confluence page.

    Args:
        ctx: The FastMCP context.
        parent_id: The ID of the parent page.
        expand: Fields to expand.
        limit: Maximum number of child pages.
        include_content: Whether to include page content.
        convert_to_markdown: Convert content to markdown if include_content is true.
        start: Starting index for pagination.

    Returns:
        JSON string representing a list of child page objects.
    """
    from . import get_confluence_fetcher  # lazy import to allow test patching

    confluence_fetcher = await get_confluence_fetcher(ctx)
    if include_content and "body" not in expand:
        expand = f"{expand},body.storage" if expand else "body.storage"

    try:
        pages = confluence_fetcher.get_page_children(
            page_id=parent_id,
            start=start,
            limit=limit,
            expand=expand,
            convert_to_markdown=convert_to_markdown,
        )
        child_pages = [page.to_simplified_dict() for page in pages]
        result = {
            "parent_id": parent_id,
            "count": len(child_pages),
            "limit_requested": limit,
            "start_requested": start,
            "results": child_pages,
        }
    except Exception as e:
        logger.error(
            f"Error getting/processing children for page ID {parent_id}: {e}",
            exc_info=True,
        )
        result = {"error": f"Failed to get child pages: {e}"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@pages_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def create_page(
    ctx: Context,
    space_id: Annotated[
        str,
        Field(
            description="The ID of the space to create the page in (e.g., '123456789' for regular spaces or '2347565058' for personal spaces)"
        ),
    ],
    title: Annotated[str, Field(description="The title of the page")],
    content: Annotated[
        str,
        Field(
            description="The content of the page. Format depends on content_format parameter. Can be Markdown (default), wiki markup, or storage format"
        ),
    ],
    parent_id: Annotated[
        str | None,
        Field(
            description="(Optional) parent page ID. If provided, this page will be created as a child of the specified page",
            default=None,
        ),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description="(Optional) The format of the content parameter. Options: 'markdown' (default), 'wiki', or 'storage'. Wiki format uses Confluence wiki markup syntax",
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
) -> str:
    """Create a new Confluence page.

    Args:
        ctx: The FastMCP context.
        space_id: The ID of the space.
        title: The title of the page.
        content: The content of the page (format depends on content_format).
        parent_id: Optional parent page ID.
        content_format: The format of the content ('markdown', 'wiki', or 'storage').
        enable_heading_anchors: Whether to enable heading anchors (markdown only).

    Returns:
        JSON string representing the created page object.

    Raises:
        ValueError: If in read-only mode, Confluence client is unavailable, or invalid content_format.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # Validate content_format
    if content_format not in ["markdown", "wiki", "storage"]:
        raise ValueError(
            f"Invalid content_format: {content_format}. Must be 'markdown', 'wiki', or 'storage'"
        )

    # Determine parameters based on content format
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # Will be converted to storage
    else:
        is_markdown = False
        content_representation = content_format  # Pass 'wiki' or 'storage' directly

    page = confluence_fetcher.create_page(
        space_id=space_id,
        title=title,
        body=content,
        parent_id=parent_id,
        is_markdown=is_markdown,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
    )
    result = page.to_simplified_dict()
    return json.dumps(
        {"message": "Page created successfully", "page": result},
        indent=2,
        ensure_ascii=False,
    )


@pages_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def update_page(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    title: Annotated[str, Field(description="The new title of the page")],
    content: Annotated[
        str,
        Field(
            description="The new content of the page. Format depends on content_format parameter"
        ),
    ],
    is_minor_edit: Annotated[
        bool, Field(description="Whether this is a minor edit", default=False)
    ] = False,
    version_comment: Annotated[
        str | None, Field(description="Optional comment for this version", default=None)
    ] = None,
    parent_id: Annotated[
        str | None,
        Field(description="Optional the new parent page ID", default=None),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description="(Optional) The format of the content parameter. Options: 'markdown' (default), 'wiki', or 'storage'. Wiki format uses Confluence wiki markup syntax",
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
) -> str:
    """Update an existing Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to update.
        title: The new title of the page.
        content: The new content of the page (format depends on content_format).
        is_minor_edit: Whether this is a minor edit.
        version_comment: Optional comment for this version.
        parent_id: Optional new parent page ID.
        content_format: The format of the content ('markdown', 'wiki', or 'storage').
        enable_heading_anchors: Whether to enable heading anchors (markdown only).

    Returns:
        JSON string representing the updated page object.

    Raises:
        ValueError: If Confluence client is not configured, available, or invalid content_format.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # Validate content_format
    if content_format not in ["markdown", "wiki", "storage"]:
        raise ValueError(
            f"Invalid content_format: {content_format}. Must be 'markdown', 'wiki', or 'storage'"
        )

    # Determine parameters based on content format
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # Will be converted to storage
    else:
        is_markdown = False
        content_representation = content_format  # Pass 'wiki' or 'storage' directly

    updated_page = confluence_fetcher.update_page(
        page_id=page_id,
        title=title,
        body=content,
        is_minor_edit=is_minor_edit,
        version_comment=version_comment,
        is_markdown=is_markdown,
        parent_id=parent_id,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
    )
    page_data = updated_page.to_simplified_dict()
    return json.dumps(
        {"message": "Page updated successfully", "page": page_data},
        indent=2,
        ensure_ascii=False,
    )


@pages_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def delete_page(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to delete")],
) -> str:
    """Delete an existing Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to delete.

    Returns:
        JSON string indicating success or failure.

    Raises:
        ValueError: If Confluence client is not configured or available.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    try:
        result = confluence_fetcher.delete_page(page_id=page_id)
        if result:
            response = {
                "success": True,
                "message": f"Page {page_id} deleted successfully",
            }
        else:
            response = {
                "success": False,
                "message": f"Unable to delete page {page_id}. API request completed but deletion unsuccessful.",
            }
    except Exception as e:
        logger.error(f"Error deleting Confluence page {page_id}: {str(e)}")
        response = {
            "success": False,
            "message": f"Error deleting page {page_id}",
            "error": str(e),
        }

    return json.dumps(response, indent=2, ensure_ascii=False)
