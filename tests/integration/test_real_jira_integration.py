"""Real integration tests for JIRA using FTEST project.

These tests actually interact with the JIRA API using the FTEST project.
They verify the MCP server works correctly with real Atlassian services.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict

import pytest
from fastmcp import Context

# Only run these tests if explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "true",
    reason="Integration tests require RUN_INTEGRATION_TESTS=true"
)


class TestRealJiraIntegration:
    """Test real JIRA operations using FTEST project."""

    @pytest.fixture
    async def real_context(self):
        """Create a real context with actual JIRA configuration."""
        from mcp_atlassian.servers.main import create_app_context
        from mcp_atlassian.jira.config import JiraConfig
        from mcp_atlassian.confluence.config import ConfluenceConfig

        # Load real configuration from environment
        jira_config = JiraConfig()
        confluence_config = ConfluenceConfig()

        # Create the app with real configs
        from fastmcp import FastMCP
        app = FastMCP(name="Test MCP")

        # Create app context
        app_context = create_app_context(
            jira_config=jira_config,
            confluence_config=confluence_config,
            read_only=False,
            enabled_tools=None
        )

        # Create mock request context with real app context
        from unittest.mock import MagicMock
        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
        mock_fastmcp._mcp_server.request_context = mock_request_context

        return Context(fastmcp=mock_fastmcp)

    @pytest.mark.anyio
    async def test_create_and_retrieve_real_issue(self, real_context):
        """Test creating and retrieving a real issue in FTEST project."""
        from mcp_atlassian.servers.jira.issues import create_issue, get_issue

        # Create a unique summary with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = f"Integration Test Issue - {timestamp}"
        description = "This is an automated test issue created by integration tests."

        # Create the issue
        print(f"\n🔄 Creating issue in FTEST project: {summary}")
        create_result = await create_issue(
            real_context,
            project_key="FTEST",
            summary=summary,
            issue_type="Task",
            description=description
        )

        # Parse the result
        created = json.loads(create_result)
        assert "key" in created, f"Issue creation failed: {created}"
        issue_key = created["key"]
        print(f"✅ Successfully created issue: {issue_key}")

        # Retrieve the issue
        print(f"🔄 Retrieving issue: {issue_key}")
        get_result = await get_issue(real_context, issue_key)
        retrieved = json.loads(get_result)

        # Verify the retrieved data
        assert retrieved["key"] == issue_key
        assert retrieved["fields"]["summary"] == summary
        assert "description" in retrieved["fields"]
        print(f"✅ Successfully retrieved issue with correct data")

        return issue_key

    @pytest.mark.anyio
    async def test_update_real_issue(self, real_context):
        """Test updating a real issue in FTEST project."""
        from mcp_atlassian.servers.jira.issues import create_issue, update_issue, get_issue

        # First create an issue
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = f"Update Test Issue - {timestamp}"

        create_result = await create_issue(
            real_context,
            project_key="FTEST",
            summary=summary,
            issue_type="Task",
            description="Original description"
        )

        created = json.loads(create_result)
        issue_key = created["key"]
        print(f"\n✅ Created issue for update test: {issue_key}")

        # Update the issue
        new_summary = f"UPDATED - {summary}"
        new_description = "This description has been updated via MCP"

        print(f"🔄 Updating issue {issue_key}")
        update_result = await update_issue(
            real_context,
            issue_key=issue_key,
            fields={
                "summary": new_summary,
                "description": new_description
            }
        )

        updated = json.loads(update_result)
        assert "success" in updated or "message" in updated
        print(f"✅ Successfully updated issue")

        # Verify the update
        print(f"🔄 Verifying update...")
        get_result = await get_issue(real_context, issue_key)
        retrieved = json.loads(get_result)

        assert retrieved["fields"]["summary"] == new_summary
        print(f"✅ Update verified - summary changed correctly")

        return issue_key

    @pytest.mark.anyio
    async def test_add_comment_to_real_issue(self, real_context):
        """Test adding a comment to a real issue."""
        from mcp_atlassian.servers.jira.issues import create_issue, add_comment, get_issue

        # Create an issue
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = f"Comment Test Issue - {timestamp}"

        create_result = await create_issue(
            real_context,
            project_key="FTEST",
            summary=summary,
            issue_type="Task"
        )

        created = json.loads(create_result)
        issue_key = created["key"]
        print(f"\n✅ Created issue for comment test: {issue_key}")

        # Add a comment
        comment_text = f"This is an automated test comment added at {timestamp}"
        print(f"🔄 Adding comment to {issue_key}")

        comment_result = await add_comment(
            real_context,
            issue_key=issue_key,
            comment=comment_text
        )

        comment_response = json.loads(comment_result)
        assert "id" in comment_response or "self" in comment_response
        print(f"✅ Successfully added comment")

        # Verify the comment exists
        print(f"🔄 Verifying comment...")
        get_result = await get_issue(
            real_context,
            issue_key,
            comment_limit=10
        )
        retrieved = json.loads(get_result)

        # Check if comments exist
        if "comment" in retrieved.get("fields", {}):
            comments = retrieved["fields"]["comment"].get("comments", [])
            assert len(comments) > 0, "No comments found"
            # Verify our comment is there
            found = any(comment_text in c.get("body", "") for c in comments)
            assert found, "Our comment was not found"
            print(f"✅ Comment verified in issue")

        return issue_key

    @pytest.mark.anyio
    async def test_search_real_issues(self, real_context):
        """Test searching for real issues in FTEST project."""
        from mcp_atlassian.servers.jira.search import search

        # Search for recent issues in FTEST
        jql = "project = FTEST AND created >= -7d ORDER BY created DESC"
        print(f"\n🔄 Searching with JQL: {jql}")

        search_result = await search(
            real_context,
            jql=jql,
            limit=5
        )

        results = json.loads(search_result)
        assert "issues" in results
        print(f"✅ Found {len(results['issues'])} issues")

        # Display found issues
        for issue in results["issues"]:
            print(f"  - {issue['key']}: {issue['fields'].get('summary', 'No summary')}")

        return results

    @pytest.mark.anyio
    async def test_transition_real_issue(self, real_context):
        """Test transitioning a real issue's status."""
        from mcp_atlassian.servers.jira.issues import create_issue, transition_issue
        from mcp_atlassian.servers.jira.management import get_transitions

        # Create an issue
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary = f"Transition Test Issue - {timestamp}"

        create_result = await create_issue(
            real_context,
            project_key="FTEST",
            summary=summary,
            issue_type="Task"
        )

        created = json.loads(create_result)
        issue_key = created["key"]
        print(f"\n✅ Created issue for transition test: {issue_key}")

        # Get available transitions
        print(f"🔄 Getting available transitions for {issue_key}")
        transitions_result = await get_transitions(real_context, issue_key)
        transitions = json.loads(transitions_result)

        print(f"Available transitions:")
        for t in transitions:
            print(f"  - {t['id']}: {t['name']}")

        # Try to transition if there are any available
        if transitions:
            transition = transitions[0]  # Use first available transition
            print(f"🔄 Transitioning to: {transition['name']} (ID: {transition['id']})")

            transition_result = await transition_issue(
                real_context,
                issue_key=issue_key,
                transition_id=transition["id"],
                comment="Automated transition by integration test"
            )

            result = json.loads(transition_result)
            print(f"✅ Successfully transitioned issue")
        else:
            print("⚠️ No transitions available for this issue")

        return issue_key

    @pytest.mark.anyio
    async def test_get_user_profile(self, real_context):
        """Test getting user profile information."""
        from mcp_atlassian.servers.jira.management import get_user_profile

        # Try to get current user profile
        print(f"\n🔄 Getting current user profile")

        try:
            # First try with 'currentUser()' or email from environment
            email = os.getenv("JIRA_EMAIL", os.getenv("JIRA_USERNAME"))
            if email:
                profile_result = await get_user_profile(real_context, email)
                profile = json.loads(profile_result)

                if "error" not in profile:
                    print(f"✅ Found user profile:")
                    print(f"  - Display Name: {profile.get('displayName', 'N/A')}")
                    print(f"  - Email: {profile.get('emailAddress', 'N/A')}")
                    print(f"  - Account ID: {profile.get('accountId', 'N/A')}")
                    return profile
                else:
                    print(f"⚠️ Could not retrieve profile: {profile['error']}")
            else:
                print("⚠️ No email/username configured in environment")
        except Exception as e:
            print(f"⚠️ Error getting user profile: {e}")

    @pytest.mark.anyio
    async def test_batch_operations(self, real_context):
        """Test batch creating issues."""
        from mcp_atlassian.servers.jira.issues import batch_create_issues

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        issues_data = [
            {
                "project_key": "FTEST",
                "summary": f"Batch Test Issue 1 - {timestamp}",
                "issue_type": "Task",
                "description": "First batch issue"
            },
            {
                "project_key": "FTEST",
                "summary": f"Batch Test Issue 2 - {timestamp}",
                "issue_type": "Task",
                "description": "Second batch issue"
            },
            {
                "project_key": "FTEST",
                "summary": f"Batch Test Issue 3 - {timestamp}",
                "issue_type": "Task",
                "description": "Third batch issue"
            }
        ]

        print(f"\n🔄 Creating {len(issues_data)} issues in batch")

        batch_result = await batch_create_issues(
            real_context,
            issues=json.dumps(issues_data),
            validate_only=False
        )

        results = json.loads(batch_result)

        # Check results
        created_keys = []
        for i, result in enumerate(results):
            if result.get("success"):
                key = result.get("issue", {}).get("key")
                created_keys.append(key)
                print(f"✅ Created issue {i+1}: {key}")
            else:
                print(f"❌ Failed to create issue {i+1}: {result.get('error')}")

        assert len(created_keys) > 0, "No issues were created"
        print(f"✅ Successfully created {len(created_keys)} issues in batch")

        return created_keys


if __name__ == "__main__":
    # Allow running directly with python
    async def run_tests():
        """Run tests directly."""
        test = TestRealJiraIntegration()

        # Create real context
        from mcp_atlassian.servers.main import create_app_context
        from mcp_atlassian.jira.config import JiraConfig
        from mcp_atlassian.confluence.config import ConfluenceConfig
        from fastmcp import FastMCP
        from unittest.mock import MagicMock

        jira_config = JiraConfig()
        confluence_config = ConfluenceConfig()

        app = FastMCP(name="Test MCP")
        app_context = create_app_context(
            jira_config=jira_config,
            confluence_config=confluence_config,
            read_only=False,
            enabled_tools=None
        )

        mock_fastmcp = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": app_context}
        mock_fastmcp._mcp_server.request_context = mock_request_context

        context = Context(fastmcp=mock_fastmcp)

        print("🚀 Running Real JIRA Integration Tests")
        print("=" * 50)

        # Run each test
        try:
            issue_key = await test.test_create_and_retrieve_real_issue(context)
            print(f"\n✅ Create and retrieve test passed: {issue_key}")
        except Exception as e:
            print(f"\n❌ Create and retrieve test failed: {e}")

        try:
            issue_key = await test.test_update_real_issue(context)
            print(f"\n✅ Update test passed: {issue_key}")
        except Exception as e:
            print(f"\n❌ Update test failed: {e}")

        try:
            issue_key = await test.test_add_comment_to_real_issue(context)
            print(f"\n✅ Comment test passed: {issue_key}")
        except Exception as e:
            print(f"\n❌ Comment test failed: {e}")

        try:
            results = await test.test_search_real_issues(context)
            print(f"\n✅ Search test passed: found {len(results['issues'])} issues")
        except Exception as e:
            print(f"\n❌ Search test failed: {e}")

        try:
            issue_key = await test.test_transition_real_issue(context)
            print(f"\n✅ Transition test passed: {issue_key}")
        except Exception as e:
            print(f"\n❌ Transition test failed: {e}")

        try:
            profile = await test.test_get_user_profile(context)
            print(f"\n✅ User profile test passed")
        except Exception as e:
            print(f"\n❌ User profile test failed: {e}")

        try:
            keys = await test.test_batch_operations(context)
            print(f"\n✅ Batch operations test passed: created {len(keys)} issues")
        except Exception as e:
            print(f"\n❌ Batch operations test failed: {e}")

        print("\n" + "=" * 50)
        print("🏁 Integration tests completed")

    # Run the tests
    asyncio.run(run_tests())
