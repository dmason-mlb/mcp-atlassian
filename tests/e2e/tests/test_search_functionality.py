"""
Search functionality tests for Jira and Confluence MCP tools.

Tests search capabilities across both services including JQL queries,
text searches, field searches, and cross-service search scenarios.
"""

import pytest
import asyncio
from typing import Dict, Any, List

from ..tests.base_test import MCPBaseTest, MCPJiraTest, MCPConfluenceTest


class TestJiraSearch(MCPJiraTest):
    """Test Jira search functionality via MCP tools."""

    @pytest.mark.api
    async def test_jira_basic_search(self, mcp_client, test_config):
        """Test basic Jira issue search functionality."""
        # Create test issues to search for
        issue1 = await self.create_test_issue(
            mcp_client,
            test_config,
            issue_type="Task",
            description="Search test issue one with unique content"
        )
        issue1_key = self.extract_issue_key(issue1)
        
        issue2 = await self.create_test_issue(
            mcp_client,
            test_config,
            issue_type="Bug",
            description="Search test issue two with different content"
        )
        issue2_key = self.extract_issue_key(issue2)
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Test project-based search
        search_result = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND summary ~ 'Test Issue' ORDER BY created DESC",
            limit=10
        )
        
        self.assert_success_response(search_result, ["issues"])
        
        # Verify both issues are found
        issues = self.extract_value(search_result, "issues", default=[])
        issue_keys = [self.extract_value(issue, "key") for issue in issues]
        
        assert issue1_key in issue_keys, f"Issue {issue1_key} not found in search results"
        assert issue2_key in issue_keys, f"Issue {issue2_key} not found in search results"

    @pytest.mark.api
    async def test_jira_jql_query_validation(self, mcp_client, test_config):
        """Test JQL query construction and validation."""
        # Create test issue with specific attributes
        test_issue = await self.create_test_issue(
            mcp_client,
            test_config,
            issue_type="Story",
            description="JQL test issue with specific attributes"
        )
        issue_key = self.extract_issue_key(test_issue)
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Test various JQL patterns
        jql_tests = [
            {
                "jql": f"key = {issue_key}",
                "description": "Direct key search",
                "should_find": True
            },
            {
                "jql": f"project = {test_config['jira_project']} AND issuetype = Story",
                "description": "Project and issue type filter",
                "should_find": True
            },
            {
                "jql": f"project = {test_config['jira_project']} AND text ~ 'JQL test issue'",
                "description": "Text search within project",
                "should_find": True
            },
            {
                "jql": f"project = {test_config['jira_project']} AND issuetype = Epic",
                "description": "Non-matching issue type",
                "should_find": False
            }
        ]
        
        for test_case in jql_tests:
            search_result = await mcp_client.jira_search(
                jql=test_case["jql"],
                limit=5
            )
            
            self.assert_success_response(search_result, ["issues"])
            
            issues = self.extract_value(search_result, "issues", default=[])
            found_keys = [self.extract_value(issue, "key") for issue in issues]
            
            if test_case["should_find"]:
                assert issue_key in found_keys, f"JQL test '{test_case['description']}' should find issue {issue_key}"
            else:
                assert issue_key not in found_keys, f"JQL test '{test_case['description']}' should not find issue {issue_key}"

    @pytest.mark.api
    async def test_jira_field_search(self, mcp_client, test_config):
        """Test Jira field search functionality."""
        # Search for available fields
        field_result = await mcp_client.jira_search_fields(
            keyword="summary",
            limit=10
        )
        
        self.assert_success_response(field_result)
        
        # Extract field data
        fields = self.extract_value(field_result, "fields") or field_result
        if isinstance(fields, dict):
            fields = [fields]
        
        assert len(fields) > 0, "Should find fields matching 'summary'"
        
        # Look for summary field
        summary_field = None
        for field in fields:
            if isinstance(field, dict) and field.get("name") == "Summary":
                summary_field = field
                break
        
        assert summary_field, "Should find Summary field in results"
        assert "id" in summary_field, "Summary field should have ID"

    @pytest.mark.api
    async def test_jira_search_with_pagination(self, mcp_client, test_config):
        """Test Jira search pagination functionality."""
        # Create multiple test issues
        issue_keys = []
        for i in range(5):
            issue = await self.create_test_issue(
                mcp_client,
                test_config,
                issue_type="Task",
                description=f"Pagination test issue {i+1}"
            )
            issue_keys.append(self.extract_issue_key(issue))
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Test pagination
        page1_result = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND summary ~ 'Pagination test' ORDER BY created DESC",
            limit=3,
            start_at=0
        )
        
        self.assert_success_response(page1_result, ["issues"])
        
        page1_issues = self.extract_value(page1_result, "issues", default=[])
        assert len(page1_issues) <= 3, "First page should have at most 3 issues"
        
        # Get second page
        page2_result = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND summary ~ 'Pagination test' ORDER BY created DESC",
            limit=3,
            start_at=3
        )
        
        self.assert_success_response(page2_result, ["issues"])
        
        page2_issues = self.extract_value(page2_result, "issues", default=[])
        
        # Verify no overlap between pages
        page1_keys = {self.extract_value(issue, "key") for issue in page1_issues}
        page2_keys = {self.extract_value(issue, "key") for issue in page2_issues}
        
        assert not (page1_keys & page2_keys), "Pages should not have overlapping issues"

    @pytest.mark.api
    async def test_jira_advanced_search_filters(self, mcp_client, test_config):
        """Test advanced JQL search filters."""
        # Create issues with different attributes
        story_issue = await self.create_test_issue(
            mcp_client,
            test_config,
            issue_type="Story",
            description="Advanced search story issue"
        )
        
        task_issue = await self.create_test_issue(
            mcp_client,
            test_config,
            issue_type="Task",
            description="Advanced search task issue"
        )
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Test date-based search
        today_search = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND created >= -1d",
            limit=10
        )
        
        self.assert_success_response(today_search, ["issues"])
        issues = self.extract_value(today_search, "issues", default=[])
        assert len(issues) >= 2, "Should find recently created issues"
        
        # Test issue type filtering
        story_search = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND issuetype = Story AND summary ~ 'Advanced search story'",
            limit=5
        )
        
        self.assert_success_response(story_search, ["issues"])
        story_issues = self.extract_value(story_search, "issues", default=[])
        
        story_key = self.extract_issue_key(story_issue)
        found_story_keys = [self.extract_value(issue, "key") for issue in story_issues]
        assert story_key in found_story_keys, "Should find the story issue"


class TestConfluenceSearch(MCPConfluenceTest):
    """Test Confluence search functionality via MCP tools."""

    @pytest.mark.api
    async def test_confluence_basic_search(self, mcp_client, test_config):
        """Test basic Confluence page search functionality."""
        # Create test pages to search for
        page1 = await self.create_test_page(
            mcp_client,
            test_config,
            content_format="markdown",
            content="# Search Test Page One\n\nThis page contains unique searchable content for testing."
        )
        page1_id = self.extract_page_id(page1)
        
        page2 = await self.create_test_page(
            mcp_client,
            test_config,
            content_format="markdown", 
            content="# Search Test Page Two\n\nThis page has different searchable content for verification."
        )
        page2_id = self.extract_page_id(page2)
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Test basic text search
        search_result = await mcp_client.confluence_search(
            query="Search Test Page",
            limit=10
        )
        
        self.assert_success_response(search_result)
        
        # Extract search results
        results = self.extract_value(search_result, "results") or search_result
        if isinstance(results, dict):
            results = [results]
        
        assert len(results) >= 2, f"Should find at least 2 test pages, found: {len(results)}"
        
        # Verify both pages are found
        found_ids = []
        for result in results:
            page_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
            if page_id:
                found_ids.append(str(page_id))
        
        assert page1_id in found_ids, f"Page {page1_id} not found in search results"
        assert page2_id in found_ids, f"Page {page2_id} not found in search results"

    @pytest.mark.api
    async def test_confluence_cql_search(self, mcp_client, test_config):
        """Test Confluence CQL (Confluence Query Language) search."""
        # Create test page with specific attributes
        test_page = await self.create_test_page(
            mcp_client,
            test_config,
            content_format="markdown",
            content="# CQL Test Page\n\nThis page is specifically for CQL testing with **bold** content."
        )
        page_id = self.extract_page_id(test_page)
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Test various CQL patterns
        cql_tests = [
            {
                "query": f"type=page AND space={test_config['confluence_space']}",
                "description": "Space-based page search",
                "should_find": True
            },
            {
                "query": f"title~'CQL Test Page'",
                "description": "Title search with fuzzy matching",
                "should_find": True
            },
            {
                "query": f"text~'CQL testing' AND space={test_config['confluence_space']}",
                "description": "Text content search within space",
                "should_find": True
            },
            {
                "query": f"type=blogpost AND space={test_config['confluence_space']}",
                "description": "Non-matching content type",
                "should_find": False
            }
        ]
        
        for test_case in cql_tests:
            search_result = await mcp_client.confluence_search(
                query=test_case["query"],
                limit=5
            )
            
            self.assert_success_response(search_result)
            
            results = self.extract_value(search_result, "results") or search_result
            if isinstance(results, dict):
                results = [results]
            
            found_ids = []
            for result in results:
                found_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
                if found_id:
                    found_ids.append(str(found_id))
            
            if test_case["should_find"]:
                assert page_id in found_ids, f"CQL test '{test_case['description']}' should find page {page_id}"
            else:
                assert page_id not in found_ids, f"CQL test '{test_case['description']}' should not find page {page_id}"

    @pytest.mark.api
    async def test_confluence_content_search(self, mcp_client, test_config):
        """Test searching within Confluence page content."""
        # Create page with rich content
        rich_content = """# Content Search Test Page

## Section One
This section contains **important information** about the search functionality.

## Section Two  
Here we have `code examples` and *emphasized text* for search testing.

## Code Block
```python
def search_function():
    return "searchable code content"
```

## Lists
- Bullet point with searchable terms
- Another item with **bold searchable text**
- Final item with search validation

## Table Content
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Search | Content | Testing |
| Data | Validation | Results |
"""
        
        content_page = await self.create_test_page(
            mcp_client,
            test_config,
            content_format="markdown",
            content=rich_content
        )
        page_id = self.extract_page_id(content_page)
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Test searching for content within the page
        content_searches = [
            "important information",
            "code examples", 
            "searchable code content",
            "bold searchable text",
            "Search Content Testing"
        ]
        
        for search_term in content_searches:
            search_result = await mcp_client.confluence_search(
                query=f"text~'{search_term}' AND space={test_config['confluence_space']}",
                limit=5
            )
            
            self.assert_success_response(search_result)
            
            results = self.extract_value(search_result, "results") or search_result
            if isinstance(results, dict):
                results = [results]
            
            # Check if our test page is found
            found_ids = []
            for result in results:
                found_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
                if found_id:
                    found_ids.append(str(found_id))
            
            assert page_id in found_ids, f"Content search for '{search_term}' should find page {page_id}"

    @pytest.mark.api
    async def test_confluence_search_pagination(self, mcp_client, test_config):
        """Test Confluence search pagination."""
        # Create multiple test pages
        page_ids = []
        for i in range(5):
            page = await self.create_test_page(
                mcp_client,
                test_config,
                content_format="markdown",
                content=f"# Pagination Test Page {i+1}\n\nContent for pagination testing {i+1}."
            )
            page_ids.append(self.extract_page_id(page))
        
        # Wait for indexing
        await asyncio.sleep(4)
        
        # Search with limited results
        search_result = await mcp_client.confluence_search(
            query=f"title~'Pagination Test Page' AND space={test_config['confluence_space']}",
            limit=3
        )
        
        self.assert_success_response(search_result)
        
        results = self.extract_value(search_result, "results") or search_result
        if isinstance(results, dict):
            results = [results]
        
        assert len(results) <= 3, "Should respect limit parameter"
        
        # Verify we find some of our test pages
        found_ids = []
        for result in results:
            found_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
            if found_id:
                found_ids.append(str(found_id))
        
        found_test_pages = [page_id for page_id in page_ids if page_id in found_ids]
        assert len(found_test_pages) > 0, "Should find at least one test page in search results"


class TestCrossServiceSearch(MCPBaseTest):
    """Test search scenarios across both Jira and Confluence services."""

    @pytest.mark.api
    async def test_coordinated_search_scenario(self, mcp_client, test_config):
        """Test coordinated search across Jira and Confluence."""
        # Create related content in both services
        project_name = "Cross-Service-Search-Test"
        
        # Create Jira issue
        jira_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=f"{project_name} Implementation Task",
            issue_type="Task",
            description=f"Task for {project_name} with cross-service search testing"
        )
        issue_key = self.extract_issue_key(jira_issue)
        self.track_resource("jira_issue", issue_key)
        
        # Create Confluence page
        confluence_page = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=f"{project_name} Documentation",
            content=f"""# {project_name} Documentation

## Overview
This documentation relates to Jira issue {issue_key} for {project_name}.

## Implementation Details
Cross-service search testing between Jira and Confluence.

## Related Issues
- {issue_key}: Implementation task
""",
            content_format="markdown"
        )
        page_id = self.extract_page_id(confluence_page)
        self.track_resource("confluence_page", page_id)
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Search in Jira
        jira_search = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND text ~ '{project_name}'",
            limit=5
        )
        
        self.assert_success_response(jira_search, ["issues"])
        
        # Search in Confluence
        confluence_search = await mcp_client.confluence_search(
            query=f"text~'{project_name}' AND space={test_config['confluence_space']}",
            limit=5
        )
        
        self.assert_success_response(confluence_search)
        
        # Verify both searches find the related content
        jira_issues = self.extract_value(jira_search, "issues", default=[])
        jira_keys = [self.extract_value(issue, "key") for issue in jira_issues]
        
        assert issue_key in jira_keys, f"Jira search should find issue {issue_key}"
        
        confluence_results = self.extract_value(confluence_search, "results") or confluence_search
        if isinstance(confluence_results, dict):
            confluence_results = [confluence_results]
        
        confluence_ids = []
        for result in confluence_results:
            found_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
            if found_id:
                confluence_ids.append(str(found_id))
        
        assert page_id in confluence_ids, f"Confluence search should find page {page_id}"

    @pytest.mark.api
    async def test_search_error_handling(self, mcp_client, test_config):
        """Test error handling in search functionality."""
        # Test invalid JQL in Jira
        try:
            invalid_jql_result = await mcp_client.jira_search(
                jql="INVALID JQL SYNTAX HERE",
                limit=5
            )
            # If no exception, check for error in result
            if invalid_jql_result:
                data = self._extract_json(invalid_jql_result)
                assert "error" in data or "errorMessages" in data, "Should return error for invalid JQL"
        except Exception as e:
            # Exception is acceptable for invalid JQL
            assert "jql" in str(e).lower() or "syntax" in str(e).lower(), f"Error should relate to JQL syntax: {e}"
        
        # Test invalid CQL in Confluence  
        try:
            invalid_cql_result = await mcp_client.confluence_search(
                query="type=INVALID_TYPE AND nonsense query",
                limit=5
            )
            # If no exception, result might be empty (which is acceptable)
            if invalid_cql_result:
                # Empty results are OK for invalid searches
                results = self.extract_value(invalid_cql_result, "results") or invalid_cql_result
                if isinstance(results, dict):
                    results = [results]
                # No specific assertions needed - empty results are fine
        except Exception as e:
            # Exception is acceptable for invalid CQL
            pass
        
        # Test search with empty query
        empty_search = await mcp_client.confluence_search(
            query="",
            limit=5
        )
        
        # Empty query should either return error or empty results
        if empty_search:
            results = self.extract_value(empty_search, "results") or empty_search
            if isinstance(results, dict):
                results = [results]
            # Empty results are acceptable for empty query

    @pytest.mark.api
    async def test_search_performance_limits(self, mcp_client, test_config):
        """Test search performance and limits."""
        # Test large result limits
        large_limit_search = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']}",
            limit=100
        )
        
        self.assert_success_response(large_limit_search, ["issues"])
        
        # Test search response time (basic performance check)
        import time
        
        start_time = time.time()
        
        performance_search = await mcp_client.confluence_search(
            query=f"space={test_config['confluence_space']}",
            limit=20
        )
        
        end_time = time.time()
        search_duration = end_time - start_time
        
        self.assert_success_response(performance_search)
        
        # Basic performance assertion (should complete within reasonable time)
        assert search_duration < 10.0, f"Search took too long: {search_duration:.2f}s"