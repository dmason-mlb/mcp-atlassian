"""Capture real API responses from JIRA to inform mock test structure.

This script runs actual API calls and saves the responses to use as fixtures
for mock tests, ensuring mocks accurately reflect real API behavior.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.jira import JiraFetcher


class RealResponseCapture:
    """Capture real JIRA API responses for test fixtures."""

    def __init__(self):
        self.config = JiraConfig.from_env()
        self.client = JiraFetcher(self.config)
        self.responses = {}
        self.fixture_dir = Path("tests/fixtures/real_responses")
        self.fixture_dir.mkdir(parents=True, exist_ok=True)

    def save_response(self, name: str, response: Any):
        """Save a response to both memory and file."""
        self.responses[name] = response

        # Save to file for future reference
        file_path = self.fixture_dir / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(response, f, indent=2, default=str)
        print(f"  💾 Saved: {file_path}")

    def capture_issue_operations(self):
        """Capture responses from issue-related operations."""
        print("\n📸 Capturing Issue Operations...")

        # Create an issue
        print("  Creating test issue...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        create_response = self.client.create_issue(
            project_key="FTEST",
            summary=f"Response Capture Test - {timestamp}",
            issue_type="Task",
            description="Test issue for capturing API responses"
        )

        if hasattr(create_response, 'to_simplified_dict'):
            create_dict = create_response.to_simplified_dict()
        else:
            create_dict = create_response

        self.save_response("issue_create", create_dict)
        issue_key = create_dict.get("key")
        print(f"  ✅ Created issue: {issue_key}")

        # Get the issue
        print(f"  Getting issue {issue_key}...")
        get_response = self.client.get_issue(
            issue_key=issue_key,
            fields=["summary", "status", "assignee", "description", "issuetype", "priority"],
            comment_limit=5
        )

        if hasattr(get_response, 'to_simplified_dict'):
            get_dict = get_response.to_simplified_dict()
        else:
            get_dict = get_response

        self.save_response("issue_get", get_dict)
        print(f"  ✅ Retrieved issue")

        # Update the issue
        print(f"  Updating issue {issue_key}...")
        update_response = self.client.update_issue(
            issue_key=issue_key,
            fields={"summary": f"UPDATED - {create_dict.get('fields', {}).get('summary', '')}"}
        )

        if hasattr(update_response, 'to_simplified_dict'):
            update_dict = update_response.to_simplified_dict()
        else:
            update_dict = {"success": True, "issue_key": issue_key}

        self.save_response("issue_update", update_dict)
        print(f"  ✅ Updated issue")

        # Add a comment
        print(f"  Adding comment to {issue_key}...")
        comment_response = self.client.add_comment(
            issue_key=issue_key,
            comment="Test comment for response capture"
        )

        if hasattr(comment_response, '__dict__'):
            comment_dict = comment_response.__dict__
        else:
            comment_dict = comment_response

        self.save_response("issue_comment", comment_dict)
        print(f"  ✅ Added comment")

        # Get transitions
        print(f"  Getting transitions for {issue_key}...")
        transitions = self.client.get_transitions(issue_key)
        self.save_response("issue_transitions", transitions)
        print(f"  ✅ Got transitions")

        return issue_key

    def capture_search_operations(self):
        """Capture responses from search operations."""
        print("\n📸 Capturing Search Operations...")

        # Search issues
        print("  Searching issues...")
        search_response = self.client.search_issues(
            jql="project = FTEST ORDER BY created DESC",
            limit=3
        )

        if hasattr(search_response, 'to_simplified_dict'):
            search_dict = search_response.to_simplified_dict()
        else:
            search_dict = search_response

        self.save_response("search_issues", search_dict)
        print(f"  ✅ Found {len(search_dict.get('issues', []))} issues")

        # Search fields
        print("  Searching fields...")
        fields_response = self.client.search_fields("priority", limit=5)
        self.save_response("search_fields", fields_response)
        print(f"  ✅ Found {len(fields_response)} fields")

    def capture_user_operations(self):
        """Capture responses from user operations."""
        print("\n📸 Capturing User Operations...")

        # Get user profile
        email = os.getenv("JIRA_EMAIL", os.getenv("JIRA_USERNAME"))
        if email:
            print(f"  Getting user profile for {email}...")
            try:
                user_response = self.client.get_user_profile(email)

                if hasattr(user_response, 'to_simplified_dict'):
                    user_dict = user_response.to_simplified_dict()
                else:
                    user_dict = user_response

                self.save_response("user_profile", user_dict)
                print(f"  ✅ Got user profile")
            except Exception as e:
                print(f"  ⚠️ Could not get user profile: {e}")

    def capture_project_operations(self):
        """Capture responses from project operations."""
        print("\n📸 Capturing Project Operations...")

        # Get all projects
        print("  Getting all projects...")
        projects = self.client.get_all_projects()

        # Convert to list of dicts
        project_list = []
        for p in projects[:5]:  # Limit to 5 for fixture
            if hasattr(p, 'to_simplified_dict'):
                project_list.append(p.to_simplified_dict())
            else:
                project_list.append(p)

        self.save_response("projects_list", project_list)
        print(f"  ✅ Got {len(projects)} projects")

        # Get project versions
        print("  Getting project versions for FTEST...")
        versions = self.client.get_project_versions("FTEST")
        self.save_response("project_versions", versions)
        print(f"  ✅ Got {len(versions)} versions")

    def capture_agile_operations(self):
        """Capture responses from agile operations."""
        print("\n📸 Capturing Agile Operations...")

        # Get boards
        print("  Getting agile boards...")
        boards = self.client.get_all_agile_boards_model(limit=3)

        board_list = []
        for b in boards:
            if hasattr(b, 'to_simplified_dict'):
                board_list.append(b.to_simplified_dict())
            else:
                board_list.append(b)

        self.save_response("agile_boards", board_list)
        print(f"  ✅ Got {len(board_list)} boards")

        # If we have boards, get sprints from first one
        if board_list:
            board_id = board_list[0].get("id")
            if board_id:
                print(f"  Getting sprints for board {board_id}...")
                sprints = self.client.get_all_sprints_from_board_model(
                    board_id=str(board_id),
                    limit=3
                )

                sprint_list = []
                for s in sprints:
                    if hasattr(s, 'to_simplified_dict'):
                        sprint_list.append(s.to_simplified_dict())
                    else:
                        sprint_list.append(s)

                self.save_response("board_sprints", sprint_list)
                print(f"  ✅ Got {len(sprint_list)} sprints")

    def generate_mock_fixtures(self):
        """Generate mock fixture file based on captured responses."""
        print("\n🔧 Generating Mock Fixtures...")

        fixture_file = Path("tests/fixtures/jira_real_responses.py")

        content = '''"""Real JIRA API responses captured for mock testing.

These responses were captured from actual JIRA API calls to ensure
mock tests accurately reflect real API behavior.

Generated: {timestamp}
"""

# Issue Operations
REAL_ISSUE_CREATE_RESPONSE = {create}

REAL_ISSUE_GET_RESPONSE = {get}

REAL_ISSUE_UPDATE_RESPONSE = {update}

REAL_ISSUE_COMMENT_RESPONSE = {comment}

REAL_ISSUE_TRANSITIONS = {transitions}

# Search Operations
REAL_SEARCH_RESPONSE = {search}

REAL_FIELDS_RESPONSE = {fields}

# User Operations
REAL_USER_PROFILE = {user}

# Project Operations
REAL_PROJECTS_LIST = {projects}

REAL_PROJECT_VERSIONS = {versions}

# Agile Operations
REAL_AGILE_BOARDS = {boards}

REAL_BOARD_SPRINTS = {sprints}
'''.format(
            timestamp=datetime.now().isoformat(),
            create=json.dumps(self.responses.get("issue_create", {}), indent=4),
            get=json.dumps(self.responses.get("issue_get", {}), indent=4),
            update=json.dumps(self.responses.get("issue_update", {}), indent=4),
            comment=json.dumps(self.responses.get("issue_comment", {}), indent=4),
            transitions=json.dumps(self.responses.get("issue_transitions", []), indent=4),
            search=json.dumps(self.responses.get("search_issues", {}), indent=4),
            fields=json.dumps(self.responses.get("search_fields", []), indent=4),
            user=json.dumps(self.responses.get("user_profile", {}), indent=4),
            projects=json.dumps(self.responses.get("projects_list", []), indent=4),
            versions=json.dumps(self.responses.get("project_versions", []), indent=4),
            boards=json.dumps(self.responses.get("agile_boards", []), indent=4),
            sprints=json.dumps(self.responses.get("board_sprints", []), indent=4)
        )

        with open(fixture_file, 'w') as f:
            f.write(content)

        print(f"  💾 Generated: {fixture_file}")

    def run(self):
        """Run all capture operations."""
        print("🚀 Starting Real Response Capture")
        print("=" * 50)

        try:
            # Capture all operations
            issue_key = self.capture_issue_operations()
            self.capture_search_operations()
            self.capture_user_operations()
            self.capture_project_operations()
            self.capture_agile_operations()

            # Generate mock fixtures
            self.generate_mock_fixtures()

            print("\n" + "=" * 50)
            print("✅ Response capture completed successfully!")
            print(f"📁 Responses saved to: {self.fixture_dir}")

            return self.responses

        except Exception as e:
            print(f"\n❌ Error during capture: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    capture = RealResponseCapture()
    responses = capture.run()

    if responses:
        print(f"\n📊 Captured {len(responses)} response types")
        print("These responses can now be used to create accurate mock tests!")
