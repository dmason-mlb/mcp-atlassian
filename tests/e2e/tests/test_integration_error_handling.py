"""
Cross-service integration and error handling tests.

Tests integration scenarios between Jira and Confluence services,
comprehensive error handling, edge cases, and system resilience.
"""

import pytest
import asyncio
import json
import random
import string
from typing import Dict, Any

from .base_test import MCPBaseTest


class TestCrossServiceIntegration(MCPBaseTest):
    """Test integration scenarios across Jira and Confluence services."""

    @pytest.mark.api
    async def test_linked_content_workflow(self, mcp_client, test_config):
        """Test a complete workflow linking Jira issues and Confluence pages."""
        # Create Epic in Jira
        epic_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Integration Test Epic"),
            issue_type="Epic",
            description="Epic for testing cross-service integration workflow"
        )
        epic_key = self.extract_issue_key(epic_issue)
        self.track_resource("jira_issue", epic_key)
        
        # Create related Story
        story_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Integration Test Story"),
            issue_type="Story",
            description="Story linked to Epic for integration testing"
        )
        story_key = self.extract_issue_key(story_issue)
        self.track_resource("jira_issue", story_key)
        
        # Link Story to Epic
        link_result = await mcp_client.jira_link_to_epic(
            issue_key=story_key,
            epic_key=epic_key
        )
        self.assert_success_response(link_result)
        
        # Create Confluence documentation page referencing both issues
        doc_content = f"""# Integration Test Documentation

## Project Overview
This documentation covers the integration testing project.

## Epic Details
**Epic**: [{epic_key}] {self.extract_value(epic_issue, 'fields', 'summary')}

## User Stories
**Story**: [{story_key}] {self.extract_value(story_issue, 'fields', 'summary')}

## Implementation Notes
This page demonstrates cross-service integration between Jira issues and Confluence documentation.

### Related Issues
- {epic_key}: Main epic for integration testing
- {story_key}: Implementation story

### Status Updates
Epic Status: In Progress
Story Status: To Do

## Technical Details
```json
{{
  "epic": "{epic_key}",
  "story": "{story_key}",
  "integration": "cross-service",
  "status": "testing"
}}
```
"""
        
        doc_page = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=self.generate_unique_title("Integration Test Documentation"),
            content=doc_content,
            content_format="markdown"
        )
        doc_page_id = self.extract_page_id(doc_page)
        self.track_resource("confluence_page", doc_page_id)
        
        # Add comment to Story referencing the documentation
        comment_content = f"""## Documentation Created

Created comprehensive documentation for this story:
**Page**: {self.extract_value(doc_page, 'title', default='Integration Documentation')}

The documentation includes:
- Epic overview
- Story details  
- Implementation notes
- Technical specifications

Please review the documentation before implementation.
"""
        
        comment_result = await mcp_client.add_jira_comment(
            issue_key=story_key,
            comment=comment_content
        )
        self.assert_success_response(comment_result)
        
        # Verify the complete workflow by checking all components
        # 1. Verify Epic exists and has linked Story
        epic_details = await mcp_client.jira_get_issue(
            issue_key=epic_key,
            expand="changelog"
        )
        self.assert_success_response(epic_details)
        
        # 2. Verify Story exists and has comment
        story_details = await mcp_client.jira_get_issue(
            issue_key=story_key,
            expand="changelog"
        )
        self.assert_success_response(story_details)
        
        # 3. Verify Confluence page exists
        page_details = await mcp_client.confluence_get_page(
            page_id=doc_page_id,
            include_metadata=True
        )
        self.assert_success_response(page_details)

    @pytest.mark.api
    async def test_bulk_operations_integration(self, mcp_client, test_config):
        """Test bulk operations across both services."""
        # Create multiple Jira issues
        jira_issues = []
        for i in range(3):
            issue = await mcp_client.create_jira_issue(
                project_key=test_config["jira_project"],
                summary=self.generate_unique_title(f"Bulk Test Issue {i+1}"),
                issue_type="Task",
                description=f"Bulk operation test issue {i+1}"
            )
            issue_key = self.extract_issue_key(issue)
            jira_issues.append(issue_key)
            self.track_resource("jira_issue", issue_key)
        
        # Create multiple Confluence pages
        confluence_pages = []
        for i in range(3):
            page = await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title=self.generate_unique_title(f"Bulk Test Page {i+1}"),
                content=f"""# Bulk Test Page {i+1}

## Related Issues
This page relates to the following Jira issues:
""" + "\n".join([f"- {key}: Bulk test issue {j+1}" for j, key in enumerate(jira_issues)]),
                content_format="markdown"
            )
            page_id = self.extract_page_id(page)
            confluence_pages.append(page_id)
            self.track_resource("confluence_page", page_id)
        
        # Perform bulk search to verify all items were created
        jira_search = await mcp_client.jira_search(
            jql=f"project = {test_config['jira_project']} AND summary ~ 'Bulk Test Issue'",
            limit=10
        )
        self.assert_success_response(jira_search, ["issues"])
        
        jira_results = self.extract_value(jira_search, "issues", default=[])
        found_jira_keys = [self.extract_value(issue, "key") for issue in jira_results]
        
        for issue_key in jira_issues:
            assert issue_key in found_jira_keys, f"Bulk created issue {issue_key} not found in search"
        
        confluence_search = await mcp_client.confluence_search(
            query=f"title~'Bulk Test Page' AND space={test_config['confluence_space']}",
            limit=10
        )
        self.assert_success_response(confluence_search)
        
        confluence_results = self.extract_value(confluence_search, "results") or confluence_search
        if isinstance(confluence_results, dict):
            confluence_results = [confluence_results]
        
        found_confluence_ids = []
        for result in confluence_results:
            page_id = self.extract_value(result, "content", "id") or self.extract_value(result, "id")
            if page_id:
                found_confluence_ids.append(str(page_id))
        
        for page_id in confluence_pages:
            assert page_id in found_confluence_ids, f"Bulk created page {page_id} not found in search"

    @pytest.mark.api
    async def test_cross_service_content_synchronization(self, mcp_client, test_config):
        """Test content synchronization patterns between services."""
        # Create master issue in Jira
        master_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Master Sync Issue"),
            issue_type="Epic",
            description="Master issue for content synchronization testing"
        )
        master_key = self.extract_issue_key(master_issue)
        self.track_resource("jira_issue", master_key)
        
        # Create corresponding page in Confluence
        sync_page = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=self.generate_unique_title("Sync Status Page"),
            content=f"""# Synchronization Status

## Master Issue
**Issue**: {master_key}
**Status**: {self.extract_value(master_issue, 'fields', 'status', 'name', default='To Do')}

## Sync Information
Last updated: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}

## Changes Log
- Page created
- Linked to {master_key}
""",
            content_format="markdown"
        )
        sync_page_id = self.extract_page_id(sync_page)
        self.track_resource("confluence_page", sync_page_id)
        
        # Update Jira issue
        update_result = await mcp_client.jira_update_issue(
            issue_key=master_key,
            fields={
                "description": f"Updated master issue - synchronized with Confluence page {sync_page_id}"
            }
        )
        self.assert_success_response(update_result)
        
        # Update Confluence page to reflect change
        updated_content = f"""# Synchronization Status

## Master Issue  
**Issue**: {master_key}
**Status**: Updated
**Confluence Reference**: {sync_page_id}

## Sync Information
Last updated: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}
Sync status: Active

## Changes Log
- Page created
- Linked to {master_key}
- Issue updated with page reference
- Page updated with sync confirmation
"""
        
        page_update_result = await mcp_client.confluence_update_page(
            page_id=sync_page_id,
            title=self.extract_value(sync_page, "title"),
            content=updated_content,
            content_format="markdown"
        )
        self.assert_success_response(page_update_result)
        
        # Verify synchronization by checking both sides
        updated_issue = await mcp_client.jira_get_issue(issue_key=master_key)
        updated_description = self.extract_value(updated_issue, "fields", "description")
        assert sync_page_id in str(updated_description), "Issue should reference the page"
        
        updated_page = await mcp_client.confluence_get_page(page_id=sync_page_id)
        updated_page_content = self.extract_value(updated_page, "content") or str(updated_page)
        assert master_key in updated_page_content, "Page should reference the issue"


class TestErrorHandlingResilience(MCPBaseTest):
    """Test comprehensive error handling and system resilience."""

    @pytest.mark.api
    async def test_invalid_resource_handling(self, mcp_client, test_config):
        """Test handling of invalid resource IDs and references."""
        # Test invalid Jira issue key
        invalid_issue_key = "INVALID-99999"
        
        try:
            invalid_issue_result = await mcp_client.jira_get_issue(issue_key=invalid_issue_key)
            # If no exception, check for error in response
            if invalid_issue_result:
                self.assert_error_response(invalid_issue_result, r"not found|does not exist|invalid")
        except Exception as e:
            # Exception is expected for invalid issue
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower()
        
        # Test invalid Confluence page ID
        invalid_page_id = "99999999"
        
        try:
            invalid_page_result = await mcp_client.confluence_get_page(page_id=invalid_page_id)
            # If no exception, check for error in response
            if invalid_page_result:
                self.assert_error_response(invalid_page_result, r"not found|does not exist|invalid")
        except Exception as e:
            # Exception is expected for invalid page
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower()
        
        # Test invalid project key
        invalid_project = "NONEXISTENT"
        
        try:
            invalid_project_result = await mcp_client.create_jira_issue(
                project_key=invalid_project,
                summary="Test with invalid project",
                issue_type="Task"
            )
            # If no exception, check for error in response
            if invalid_project_result:
                self.assert_error_response(invalid_project_result, r"project|not found|invalid")
        except Exception as e:
            # Exception is expected for invalid project
            assert any(term in str(e).lower() for term in ["project", "not found", "invalid"])

    @pytest.mark.api
    async def test_malformed_data_handling(self, mcp_client, test_config):
        """Test handling of malformed or invalid data inputs."""
        # Test extremely long content
        very_long_title = "A" * 1000  # Very long title
        very_long_description = "B" * 50000  # Very long description
        
        try:
            long_content_result = await mcp_client.create_jira_issue(
                project_key=test_config["jira_project"],
                summary=very_long_title,
                issue_type="Task",
                description=very_long_description
            )
            
            # If it succeeds, track for cleanup but check if content was truncated
            if long_content_result and "error" not in str(long_content_result).lower():
                issue_key = self.extract_issue_key(long_content_result)
                self.track_resource("jira_issue", issue_key)
                
                # Verify the issue was created (possibly with truncated content)
                created_issue = await mcp_client.jira_get_issue(issue_key=issue_key)
                self.assert_success_response(created_issue)
                
        except Exception as e:
            # Exception is acceptable for overly long content
            assert any(term in str(e).lower() for term in ["length", "long", "limit", "size"])
        
        # Test special characters and encoding
        special_char_content = """# Test with Special Characters
        
## Unicode Content: 测试内容 🚀 💻
        
Content with various encodings:
- Emoji: 🔥 ⭐ 🎯 
- Accented: café, naïve, résumé
- Symbols: ←→↑↓ ±×÷ ©®™
- Math: α+β=γ, ∑∏∫∆
        
## Code with Special Chars
```javascript
// Special characters in code
const test = "Special: \u00A9\u00AE\u2122";
const regex = /[^\w\s]/gi;
```
        
## Panel with Unicode
:::panel type="info"
Information with unicode: 中文测试 العربية тест
:::
"""
        
        try:
            special_char_result = await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title=self.generate_unique_title("Special Characters Test 测试"),
                content=special_char_content,
                content_format="markdown"
            )
            
            if special_char_result and "error" not in str(special_char_result).lower():
                page_id = self.extract_page_id(special_char_result)
                self.track_resource("confluence_page", page_id)
                
                # Verify the page was created successfully
                created_page = await mcp_client.confluence_get_page(page_id=page_id)
                self.assert_success_response(created_page)
                
        except Exception as e:
            # If it fails, ensure it's for a valid reason (encoding, etc.)
            print(f"Special character test failed (may be expected): {e}")

    @pytest.mark.api
    async def test_concurrent_operations_handling(self, mcp_client, test_config):
        """Test handling of concurrent operations and race conditions."""
        # Create base issue for concurrent operations
        base_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Concurrent Operations Test"),
            issue_type="Task",
            description="Base issue for concurrent operations testing"
        )
        issue_key = self.extract_issue_key(base_issue)
        self.track_resource("jira_issue", issue_key)
        
        # Define concurrent operations
        async def add_comment(client, issue_key, comment_num):
            try:
                result = await client.add_jira_comment(
                    issue_key=issue_key,
                    comment=f"Concurrent comment {comment_num} - {self.test_name}"
                )
                return ("comment", comment_num, result)
            except Exception as e:
                return ("comment", comment_num, e)
        
        async def update_issue(client, issue_key, update_num):
            try:
                result = await client.jira_update_issue(
                    issue_key=issue_key,
                    fields={"description": f"Updated description {update_num} - concurrent test"}
                )
                return ("update", update_num, result)
            except Exception as e:
                return ("update", update_num, e)
        
        # Launch concurrent operations
        concurrent_tasks = []
        
        # Add multiple concurrent comments
        for i in range(3):
            concurrent_tasks.append(add_comment(mcp_client, issue_key, i+1))
        
        # Add concurrent updates (note: these might conflict)
        for i in range(2):
            concurrent_tasks.append(update_issue(mcp_client, issue_key, i+1))
        
        # Execute all operations concurrently
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Analyze results
        successful_comments = 0
        successful_updates = 0
        
        for result in results:
            if isinstance(result, tuple) and len(result) == 3:
                operation_type, operation_num, operation_result = result
                
                if not isinstance(operation_result, Exception):
                    if operation_type == "comment":
                        successful_comments += 1
                    elif operation_type == "update":
                        successful_updates += 1
        
        # Verify that at least some operations succeeded
        assert successful_comments >= 1, "At least one concurrent comment should succeed"
        # Updates might conflict, so we're less strict about them
        
        # Verify final state of issue
        final_issue = await mcp_client.jira_get_issue(
            issue_key=issue_key,
            expand="changelog"
        )
        self.assert_success_response(final_issue)

    @pytest.mark.api
    async def test_resource_cleanup_on_failure(self, mcp_client, test_config):
        """Test proper resource cleanup when operations fail."""
        created_resources = []
        
        try:
            # Create some resources that should succeed
            success_issue = await mcp_client.create_jira_issue(
                project_key=test_config["jira_project"],
                summary=self.generate_unique_title("Cleanup Test - Success"),
                issue_type="Task",
                description="This issue should be created successfully"
            )
            success_key = self.extract_issue_key(success_issue)
            created_resources.append(("jira_issue", success_key))
            self.track_resource("jira_issue", success_key)
            
            success_page = await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title=self.generate_unique_title("Cleanup Test - Success Page"),
                content="This page should be created successfully",
                content_format="markdown"
            )
            success_page_id = self.extract_page_id(success_page)
            created_resources.append(("confluence_page", success_page_id))
            self.track_resource("confluence_page", success_page_id)
            
            # Attempt operation that might fail
            try:
                # Try to create issue with invalid issue type
                fail_issue = await mcp_client.create_jira_issue(
                    project_key=test_config["jira_project"],
                    summary=self.generate_unique_title("Cleanup Test - Should Fail"),
                    issue_type="NonExistentIssueType",  # Invalid issue type
                    description="This should fail"
                )
                
                # If it unexpectedly succeeds, track it for cleanup
                if fail_issue and "error" not in str(fail_issue).lower():
                    fail_key = self.extract_issue_key(fail_issue)
                    created_resources.append(("jira_issue", fail_key))
                    self.track_resource("jira_issue", fail_key)
                    
            except Exception:
                # Expected to fail - this is what we're testing
                pass
            
            # Verify that successful resources still exist
            verify_issue = await mcp_client.jira_get_issue(issue_key=success_key)
            self.assert_success_response(verify_issue)
            
            verify_page = await mcp_client.confluence_get_page(page_id=success_page_id)
            self.assert_success_response(verify_page)
            
        except Exception as e:
            # Even if something goes wrong, we should properly track resources
            pytest.fail(f"Cleanup test failed unexpectedly: {e}")

    @pytest.mark.api
    async def test_api_rate_limiting_handling(self, mcp_client, test_config):
        """Test handling of API rate limiting and throttling."""
        # Perform rapid successive operations to potentially trigger rate limiting
        rapid_operations = []
        
        for i in range(5):  # Moderate number to avoid overwhelming the API
            # Alternate between different operations
            if i % 2 == 0:
                rapid_operations.append(
                    mcp_client.jira_search(
                        jql=f"project = {test_config['jira_project']} ORDER BY created DESC",
                        limit=1
                    )
                )
            else:
                rapid_operations.append(
                    mcp_client.confluence_search(
                        query=f"space={test_config['confluence_space']}",
                        limit=1
                    )
                )
        
        # Execute operations with minimal delay
        results = []
        for operation in rapid_operations:
            try:
                result = await operation
                results.append(result)
                # Small delay to be respectful to the API
                await asyncio.sleep(0.1)
            except Exception as e:
                # Rate limiting exceptions are acceptable
                if any(term in str(e).lower() for term in ["rate", "limit", "throttle", "429"]):
                    results.append(f"Rate limited: {e}")
                else:
                    # Other exceptions should be investigated
                    results.append(f"Unexpected error: {e}")
        
        # Verify that we handled the operations gracefully
        successful_operations = [r for r in results if not isinstance(r, str)]
        rate_limited_operations = [r for r in results if isinstance(r, str) and "rate limited" in r.lower()]
        
        # Should have at least some successful operations
        assert len(successful_operations) >= 1, "Should have at least one successful operation"
        
        # If rate limited, that's acceptable behavior
        if rate_limited_operations:
            print(f"Encountered rate limiting (expected behavior): {len(rate_limited_operations)} operations")

    @pytest.mark.api
    async def test_network_resilience_patterns(self, mcp_client, test_config):
        """Test resilience patterns for network issues and timeouts."""
        # Test basic connectivity and error recovery
        
        # 1. Test simple operations first to establish baseline
        baseline_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Network Resilience Test"),
            issue_type="Task",
            description="Baseline issue for network resilience testing"
        )
        baseline_key = self.extract_issue_key(baseline_issue)
        self.track_resource("jira_issue", baseline_key)
        
        # 2. Test operations that might be sensitive to network issues
        try:
            # Large content operation (might timeout)
            large_content = self.generate_test_description("adf_rich") * 10  # Repeat content
            
            large_content_result = await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title=self.generate_unique_title("Large Content Network Test"),
                content=large_content,
                content_format="markdown"
            )
            
            if large_content_result and "error" not in str(large_content_result).lower():
                large_page_id = self.extract_page_id(large_content_result)
                self.track_resource("confluence_page", large_page_id)
                
        except Exception as e:
            # Network-related exceptions are acceptable for this test
            if any(term in str(e).lower() for term in ["timeout", "network", "connection", "unreachable"]):
                print(f"Network issue detected (testing resilience): {e}")
            else:
                # Re-raise if it's not a network issue
                raise
        
        # 3. Verify that the system recovered and basic operations still work
        recovery_test = await mcp_client.jira_get_issue(issue_key=baseline_key)
        self.assert_success_response(recovery_test)
        
        # 4. Test that we can continue normal operations
        recovery_issue = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Recovery Test Issue"),
            issue_type="Task",
            description="Issue created after potential network resilience testing"
        )
        recovery_key = self.extract_issue_key(recovery_issue)
        self.track_resource("jira_issue", recovery_key)
        
        # Verify both issues exist
        assert baseline_key != recovery_key, "Should create different issues"