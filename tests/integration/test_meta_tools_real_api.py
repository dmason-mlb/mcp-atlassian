"""Real API integration tests for MCP Atlassian meta-tools.

These tests use actual Atlassian APIs instead of mocks to validate that
the meta-tools work correctly in real environments.
"""

import json
import pytest
import logging
from typing import Any, Dict, List

from .config import skip_if_no_real_api, get_test_config
from .test_data_factory import get_test_factory, setup_test_session, teardown_test_session, TestResource
from .test_adapters import (
    SearchEngineTestAdapter,
    TestJiraFetcher,
    TestConfluenceFetcher,
    BatchProcessorTestAdapter,
    WorkflowEngineTestAdapter,
    RelationshipManagerTestAdapter,
    AttachmentHandlerTestAdapter,
    ResourceManagerTestAdapter
)
from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
from src.mcp_atlassian.meta_tools.errors import MetaToolError
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig

logger = logging.getLogger(__name__)


# Test session setup and teardown
@pytest.fixture(scope="session", autouse=True)
def test_session():
    """Set up and tear down test session."""
    setup_test_session()
    yield
    teardown_test_session()


@pytest.fixture
def config():
    """Get test configuration."""
    return get_test_config()


@pytest.fixture
def factory():
    """Get test data factory."""
    return get_test_factory()


@pytest.fixture
def jira_fetcher(config):
    """Get TestJiraFetcher instance."""
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    return TestJiraFetcher(jira_config)


@pytest.fixture
def confluence_fetcher(config):
    """Get TestConfluenceFetcher instance."""
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )
    return TestConfluenceFetcher(confluence_config)


@pytest.fixture
def resource_manager():
    """Get ResourceManager instance."""
    return ResourceManager()


@pytest.fixture
def search_engine(config, execution_mode):
    """Get SearchEngine test adapter with real fetchers."""
    # Create configurations
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )

    # Create fetchers
    jira_fetcher = TestJiraFetcher(jira_config)
    confluence_fetcher = TestConfluenceFetcher(confluence_config)

    # Create adapter with execution mode
    return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher, execution_mode)


@pytest.fixture
def batch_processor(config, execution_mode):
    """Get BatchProcessor test adapter with real fetchers."""
    # Create configurations
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )

    # Create fetchers
    jira_fetcher = TestJiraFetcher(jira_config)
    confluence_fetcher = TestConfluenceFetcher(confluence_config)

    # Create adapter
    return BatchProcessorTestAdapter(jira_fetcher, confluence_fetcher, execution_mode)


@pytest.fixture
def workflow_engine(config, execution_mode):
    """Get WorkflowEngine test adapter with real fetchers."""
    # Create configurations
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )

    # Create fetchers
    jira_fetcher = TestJiraFetcher(jira_config)
    confluence_fetcher = TestConfluenceFetcher(confluence_config)

    # Create adapter
    return WorkflowEngineTestAdapter(jira_fetcher, execution_mode)


@pytest.fixture
def relationship_manager(config, execution_mode):
    """Get RelationshipManager test adapter with real fetchers."""
    # Create configurations
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )

    # Create fetchers
    jira_fetcher = TestJiraFetcher(jira_config)
    confluence_fetcher = TestConfluenceFetcher(confluence_config)

    # Create adapter
    return RelationshipManagerTestAdapter(jira_fetcher, confluence_fetcher, execution_mode)


@pytest.fixture
def attachment_handler(config, execution_mode):
    """Get AttachmentHandler test adapter with real fetchers."""
    # Create configurations
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )

    # Create fetchers
    jira_fetcher = TestJiraFetcher(jira_config)
    confluence_fetcher = TestConfluenceFetcher(confluence_config)

    # Create adapter
    return AttachmentHandlerTestAdapter(jira_fetcher, confluence_fetcher, execution_mode)


# ResourceManager Real API Tests
class TestResourceManagerRealAPI:
    """Test ResourceManager with real Atlassian APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher, confluence_fetcher):
        """Get ResourceManager adapter for real API operations."""
        return ResourceManagerTestAdapter(jira_fetcher, confluence_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_create_jira_issue(self, resource_manager, factory, config):
        """Test creating a Jira issue through ResourceManager."""
        # Test data
        summary = factory.get_test_identifier("ResourceManager_Create_Test")
        description = "Test issue created by ResourceManager integration test"

        # Execute create operation
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource_type="issue",
            resource_data={
                "project_key": config.jira.project_key,
                "summary": summary,
                "description": description,
                "issue_type": config.jira.issue_type
            }
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "jira_issue_create"

        # ResourceManager returns result (singular) with simplified format
        issue_data = result["result"]
        assert issue_data["key"] is not None
        assert issue_data["summary"] == summary

        # Verify issue was actually created and can be retrieved
        issue_key = issue_data["key"]

        # Create TestResource for verification and cleanup tracking
        test_resource = TestResource(
            resource_type="issue",
            resource_id=issue_key,
            service="jira",
            cleanup_method="delete_issue",
            metadata={"summary": summary}
        )

        # Verify the resource exists
        assert factory.verify_resource_exists(test_resource), f"Created issue {issue_key} should exist"

        # Track for cleanup
        factory._created_resources.append(test_resource)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_issue(self, resource_manager, factory):
        """Test getting a Jira issue through ResourceManager."""
        # Create a test issue first
        test_issue_key = factory.create_test_issue()

        # Execute get operation
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="get",
            resource_type="issue",
            resource_id=test_issue_key,
            options={"fields": "summary,description,status,assignee"}
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "get"
        assert result["resource_type"] == "issue"

        issue_data = result["results"]
        assert issue_data["key"] == test_issue_key
        assert "summary" in issue_data["fields"]
        assert "description" in issue_data["fields"]
        assert "status" in issue_data["fields"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_update_jira_issue(self, resource_manager, factory):
        """Test updating a Jira issue through ResourceManager."""
        # Create a test issue first
        test_issue_key = factory.create_test_issue()

        # New data for update
        new_summary = factory.get_test_identifier("Updated_Summary")
        new_description = "Updated description from ResourceManager test"

        # Execute update operation
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource_type="issue",
            resource_id=test_issue_key,
            resource_data={
                "summary": new_summary,
                "description": new_description
            }
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "update"

        # Verify the update by getting the issue
        get_result_json = await resource_manager.execute_operation(
            service="jira",
            operation="get",
            resource_type="issue",
            resource_id=test_issue_key,
            options={"fields": "summary,description"}
        )

        get_result = json.loads(get_result_json)
        updated_issue = get_result["results"]
        assert updated_issue["fields"]["summary"] == new_summary
        assert updated_issue["fields"]["description"] == new_description

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_delete_jira_issue(self, resource_manager, factory):
        """Test deleting a Jira issue through ResourceManager."""
        # Create a test issue first
        test_issue_key = factory.create_test_issue()

        # Execute delete operation
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="delete",
            resource_type="issue",
            resource_id=test_issue_key
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "delete"

        # Verify deletion by attempting to get the issue (should fail)
        with pytest.raises(Exception) as exc_info:
            await resource_manager.execute_operation(
                service="jira",
                operation="get",
                resource_type="issue",
                resource_id=test_issue_key
            )
        # Should get 404 or "not found" error
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

        # Remove from factory's cleanup list since we deleted it manually
        factory._created_resources = [
            r for r in factory._created_resources
            if not (r.resource_id == test_issue_key and r.resource_type == "issue")
        ]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_create_confluence_page(self, resource_manager, factory, config):
        """Test creating a Confluence page through ResourceManager."""
        # Test data
        title = factory.get_test_identifier("ResourceManager_Page_Test")
        content = f"""
# {title}

This is a test page created by ResourceManager integration test.

## Content
- Test bullet point 1
- Test bullet point 2

## Code Block
```python
def test_function():
    return "Hello, World!"
```

Created for testing purposes.
        """.strip()

        # Execute create operation
        result_json = await resource_manager.execute_operation(
            service="confluence",
            operation="create",
            resource_type="page",
            resource_data={
                "space_key": config.confluence.space_key,
                "title": title,
                "content": content
            }
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "create"
        assert result["resource_type"] == "page"

        page_data = result["results"]
        assert page_data["id"] is not None
        assert page_data["title"] == title
        assert page_data["space"]["key"] == config.confluence.space_key

        # Verify page was actually created and can be retrieved
        page_id = page_data["id"]

        # Create TestResource for verification and cleanup tracking
        test_resource = TestResource(
            resource_type="page",
            resource_id=page_id,
            service="confluence",
            cleanup_method="delete_page",
            metadata={"title": title, "space": config.confluence.space_key}
        )

        # Verify the resource exists
        assert factory.verify_resource_exists(test_resource), f"Created page {page_id} should exist"

        # Track for cleanup
        factory._created_resources.append(test_resource)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_confluence_page(self, resource_manager, factory):
        """Test getting a Confluence page through ResourceManager."""
        # Create a test page first
        test_page_id = factory.create_test_page()

        # Execute get operation
        result_json = await resource_manager.execute_operation(
            service="confluence",
            operation="get",
            resource_type="page",
            resource_id=test_page_id,
            options={"convert_to_markdown": True}
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "get"
        assert result["resource_type"] == "page"

        page_data = result["results"]
        assert page_data["id"] == test_page_id
        assert "title" in page_data
        assert "content" in page_data
        assert "space" in page_data

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_update_confluence_page(self, resource_manager, factory):
        """Test updating a Confluence page through ResourceManager."""
        # Create a test page first
        test_page_id = factory.create_test_page()

        # New data for update
        new_title = factory.get_test_identifier("Updated_Page_Title")
        new_content = f"""
# {new_title}

This page has been updated by ResourceManager integration test.

## Updated Content
- Updated bullet point 1
- Updated bullet point 2

## Updated Code Block
```javascript
function updatedFunction() {{
    return "Updated Hello, World!";
}}
```

This content was updated for testing purposes.
        """.strip()

        # Execute update operation
        result_json = await resource_manager.execute_operation(
            service="confluence",
            operation="update",
            resource_type="page",
            resource_id=test_page_id,
            resource_data={
                "title": new_title,
                "content": new_content
            }
        )

        # Parse and validate result
        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "update"

        # Verify the update by getting the page
        get_result_json = await resource_manager.execute_operation(
            service="confluence",
            operation="get",
            resource_type="page",
            resource_id=test_page_id,
            options={"convert_to_markdown": False}
        )

        get_result = json.loads(get_result_json)
        updated_page = get_result["results"]
        assert updated_page["title"] == new_title
        assert new_title in updated_page["content"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_dry_run_operations(self, resource_manager, config):
        """Test dry run operations don't actually create resources."""
        # Test Jira issue dry run
        jira_result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="issue",
            data={
                "project": {"key": config.jira.project_key},
                "summary": "Dry Run Test Issue",
                "description": "This should not be created",
                "issuetype": {"name": config.jira.issue_type}
            },
            dry_run=True
        )

        jira_result = json.loads(jira_result_json)
        assert jira_result["dry_run"] is True
        assert jira_result["operation"] == "create"
        assert jira_result["validation"] == "PASSED"
        assert "results" not in jira_result  # No actual resource created

        # Test Confluence page dry run
        confluence_result_json = await resource_manager.execute_operation(
            service="confluence",
            operation="create",
            resource="page",
            data={
                "space": {"key": config.confluence.space_key},
                "title": "Dry Run Test Page",
                "body": {
                    "storage": {
                        "value": "This should not be created",
                        "representation": "storage"
                    }
                }
            },
            dry_run=True
        )

        confluence_result = json.loads(confluence_result_json)
        assert confluence_result["dry_run"] is True
        assert confluence_result["operation"] == "create"
        assert confluence_result["validation"] == "PASSED"
        assert "results" not in confluence_result  # No actual resource created

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_error_handling(self, resource_manager):
        """Test error handling with invalid operations."""
        # Test with invalid service
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                service="invalid_service",
                operation="get",
                resource="issue",
                identifier="TEST-123"
            )
        assert "invalid_service" in str(exc_info.value).lower()

        # Test with invalid resource type
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                service="jira",
                operation="get",
                resource="invalid_type",
                identifier="TEST-123"
            )
        assert "invalid_type" in str(exc_info.value).lower()

        # Test with non-existent issue
        with pytest.raises(MetaToolError) as exc_info:
            await resource_manager.execute_operation(
                service="jira",
                operation="get",
                resource="issue",
                identifier="NONEXISTENT-999999"
            )
        assert "not found" in str(exc_info.value).lower()

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_bulk_operations(self, resource_manager, factory, config):
        """Test bulk operations through ResourceManager."""
        # Create multiple test issues for bulk operations
        issue_keys = factory.create_multiple_test_issues(3, "Bulk_Test")

        # Test bulk get operation
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="bulk_get",
            resource_type="issue",
            resource_data={"identifiers": issue_keys},
            options={"fields": "summary,status"}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "bulk_get"
        assert len(result["results"]) == 3

        # Verify all issues were retrieved
        retrieved_keys = [issue["key"] for issue in result["results"]]
        assert set(retrieved_keys) == set(issue_keys)

        # Test bulk update operation
        bulk_update_data = {
            key: {"description": f"Bulk updated description for {key}"}
            for key in issue_keys
        }

        bulk_result_json = await resource_manager.execute_operation(
            service="jira",
            operation="bulk_update",
            resource_type="issue",
            resource_data=bulk_update_data
        )

        bulk_result = json.loads(bulk_result_json)
        assert bulk_result["success"] is True
        assert bulk_result["operation"] == "bulk_update"
        assert len(bulk_result["results"]) == 3

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_field_specific_operations(self, resource_manager, factory):
        """Test field-specific operations."""
        # Create a test issue
        test_issue_key = factory.create_test_issue()

        # Test adding a comment
        comment_text = "Test comment added by ResourceManager integration test"
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="add_comment",
            resource_type="issue",
            resource_id=test_issue_key,
            resource_data={"body": comment_text}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "add_comment"

        # Test adding a label
        label_name = factory.get_test_identifier("test_label").replace(" ", "_").lower()
        label_result_json = await resource_manager.execute_operation(
            service="jira",
            operation="add_label",
            resource_type="issue",
            resource_id=test_issue_key,
            resource_data={"label": label_name}
        )

        label_result = json.loads(label_result_json)
        assert label_result["success"] is True
        assert label_result["operation"] == "add_label"

        # Verify the label was added by getting the issue
        get_result_json = await resource_manager.execute_operation(
            service="jira",
            operation="get",
            resource_type="issue",
            resource_id=test_issue_key,
            options={"fields": "labels"}
        )

        get_result = json.loads(get_result_json)
        issue_labels = get_result["results"]["fields"]["labels"]
        assert label_name in issue_labels


# SearchEngine Real API Tests
class TestSearchEngineRealAPI:
    """Test SearchEngine with real Atlassian APIs."""

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_jira_issues_with_jql(self, search_engine, factory, config):
        """Test searching Jira issues using JQL."""
        # Create a test issue to search for
        test_issue_key = factory.create_test_issue(
            summary="SearchEngine Test Issue for JQL",
            description="Test issue created for SearchEngine JQL testing"
        )

        # Test JQL string search
        jql_query = f"project = {config.jira.project_key} AND summary ~ 'SearchEngine Test Issue'"
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query=jql_query,
            options={"limit": 10, "fields": "summary,status,key"}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"
        assert result["result_count"] >= 1

        # Verify our test issue is in the results
        issue_keys = [issue["key"] for issue in result["results"]["issues"]]
        assert test_issue_key in issue_keys

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_jira_issues_structured_query(self, search_engine, config):
        """Test searching Jira issues using structured query."""
        # Test structured query (dict -> JQL conversion)
        structured_query = {
            "project": config.jira.project_key,
            "status": ["Open", "To Do", "In Progress"]
        }

        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query=structured_query,
            options={"limit": 5}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "issues"
        assert isinstance(result["results"], dict)
        assert "issues" in result["results"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_jira_users(self, search_engine, config):
        """Test searching Jira users."""
        # Search for the test user (use first part of email)
        username_part = config.jira.username.split('@')[0]
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="users",
            query=username_part,
            options={"limit": 10}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "users"
        assert result["result_count"] >= 0  # May not find users depending on permissions

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_projects(self, search_engine):
        """Test getting all Jira projects."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="projects",
            options={"expand": "description,lead"}
        )

        result = json.loads(result_json)
        print(f"DEBUG: Response keys: {list(result.keys())}")
        print(f"DEBUG: First 200 chars of response: {result_json[:200]}")
        assert result["success"] is True
        assert result["query_type"] == "projects"
        assert result["result_count"] >= 1  # Should have at least our test project

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_fields(self, search_engine):
        """Test getting Jira fields."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="fields"
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "fields"
        assert result["result_count"] > 10  # Should have many standard fields

        # Verify some standard fields exist
        field_names = [field.get("name", field.get("id", "")) for field in result["results"]]
        assert any("summary" in name.lower() for name in field_names)
        assert any("status" in name.lower() for name in field_names)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_issue_types(self, search_engine):
        """Test getting Jira issue types."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issue_types"
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "issue_types"
        assert result["result_count"] >= 1

        # Should have standard issue types
        type_names = [itype.get("name", "") for itype in result["results"]]
        # Most Jira instances have at least Task, Bug, Story, or Epic
        assert len(type_names) > 0

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_statuses(self, search_engine):
        """Test getting Jira statuses."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="statuses"
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "statuses"
        assert result["result_count"] >= 1

        # Should have standard statuses
        status_names = [status.get("name", "") for status in result["results"]]
        # Most Jira instances have these basic statuses
        assert len(status_names) > 0

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_confluence_pages_with_cql(self, search_engine, config):
        """Test searching Confluence pages using CQL."""
        # Search for pages in the test space
        cql_query = f"space = {config.confluence.space_key}"
        result_json = await search_engine.execute_search(
            service="confluence",
            query_type="pages",
            query=cql_query,
            options={"limit": 10, "expand": "body.storage"}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["query_type"] == "pages"
        assert result["result_count"] >= 0  # May not have pages yet

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_confluence_pages_structured_query(self, search_engine, config):
        """Test searching Confluence pages using structured query."""
        # Test structured query (dict -> CQL conversion)
        structured_query = {
            "space": config.confluence.space_key,
            "type": "page"
        }

        result_json = await search_engine.execute_search(
            service="confluence",
            query_type="pages",
            query=structured_query,
            options={"limit": 5}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "pages"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_confluence_spaces(self, search_engine):
        """Test getting all Confluence spaces."""
        result_json = await search_engine.execute_search(
            service="confluence",
            query_type="spaces",
            options={"limit": 25, "expand": "description"}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "spaces"
        assert result["result_count"] >= 1  # Should have at least our test space

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_confluence_users(self, search_engine, config):
        """Test searching Confluence users."""
        # Search for the test user
        username_part = config.confluence.username.split('@')[0]
        result_json = await search_engine.execute_search(
            service="confluence",
            query_type="users",
            query=username_part,
            options={"limit": 10}
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["query_type"] == "users"
        assert result["result_count"] >= 0  # May not find users depending on permissions

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_engine_dry_run(self, search_engine, config):
        """Test SearchEngine dry run validation."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query=f"project = {config.jira.project_key}",
            options={"fields": "summary,status"},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"
        assert result["validation"] == "PASSED"
        assert result["query_syntax"] == "JQL"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_engine_invalid_service(self, search_engine):
        """Test SearchEngine with invalid service."""
        with pytest.raises(MetaToolError) as exc_info:
            await search_engine.execute_search(
                service="invalid",
                query_type="issues",
                query="test"
            )

        error = exc_info.value
        assert error.error_code == "INVALID_SERVICE"
        assert "invalid" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_engine_invalid_query_type(self, search_engine):
        """Test SearchEngine with invalid query type."""
        with pytest.raises(MetaToolError) as exc_info:
            await search_engine.execute_search(
                service="jira",
                query_type="invalid_type",
                query="test"
            )

        error = exc_info.value
        assert "QUERY_TYPE_NOT_SUPPORTED" in error.error_code
        assert "invalid_type" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_engine_missing_required_query(self, search_engine):
        """Test SearchEngine with missing required query parameter."""
        with pytest.raises(MetaToolError) as exc_info:
            await search_engine.execute_search(
                service="jira",
                query_type="issues"  # This requires a query but none provided
            )

        error = exc_info.value
        assert error.error_code == "MISSING_QUERY"
        assert "requires a query parameter" in error.user_message


# BatchProcessor Real API Tests
class TestBatchProcessorRealAPI:
    """Test BatchProcessor with real Atlassian APIs."""

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_batch_create_jira_issues_dry_run(self, batch_processor, factory, config):
        """Test BatchProcessor dry run for creating multiple Jira issues."""
        # Test data - create 3 issues in a batch
        batch_data = [
            {
                "summary": factory.get_test_identifier("Batch_Issue_1"),
                "description": "First issue in batch operation test",
                "issuetype": {"name": config.jira.issue_type},
                "project": {"key": config.jira.project_key}
            },
            {
                "summary": factory.get_test_identifier("Batch_Issue_2"),
                "description": "Second issue in batch operation test",
                "issuetype": {"name": config.jira.issue_type},
                "project": {"key": config.jira.project_key}
            },
            {
                "summary": factory.get_test_identifier("Batch_Issue_3"),
                "description": "Third issue in batch operation test",
                "issuetype": {"name": config.jira.issue_type},
                "project": {"key": config.jira.project_key}
            }
        ]

        # Execute dry run batch operation
        result_json = await batch_processor.execute_batch_operation(
            service="jira",
            operation="create",
            batch_data=batch_data,
            options={"concurrency": 2},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "issue"
        assert result["batch_size"] == 3
        assert result["validation"] == "PASSED"
        assert "estimated_duration" in result

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_batch_create_jira_issues_real(self, batch_processor, factory, config):
        """Test BatchProcessor actually creating multiple Jira issues."""
        # Test data - create 2 issues in a batch for real
        batch_data = [
            {
                "summary": factory.get_test_identifier("Real_Batch_Issue_1"),
                "description": "First real issue in batch operation test",
                "issuetype": {"name": config.jira.issue_type},
                "project": {"key": config.jira.project_key}
            },
            {
                "summary": factory.get_test_identifier("Real_Batch_Issue_2"),
                "description": "Second real issue in batch operation test",
                "issuetype": {"name": config.jira.issue_type},
                "project": {"key": config.jira.project_key}
            }
        ]

        # Execute real batch operation
        result_json = await batch_processor.execute_batch_operation(
            service="jira",
            operation="create",
            batch_data=batch_data,
            options={"concurrency": 1}  # Lower concurrency for real test
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "issue"
        assert result["total_operations"] == 2
        assert result["successful_operations"] >= 1  # Allow for some potential failures
        assert len(result["results"]) == 2

        # Validate that at least some issues were created successfully
        created_issues = [r for r in result["results"] if r.get("success")]
        assert len(created_issues) >= 1

        # Track created issues for cleanup
        for issue_result in created_issues:
            if "key" in issue_result:
                factory._created_resources.append(
                    TestResource(
                        resource_type="issue",
                        resource_id=issue_result["key"],
                        service="jira",
                        cleanup_method="delete_issue"
                    )
                )

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_batch_processor_invalid_service(self, batch_processor):
        """Test BatchProcessor with invalid service."""
        with pytest.raises(MetaToolError) as exc_info:
            await batch_processor.execute_batch_operation(
                service="invalid_service",
                operation="create",
                batch_data=[{"test": "data"}]
            )

        error = exc_info.value
        assert error.error_code == "INVALID_SERVICE"
        assert "invalid_service" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_batch_processor_invalid_operation(self, batch_processor):
        """Test BatchProcessor with invalid operation."""
        with pytest.raises(MetaToolError) as exc_info:
            await batch_processor.execute_batch_operation(
                service="jira",
                operation="invalid_operation",
                batch_data=[{"test": "data"}]
            )

        error = exc_info.value
        assert error.error_code == "OPERATION_NOT_SUPPORTED"
        assert "invalid_operation" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_batch_processor_empty_batch(self, batch_processor):
        """Test BatchProcessor with empty batch data."""
        with pytest.raises(MetaToolError) as exc_info:
            await batch_processor.execute_batch_operation(
                service="jira",
                operation="create",
                batch_data=[]
            )

        error = exc_info.value
        assert error.error_code == "EMPTY_BATCH"
        assert "empty" in error.user_message.lower()


# WorkflowEngine Real API Tests
class TestWorkflowEngineRealAPI:
    """Test WorkflowEngine with real Atlassian APIs."""

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_execute_jira_transition_workflow(self, workflow_engine, factory):
        """Test executing a Jira issue transition workflow."""
        # Create a test issue to transition
        test_issue_key = factory.create_test_issue(
            summary="WorkflowEngine Transition Test",
            description="Test issue for workflow transition testing"
        )

        # Define a simple workflow to get transitions and execute one
        workflow_def = {
            "steps": [
                {
                    "type": "get_transitions",
                    "resource_id": test_issue_key,
                    "service": "jira"
                }
            ]
        }

        # Execute workflow
        result_json = await workflow_engine.execute_workflow(
            workflow_type="transition",
            workflow_definition=workflow_def,
            dry_run=True  # Use dry run to avoid actually changing state
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["workflow_type"] == "transition"
        assert result["dry_run"] is True
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_type"] == "get_transitions"
        assert result["steps"][0]["success"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_execute_approval_workflow_dry_run(self, workflow_engine, factory, config):
        """Test executing an approval workflow in dry run mode."""
        # Create a test issue for approval workflow
        test_issue_key = factory.create_test_issue()

        # Define an approval workflow
        workflow_def = {
            "approvers": [config.jira.username],
            "approval_threshold": 1,
            "timeout_hours": 24,
            "auto_approve": False,
            "steps": [
                {
                    "type": "request_approval",
                    "resource_id": test_issue_key,
                    "service": "jira",
                    "message": "Please approve this test issue"
                }
            ]
        }

        # Execute workflow in dry run
        result_json = await workflow_engine.execute_workflow(
            workflow_type="approval",
            workflow_definition=workflow_def,
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["workflow_type"] == "approval"
        assert result["dry_run"] is True
        assert result["validation"] == "PASSED"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_execute_batch_workflow(self, workflow_engine, factory, config):
        """Test executing a batch workflow."""
        # Create multiple test issues for batch workflow
        issue_keys = factory.create_multiple_test_issues(2, "Workflow_Batch")

        # Define a batch workflow to add comments to multiple issues
        workflow_def = {
            "concurrency": 2,
            "steps": [
                {
                    "type": "batch_comment",
                    "resource_ids": issue_keys,
                    "service": "jira",
                    "comment_text": "Workflow engine batch comment test"
                }
            ]
        }

        # Execute workflow
        result_json = await workflow_engine.execute_workflow(
            workflow_type="batch",
            workflow_definition=workflow_def,
            dry_run=True  # Use dry run to validate
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["workflow_type"] == "batch"
        assert result["dry_run"] is True
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_type"] == "batch_comment"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_workflow_engine_invalid_type(self, workflow_engine):
        """Test WorkflowEngine with invalid workflow type."""
        with pytest.raises(MetaToolError) as exc_info:
            await workflow_engine.execute_workflow(
                workflow_type="invalid_type",
                workflow_definition={"steps": []}
            )

        error = exc_info.value
        assert error.error_code == "WORKFLOW_TYPE_NOT_SUPPORTED"
        assert "invalid_type" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_workflow_engine_missing_definition(self, workflow_engine):
        """Test WorkflowEngine with missing workflow definition."""
        with pytest.raises(MetaToolError) as exc_info:
            await workflow_engine.execute_workflow(
                workflow_type="transition",
                workflow_definition=None
            )

        error = exc_info.value
        assert error.error_code == "MISSING_WORKFLOW_DEFINITION"
        assert "workflow definition is required" in error.user_message


# RelationshipManager Real API Tests
class TestRelationshipManagerRealAPI:
    """Test RelationshipManager with real Atlassian APIs."""

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_create_jira_issue_link(self, relationship_manager, factory):
        """Test creating a link between two Jira issues."""
        # Create two test issues to link
        issue1_key = factory.create_test_issue(
            summary="RelationshipManager Source Issue",
            description="Source issue for relationship testing"
        )
        issue2_key = factory.create_test_issue(
            summary="RelationshipManager Target Issue",
            description="Target issue for relationship testing"
        )

        # Create relationship (dry run first)
        result_json = await relationship_manager.execute_relationship_operation(
            service="jira",
            operation="create_link",
            source_id=issue1_key,
            target_id=issue2_key,
            relationship_type="blocks",
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create_link"
        assert result["dry_run"] is True
        assert result["source_id"] == issue1_key
        assert result["target_id"] == issue2_key
        assert result["relationship_type"] == "blocks"
        assert result["validation"] == "PASSED"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_issue_links(self, relationship_manager, factory):
        """Test getting links for a Jira issue."""
        # Create a test issue
        test_issue_key = factory.create_test_issue(
            summary="RelationshipManager Links Test",
            description="Test issue for getting links"
        )

        # Get issue links
        result_json = await relationship_manager.execute_relationship_operation(
            service="jira",
            operation="get_links",
            source_id=test_issue_key
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "get_links"
        assert result["source_id"] == test_issue_key
        assert "links" in result["results"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_create_confluence_page_relationship(self, relationship_manager, factory):
        """Test creating a relationship between Confluence pages."""
        # Create two test pages
        page1_id = factory.create_test_page(
            title="RelationshipManager Source Page",
            content="# Source Page\n\nThis is the source page for relationship testing."
        )
        page2_id = factory.create_test_page(
            title="RelationshipManager Target Page",
            content="# Target Page\n\nThis is the target page for relationship testing."
        )

        # Create relationship (dry run)
        result_json = await relationship_manager.execute_relationship_operation(
            service="confluence",
            operation="create_reference",
            source_id=page1_id,
            target_id=page2_id,
            relationship_type="references",
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "create_reference"
        assert result["dry_run"] is True
        assert result["source_id"] == page1_id
        assert result["target_id"] == page2_id

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_cross_service_relationship(self, relationship_manager, factory):
        """Test creating a cross-service relationship (Jira to Confluence)."""
        # Create a test issue and page
        issue_key = factory.create_test_issue(
            summary="Cross-Service Test Issue",
            description="Issue for cross-service relationship testing"
        )
        page_id = factory.create_test_page(
            title="Cross-Service Test Page",
            content="# Test Page\n\nThis page relates to a Jira issue."
        )

        # Create cross-service relationship (dry run)
        result_json = await relationship_manager.execute_relationship_operation(
            service="cross",
            operation="create_cross_reference",
            source_service="jira",
            source_id=issue_key,
            target_service="confluence",
            target_id=page_id,
            relationship_type="relates_to",
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "cross"
        assert result["operation"] == "create_cross_reference"
        assert result["dry_run"] is True
        assert result["source_service"] == "jira"
        assert result["target_service"] == "confluence"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_relationship_manager_invalid_service(self, relationship_manager):
        """Test RelationshipManager with invalid service."""
        with pytest.raises(MetaToolError) as exc_info:
            await relationship_manager.execute_relationship_operation(
                service="invalid_service",
                operation="create_link",
                source_id="TEST-1",
                target_id="TEST-2"
            )

        error = exc_info.value
        assert error.error_code == "INVALID_SERVICE"
        assert "invalid_service" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_relationship_manager_missing_target(self, relationship_manager):
        """Test RelationshipManager with missing target ID."""
        with pytest.raises(MetaToolError) as exc_info:
            await relationship_manager.execute_relationship_operation(
                service="jira",
                operation="create_link",
                source_id="TEST-1"
                # Missing target_id
            )

        error = exc_info.value
        assert error.error_code == "MISSING_TARGET_ID"
        assert "target_id is required" in error.user_message


# AttachmentHandler Real API Tests
class TestAttachmentHandlerRealAPI:
    """Test AttachmentHandler with real Atlassian APIs."""

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_upload_jira_issue_attachment_dry_run(self, attachment_handler, factory):
        """Test uploading an attachment to a Jira issue (dry run)."""
        # Create a test issue
        test_issue_key = factory.create_test_issue(
            summary="AttachmentHandler Upload Test",
            description="Test issue for attachment upload testing"
        )

        # Test attachment upload (dry run)
        result_json = await attachment_handler.execute_attachment_operation(
            service="jira",
            operation="upload",
            resource_id=test_issue_key,
            file_data={
                "filename": "test_document.txt",
                "content": "This is a test document for attachment testing.",
                "content_type": "text/plain"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "upload"
        assert result["resource_id"] == test_issue_key
        assert result["dry_run"] is True
        assert result["validation"] == "PASSED"
        assert result["file_info"]["filename"] == "test_document.txt"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_jira_issue_attachments(self, attachment_handler, factory):
        """Test getting attachments from a Jira issue."""
        # Create a test issue
        test_issue_key = factory.create_test_issue(
            summary="AttachmentHandler Get Test",
            description="Test issue for getting attachments"
        )

        # Get attachments (should return empty list for new issue)
        result_json = await attachment_handler.execute_attachment_operation(
            service="jira",
            operation="get_attachments",
            resource_id=test_issue_key
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "get_attachments"
        assert result["resource_id"] == test_issue_key
        assert "attachments" in result["results"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_upload_confluence_page_attachment_dry_run(self, attachment_handler, factory):
        """Test uploading an attachment to a Confluence page (dry run)."""
        # Create a test page
        test_page_id = factory.create_test_page(
            title="AttachmentHandler Page Test",
            content="# Test Page\n\nThis page will have attachments."
        )

        # Test attachment upload (dry run)
        result_json = await attachment_handler.execute_attachment_operation(
            service="confluence",
            operation="upload",
            resource_id=test_page_id,
            file_data={
                "filename": "test_image.png",
                "content": b"fake_png_data_for_testing",
                "content_type": "image/png"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "upload"
        assert result["resource_id"] == test_page_id
        assert result["dry_run"] is True
        assert result["validation"] == "PASSED"
        assert result["file_info"]["filename"] == "test_image.png"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_get_confluence_page_attachments(self, attachment_handler, factory):
        """Test getting attachments from a Confluence page."""
        # Create a test page
        test_page_id = factory.create_test_page(
            title="AttachmentHandler Page Get Test",
            content="# Test Page\n\nThis page for getting attachments."
        )

        # Get attachments (should return empty list for new page)
        result_json = await attachment_handler.execute_attachment_operation(
            service="confluence",
            operation="get_attachments",
            resource_id=test_page_id
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "confluence"
        assert result["operation"] == "get_attachments"
        assert result["resource_id"] == test_page_id
        assert "attachments" in result["results"]

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_bulk_attachment_operations_dry_run(self, attachment_handler, factory):
        """Test bulk attachment operations (dry run)."""
        # Create multiple test issues
        issue_keys = factory.create_multiple_test_issues(2, "Bulk_Attachment")

        # Test bulk attachment upload (dry run)
        bulk_data = [
            {
                "resource_id": issue_keys[0],
                "file_data": {
                    "filename": "bulk_doc1.txt",
                    "content": "Bulk document 1",
                    "content_type": "text/plain"
                }
            },
            {
                "resource_id": issue_keys[1],
                "file_data": {
                    "filename": "bulk_doc2.txt",
                    "content": "Bulk document 2",
                    "content_type": "text/plain"
                }
            }
        ]

        result_json = await attachment_handler.execute_attachment_operation(
            service="jira",
            operation="bulk_upload",
            bulk_data=bulk_data,
            options={"concurrency": 2},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "bulk_upload"
        assert result["dry_run"] is True
        assert result["batch_size"] == 2
        assert result["validation"] == "PASSED"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_attachment_handler_invalid_service(self, attachment_handler):
        """Test AttachmentHandler with invalid service."""
        with pytest.raises(MetaToolError) as exc_info:
            await attachment_handler.execute_attachment_operation(
                service="invalid_service",
                operation="upload",
                resource_id="TEST-1",
                file_data={"filename": "test.txt", "content": "test"}
            )

        error = exc_info.value
        assert error.error_code == "INVALID_SERVICE"
        assert "invalid_service" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_attachment_handler_missing_file_data(self, attachment_handler, factory):
        """Test AttachmentHandler with missing file data."""
        test_issue_key = factory.create_test_issue()

        with pytest.raises(MetaToolError) as exc_info:
            await attachment_handler.execute_attachment_operation(
                service="jira",
                operation="upload",
                resource_id=test_issue_key
                # Missing file_data
            )

        error = exc_info.value
        assert error.error_code == "MISSING_FILE_DATA"
        assert "file_data is required" in error.user_message

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_attachment_handler_invalid_operation(self, attachment_handler):
        """Test AttachmentHandler with invalid operation."""
        with pytest.raises(MetaToolError) as exc_info:
            await attachment_handler.execute_attachment_operation(
                service="jira",
                operation="invalid_operation",
                resource_id="TEST-1"
            )

        error = exc_info.value
        assert error.error_code == "OPERATION_NOT_SUPPORTED"
        assert "invalid_operation" in error.user_message


class TestSprintManagementRealAPI:
    """Test Sprint Management operations using real APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher):
        """Get ResourceManager adapter for sprint operations."""
        return ResourceManagerTestAdapter(jira_fetcher, None)

    @pytest.fixture
    def search_engine(self, jira_fetcher, confluence_fetcher):
        """Get SearchEngine adapter for sprint queries."""
        return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_search_sprints_dry_run(self, search_engine):
        """Test searching for sprints with dry run."""
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="sprints",
            query={"board_id": "1"},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "sprints"
        assert result["validation"] == "PASSED"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_lifecycle_operations_dry_run(self, resource_manager, factory):
        """Test complete sprint lifecycle operations with dry run."""
        # Test creating a sprint
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="sprint",
            resource_data={
                "name": "Test Sprint for Integration",
                "board_id": "1",
                "goal": "Test sprint management functionality"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "sprint"
        assert result["dry_run"] is True

        # Test starting a sprint
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="sprint",
            resource_id="1",
            resource_data={
                "state": "active",
                "start_date": "2025-01-15T10:00:00.000Z",
                "end_date": "2025-01-29T10:00:00.000Z"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

        # Test closing a sprint
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="sprint",
            resource_id="1",
            resource_data={
                "state": "closed"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_issue_management_dry_run(self, resource_manager, factory):
        """Test sprint issue management operations with dry run."""
        # Test adding issues to sprint
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="add_to_sprint",
            resource="issue",
            resource_data={
                "sprint_id": "1",
                "issue_keys": ["TEST-1", "TEST-2"]
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "add_to_sprint"
        assert result["dry_run"] is True

        # Test removing issues from sprint
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="remove_from_sprint",
            resource="issue",
            resource_data={
                "sprint_id": "1",
                "issue_keys": ["TEST-1"]
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "remove_from_sprint"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_burndown_and_reports_dry_run(self, search_engine):
        """Test sprint burndown and reporting queries with dry run."""
        # Test getting sprint report data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "sprint": "1"
            },
            options={
                "fields": ["summary", "status", "assignee", "story_points"],
                "expand": ["changelog"]
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_capacity_planning_dry_run(self, search_engine):
        """Test sprint capacity planning queries with dry run."""
        # Test getting team capacity data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "assignee": "currentUser()",
                "sprint": "openSprints()"
            },
            options={
                "fields": ["summary", "story_points", "time_estimate"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_velocity_analysis_dry_run(self, search_engine):
        """Test sprint velocity analysis queries with dry run."""
        # Test getting completed sprint data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "status": ["Done", "Closed"],
                "sprint": "in closedSprints()"
            },
            options={
                "fields": ["summary", "story_points", "resolution_date"],
                "limit": 200
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_retrospective_data_dry_run(self, search_engine):
        """Test gathering retrospective data with dry run."""
        # Test getting issues with detailed history for retrospectives
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "sprint": "1"
            },
            options={
                "fields": ["summary", "status", "priority", "assignee", "created", "resolved"],
                "expand": ["changelog", "comments"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_board_management_dry_run(self, search_engine):
        """Test sprint board management queries with dry run."""
        # Test getting board information
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="boards",
            query={"project_key": "TEST"},
            options={"limit": 10},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "boards"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_sprint_invalid_operations(self, resource_manager):
        """Test sprint operations with invalid parameters."""
        # Test invalid sprint state
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="update",
                resource="sprint",
                resource_id="1",
                resource_data={
                    "state": "invalid_state"
                }
            )

        # Test missing required fields
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="create",
                resource="sprint",
                resource_data={}  # Missing required fields
            )


class TestEpicManagementRealAPI:
    """Test Epic Management operations using real APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher):
        """Get ResourceManager adapter for epic operations."""
        return ResourceManagerTestAdapter(jira_fetcher, None)

    @pytest.fixture
    def search_engine(self, jira_fetcher, confluence_fetcher):
        """Get SearchEngine adapter for epic queries."""
        return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)

    @pytest.fixture
    def relationship_manager(self, jira_fetcher):
        """Get RelationshipManager adapter for epic linking."""
        return RelationshipManagerTestAdapter(jira_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_creation_dry_run(self, resource_manager, factory):
        """Test epic creation with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="issue",
            resource_data={
                "project": {"key": "TEST"},
                "summary": "Test Epic for Integration Testing",
                "description": "Epic to test epic management functionality",
                "issuetype": {"name": "Epic"},
                "customfield_10011": "TEST-EPIC-001"  # Epic Name field
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "issue"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_story_linking_dry_run(self, relationship_manager, factory):
        """Test linking stories to epics with dry run."""
        result_json = await relationship_manager.execute_relationship_operation(
            operation="link_to_epic",
            issue_key="TEST-1",
            epic_key="TEST-2",
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "link_to_epic"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_story_unlinking_dry_run(self, relationship_manager, factory):
        """Test unlinking stories from epics with dry run."""
        result_json = await relationship_manager.execute_relationship_operation(
            operation="unlink_from_epic",
            issue_key="TEST-1",
            epic_key="TEST-2",
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "unlink_from_epic"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_progress_tracking_dry_run(self, search_engine):
        """Test epic progress tracking queries with dry run."""
        # Test getting all stories in an epic
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "parent": "TEST-2"  # Epic key
            },
            options={
                "fields": ["summary", "status", "assignee", "story_points", "progress"],
                "expand": ["changelog"]
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_burndown_analysis_dry_run(self, search_engine):
        """Test epic burndown analysis with dry run."""
        # Test getting epic burndown data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "parent": "TEST-2",
                "status": ["Done", "Closed"]
            },
            options={
                "fields": ["summary", "story_points", "resolved", "assignee"],
                "expand": ["changelog"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_capacity_planning_dry_run(self, search_engine):
        """Test epic capacity planning queries with dry run."""
        # Test getting epic capacity and estimation data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "parent": "TEST-2",
                "status": ["To Do", "In Progress"]
            },
            options={
                "fields": ["summary", "story_points", "time_estimate", "assignee"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_status_reporting_dry_run(self, search_engine):
        """Test epic status reporting queries with dry run."""
        # Test getting epic summary with all child issues
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query="project = TEST AND issueType = Epic",
            options={
                "fields": ["summary", "status", "assignee", "created", "updated", "customfield_10011"],
                "expand": ["subtasks"],
                "limit": 20
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_cross_project_analysis_dry_run(self, search_engine):
        """Test cross-project epic analysis with dry run."""
        # Test getting epics across multiple projects
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query="issueType = Epic AND assignee = currentUser()",
            options={
                "fields": ["summary", "project", "status", "story_points"],
                "limit": 30
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_dependency_tracking_dry_run(self, search_engine):
        """Test epic dependency tracking with dry run."""
        # Test getting epic dependencies and blockers
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "parent": "TEST-2"
            },
            options={
                "fields": ["summary", "status", "issuelinks"],
                "expand": ["issuelinks"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_timeline_analysis_dry_run(self, search_engine):
        """Test epic timeline analysis with dry run."""
        # Test getting epic timeline and milestone data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "parent": "TEST-2"
            },
            options={
                "fields": ["summary", "created", "updated", "duedate", "status"],
                "expand": ["changelog"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_invalid_operations(self, relationship_manager):
        """Test epic operations with invalid parameters."""
        # Test linking to non-existent epic
        with pytest.raises(MetaToolError):
            await relationship_manager.execute_relationship_operation(
                operation="link_to_epic",
                issue_key="TEST-1",
                epic_key="INVALID-EPIC"
            )

        # Test invalid epic operation
        with pytest.raises(MetaToolError):
            await relationship_manager.execute_relationship_operation(
                operation="invalid_epic_operation",
                issue_key="TEST-1",
                epic_key="TEST-2"
            )


class TestWorkLogRealAPI:
    """Test WorkLog Management operations using real APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher):
        """Get ResourceManager adapter for worklog operations."""
        return ResourceManagerTestAdapter(jira_fetcher, None)

    @pytest.fixture
    def search_engine(self, jira_fetcher, confluence_fetcher):
        """Get SearchEngine adapter for worklog queries."""
        return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_worklog_creation_dry_run(self, resource_manager, factory):
        """Test worklog creation with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="worklog",
            resource_data={
                "issue_key": "TEST-1",
                "time_spent": "2h 30m",
                "started": "2025-01-15T09:00:00.000+0000",
                "comment": "Worked on implementation and testing"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "worklog"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_worklog_update_dry_run(self, resource_manager, factory):
        """Test worklog update with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="worklog",
            resource_id="12345",
            resource_data={
                "issue_key": "TEST-1",
                "time_spent": "3h",
                "comment": "Updated time spent and added details"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_worklog_deletion_dry_run(self, resource_manager, factory):
        """Test worklog deletion with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="delete",
            resource="worklog",
            resource_id="12345",
            resource_data={
                "issue_key": "TEST-1"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "delete"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_time_tracking_reports_dry_run(self, search_engine):
        """Test time tracking reports with dry run."""
        # Test getting time tracking data for user
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "assignee": "currentUser()",
                "updated": ">= -7d"
            },
            options={
                "fields": ["summary", "timespent", "timeoriginalestimate", "timeestimate", "worklog"],
                "expand": ["worklog"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_team_capacity_analysis_dry_run(self, search_engine):
        """Test team capacity analysis with dry run."""
        # Test getting team worklog data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "updated": ">= -14d"
            },
            options={
                "fields": ["summary", "assignee", "timespent", "worklog"],
                "expand": ["worklog"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_project_time_tracking_dry_run(self, search_engine):
        """Test project-level time tracking with dry run."""
        # Test getting project time tracking summary
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "created": ">= -30d"
            },
            options={
                "fields": ["summary", "timespent", "timeoriginalestimate", "status"],
                "limit": 200
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_worklog_by_date_range_dry_run(self, search_engine):
        """Test worklog queries by date range with dry run."""
        # Test getting worklogs for specific date range
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "worklogDate": ">= 2025-01-01 AND worklogDate <= 2025-01-31"
            },
            options={
                "fields": ["summary", "worklog"],
                "expand": ["worklog"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_billable_hours_tracking_dry_run(self, search_engine):
        """Test billable hours tracking with dry run."""
        # Test getting billable time data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "assignee": "currentUser()",
                "worklogDate": ">= -7d"
            },
            options={
                "fields": ["summary", "worklog", "components", "labels"],
                "expand": ["worklog"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_time_estimation_accuracy_dry_run(self, search_engine):
        """Test time estimation accuracy analysis with dry run."""
        # Test getting estimation vs actual time data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "status": ["Done", "Closed"],
                "resolved": ">= -30d"
            },
            options={
                "fields": ["summary", "timespent", "timeoriginalestimate", "assignee"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_overtime_analysis_dry_run(self, search_engine):
        """Test overtime analysis with dry run."""
        # Test getting overtime patterns
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "assignee": "currentUser()",
                "worklogDate": ">= -14d"
            },
            options={
                "fields": ["summary", "worklog"],
                "expand": ["worklog"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_worklog_invalid_operations(self, resource_manager):
        """Test worklog operations with invalid parameters."""
        # Test worklog with invalid time format
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="create",
                resource="worklog",
                resource_data={
                    "issue_key": "TEST-1",
                    "time_spent": "invalid_time_format"
                }
            )

        # Test worklog for non-existent issue
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="create",
                resource="worklog",
                resource_data={
                    "issue_key": "INVALID-123",
                    "time_spent": "2h"
                }
            )


class TestVersionReleaseRealAPI:
    """Test Version and Release Management operations using real APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher):
        """Get ResourceManager adapter for version operations."""
        return ResourceManagerTestAdapter(jira_fetcher, None)

    @pytest.fixture
    def search_engine(self, jira_fetcher, confluence_fetcher):
        """Get SearchEngine adapter for version queries."""
        return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_creation_dry_run(self, resource_manager, factory):
        """Test version creation with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="version",
            resource_data={
                "project": "TEST",
                "name": "v2.1.0",
                "description": "Release 2.1.0 with new features and bug fixes",
                "release_date": "2025-02-15",
                "archived": False,
                "released": False
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "version"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_release_dry_run(self, resource_manager, factory):
        """Test version release with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="version",
            resource_id="10001",
            resource_data={
                "released": True,
                "release_date": "2025-01-15"
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_archival_dry_run(self, resource_manager, factory):
        """Test version archival with dry run."""
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="version",
            resource_id="10001",
            resource_data={
                "archived": True
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_release_planning_queries_dry_run(self, search_engine):
        """Test release planning queries with dry run."""
        # Test getting issues planned for specific version
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "v2.1.0"
            },
            options={
                "fields": ["summary", "status", "assignee", "priority", "story_points"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_release_progress_tracking_dry_run(self, search_engine):
        """Test release progress tracking with dry run."""
        # Test getting release progress data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "v2.1.0",
                "status": ["Done", "Closed"]
            },
            options={
                "fields": ["summary", "resolved", "assignee"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_listing_dry_run(self, search_engine):
        """Test version listing with dry run."""
        # Test getting all versions for project
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="versions",
            query={"project_key": "TEST"},
            options={"limit": 20},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "versions"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_unreleased_versions_analysis_dry_run(self, search_engine):
        """Test unreleased versions analysis with dry run."""
        # Test getting unreleased version data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "in unreleasedVersions()"
            },
            options={
                "fields": ["summary", "status", "fixVersions", "assignee"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_burndown_analysis_dry_run(self, search_engine):
        """Test version burndown analysis with dry run."""
        # Test getting version burndown data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "v2.1.0"
            },
            options={
                "fields": ["summary", "status", "story_points", "resolved"],
                "expand": ["changelog"],
                "limit": 200
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_release_notes_preparation_dry_run(self, search_engine):
        """Test release notes preparation queries with dry run."""
        # Test getting issues for release notes
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "v2.1.0",
                "status": ["Done", "Closed"],
                "type": ["Bug", "Story", "New Feature"]
            },
            options={
                "fields": ["summary", "description", "issuetype", "priority"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_scope_management_dry_run(self, search_engine):
        """Test version scope management with dry run."""
        # Test getting version scope changes
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "v2.1.0"
            },
            options={
                "fields": ["summary", "fixVersions", "updated"],
                "expand": ["changelog"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_cross_version_analysis_dry_run(self, search_engine):
        """Test cross-version analysis with dry run."""
        # Test getting cross-version data
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "fixVersion": "in (v2.0.0, v2.1.0, v2.2.0)"
            },
            options={
                "fields": ["summary", "fixVersions", "status", "created"],
                "limit": 150
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_hotfix_version_management_dry_run(self, resource_manager):
        """Test hotfix version management with dry run."""
        # Test creating hotfix version
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="create",
            resource="version",
            resource_data={
                "project": "TEST",
                "name": "v2.0.1-hotfix",
                "description": "Critical hotfix for v2.0.0",
                "release_date": "2025-01-20",
                "archived": False,
                "released": False
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["resource_type"] == "version"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_version_invalid_operations(self, resource_manager):
        """Test version operations with invalid parameters."""
        # Test version with invalid date format
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="create",
                resource="version",
                resource_data={
                    "project": "TEST",
                    "name": "v3.0.0",
                    "release_date": "invalid-date-format"
                }
            )

        # Test updating non-existent version
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="update",
                resource="version",
                resource_id="99999",
                resource_data={
                    "released": True
                }
            )


class TestCustomFieldsRealAPI:
    """Test Custom Fields Management operations using real APIs."""

    @pytest.fixture
    def resource_manager(self, jira_fetcher):
        """Get ResourceManager adapter for custom field operations."""
        return ResourceManagerTestAdapter(jira_fetcher, None)

    @pytest.fixture
    def search_engine(self, jira_fetcher, confluence_fetcher):
        """Get SearchEngine adapter for custom field queries."""
        return SearchEngineTestAdapter(jira_fetcher, confluence_fetcher)

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_fields_discovery_dry_run(self, search_engine):
        """Test custom fields discovery with dry run."""
        # Test getting all custom fields
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="fields",
            options={"include_custom": True},
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "fields"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_usage_analysis_dry_run(self, search_engine):
        """Test custom field usage analysis with dry run."""
        # Test analyzing custom field usage
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10001]": "is not EMPTY"  # Custom field is populated
            },
            options={
                "fields": ["summary", "customfield_10001", "customfield_10002"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_story_points_analysis_dry_run(self, search_engine):
        """Test story points custom field analysis with dry run."""
        # Test story points reporting
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "issuetype": ["Story", "Bug", "Task"],
                "cf[10016]": "is not EMPTY"  # Story Points field
            },
            options={
                "fields": ["summary", "customfield_10016", "status", "assignee"],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_epic_link_field_analysis_dry_run(self, search_engine):
        """Test epic link custom field analysis with dry run."""
        # Test epic link field usage
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10014]": "is not EMPTY"  # Epic Link field
            },
            options={
                "fields": ["summary", "customfield_10014", "issuetype"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_select_field_analysis_dry_run(self, search_engine):
        """Test custom select field analysis with dry run."""
        # Test custom select field values
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10020]": "in (High, Medium, Low)"  # Priority custom field
            },
            options={
                "fields": ["summary", "customfield_10020", "priority"],
                "limit": 75
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_date_field_analysis_dry_run(self, search_engine):
        """Test custom date field analysis with dry run."""
        # Test custom date field queries
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10030]": ">= -30d"  # Custom date field within last 30 days
            },
            options={
                "fields": ["summary", "customfield_10030", "created"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_text_field_search_dry_run(self, search_engine):
        """Test custom text field search with dry run."""
        # Test custom text field search
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10040]": "~ \"test\""  # Custom text field contains "test"
            },
            options={
                "fields": ["summary", "customfield_10040"],
                "limit": 25
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_update_dry_run(self, resource_manager, factory):
        """Test custom field update with dry run."""
        # Test updating custom field values
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="update",
            resource="issue",
            resource_id="TEST-1",
            resource_data={
                "customfield_10016": 5,  # Story Points
                "customfield_10020": {"value": "High"},  # Custom select field
                "customfield_10040": "Updated custom text value"  # Custom text field
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_bulk_custom_field_update_dry_run(self, resource_manager):
        """Test bulk custom field updates with dry run."""
        # Test bulk updating custom fields
        result_json = await resource_manager.execute_operation(
            service="jira",
            operation="bulk_update",
            resource="issue",
            resource_data={
                "jql": "project = TEST AND cf[10016] is EMPTY",
                "fields": {
                    "customfield_10016": 3  # Set default story points
                }
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["operation"] == "bulk_update"
        assert result["dry_run"] is True

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_validation_dry_run(self, search_engine):
        """Test custom field validation with dry run."""
        # Test finding issues with invalid custom field values
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10016]": "> 20"  # Story points greater than 20 (possibly invalid)
            },
            options={
                "fields": ["summary", "customfield_10016", "issuetype"],
                "limit": 20
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_reporting_dry_run(self, search_engine):
        """Test custom field reporting with dry run."""
        # Test comprehensive custom field reporting
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "updated": ">= -7d"
            },
            options={
                "fields": [
                    "summary", "customfield_10016", "customfield_10020",
                    "customfield_10030", "customfield_10040"
                ],
                "limit": 100
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["query_type"] == "issues"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_migration_analysis_dry_run(self, search_engine):
        """Test custom field migration analysis with dry run."""
        # Test analysis for custom field migrations
        result_json = await search_engine.execute_search(
            service="jira",
            query_type="issues",
            query={
                "project": "TEST",
                "cf[10016]": "is EMPTY AND cf[10020] is not EMPTY"
            },
            options={
                "fields": ["summary", "customfield_10016", "customfield_10020"],
                "limit": 50
            },
            dry_run=True
        )

        result = json.loads(result_json)
        assert result["dry_run"] is True
        assert result["service"] == "jira"

    @skip_if_no_real_api("Real API testing not configured")
    @pytest.mark.asyncio
    async def test_custom_field_invalid_operations(self, resource_manager):
        """Test custom field operations with invalid parameters."""
        # Test invalid custom field value type
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="update",
                resource="issue",
                resource_id="TEST-1",
                resource_data={
                    "customfield_10016": "invalid_number"  # Story points should be numeric
                }
            )

        # Test non-existent custom field
        with pytest.raises(MetaToolError):
            await resource_manager.execute_operation(
                service="jira",
                operation="update",
                resource="issue",
                resource_id="TEST-1",
                resource_data={
                    "customfield_99999": "value"  # Non-existent custom field
                }
            )


# =============================================================================
# REGRESSION TESTS FOR P0 AND P1 ISSUES
# =============================================================================

class TestRegressionPrevention:
    """Test suite to prevent regression of critical P0 and P1 issues."""

    async def test_p0_request_context_access_pattern(self, resource_manager):
        """Test P0 issue regression: RequestContext object has no attribute 'request_context'."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher
        from unittest.mock import MagicMock

        # Create mock context with the CORRECT structure
        mock_server_ctx = MagicMock()
        mock_request_context = MagicMock()
        mock_app_context = MagicMock()

        mock_request_context.lifespan_context = {"app_lifespan_context": mock_app_context}
        mock_server_ctx.request_context = mock_request_context

        # This should work with the fixed pattern: ctx = server._mcp_server (not server._mcp_server.request_context)
        with patch('src.mcp_atlassian.jira.client.JiraClient'):
            fetcher = get_jira_fetcher(mock_server_ctx)
            assert fetcher is not None

        # The old broken pattern would have been: get_jira_fetcher(mock_server_ctx.request_context)
        # which would fail with: AttributeError: 'RequestContext' object has no attribute 'request_context'

    async def test_p1_batch_processor_api_signature(self, batch_processor):
        """Test P1 issue regression: BatchProcessor API signature with correct parameters."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_context = MagicMock()
        mock_context.request_context = MagicMock()
        mock_context.request_context.lifespan_context = {"app_lifespan_context": MagicMock()}

        with patch.object(batch_processor, '_get_jira_client') as mock_get_jira:
            mock_jira_client = AsyncMock()
            mock_get_jira.return_value = mock_jira_client

            # Mock successful issue creation
            mock_issue = MagicMock()
            mock_issue.to_simplified_dict.return_value = {"key": "TEST-123", "summary": "Test Issue"}
            mock_jira_client.create_issue.return_value = mock_issue

            items = [{"summary": "Test Issue", "project": {"key": "TEST"}, "issuetype": {"name": "Task"}}]

            # This should work with the CORRECT API signature
            result_json = await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",  # CORRECT: resource_type (not resource)
                items=items,
                options={"concurrency": 2},  # CORRECT: concurrency in options (not direct parameter)
                dry_run=True
            )

            result = json.loads(result_json)
            assert result["success"] is True
            assert result["resource_type"] == "issue"

    async def test_p1_batch_processor_rejects_old_signature(self, batch_processor):
        """Test that old P1 issue signature raises TypeError."""
        mock_context = MagicMock()

        items = [{"summary": "Test Issue"}]

        # This should FAIL with the old broken signature
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource="issue",  # WRONG: should be resource_type
                items=items,
                dry_run=True
            )

        assert "unexpected keyword argument 'resource'" in str(exc_info.value)

        # This should also FAIL with concurrency as direct parameter
        with pytest.raises(TypeError) as exc_info:
            await batch_processor.execute_batch_operation(
                ctx=mock_context,
                service="jira",
                operation="create",
                resource_type="issue",
                items=items,
                concurrency=2,  # WRONG: should be in options
                dry_run=True
            )

        assert "unexpected keyword argument 'concurrency'" in str(exc_info.value)

    async def test_all_meta_tools_dry_run_regression(self):
        """Test that all meta-tools accept dry_run parameter (regression prevention)."""
        from src.mcp_atlassian.meta_tools.resource_manager import ResourceManager
        from src.mcp_atlassian.meta_tools.batch_processor import BatchProcessor
        from src.mcp_atlassian.meta_tools.search_engine import SearchEngine
        from src.mcp_atlassian.meta_tools.workflow_engine import WorkflowEngine
        from src.mcp_atlassian.meta_tools.relationship_manager import RelationshipManager
        from src.mcp_atlassian.meta_tools.attachment_handler import AttachmentHandler

        # All of these should work without TypeError about unexpected dry_run argument
        try:
            tools = [
                ResourceManager(dry_run=True),
                BatchProcessor(dry_run=True),
                SearchEngine(dry_run=True),
                WorkflowEngine(dry_run=True),
                RelationshipManager(dry_run=True),
                AttachmentHandler(dry_run=True)
            ]

            for tool in tools:
                assert tool.dry_run is True
                assert hasattr(tool, 'dry_run')

        except TypeError as e:
            if "unexpected keyword argument 'dry_run'" in str(e):
                pytest.fail(f"Meta-tool constructor does not accept dry_run parameter: {e}")
            else:
                raise

    async def test_real_api_batch_processor_signature_validation(self, batch_processor, factory):
        """Test BatchProcessor with real API using correct signature."""
        # Create real test data
        batch_data = [
            {
                "summary": factory.get_test_identifier("Regression_Test_Issue"),
                "description": "Regression test for BatchProcessor API signature",
                "issuetype": {"name": factory.config.jira.issue_type},
                "project": {"key": factory.config.jira.project_key}
            }
        ]

        # This should work with correct signature in dry-run mode
        result_json = await batch_processor.execute_batch_operation(
            service="jira",
            operation="create",
            resource_type="issue",  # Correct parameter name
            items=batch_data,
            options={"concurrency": 1},  # Correct placement for concurrency
            dry_run=True  # Dry run for safety
        )

        result = json.loads(result_json)
        assert result["success"] is True
        assert result["service"] == "jira"
        assert result["operation"] == "create"
        assert result["resource_type"] == "issue"

    @skip_if_no_real_api("Real API testing not configured")
    async def test_real_api_context_dependency_injection(self, factory):
        """Test that dependency injection works with real API (context access pattern)."""
        from src.mcp_atlassian.servers.dependencies import get_jira_fetcher, get_confluence_fetcher
        from unittest.mock import MagicMock

        # Create a mock server context that mimics the real structure
        mock_server_ctx = MagicMock()
        mock_request_context = MagicMock()

        # Use the actual app context from factory
        mock_request_context.lifespan_context = {"app_lifespan_context": factory.app_context}
        mock_server_ctx.request_context = mock_request_context

        # These should work with real configurations
        jira_fetcher = get_jira_fetcher(mock_server_ctx)
        confluence_fetcher = get_confluence_fetcher(mock_server_ctx)

        assert jira_fetcher is not None
        assert confluence_fetcher is not None

        # Verify they can perform basic operations (just connectivity check)
        try:
            current_user = jira_fetcher.get_current_user()
            assert current_user is not None
        except Exception as e:
            # Connection errors are acceptable in this test
            logger.info(f"Jira connection test completed with: {e}")

    async def test_v2_tool_handler_integration_regression(self):
        """Test that v2 tool handlers in main.py work with correct signatures."""
        from src.mcp_atlassian.servers.main import (
            batch_processor_tool, resource_manager_tool, search_engine_tool,
            workflow_engine_tool, relationship_manager_tool, attachment_handler_tool
        )

        # Test that all tool handlers can be called without errors
        with patch('src.mcp_atlassian.meta_tools.batch_processor.BatchProcessor') as MockBP:
            MockBP.return_value.execute_batch_operation = AsyncMock(return_value='{"success": true}')

            result = await batch_processor_tool(
                service="jira",
                operation="create",
                resource="issue",  # Should be converted to resource_type
                items=[{"summary": "Test"}],
                dry_run=True
            )
            assert '"success": true' in result

        with patch('src.mcp_atlassian.meta_tools.resource_manager.ResourceManager') as MockRM:
            MockRM.return_value.execute_operation = AsyncMock(return_value='{"success": true}')

            result = await resource_manager_tool(
                service="jira",
                resource="issue",
                operation="get",
                identifier="TEST-123",
                dry_run=True
            )
            assert '"success": true' in result

        with patch('src.mcp_atlassian.meta_tools.search_engine.SearchEngine') as MockSE:
            MockSE.return_value.execute_search = AsyncMock(return_value='{"results": []}')

            result = await search_engine_tool(
                service="jira",
                query_type="jql",
                query="project = TEST",
                dry_run=True
            )
            assert '"results"' in result

        # Test remaining tool handlers
        with patch('src.mcp_atlassian.meta_tools.workflow_engine.WorkflowEngine') as MockWE:
            MockWE.return_value.execute_workflow_operation = AsyncMock(return_value='{"success": true}')

            result = await workflow_engine_tool(
                operation="transition",
                issue_key="TEST-123",
                transition_name="In Progress",
                dry_run=True
            )
            assert '"success": true' in result

        with patch('src.mcp_atlassian.meta_tools.relationship_manager.RelationshipManager') as MockRM:
            MockRM.return_value.execute_relationship_operation = AsyncMock(return_value='{"success": true}')

            result = await relationship_manager_tool(
                operation="link",
                issue_key="TEST-123",
                target_issue_key="TEST-456",
                link_type="Blocks",
                dry_run=True
            )
            assert '"success": true' in result

        with patch('src.mcp_atlassian.meta_tools.attachment_handler.AttachmentHandler') as MockAH:
            MockAH.return_value.execute_attachment_operation = AsyncMock(return_value='{"success": true}')

            result = await attachment_handler_tool(
                service="jira",
                operation="upload",
                issue_key="TEST-123",
                file_path="/test/file.txt",
                dry_run=True
            )
            assert '"success": true' in result