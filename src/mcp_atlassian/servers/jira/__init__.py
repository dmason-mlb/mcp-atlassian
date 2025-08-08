"""Jira server module with organized tool categories."""

from fastmcp import FastMCP

# Create main jira_mcp for backward compatibility
jira_mcp = FastMCP(
    name="Jira MCP Service",
    description="Provides tools for interacting with Atlassian Jira.",
)

# Import module MCP instances
from .agile import agile_mcp
from .issues import issues_mcp
from .management import management_mcp
from .search import search_mcp

# Mount all module instances to aggregate their tools
jira_mcp.mount("issues", issues_mcp)
jira_mcp.mount("search", search_mcp)
jira_mcp.mount("agile", agile_mcp)
jira_mcp.mount("management", management_mcp)

# Import server classes for future extensibility
# Import all agile tools for backward compatibility
from .agile import (
    AgileServer,
    create_sprint,
    get_agile_boards,
    get_board_issues,
    get_sprint_issues,
    get_sprints_from_board,
    update_sprint,
)

# Import all issue tools for backward compatibility
from .issues import (
    IssuesServer,
    add_comment,
    batch_create_issues,
    batch_get_changelogs,
    create_issue,
    delete_issue,
    get_issue,
    transition_issue,
    update_issue,
)

# Import all management tools for backward compatibility
from .management import (
    ManagementServer,
    batch_create_versions,
    create_issue_link,
    create_remote_issue_link,
    create_version,
    download_attachments,
    get_all_projects,
    get_link_types,
    get_project_versions,
    get_transitions,
    get_user_profile,
    link_to_epic,
    remove_issue_link,
    upload_attachment,
)

# Import all search tools for backward compatibility
from .search import SearchServer, get_project_issues, search, search_fields

__all__ = [
    "jira_mcp",  # For backward compatibility
    "IssuesServer",
    "SearchServer",
    "AgileServer",
    "ManagementServer",
]
