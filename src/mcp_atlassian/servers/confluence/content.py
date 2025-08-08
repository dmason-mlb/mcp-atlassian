"""Confluence content interaction tools."""

import json
import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp_atlassian.servers.dependencies import get_confluence_fetcher
from mcp_atlassian.utils.decorators import check_write_access

logger = logging.getLogger(__name__)

# Create FastMCP instance for content
content_mcp = FastMCP(
    name="Confluence Content Service",
    description="Provides tools for Confluence content interactions (comments, labels).",
)


class ContentServer:
    """Container for Confluence content interaction tools."""

    def __init__(self):
        self.mcp = content_mcp

    def get_tools(self):
        """Get all content interaction tools."""
        return self.mcp.tools


@content_mcp.tool(tags={"confluence", "read"})
async def get_comments(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be parsed from URL, "
                "e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' "
                "-> '123456789')"
            )
        ),
    ],
) -> str:
    """Get comments for a specific Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: Confluence page ID.

    Returns:
        JSON string representing a list of comment objects.
    """
    from . import get_confluence_fetcher  # lazy import to allow test patching

    confluence_fetcher = await get_confluence_fetcher(ctx)
    comments = confluence_fetcher.get_page_comments(page_id)
    formatted_comments = [comment.to_simplified_dict() for comment in comments]
    return json.dumps(formatted_comments, indent=2, ensure_ascii=False)


@content_mcp.tool(tags={"confluence", "read"})
async def get_labels(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be parsed from URL, "
                "e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' "
                "-> '123456789')"
            )
        ),
    ],
) -> str:
    """Get labels for a specific Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: Confluence page ID.

    Returns:
        JSON string representing a list of label objects.
    """
    from . import get_confluence_fetcher  # lazy import to allow test patching

    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.get_page_labels(page_id)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@content_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def add_label(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    name: Annotated[str, Field(description="The name of the label")],
) -> str:
    """Add label to an existing Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to update.
        name: The name of the label.

    Returns:
        JSON string representing the updated list of label objects for the page.

    Raises:
        ValueError: If in read-only mode or Confluence client is unavailable.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.add_page_label(page_id, name)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@content_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def add_comment(
    ctx: Context,
    page_id: Annotated[
        str, Field(description="The ID of the page to add a comment to")
    ],
    content: Annotated[
        str, Field(description="The comment content in Markdown format")
    ],
) -> str:
    """Add a comment to a Confluence page.

    Args:
        ctx: The FastMCP context.
        page_id: The ID of the page to add a comment to.
        content: The comment content in Markdown format.

    Returns:
        JSON string representing the created comment.

    Raises:
        ValueError: If in read-only mode or Confluence client is unavailable.
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    try:
        comment = confluence_fetcher.add_comment(page_id=page_id, content=content)
        if comment:
            comment_data = comment.to_simplified_dict()
            response = {
                "success": True,
                "message": "Comment added successfully",
                "comment": comment_data,
            }
        else:
            response = {
                "success": False,
                "message": f"Unable to add comment to page {page_id}. API request completed but comment creation unsuccessful.",
            }
    except Exception as e:
        logger.error(f"Error adding comment to Confluence page {page_id}: {str(e)}")
        response = {
            "success": False,
            "message": f"Error adding comment to page {page_id}",
            "error": str(e),
        }

    return json.dumps(response, indent=2, ensure_ascii=False)
