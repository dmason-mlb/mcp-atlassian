"""Modular Jira FastMCP server with core functions extracted to focused modules."""

# Import the shared FastMCP instance and common dependencies
from .jira_shared import jira_mcp

# Import core CRUD functions from focused modules
from .jira_core import (
    add_comment,
    create_issue,
    delete_issue,
    get_issue,
    update_issue,
)

# Import search functions from focused modules
from .jira_search import (
    get_project_issues,
    search,
    search_fields,
)

# Import workflow functions from focused modules
from .jira_workflow import (
    download_attachments,
    upload_attachment,
    get_transitions,
    transition_issue,
)

# Import project functions from focused modules
from .jira_project import (
    batch_create_issues,
    batch_get_changelogs,
    create_version,
    get_all_projects,
    get_project_versions,
)

# Import linking functions from focused modules
from .jira_links import (
    create_issue_link,
    create_remote_issue_link,
    get_link_types,
    link_to_epic,
    remove_issue_link,
)

# Import agile functions from focused modules
from .jira_agile import (
    create_sprint,
    get_agile_boards,
    get_board_issues,
    get_sprint_issues,
    get_sprints_from_board,
    get_user_profile,
    update_sprint,
)

# Export the FastMCP app instance
__all__ = ["jira_mcp"]