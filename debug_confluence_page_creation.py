#!/usr/bin/env python3
"""Debug script to test Confluence page creation."""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence.pages import PagesMixin
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor
from mcp_atlassian.formatting.router import FormatRouter


def test_confluence_page_creation():
    """Test Confluence page creation with ADF/storage format."""
    
    # Test markdown content
    markdown_content = """# Test Page

This is a **test page** with *italic* text.

## Features

- Bullet point 1
- Bullet point 2

Here's some `inline code` and a [link](https://example.com).
"""
    
    # Test with Cloud URL (should use ADF)
    cloud_url = "https://test.atlassian.net/wiki"
    print(f"Testing with Cloud URL: {cloud_url}")
    
    # Create preprocessor
    preprocessor = ConfluencePreprocessor(base_url=cloud_url)
    
    # Convert markdown to Confluence format (should return ADF dict)
    result = preprocessor.markdown_to_confluence(markdown_content, enable_adf=True)
    
    print("Conversion result type:", type(result))
    print("Conversion result:")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
        print("\nUsing representation: atlas_doc_format")
    else:
        print(result)
        print("\nUsing representation: storage")
    
    print("\n" + "="*60 + "\n")
    
    # Test with Server URL (should use storage format)
    server_url = "https://confluence.company.com"
    print(f"Testing with Server URL: {server_url}")
    
    # Create preprocessor
    preprocessor = ConfluencePreprocessor(base_url=server_url)
    
    # Convert markdown to Confluence format (should return storage format string)
    result = preprocessor.markdown_to_confluence(markdown_content, enable_adf=True)
    
    print("Conversion result type:", type(result))
    print("Conversion result:")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
        print("\nUsing representation: atlas_doc_format")
    else:
        print(result)
        print("\nUsing representation: storage")
    
    print("\n" + "="*60 + "\n")
    
    # Test FormatRouter directly
    print("Testing FormatRouter directly:")
    router = FormatRouter()
    
    # Test Cloud
    cloud_result = router.convert_markdown(markdown_content, cloud_url)
    print(f"Cloud deployment result: format={cloud_result['format']}, type={cloud_result['deployment_type']}")
    print(f"Content type: {type(cloud_result['content'])}")
    if isinstance(cloud_result['content'], dict):
        print("ADF Content:", json.dumps(cloud_result['content'], indent=2))
    
    print("\n" + "-"*40 + "\n")
    
    # Test Server
    server_result = router.convert_markdown(markdown_content, server_url)
    print(f"Server deployment result: format={server_result['format']}, type={server_result['deployment_type']}")
    print(f"Content type: {type(server_result['content'])}")
    print(f"Storage Content: {server_result['content'][:200]}...")


if __name__ == "__main__":
    test_confluence_page_creation()