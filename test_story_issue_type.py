#!/usr/bin/env python3
"""Test Story issue type creation."""

import os
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.jira.mixins.creation import IssueCreationMixin
from mcp_atlassian.jira.config import JiraConfig


def test_story_issue_type():
    """Test creating a Story issue type."""
    
    # Create a mock Jira client
    mock_jira = MagicMock()
    
    # Mock the create_issue API call
    mock_jira.create_issue.return_value = {
        "id": "10001",
        "key": "TEST-123",
        "self": "https://test.atlassian.net/rest/api/2/issue/10001",
        "fields": {
            "summary": "Test Story",
            "issuetype": {
                "self": "https://test.atlassian.net/rest/api/2/issuetype/10001",
                "id": "10001",
                "description": "Created by Jira Software - do not edit or delete. Issue type for a user story.",
                "iconUrl": "https://test.atlassian.net/images/icons/issuetypes/story.svg",
                "name": "Story",
                "subtask": False
            },
            "project": {
                "self": "https://test.atlassian.net/rest/api/2/project/10000",
                "id": "10000",
                "key": "TEST",
                "name": "Test Project"
            },
            "status": {
                "self": "https://test.atlassian.net/rest/api/2/status/10000",
                "description": "",
                "iconUrl": "https://test.atlassian.net/",
                "name": "To Do",
                "id": "10000"
            }
        }
    }
    
    # Create a config
    config = JiraConfig(
        url="https://test.atlassian.net",
        username="test@example.com",
        api_token="test_token",
        auth_type="token"
    )
    
    # Create the mixin instance
    class TestMixin(IssueCreationMixin):
        def __init__(self):
            self.jira = mock_jira
            self.config = config
            self.preprocessor = MagicMock()
            self.preprocessor.markdown_to_jira.return_value = "Test description"
            
        def _get_account_id(self, assignee):
            return "account123"
            
        def _add_assignee_to_fields(self, fields, account_id):
            fields["assignee"] = {"accountId": account_id}
            
        def markdown_to_jira(self, text, return_raw_adf=False):
            return text  # Return as-is for testing
    
    mixin = TestMixin()
    
    print("Testing Story issue type creation...")
    
    # Test different case variations
    test_cases = [
        "Story",
        "story", 
        "STORY",
        "User Story",
        "user story"
    ]
    
    for issue_type in test_cases:
        print(f"\nTesting with issue_type: '{issue_type}'")
        
        try:
            result = mixin.create_issue(
                project_key="TEST",
                summary="Test Story",
                issue_type=issue_type,
                description="This is a test story"
            )
            
            print(f"  ✓ Success! Created issue: {result.key}")
            
            # Check what was passed to the API
            call_args = mock_jira.create_issue.call_args
            if call_args:
                kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1]
                fields = kwargs.get('fields', {})
                issuetype = fields.get('issuetype', {})
                print(f"  API received issuetype: {issuetype}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)
    print("Testing field detection...")
    
    # Test if Story is detected as Epic
    print(f"Is 'Story' an Epic? {mixin._is_epic_issue_type('Story')}")
    print(f"Is 'Epic' an Epic? {mixin._is_epic_issue_type('Epic')}")
    
    # Test field preparation
    fields = {
        "project": {"key": "TEST"},
        "summary": "Test Story",
        "issuetype": {"name": "Story"}
    }
    kwargs = {}
    
    if mixin._is_epic_issue_type("Story"):
        print("Story detected as Epic - this might be the problem!")
        mixin._prepare_epic_fields(fields, "Test Story", kwargs)
    else:
        print("Story not detected as Epic - correct behavior")
        mixin._prepare_parent_fields(fields, kwargs)
    
    print(f"Final fields: {json.dumps(fields, indent=2)}")


if __name__ == "__main__":
    test_story_issue_type()