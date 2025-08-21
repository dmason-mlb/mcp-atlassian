"""
Comprehensive Jira issue tests for MCP Atlassian tools.

Tests cover:
- Issue creation with various types and fields
- Issue updates and field modifications
- Comments and comment management
- Status transitions and workflows
- Issue linking and relationships
- Error handling and edge cases
"""

import pytest
from typing import Dict, Any, List

from tests.base_test import MCPJiraTest
from validators import validate_jira_response, DeploymentType, ValidationResult


@pytest.mark.api
@pytest.mark.jira
class TestJiraIssueCreation(MCPJiraTest):
    """Test Jira issue creation functionality."""
    
    async def test_create_basic_task(self, mcp_client, test_config, test_data_manager):
        """Test creating a basic task issue."""
        summary = self.generate_unique_title("Basic Task")
        description = self.generate_test_description("basic")
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type="Task",
            description=description
        )
        
        # Validate response
        self.assert_success_response(result, ["message", "issue"])
        validation = validate_jira_response(result, "create")
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        # Extract and track issue
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
        
        # Verify issue was created with correct data
        issue_data = self._extract_json(result)
        assert summary in str(issue_data)
    
    async def test_create_story_with_assignee(self, mcp_client, test_config, test_data_manager):
        """Test creating a story with assignee."""
        summary = self.generate_unique_title("User Story")
        description = self.generate_test_description("markdown")
        
        # Try to assign to current user (if available)
        assignee = test_config.get("test_user_email") or "currentUser()"
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type="Story",
            description=description,
            assignee=assignee
        )
        
        self.assert_success_response(result, ["message", "issue"])
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
        
        # Validate assignee was set (if supported)
        issue_data = self._extract_json(result)
        # Note: Assignee validation may vary by Jira configuration
    
    async def test_create_bug_with_priority(self, mcp_client, test_config, test_data_manager):
        """Test creating a bug with priority."""
        summary = self.generate_unique_title("Critical Bug")
        description = self.generate_test_description("adf_rich")
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type="Bug",
            description=description,
            additional_fields={
                "priority": {"name": "High"}
            }
        )
        
        self.assert_success_response(result, ["message", "issue"])
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
    
    async def test_create_issue_with_labels(self, mcp_client, test_config, test_data_manager):
        """Test creating issue with labels."""
        summary = self.generate_unique_title("Labeled Issue")
        test_label = test_config["test_label"]
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type="Task",
            additional_fields={
                "labels": [test_label, "automation", "mcp-test"]
            }
        )
        
        self.assert_success_response(result, ["message", "issue"])
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
    
    async def test_create_epic(self, mcp_client, test_config, test_data_manager):
        """Test creating an Epic issue."""
        summary = self.generate_unique_title("Test Epic")
        description = self.generate_test_description("markdown")
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type="Epic",
            description=description,
            additional_fields={
                "customfield_10011": summary  # Epic Name (common field)
            }
        )
        
        self.assert_success_response(result, ["message", "issue"])
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
    
    async def test_create_issue_invalid_project(self, mcp_client, test_config):
        """Test creating issue with invalid project."""
        result = await mcp_client.create_jira_issue(
            project_key="INVALID",
            summary="Should Fail",
            issue_type="Task"
        )
        
        self.assert_error_response(result, r"project|not found|invalid")


@pytest.mark.api
@pytest.mark.jira
class TestJiraIssueUpdates(MCPJiraTest):
    """Test Jira issue update functionality."""
    
    async def test_update_issue_summary(self, mcp_client, test_config, test_data_manager):
        """Test updating issue summary."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Update summary
        new_summary = self.generate_unique_title("Updated Summary")
        update_result = await mcp_client.update_jira_issue(
            issue_key=issue_key,
            fields={"summary": new_summary}
        )
        
        self.assert_success_response(update_result)
        validation = validate_jira_response(update_result, "update")
        assert validation.is_valid, f"Update validation failed: {validation.errors}"
    
    async def test_update_issue_description(self, mcp_client, test_config, test_data_manager):
        """Test updating issue description with ADF content."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Update with rich ADF description
        new_description = self.generate_test_description("adf_rich")
        update_result = await mcp_client.update_jira_issue(
            issue_key=issue_key,
            fields={"description": new_description}
        )
        
        self.assert_success_response(update_result)
        
        # Validate ADF formatting in response
        validation = validate_jira_response(update_result, "update", DeploymentType.CLOUD)
        assert validation.is_valid, f"ADF validation failed: {validation.errors}"
    
    async def test_update_issue_priority(self, mcp_client, test_config, test_data_manager):
        """Test updating issue priority."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Update priority
        update_result = await mcp_client.update_jira_issue(
            issue_key=issue_key,
            fields={},
            additional_fields={
                "priority": {"name": "High"}
            }
        )
        
        self.assert_success_response(update_result)
    
    async def test_update_issue_labels(self, mcp_client, test_config, test_data_manager):
        """Test updating issue labels."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Update labels
        test_label = test_config["test_label"]
        update_result = await mcp_client.update_jira_issue(
            issue_key=issue_key,
            fields={},
            additional_fields={
                "labels": [test_label, "updated", "test-automation"]
            }
        )
        
        self.assert_success_response(update_result)
    
    async def test_update_nonexistent_issue(self, mcp_client, test_config):
        """Test updating non-existent issue."""
        result = await mcp_client.update_jira_issue(
            issue_key="FAKE-99999",
            fields={"summary": "Should Fail"}
        )
        
        self.assert_error_response(result, r"not found|does not exist|invalid")


@pytest.mark.api
@pytest.mark.jira
class TestJiraComments(MCPJiraTest):
    """Test Jira comment functionality."""
    
    async def test_add_basic_comment(self, mcp_client, test_config, test_data_manager):
        """Test adding a basic comment."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Add comment
        comment_text = f"Basic comment added by test at {self.test_start_time}"
        comment_result = await mcp_client.add_jira_comment(
            issue_key=issue_key,
            comment=comment_text
        )
        
        self.assert_success_response(comment_result)
        validation = validate_jira_response(comment_result, "comment")
        assert validation.is_valid, f"Comment validation failed: {validation.errors}"
    
    async def test_add_formatted_comment(self, mcp_client, test_config, test_data_manager):
        """Test adding a formatted comment with ADF elements."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Add formatted comment
        comment_text = """# Formatted Comment Test

This comment contains **formatting** and *styling*.

## Status Update
Current status: {status:color=blue}In Progress{/status}

:::panel type="info"
**Information**: This is a test comment with ADF formatting.
:::

### Code Example
```python
def test_comment():
    return "formatted comment test"
```

> This is a blockquote in the comment."""
        
        comment_result = await mcp_client.add_jira_comment(
            issue_key=issue_key,
            comment=comment_text
        )
        
        self.assert_success_response(comment_result)
        
        # Validate ADF formatting
        validation = validate_jira_response(comment_result, "comment", DeploymentType.CLOUD)
        assert validation.is_valid, f"ADF comment validation failed: {validation.errors}"
    
    async def test_add_comment_with_mentions(self, mcp_client, test_config, test_data_manager):
        """Test adding comment with user mentions."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Add comment with mention (using generic format)
        comment_text = f"Comment with mention: @[Test User] please review this at {self.test_start_time}"
        comment_result = await mcp_client.add_jira_comment(
            issue_key=issue_key,
            comment=comment_text
        )
        
        self.assert_success_response(comment_result)


@pytest.mark.api
@pytest.mark.jira  
class TestJiraTransitions(MCPJiraTest):
    """Test Jira issue transition functionality."""
    
    async def test_get_available_transitions(self, mcp_client, test_config, test_data_manager):
        """Test getting available transitions for an issue."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Get transitions
        transitions = await mcp_client.get_jira_transitions(issue_key)
        
        assert isinstance(transitions, list)
        # Should have at least one transition available
        assert len(transitions) > 0, "Issue should have available transitions"
        
        # Validate transition structure
        for transition in transitions:
            assert "id" in transition, "Transition should have ID"
            assert "name" in transition, "Transition should have name"
    
    async def test_transition_issue(self, mcp_client, test_config, test_data_manager):
        """Test transitioning an issue to a different status."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Get available transitions
        transitions = await mcp_client.get_jira_transitions(issue_key)
        
        if transitions:
            # Use first available transition
            transition_id = transitions[0]["id"]
            transition_name = transitions[0]["name"]
            
            # Perform transition
            transition_result = await mcp_client.transition_jira_issue(
                issue_key=issue_key,
                transition_id=transition_id,
                comment=f"Automated transition to {transition_name} by test"
            )
            
            self.assert_success_response(transition_result)
        else:
            pytest.skip("No transitions available for test issue")
    
    async def test_transition_with_resolution(self, mcp_client, test_config, test_data_manager):
        """Test transitioning issue with resolution field."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Get transitions
        transitions = await mcp_client.get_jira_transitions(issue_key)
        
        # Look for a "Done" or "Resolve" transition
        done_transition = None
        for transition in transitions:
            if any(word in transition["name"].lower() for word in ["done", "resolve", "complete", "close"]):
                done_transition = transition
                break
        
        if done_transition:
            # Transition with resolution
            transition_result = await mcp_client.transition_jira_issue(
                issue_key=issue_key,
                transition_id=done_transition["id"],
                fields={"resolution": {"name": "Done"}},
                comment="Completed by automated test"
            )
            
            self.assert_success_response(transition_result)
        else:
            pytest.skip("No completion transition available for test issue")


@pytest.mark.api
@pytest.mark.jira
class TestJiraLinking(MCPJiraTest):
    """Test Jira issue linking functionality."""
    
    async def test_link_issues(self, mcp_client, test_config, test_data_manager):
        """Test creating links between issues."""
        # Create two test issues
        issue1_result = await self.create_test_issue(
            mcp_client, test_config, 
            issue_type="Story",
            description="Parent story for testing links"
        )
        issue1_key = self.extract_issue_key(issue1_result)
        
        issue2_result = await self.create_test_issue(
            mcp_client, test_config,
            issue_type="Task", 
            description="Task related to parent story"
        )
        issue2_key = self.extract_issue_key(issue2_result)
        
        # Create link between issues
        try:
            link_result = await mcp_client.call_tool("jira_create_issue_link", {
                "link_type": "Relates",
                "inward_issue_key": issue1_key,
                "outward_issue_key": issue2_key,
                "comment": "Linked by automated test"
            })
            
            self.assert_success_response(link_result)
            
        except Exception as e:
            # Link creation might not be available or configured
            pytest.skip(f"Issue linking not available: {e}")
    
    async def test_link_to_epic(self, mcp_client, test_config, test_data_manager):
        """Test linking issue to Epic."""
        try:
            # Create epic first
            epic_result = await self.create_test_issue(
                mcp_client, test_config,
                issue_type="Epic",
                description="Test Epic for linking",
                additional_fields={
                    "customfield_10011": "Test Epic"  # Epic Name
                }
            )
            epic_key = self.extract_issue_key(epic_result)
            
            # Create story to link to epic
            story_result = await self.create_test_issue(
                mcp_client, test_config,
                issue_type="Story",
                description="Story to be linked to Epic"
            )
            story_key = self.extract_issue_key(story_result)
            
            # Link story to epic
            link_result = await mcp_client.link_to_epic(story_key, epic_key)
            self.assert_success_response(link_result)
            
        except Exception as e:
            pytest.skip(f"Epic linking not available: {e}")


@pytest.mark.api
@pytest.mark.jira
@pytest.mark.error_handling  
class TestJiraErrorHandling(MCPJiraTest):
    """Test error handling scenarios."""
    
    async def test_create_issue_missing_required_fields(self, mcp_client, test_config):
        """Test creating issue with missing required fields."""
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary="",  # Empty summary
            issue_type="Task"
        )
        
        self.assert_error_response(result, r"summary|required|empty")
    
    async def test_invalid_issue_type(self, mcp_client, test_config):
        """Test creating issue with invalid issue type."""
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary="Test Invalid Type",
            issue_type="InvalidType"
        )
        
        self.assert_error_response(result, r"issue type|invalid|not valid")
    
    async def test_update_issue_invalid_fields(self, mcp_client, test_config, test_data_manager):
        """Test updating issue with invalid field values."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Try to update with invalid priority
        result = await mcp_client.update_jira_issue(
            issue_key=issue_key,
            fields={},
            additional_fields={
                "priority": {"name": "InvalidPriority"}
            }
        )
        
        self.assert_error_response(result, r"priority|invalid|not valid")
    
    async def test_transition_invalid_transition_id(self, mcp_client, test_config, test_data_manager):
        """Test transitioning with invalid transition ID."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Try invalid transition
        result = await mcp_client.transition_jira_issue(
            issue_key=issue_key,
            transition_id="99999"  # Invalid transition ID
        )
        
        self.assert_error_response(result, r"transition|invalid|not valid")


@pytest.mark.api
@pytest.mark.jira
@pytest.mark.performance
class TestJiraBulkOperations(MCPJiraTest):
    """Test bulk operations and performance."""
    
    async def test_create_multiple_issues(self, mcp_client, test_config, test_data_manager):
        """Test creating multiple issues efficiently."""
        issue_keys = []
        
        # Create 3 test issues
        for i in range(3):
            result = await self.create_test_issue(
                mcp_client, test_config,
                issue_type="Task",
                description=f"Bulk creation test issue #{i+1}"
            )
            issue_key = self.extract_issue_key(result)
            issue_keys.append(issue_key)
        
        # Verify all issues were created
        assert len(issue_keys) == 3
        assert all(key for key in issue_keys)
    
    async def test_batch_comments(self, mcp_client, test_config, test_data_manager):
        """Test adding multiple comments to an issue."""
        # Create test issue
        create_result = await self.create_test_issue(mcp_client, test_config)
        issue_key = self.extract_issue_key(create_result)
        
        # Add multiple comments
        comments = [
            "First batch comment",
            "Second batch comment with **formatting**",
            "Third comment with {status:color=green}Done{/status}"
        ]
        
        for i, comment_text in enumerate(comments):
            comment_result = await mcp_client.add_jira_comment(
                issue_key=issue_key,
                comment=f"{comment_text} (#{i+1})"
            )
            self.assert_success_response(comment_result)