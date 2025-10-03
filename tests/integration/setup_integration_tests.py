#!/usr/bin/env python3
"""Setup script for real API integration tests."""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.config import get_test_config, ConfigurationError
from tests.integration.test_data_factory import TestDataFactory


def setup_logging(log_level: str = "INFO"):
    """Set up logging for the setup script."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("tests/logs/setup.log", mode="w")
        ]
    )


def validate_environment():
    """Validate that the test environment is properly configured."""
    print("🔍 Validating test environment configuration...")

    try:
        config = get_test_config()
        print("✅ Configuration loaded successfully")

        if not config.test_environment.enabled:
            print("❌ Test environment is not enabled")
            print("   Set test_environment.enabled=true in test_config.yaml")
            return False

        print(f"✅ Test environment enabled")
        print(f"   Resource prefix: {config.test_environment.resource_prefix}")
        print(f"   Auto-cleanup: {config.test_environment.auto_cleanup}")

        # Validate Jira configuration
        print("\n🎯 Validating Jira configuration...")
        if config.jira.url:
            print(f"✅ Jira URL: {config.jira.url}")
        else:
            print("❌ Jira URL not configured")
            return False

        if config.jira.api_token or config.jira.pat:
            auth_type = "API Token" if config.jira.api_token else "PAT"
            print(f"✅ Jira authentication: {auth_type}")
        else:
            print("❌ Jira authentication not configured")
            return False

        print(f"✅ Jira project: {config.jira.project_key}")

        # Validate Confluence configuration
        print("\n📖 Validating Confluence configuration...")
        if config.confluence.url:
            print(f"✅ Confluence URL: {config.confluence.url}")
        else:
            print("❌ Confluence URL not configured")
            return False

        if config.confluence.api_token or config.confluence.pat:
            auth_type = "API Token" if config.confluence.api_token else "PAT"
            print(f"✅ Confluence authentication: {auth_type}")
        else:
            print("❌ Confluence authentication not configured")
            return False

        print(f"✅ Confluence space: {config.confluence.space_key}")

        return True

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error validating configuration: {e}")
        return False


def test_api_connectivity():
    """Test connectivity to Jira and Confluence APIs."""
    print("\n🌐 Testing API connectivity...")

    try:
        factory = TestDataFactory()

        # Test Jira connection
        print("  Testing Jira connection...")
        try:
            # Try to get current user to test authentication
            current_user = factory.jira_client.jira.current_user()
            print(f"  ✅ Jira connection successful (user: {current_user})")
        except Exception as e:
            print(f"  ❌ Jira connection failed: {e}")
            return False

        # Test Confluence connection
        print("  Testing Confluence connection...")
        try:
            # Try to get current user to test authentication
            current_user = factory.confluence_client.confluence.get_current_user()
            user_name = current_user.get("displayName", "Unknown")
            print(f"  ✅ Confluence connection successful (user: {user_name})")
        except Exception as e:
            print(f"  ❌ Confluence connection failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Error testing API connectivity: {e}")
        return False


def create_test_resources():
    """Create initial test resources for testing."""
    print("\n🏗️  Creating test resources...")

    try:
        factory = TestDataFactory()

        # Clean up any existing test resources first
        print("  Cleaning up existing test resources...")
        factory.cleanup_existing_test_resources()

        # Create a test issue
        print("  Creating test issue...")
        test_issue = factory.create_test_issue(
            summary="Test Issue for Integration Testing",
            description="This issue is created for testing MCP Atlassian meta-tools integration."
        )
        print(f"  ✅ Created test issue: {test_issue}")

        # Create a test page
        print("  Creating test page...")
        test_page = factory.create_test_page(
            title="Test Page for Integration Testing",
            content="""
# Test Page for MCP Atlassian Integration Testing

This page is created for testing Confluence operations with meta-tools.

## Purpose
- Test content retrieval
- Test content updates
- Test search operations

## Auto-generated Content
This page was created automatically by the integration test setup script.
            """.strip()
        )
        print(f"  ✅ Created test page: {test_page}")

        # Try to create a test epic if Epic issue type exists
        try:
            print("  Creating test epic...")
            test_epic = factory.create_test_epic("Test Epic for Integration Testing")
            print(f"  ✅ Created test epic: {test_epic}")
        except Exception as e:
            print(f"  ⚠️  Could not create test epic (Epic issue type may not exist): {e}")

        print(f"\n✅ Test resources created successfully!")
        print(f"   Test issues can be viewed in project: {factory.config.jira.project_key}")
        print(f"   Test pages can be viewed in space: {factory.config.confluence.space_key}")

        return True

    except Exception as e:
        print(f"❌ Error creating test resources: {e}")
        return False


def cleanup_test_resources():
    """Clean up all test resources."""
    print("\n🧹 Cleaning up test resources...")

    try:
        factory = TestDataFactory()
        factory.cleanup_existing_test_resources()
        print("✅ Test resources cleaned up successfully!")
        return True

    except Exception as e:
        print(f"❌ Error cleaning up test resources: {e}")
        return False


def show_configuration_template():
    """Show a template for environment variable configuration."""
    print("""
📋 Environment Variable Configuration Template

Copy these environment variables to your shell or .env file and update with your values:

# Jira Configuration
export JIRA_TEST_URL="https://your-domain.atlassian.net"
export JIRA_TEST_USERNAME="your-email@example.com"
export JIRA_TEST_API_TOKEN="your-jira-api-token"
export JIRA_TEST_PROJECT="TEST"  # Your test project key
export JIRA_TEST_EPIC="TEST-1"   # Optional: existing epic for testing
export JIRA_TEST_ISSUE="TEST-2"  # Optional: existing issue for read-only tests
export JIRA_TEST_ASSIGNEE="your-email@example.com"
export JIRA_TEST_COMPONENT="Backend"  # Optional: component name

# Confluence Configuration
export CONFLUENCE_TEST_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_TEST_USERNAME="your-email@example.com"
export CONFLUENCE_TEST_API_TOKEN="your-confluence-api-token"
export CONFLUENCE_TEST_SPACE="TEST"  # Your test space key
export CONFLUENCE_TEST_PARENT_PAGE="123456"  # Optional: parent page ID
export CONFLUENCE_TEST_PAGE="789012"  # Optional: existing page for read-only tests

# Test Environment
export TEST_ENVIRONMENT="development"

For Server/DC instances, use PAT instead of API tokens:
export JIRA_TEST_PAT="your-jira-pat"
export CONFLUENCE_TEST_PAT="your-confluence-pat"

🔑 How to get API tokens:
- Jira/Confluence Cloud: https://id.atlassian.com/manage-profile/security/api-tokens
- Jira/Confluence Server/DC: Generate Personal Access Tokens in your instance
    """)


def main():
    """Main setup script entry point."""
    parser = argparse.ArgumentParser(description="Setup real API integration tests for MCP Atlassian")
    parser.add_argument("--validate", action="store_true", help="Validate configuration only")
    parser.add_argument("--test-connectivity", action="store_true", help="Test API connectivity only")
    parser.add_argument("--create-resources", action="store_true", help="Create test resources")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test resources")
    parser.add_argument("--show-config", action="store_true", help="Show configuration template")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--all", action="store_true", help="Run all setup steps")

    args = parser.parse_args()

    # Create logs directory
    os.makedirs("tests/logs", exist_ok=True)
    setup_logging(args.log_level)

    print("🚀 MCP Atlassian Integration Test Setup")
    print("=" * 50)

    success = True

    if args.show_config:
        show_configuration_template()
        return 0

    if args.cleanup:
        success = cleanup_test_resources()
        return 0 if success else 1

    if args.all or args.validate:
        success = validate_environment()
        if not success:
            print("\n❌ Configuration validation failed. Use --show-config for setup instructions.")
            return 1

    if args.all or args.test_connectivity:
        if success:
            success = test_api_connectivity()

    if args.all or args.create_resources:
        if success:
            success = create_test_resources()

    if success:
        print(f"\n🎉 Setup completed successfully!")
        print(f"   You can now run integration tests with: pytest tests/integration/ -v")
        print(f"   Or run specific meta-tool tests: pytest tests/integration/test_meta_tools_real_api.py -v")
        return 0
    else:
        print(f"\n❌ Setup failed. Check the errors above and configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())