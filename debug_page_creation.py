#!/usr/bin/env python3

"""Test Confluence page creation through our MCP system."""

import asyncio
import os
from dotenv import load_dotenv

from src.mcp_atlassian.confluence.pages import PagesMixin
from src.mcp_atlassian.confluence.config import ConfluenceConfig

# Load environment variables
load_dotenv()

async def test_page_creation():
    """Test creating a Confluence page using our updated logic."""
    
    # Create config from environment
    config = ConfluenceConfig(
        url=os.getenv("ATLASSIAN_URL", "https://baseball.atlassian.net") + "/wiki",
        auth_type="token",
        username=os.getenv("ATLASSIAN_EMAIL"),
        api_token=os.getenv("ATLASSIAN_API_TOKEN"),
    )
    
    if not config.is_auth_configured:
        print("❌ Confluence is not configured")
        return
    
    # Create client
    client = PagesMixin(config)
    
    try:
        # Test creating a page with markdown content
        markdown_content = """# Test Heading

This is a **bold** text and *italic* text.

## Code Example

```python
def hello():
    print("Hello World")
```

- Item 1
- Item 2
- Item 3
"""
        
        print("🔄 Creating Confluence page...")
        page = client.create_page(
            space_id="655361",  # From env
            title="Debug Test Page via MCP",
            body=markdown_content,
            is_markdown=True
        )
        
        print(f"✅ Success! Created page: {page.title}")
        print(f"   Page ID: {page.id}")
        print(f"   URL: {page.url}")
        
        # Clean up - delete the test page
        print("🧹 Cleaning up test page...")
        success = client.delete_page(page.id)
        if success:
            print("✅ Test page deleted successfully")
        else:
            print("❌ Failed to delete test page")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_page_creation())