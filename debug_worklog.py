#!/usr/bin/env python3
"""Debug script to test worklog functionality."""

import json
import os
from mcp_atlassian.jira.client import JiraClient

# Get config from environment
jira_url = os.environ.get("JIRA_BASE_URL", os.environ.get("ATLASSIAN_URL"))
username = os.environ.get("JIRA_EMAIL", os.environ.get("JIRA_USERNAME"))
api_token = os.environ.get("ATLASSIAN_TOKEN", os.environ.get("JIRA_API_TOKEN"))

if not all([jira_url, username, api_token]):
    print("Missing required environment variables")
    exit(1)

# Create client
client = JiraClient(
    base_url=jira_url,
    username=username,
    api_token=api_token,
)

# Test issue key - you may need to change this
test_issue_key = "TEST-1"

print(f"Testing worklog for issue: {test_issue_key}")
print("=" * 50)

# Test get_worklog (returns raw dict)
print("\n1. Testing get_worklog (raw dict):")
try:
    raw_worklog = client.get_worklog(test_issue_key)
    print(f"Type: {type(raw_worklog)}")
    print(f"Keys: {raw_worklog.keys() if isinstance(raw_worklog, dict) else 'N/A'}")
    if "worklogs" in raw_worklog:
        print(f"Number of worklogs: {len(raw_worklog['worklogs'])}")
except Exception as e:
    print(f"Error: {e}")

# Test get_worklog_models (returns models)
print("\n2. Testing get_worklog_models (JiraWorklog models):")
try:
    worklog_models = client.get_worklog_models(test_issue_key)
    print(f"Type: {type(worklog_models)}")
    print(f"Number of models: {len(worklog_models)}")
    if worklog_models:
        first = worklog_models[0]
        print(f"First worklog type: {type(first)}")
        print(f"Has to_simplified_dict: {hasattr(first, 'to_simplified_dict')}")
        if hasattr(first, 'to_simplified_dict'):
            simplified = first.to_simplified_dict()
            print(f"Simplified dict keys: {simplified.keys()}")
except Exception as e:
    print(f"Error: {e}")

# Test get_worklogs (returns simplified dicts)
print("\n3. Testing get_worklogs (simplified dicts):")
try:
    worklogs = client.get_worklogs(test_issue_key)
    print(f"Type: {type(worklogs)}")
    print(f"Number of worklogs: {len(worklogs)}")
    if worklogs:
        first = worklogs[0]
        print(f"First worklog type: {type(first)}")
        print(f"First worklog keys: {first.keys()}")
        print(f"Has to_simplified_dict: {hasattr(first, 'to_simplified_dict')}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Diagnosis:")
print("- get_worklog returns raw API dict")
print("- get_worklog_models returns JiraWorklog model instances")
print("- get_worklogs returns list of simplified dicts")
print("\nThe error likely occurs when something expects a model but gets a dict.")