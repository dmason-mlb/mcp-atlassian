#!/usr/bin/env python3
"""Check available Confluence spaces."""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig


def check_spaces():
    """Check available Confluence spaces."""

    print("=" * 60)
    print("CHECKING AVAILABLE CONFLUENCE SPACES")
    print("=" * 60)

    try:
        # Initialize Confluence client
        config = ConfluenceConfig.from_env()
        confluence = ConfluenceClient(config)
        print("✅ Confluence client initialized")
        print(f"   URL: {config.url}")

        # Get all spaces
        print("\nFetching all available spaces...")
        spaces = confluence.confluence.get_all_spaces(limit=50)

        if spaces:
            print(f"\nFound {len(spaces)} spaces:")
            for space in spaces:
                key = space.get("key", "Unknown")
                name = space.get("name", "Unknown")
                space_type = space.get("type", "Unknown")
                print(f"   - {key}: {name} (Type: {space_type})")
        else:
            print("   No spaces found or accessible")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_spaces()
