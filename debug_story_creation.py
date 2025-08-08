#!/usr/bin/env python3
"""Debug script for Story creation with additional_fields."""

import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.jira import JiraFetcher

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

def test_story_creation_with_additional_fields():
    """Test Story creation with additional_fields."""
    
    # Initialize Jira Fetcher
    print("Initializing JiraFetcher...")
    jira = JiraFetcher()
    
    # Test 1: Simple Story creation (should work)
    print("\n=== Test 1: Simple Story creation ===")
    try:
        issue = jira.create_issue(
            project_key="FTEST",
            summary="Test Story - Simple",
            issue_type="Story",
            description="This is a simple story without additional fields",
        )
        print(f"✅ Simple Story created: {issue.key}")
    except Exception as e:
        print(f"❌ Simple Story creation failed: {e}")
    
    # Test 2: Story with priority in additional_fields
    print("\n=== Test 2: Story with priority in additional_fields ===")
    try:
        # Try to get the field ID for priority
        priority_field_id = jira.get_field_id("priority")
        print(f"Priority field ID: {priority_field_id}")
        
        issue = jira.create_issue(
            project_key="FTEST",
            summary="Test Story - With Priority",
            issue_type="Story",
            description="This story has priority in additional_fields",
            priority="High"
        )
        print(f"✅ Story with priority created: {issue.key}")
    except Exception as e:
        print(f"❌ Story with priority failed: {e}")
        # Try without priority to confirm that's the issue
        try:
            print("Trying same story without priority...")
            issue2 = jira.create_issue(
                project_key="FTEST",
                summary="Test Story - Without Priority",
                issue_type="Story",
                description="This story has no priority field"
            )
            print(f"✅ Story without priority created: {issue2.key}")
        except Exception as e2:
            print(f"❌ Even without priority failed: {e2}")
    
    # Test 3: Story with labels
    print("\n=== Test 3: Story with labels ===")
    try:
        issue = jira.create_issue(
            project_key="FTEST",
            summary="Test Story - With Labels",
            issue_type="Story", 
            description="This story has labels",
            labels=["test-label", "debug"]
        )
        print(f"✅ Story with labels created: {issue.key}")
    except Exception as e:
        print(f"❌ Story with labels failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Story with fixVersions
    print("\n=== Test 4: Story with fixVersions ===")
    try:
        issue = jira.create_issue(
            project_key="FTEST",
            summary="Test Story - With Fix Version",
            issue_type="Story",
            description="This story has a fix version",
            fixVersions=[{"name": "1.0"}]
        )
        print(f"✅ Story with fixVersions created: {issue.key}")
    except Exception as e:
        print(f"❌ Story with fixVersions failed: {e}")
    
    # Test 5: Story with reporter
    print("\n=== Test 5: Story with reporter ===")
    try:
        issue = jira.create_issue(
            project_key="FTEST",
            summary="Test Story - With Reporter",
            issue_type="Story",
            description="This story has a reporter",
            reporter="douglas.mason@mlb.com"
        )
        print(f"✅ Story with reporter created: {issue.key}")
    except Exception as e:
        print(f"❌ Story with reporter failed: {e}")
    
    # Test 6: Listing available fields
    print("\n=== Test 6: Listing available fields ===")
    try:
        fields = jira.get_fields()
        print(f"Found {len(fields)} fields")
        
        # Look for priority field specifically
        priority_fields = [f for f in fields if 'priority' in f.get('name', '').lower()]
        print(f"\nPriority-related fields:")
        for field in priority_fields:
            print(f"  - {field.get('name')} (ID: {field.get('id')})")
        
        # Look for standard fields
        standard_fields = ['priority', 'labels', 'fixVersions', 'reporter', 'assignee', 'duedate']
        print(f"\nStandard fields:")
        for field_name in standard_fields:
            field_id = jira.get_field_id(field_name)
            if field_id:
                print(f"  - {field_name}: {field_id}")
            else:
                print(f"  - {field_name}: NOT FOUND")
                
    except Exception as e:
        print(f"❌ Failed to list fields: {e}")

if __name__ == "__main__":
    test_story_creation_with_additional_fields()