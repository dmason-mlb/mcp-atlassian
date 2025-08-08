#!/usr/bin/env python3
"""Test Confluence space access."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig

def test_confluence_space():
    """Test Confluence space access."""
    
    print("=" * 60)
    print("TESTING CONFLUENCE SPACE ACCESS")
    print("=" * 60)
    
    try:
        # Initialize Confluence client
        config = ConfluenceConfig.from_env()
        confluence = ConfluenceClient(config)
        print(f"✅ Confluence client initialized")
        print(f"   URL: {config.url}")
        print(f"   Cloud: {config.is_cloud}")
        
        # Try to search for pages in MLBENG space
        print("\nSearching for pages in MLBENG space...")
        try:
            # Use CQL to search within the space
            result = confluence.confluence.cql(
                'space="MLBENG" AND type=page',
                limit=5
            )
            print(f"   Found {result.get('totalSize', 0)} pages in MLBENG space")
            if result.get('totalSize', 0) > 0:
                print("   ✅ Space exists and is accessible")
            else:
                print("   ⚠️  Space exists but has no pages")
        except Exception as e:
            print(f"   ❌ Error searching space: {e}")
            
        # Try to get space information
        print("\nGetting space information...")
        try:
            space = confluence.confluence.get_space(key="MLBENG")
            print(f"   ✅ Space found: {space.get('name', 'Unknown')}")
            print(f"   Space ID: {space.get('id')}")
            print(f"   Type: {space.get('type')}")
        except Exception as e:
            print(f"   ❌ Error getting space: {e}")
            
        # List available spaces
        print("\nListing available spaces...")
        try:
            spaces = confluence.confluence.get_all_spaces(limit=10)
            print(f"   Found {len(spaces)} spaces:")
            for space in spaces[:5]:
                print(f"   - {space.get('key')}: {space.get('name')}")
        except Exception as e:
            print(f"   ❌ Error listing spaces: {e}")
            
    except Exception as e:
        print(f"❌ Failed to initialize Confluence: {e}")

if __name__ == "__main__":
    test_confluence_space()