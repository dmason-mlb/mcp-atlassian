#!/usr/bin/env python3
"""Debug script to test comment ADF support."""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.jira.comments import CommentsMixin
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.preprocessing.jira import JiraPreprocessor
from mcp_atlassian.formatting.router import FormatRouter


def test_comment_adf_conversion():
    """Test markdown to ADF conversion for comments."""
    
    # Test markdown content
    markdown_text = """
# Test Comment

This is a **bold** comment with *italic* text.

- Bullet point 1
- Bullet point 2

Here's some `inline code` and a [link](https://example.com).
"""
    
    # Test with Cloud URL (should use ADF)
    cloud_url = "https://test.atlassian.net"
    print(f"Testing with Cloud URL: {cloud_url}")
    
    # Create preprocessor
    preprocessor = JiraPreprocessor(base_url=cloud_url)
    
    # Convert markdown to Jira format (should return ADF dict)
    result = preprocessor.markdown_to_jira(markdown_text, enable_adf=True)
    
    print("Conversion result type:", type(result))
    print("Conversion result:")
    if isinstance(result, dict):
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result)
    
    print("\n" + "="*60 + "\n")
    
    # Test with Server URL (should use wiki markup)
    server_url = "https://jira.company.com"
    print(f"Testing with Server URL: {server_url}")
    
    # Create preprocessor
    preprocessor = JiraPreprocessor(base_url=server_url)
    
    # Convert markdown to Jira format (should return wiki markup string)
    result = preprocessor.markdown_to_jira(markdown_text, enable_adf=True)
    
    print("Conversion result type:", type(result))
    print("Conversion result:")
    if isinstance(result, dict):
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result)
    
    print("\n" + "="*60 + "\n")
    
    # Test FormatRouter directly
    print("Testing FormatRouter directly:")
    router = FormatRouter()
    
    # Test Cloud
    cloud_result = router.convert_markdown(markdown_text, cloud_url)
    print(f"Cloud deployment result: format={cloud_result['format']}, type={cloud_result['deployment_type']}")
    print(f"Content type: {type(cloud_result['content'])}")
    if isinstance(cloud_result['content'], dict):
        import json
        print("ADF Content:", json.dumps(cloud_result['content'], indent=2))
    
    print("\n" + "-"*40 + "\n")
    
    # Test Server
    server_result = router.convert_markdown(markdown_text, server_url)
    print(f"Server deployment result: format={server_result['format']}, type={server_result['deployment_type']}")
    print(f"Content type: {type(server_result['content'])}")
    print(f"Wiki Content: {server_result['content']}")


if __name__ == "__main__":
    test_comment_adf_conversion()