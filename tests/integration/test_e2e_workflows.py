"""End-to-end integration tests for critical MCP Atlassian workflows.

These tests use the FTEST project for Jira and personal Confluence space for testing.
They require proper environment configuration with test credentials.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastmcp import Context

from mcp_atlassian.servers.main import main_lifespan, main_mcp


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("JIRA_URL") or not os.getenv("ATLASSIAN_TOKEN"),
    reason="Requires Jira credentials for integration testing",
)
class TestJiraE2EWorkflows:
    """End-to-end tests for Jira workflows using FTEST project."""

    @pytest.fixture
    async def integration_context(self):
        """Create an integration test context with real configuration."""
        async with main_lifespan(main_mcp) as ctx:
            yield Context(lifespan_context=ctx)

    @pytest.mark.anyio
    async def test_complete_issue_lifecycle(self, integration_context):
        """Test complete issue lifecycle: create, update, transition, delete."""
        # This test demonstrates the full workflow
        from mcp_atlassian.servers.jira import jira_mcp

        # Step 1: Create an issue in FTEST project
        create_result = await jira_mcp.tools["create_issue"](
            integration_context,
            project_key="FTEST",
            summary=f"E2E Test Issue - {datetime.now().isoformat()}",
            issue_type="Task",
            description="This is an automated E2E test issue that will be deleted.",
        )
        created_issue = json.loads(create_result)
        issue_key = created_issue.get("key")

        assert issue_key is not None
        assert issue_key.startswith("FTEST-")

        try:
            # Step 2: Update the issue
            update_result = await jira_mcp.tools["update_issue"](
                integration_context,
                issue_key=issue_key,
                fields=json.dumps(
                    {
                        "summary": f"Updated E2E Test - {datetime.now().isoformat()}",
                        "description": "Updated description for E2E test",
                    }
                ),
            )
            updated_issue = json.loads(update_result)
            assert "Updated E2E Test" in updated_issue.get("fields", {}).get(
                "summary", ""
            )

            # Step 3: Add a comment
            comment_result = await jira_mcp.tools["add_comment"](
                integration_context,
                issue_key=issue_key,
                comment="This is an automated test comment.",
            )
            comment_data = json.loads(comment_result)
            assert comment_data.get("success") is True

            # Step 4: Get available transitions
            transitions_result = await jira_mcp.tools["get_transitions"](
                integration_context, issue_key=issue_key
            )
            transitions = json.loads(transitions_result)

            # Step 5: Transition the issue (if possible)
            if transitions and len(transitions) > 0:
                first_transition = transitions[0]
                transition_result = await jira_mcp.tools["transition_issue"](
                    integration_context,
                    issue_key=issue_key,
                    transition_id=first_transition["id"],
                )

        finally:
            # Step 6: Clean up - delete the test issue
            if issue_key:
                delete_result = await jira_mcp.tools["delete_issue"](
                    integration_context, issue_key=issue_key
                )
                deleted = json.loads(delete_result)
                assert deleted.get("success") is True

    @pytest.mark.anyio
    async def test_search_and_bulk_operations(self, integration_context):
        """Test search functionality and bulk operations."""
        from mcp_atlassian.servers.jira import jira_mcp

        # Search for issues in FTEST project
        search_result = await jira_mcp.tools["search"](
            integration_context,
            jql="project = FTEST AND created >= -30d ORDER BY created DESC",
            limit=5,
        )
        search_data = json.loads(search_result)

        assert "issues" in search_data
        assert search_data.get("total", 0) >= 0

        # If we have issues, test bulk comment operation
        if search_data.get("issues"):
            issue_keys = [issue["key"] for issue in search_data["issues"][:2]]

            # Batch create comments
            for key in issue_keys:
                await jira_mcp.tools["add_comment"](
                    integration_context,
                    issue_key=key,
                    comment=f"Bulk test comment - {datetime.now().isoformat()}",
                )

    @pytest.mark.anyio
    async def test_agile_workflow(self, integration_context):
        """Test Agile-specific workflows: sprints, boards."""
        from mcp_atlassian.servers.jira_agile import jira_agile_tools

        # Get agile boards
        boards_result = await jira_agile_tools["get_agile_boards"](
            integration_context, project_key="FTEST", limit=5
        )
        boards = json.loads(boards_result)

        if boards.get("values"):
            board_id = boards["values"][0]["id"]

            # Get active sprints
            sprints_result = await jira_agile_tools["get_sprints_from_board"](
                integration_context, board_id=str(board_id), state="active"
            )
            sprints = json.loads(sprints_result)

            # Create a test sprint if board supports it
            if boards["values"][0].get("type") == "scrum":
                sprint_result = await jira_agile_tools["create_sprint"](
                    integration_context,
                    board_id=str(board_id),
                    sprint_name=f"E2E Test Sprint - {datetime.now().isoformat()}",
                    start_date=(datetime.now() + timedelta(days=1)).isoformat(),
                    end_date=(datetime.now() + timedelta(days=14)).isoformat(),
                    goal="Automated E2E test sprint",
                )
                created_sprint = json.loads(sprint_result)
                assert created_sprint.get("id") is not None


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("CONFLUENCE_URL") or not os.getenv("ATLASSIAN_TOKEN"),
    reason="Requires Confluence credentials for integration testing",
)
class TestConfluenceE2EWorkflows:
    """End-to-end tests for Confluence workflows using personal space."""

    @pytest.fixture
    async def integration_context(self):
        """Create an integration test context with real configuration."""
        async with main_lifespan(main_mcp) as ctx:
            yield Context(lifespan_context=ctx)

    @pytest.fixture
    def personal_space_id(self):
        """Get personal space ID from environment or use default."""
        return os.getenv("CONFLUENCE_TEST_SPACE_ID", "~testuser")

    @pytest.mark.anyio
    async def test_complete_page_lifecycle(
        self, integration_context, personal_space_id
    ):
        """Test complete page lifecycle: create, update, comment, delete."""
        from mcp_atlassian.servers.confluence import confluence_mcp

        # Step 1: Create a test page
        create_result = await confluence_mcp.tools["create_page"](
            integration_context,
            space_id=personal_space_id,
            title=f"E2E Test Page - {datetime.now().isoformat()}",
            content="# Test Page\n\nThis is an automated E2E test page.",
        )
        created_page = json.loads(create_result)
        page_id = created_page.get("id")

        assert page_id is not None

        try:
            # Step 2: Update the page
            update_result = await confluence_mcp.tools["update_page"](
                integration_context,
                page_id=page_id,
                title=f"Updated E2E Test - {datetime.now().isoformat()}",
                content="# Updated Test Page\n\n**Bold** content with *italic* text.",
            )
            updated_page = json.loads(update_result)
            assert "Updated E2E Test" in updated_page.get("title", "")

            # Step 3: Add a comment
            comment_result = await confluence_mcp.tools["add_comment"](
                integration_context,
                page_id=page_id,
                content="This is an automated test comment in markdown.",
            )
            comment_data = json.loads(comment_result)
            assert comment_data.get("id") is not None

            # Step 4: Add labels
            label_result = await confluence_mcp.tools["add_label"](
                integration_context, page_id=page_id, name="e2e-test"
            )
            labels = json.loads(label_result)
            assert any(label["name"] == "e2e-test" for label in labels)

            # Step 5: Get the page to verify
            get_result = await confluence_mcp.tools["get_page"](
                integration_context, page_id=page_id, include_metadata=True
            )
            page_data = json.loads(get_result)
            assert page_data.get("page", {}).get("id") == page_id

        finally:
            # Step 6: Clean up - delete the test page
            if page_id:
                delete_result = await confluence_mcp.tools["delete_page"](
                    integration_context, page_id=page_id
                )
                deleted = json.loads(delete_result)
                assert deleted.get("success") is True

    @pytest.mark.anyio
    async def test_search_and_navigation(self, integration_context):
        """Test search functionality and page navigation."""
        from mcp_atlassian.servers.confluence import confluence_mcp

        # Search for pages
        search_result = await confluence_mcp.tools["search"](
            integration_context, query="type=page", limit=10
        )
        search_data = json.loads(search_result)

        assert "results" in search_data

        # If we have results, test page children navigation
        if search_data.get("results"):
            first_page = search_data["results"][0]
            page_id = first_page.get("id")

            if page_id:
                # Get page children
                children_result = await confluence_mcp.tools["get_page_children"](
                    integration_context, parent_id=page_id, limit=5
                )
                children = json.loads(children_result)
                assert "results" in children


@pytest.mark.integration
class TestCrossServiceWorkflows:
    """Test workflows that involve both Jira and Confluence."""

    @pytest.fixture
    async def integration_context(self):
        """Create an integration test context with real configuration."""
        async with main_lifespan(main_mcp) as ctx:
            yield Context(lifespan_context=ctx)

    @pytest.mark.anyio
    @pytest.mark.skipif(
        not (os.getenv("JIRA_URL") and os.getenv("CONFLUENCE_URL")),
        reason="Requires both Jira and Confluence credentials",
    )
    async def test_jira_confluence_integration(self, integration_context):
        """Test creating linked content between Jira and Confluence."""
        from mcp_atlassian.servers.confluence import confluence_mcp
        from mcp_atlassian.servers.jira import jira_mcp

        # Create a Jira issue
        jira_result = await jira_mcp.tools["create_issue"](
            integration_context,
            project_key="FTEST",
            summary=f"Cross-service test - {datetime.now().isoformat()}",
            issue_type="Task",
            description="Issue for cross-service testing",
        )
        jira_issue = json.loads(jira_result)
        issue_key = jira_issue.get("key")

        try:
            # Create a Confluence page that references the Jira issue
            space_id = os.getenv("CONFLUENCE_TEST_SPACE_ID", "~testuser")
            confluence_result = await confluence_mcp.tools["create_page"](
                integration_context,
                space_id=space_id,
                title=f"Documentation for {issue_key}",
                content=f"# Documentation\n\nThis page documents Jira issue [{issue_key}]",
            )
            confluence_page = json.loads(confluence_result)
            page_id = confluence_page.get("id")

            # Add a comment in Jira linking to the Confluence page
            if page_id:
                confluence_url = os.getenv("CONFLUENCE_URL", "")
                comment_text = (
                    f"Documentation created: {confluence_url}/pages/{page_id}"
                )

                await jira_mcp.tools["add_comment"](
                    integration_context, issue_key=issue_key, comment=comment_text
                )

            # Clean up Confluence page
            if page_id:
                await confluence_mcp.tools["delete_page"](
                    integration_context, page_id=page_id
                )

        finally:
            # Clean up Jira issue
            if issue_key:
                await jira_mcp.tools["delete_issue"](
                    integration_context, issue_key=issue_key
                )


@pytest.mark.integration
class TestAuthenticationFlows:
    """Test different authentication mechanisms."""

    @pytest.mark.anyio
    async def test_oauth_flow(self):
        """Test OAuth 2.0 authentication flow."""
        with patch.dict(
            os.environ,
            {
                "ATLASSIAN_OAUTH_ENABLE": "true",
                "ATLASSIAN_OAUTH_CLIENT_ID": "test_client",
                "ATLASSIAN_OAUTH_CLIENT_SECRET": "test_secret",
                "ATLASSIAN_OAUTH_REDIRECT_URI": "http://localhost:8000/callback",
            },
        ):
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Verify OAuth configuration is loaded
                if app_context.full_jira_config:
                    assert app_context.full_jira_config.auth_type == "oauth"

    @pytest.mark.anyio
    async def test_api_token_auth(self):
        """Test API token authentication."""
        with patch.dict(
            os.environ,
            {
                "JIRA_URL": "https://test.atlassian.net",
                "JIRA_USERNAME": "test@example.com",
                "ATLASSIAN_TOKEN": "test_token",
            },
        ):
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Verify API token configuration
                if app_context.full_jira_config:
                    assert app_context.full_jira_config.auth_type == "basic"
                    assert app_context.full_jira_config.username == "test@example.com"

    @pytest.mark.anyio
    async def test_pat_auth(self):
        """Test Personal Access Token authentication."""
        with patch.dict(
            os.environ,
            {
                "JIRA_URL": "https://jira.company.com",
                "JIRA_PAT": "personal_access_token_123",
            },
        ):
            async with main_lifespan(main_mcp) as ctx:
                app_context = ctx["app_lifespan_context"]

                # Verify PAT configuration
                if app_context.full_jira_config:
                    assert app_context.full_jira_config.auth_type == "pat"
                    assert app_context.full_jira_config.personal_token is not None


@pytest.mark.integration
class TestPerformanceAndScale:
    """Test performance and scalability aspects."""

    @pytest.mark.anyio
    async def test_concurrent_tool_execution(self):
        """Test concurrent execution of multiple tools."""
        async with main_lifespan(main_mcp) as ctx:
            context = Context(lifespan_context=ctx)

            # Create multiple concurrent tasks
            tasks = []
            for i in range(5):
                # Mix of read operations
                if i % 2 == 0:
                    from mcp_atlassian.servers.jira import jira_mcp

                    task = jira_mcp.tools["search"](
                        context,
                        jql=f"project = FTEST AND created >= -{i + 1}d",
                        limit=1,
                    )
                else:
                    from mcp_atlassian.servers.confluence import confluence_mcp

                    task = confluence_mcp.tools["search"](
                        context, query="type=page", limit=1
                    )
                tasks.append(task)

            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify all completed
            for result in results:
                if not isinstance(result, Exception):
                    data = json.loads(result)
                    assert data is not None

    @pytest.mark.anyio
    async def test_token_cache_performance(self):
        """Test token validation cache performance."""
        from mcp_atlassian.servers.main import token_cache_lock, token_validation_cache

        # Simulate multiple token validations
        tokens = [f"token_{i}" for i in range(100)]

        async def validate_token(token):
            with token_cache_lock:
                # Check cache
                cache_key = hash(token)
                if cache_key not in token_validation_cache:
                    # Simulate validation
                    await asyncio.sleep(0.001)
                    token_validation_cache[cache_key] = (True, token, None, None)
                return token_validation_cache[cache_key]

        # First pass - populate cache
        tasks = [validate_token(token) for token in tokens]
        await asyncio.gather(*tasks)

        # Second pass - should hit cache
        import time

        start = time.time()
        tasks = [validate_token(token) for token in tokens]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # Cache hits should be fast
        assert elapsed < 0.1  # 100ms for 100 cache hits
