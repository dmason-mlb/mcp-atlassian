#!/usr/bin/env python3
"""
Test to validate Bug #1 analysis: ADF returns dict, but code expects string.
"""

from mcp_atlassian.formatting.router import FormatRouter
from mcp_atlassian.preprocessing.jira import JiraPreprocessor


def test_adf_returns_dict():
    """Test to confirm FormatRouter returns dict for Cloud deployments."""

    router = FormatRouter()
    cloud_url = "https://company.atlassian.net"
    server_url = "https://company.example.com/jira"

    print("=== Testing FormatRouter Return Types ===")

    # Test Cloud deployment (should return dict)
    result_cloud = router.convert_markdown("**bold text**", cloud_url)
    print(f"Cloud URL: {cloud_url}")
    print(f"Result format: {result_cloud['format']}")
    print(f"Content type: {type(result_cloud['content'])}")
    print(f"Is content a dict? {isinstance(result_cloud['content'], dict)}")
    print()

    # Test Server deployment (should return string)
    result_server = router.convert_markdown("**bold text**", server_url)
    print(f"Server URL: {server_url}")
    print(f"Result format: {result_server['format']}")
    print(f"Content type: {type(result_server['content'])}")
    print(f"Is content a string? {isinstance(result_server['content'], str)}")
    print()

    # Test JiraPreprocessor (the method that callers actually use)
    preprocessor = JiraPreprocessor(base_url=cloud_url)
    jira_result = preprocessor.markdown_to_jira("**bold text**")
    print(f"JiraPreprocessor result type: {type(jira_result)}")
    print(f"Is JiraPreprocessor result a dict? {isinstance(jira_result, dict)}")
    print()

    return result_cloud, result_server, jira_result


if __name__ == "__main__":
    test_adf_returns_dict()
