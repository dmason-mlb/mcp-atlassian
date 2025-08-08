"""Shared FastMCP instance and common imports for Jira tools."""

import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

jira_mcp = FastMCP(
    name="Jira MCP Service",
    description="Provides tools for interacting with Atlassian Jira.",
)
