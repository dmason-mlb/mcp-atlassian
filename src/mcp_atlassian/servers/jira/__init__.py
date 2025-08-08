"""Jira server module with organized tool categories."""

from fastmcp import FastMCP

# Create main jira_mcp for backward compatibility
jira_mcp = FastMCP(
    name="Jira MCP Service",
    description="Provides tools for interacting with Atlassian Jira.",
)

# Import module MCP instances
from .issues import issues_mcp
from .search import search_mcp
from .agile import agile_mcp
from .management import management_mcp

# Mount all module instances to aggregate their tools
jira_mcp.mount("issues", issues_mcp)
jira_mcp.mount("search", search_mcp)
jira_mcp.mount("agile", agile_mcp)
jira_mcp.mount("management", management_mcp)

# Import server classes for future extensibility
from .issues import IssuesServer
from .search import SearchServer  
from .agile import AgileServer
from .management import ManagementServer

# Import all issue tools for backward compatibility
from .issues import (
    get_issue, 
    create_issue, 
    update_issue, 
    delete_issue, 
    add_comment, 
    transition_issue, 
    batch_create_issues, 
    batch_get_changelogs
)

# Import all search tools for backward compatibility
from .search import (
    search,
    search_fields, 
    get_project_issues
)

# Import all agile tools for backward compatibility
from .agile import (
    get_agile_boards,
    get_board_issues,
    get_sprints_from_board,
    get_sprint_issues,
    create_sprint,
    update_sprint
)

# Import all management tools for backward compatibility
from .management import (
    get_user_profile,
    get_transitions,
    download_attachments,
    upload_attachment,
    get_link_types,
    link_to_epic,
    create_issue_link,
    create_remote_issue_link,
    remove_issue_link,
    get_project_versions,
    get_all_projects,
    create_version,
    batch_create_versions
)

__all__ = [
    "jira_mcp",  # For backward compatibility
    "IssuesServer",
    "SearchServer", 
    "AgileServer",
    "ManagementServer",
]