#!/usr/bin/env python3
"""Test the complete Confluence page creation flow."""

import os
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence.pages import PagesMixin
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.preprocessing.confluence import ConfluencePreprocessor


def test_page_creation_flow():
    """Test the complete page creation flow with mocked API calls."""
    
    # Create a mock Confluence client
    mock_confluence = MagicMock()
    mock_confluence.url = "https://test.atlassian.net/wiki"
    mock_confluence._session = MagicMock()
    
    # Create config
    config = ConfluenceConfig(
        url="https://test.atlassian.net/wiki",
        username="test@example.com",
        api_token="test_token",
        auth_type="token"
    )
    
    # Create PagesMixin instance
    pages_mixin = PagesMixin(config=config)
    pages_mixin.confluence = mock_confluence
    pages_mixin.preprocessor = ConfluencePreprocessor(base_url=config.url)
    
    # Mock the create_page API call
    mock_confluence.create_page.return_value = {
        "id": "123456",
        "type": "page",
        "title": "Test Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "body": {
            "storage": {
                "value": "<p>Test content</p>",
                "representation": "storage"
            }
        }
    }
    
    # Mock the get_page_by_id call for fetching created page
    mock_confluence.get_page_by_id.return_value = {
        "id": "123456",
        "type": "page",
        "title": "Test Page",
        "space": {"key": "TEST"},
        "version": {"number": 1},
        "body": {
            "storage": {
                "value": "<p>Test content</p>",
                "representation": "storage"
            }
        }
    }
    
    # Test markdown content
    markdown_content = """# Test Page

This is a **test page** with *italic* text.

## Features

- Bullet point 1
- Bullet point 2

Here's some `inline code` and a [link](https://example.com).
"""
    
    print("Testing page creation flow...")
    print(f"Config URL: {config.url}")
    print(f"Is Cloud: {config.is_cloud}")
    
    try:
        # Call create_page
        result = pages_mixin.create_page(
            space_key="TEST",
            title="Test Page",
            body=markdown_content,
            is_markdown=True
        )
        
        print("\nPage creation successful!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        # Check what was passed to the API
        print("\n" + "="*60)
        print("API call details:")
        print(f"create_page was called: {mock_confluence.create_page.called}")
        
        if mock_confluence.create_page.called:
            call_args = mock_confluence.create_page.call_args
            print(f"Call args: {call_args}")
            
            # Extract the body argument
            if call_args:
                kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1]
                body = kwargs.get('body')
                representation = kwargs.get('representation')
                
                print(f"\nBody type: {type(body)}")
                print(f"Representation: {representation}")
                
                if isinstance(body, dict):
                    print("Body (ADF JSON):")
                    print(json.dumps(body, indent=2))
                else:
                    print(f"Body (string): {body[:200]}...")
        
    except Exception as e:
        print(f"\nError during page creation: {e}")
        import traceback
        traceback.print_exc()


def test_v2_adapter_flow():
    """Test page creation using V2 adapter for OAuth."""
    
    from mcp_atlassian.confluence.v2_adapter import ConfluenceV2Adapter
    
    # Create mock session
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": "789012",
        "title": "Test Page V2",
        "spaceId": "space123",
        "version": {"number": 1},
        "status": "current"
    }
    
    # Mock space lookup
    space_response = MagicMock()
    space_response.status_code = 200
    space_response.json.return_value = {
        "results": [{"id": "space123", "key": "TEST"}]
    }
    
    # Configure mock session
    def mock_get(url, **kwargs):
        if "spaces" in url and "space123" not in url:
            return space_response
        return mock_response
    
    def mock_post(url, **kwargs):
        return mock_response
    
    mock_session.get = mock_get
    mock_session.post = mock_post
    
    # Create V2 adapter
    v2_adapter = ConfluenceV2Adapter(
        session=mock_session,
        base_url="https://test.atlassian.net/wiki"
    )
    
    print("\n" + "="*60)
    print("Testing V2 adapter page creation...")
    
    # Test ADF body
    adf_body = {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Test content with "},
                    {"type": "text", "text": "bold", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": " text"}
                ]
            }
        ]
    }
    
    try:
        result = v2_adapter.create_page(
            space_key="TEST",
            title="Test Page V2",
            body=adf_body,
            representation="atlas_doc_format"
        )
        
        print("V2 adapter creation successful!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Check what was sent
        if mock_session.post.called:
            call_args = mock_session.post.call_args
            kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1]
            json_data = kwargs.get('json')
            
            print("\n" + "-"*40)
            print("Data sent to API:")
            print(json.dumps(json_data, indent=2))
            
    except Exception as e:
        print(f"Error in V2 adapter test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_page_creation_flow()
    test_v2_adapter_flow()