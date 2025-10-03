"""Real API validation tests for MCP Atlassian.

This module validates that the real API testing infrastructure works correctly
with actual Atlassian instances using the user's credentials.
"""

import json
import pytest
import logging
from typing import Any, Dict

from .config import skip_if_no_real_api, get_test_config
from .test_data_factory import TestDataFactory
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.jira.client import JiraClient
from src.mcp_atlassian.confluence.config import ConfluenceConfig
from src.mcp_atlassian.confluence.client import ConfluenceClient

logger = logging.getLogger(__name__)


@pytest.fixture
def config():
    """Get test configuration."""
    return get_test_config()


@pytest.fixture
def jira_client(config):
    """Get JiraClient instance."""
    jira_config = JiraConfig(
        url=config.jira.url,
        auth_type="basic",
        username=config.jira.username,
        api_token=config.jira.api_token,
    )
    return JiraClient(jira_config)


@pytest.fixture
def confluence_client(config):
    """Get ConfluenceClient instance."""
    confluence_config = ConfluenceConfig(
        url=config.confluence.url,
        auth_type="basic",
        username=config.confluence.username,
        api_token=config.confluence.api_token,
    )
    return ConfluenceClient(confluence_config)


@pytest.fixture
def factory(config):
    """Get test data factory."""
    factory = TestDataFactory()
    yield factory
    # Cleanup after test
    factory.cleanup_all_resources()


class TestRealAPIValidation:
    """Validate real API testing infrastructure works correctly."""

    def test_configuration_loading(self, config):
        """Test that configuration loads correctly with fallback credentials."""
        assert config.test_environment.enabled is True
        assert config.jira.url is not None
        assert config.confluence.url is not None
        assert config.jira.username is not None
        assert config.confluence.username is not None

        # Verify URL transformation for Confluence
        assert config.confluence.url.endswith('/wiki')

        # Verify fallback from shared credentials worked
        logger.info(f"Jira URL: {config.jira.url}")
        logger.info(f"Confluence URL: {config.confluence.url}")
        logger.info(f"Project: {config.jira.project_key}")
        logger.info(f"Space: {config.confluence.space_key}")

    @skip_if_no_real_api("Real API testing not configured")
    def test_jira_client_connectivity(self, jira_client, config):
        """Test that JiraClient can connect to real API."""
        # Test basic connectivity by getting server info
        try:
            # Try to get current user info (this requires authentication)
            user_info = jira_client.get_current_user()
            assert user_info is not None
            logger.info(f"Successfully authenticated as Jira user: {user_info.get('displayName', 'Unknown')}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Jira API: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    def test_confluence_client_connectivity(self, confluence_client, config):
        """Test that ConfluenceClient can connect to real API."""
        # Test basic connectivity by getting space info
        try:
            # Try to get space information
            space_info = confluence_client.get_space(config.confluence.space_key)
            assert space_info is not None
            logger.info(f"Successfully connected to Confluence space: {space_info.get('name', 'Unknown')}")
        except Exception as e:
            pytest.fail(f"Failed to connect to Confluence API: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    def test_jira_project_access(self, jira_client, config):
        """Test that we can access the test project in Jira."""
        try:
            project = jira_client.get_project(config.jira.project_key)
            assert project is not None
            assert project.get('key') == config.jira.project_key
            logger.info(f"Successfully accessed Jira project: {project.get('name', 'Unknown')}")
        except Exception as e:
            pytest.fail(f"Failed to access Jira project {config.jira.project_key}: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    def test_test_data_factory_initialization(self, factory, config):
        """Test that TestDataFactory initializes correctly."""
        assert factory is not None
        assert hasattr(factory, 'jira_client')
        assert hasattr(factory, 'confluence_client')

        # Test that factory can create and track resources
        # This is a dry run test - no actual resources created
        assert len(factory._created_resources) == 0

    @skip_if_no_real_api("Real API testing not configured")
    def test_create_and_cleanup_test_issue(self, factory):
        """Test creating and cleaning up a real test issue."""
        # Create a test issue
        issue_key = factory.create_test_issue(
            summary="Real API Validation Test Issue",
            description="This issue was created to validate the real API testing infrastructure"
        )

        assert issue_key is not None
        assert issue_key.startswith(factory.config.jira.project_key)
        logger.info(f"Created test issue: {issue_key}")

        # Verify the issue exists by trying to get it
        issue = factory.jira_client.get_issue(issue_key)
        assert issue is not None
        assert issue.get('key') == issue_key

        # Verify it's tracked for cleanup
        assert len(factory._created_resources) == 1
        assert factory._created_resources[0].resource_id == issue_key

    @skip_if_no_real_api("Real API testing not configured")
    def test_create_and_cleanup_test_page(self, factory):
        """Test creating and cleaning up a real test page."""
        # Create a test page
        page_id = factory.create_test_page(
            title="Real API Validation Test Page",
            content="# Test Page\n\nThis page was created to validate the real API testing infrastructure"
        )

        assert page_id is not None
        logger.info(f"Created test page: {page_id}")

        # Verify the page exists by trying to get it
        page = factory.confluence_client.get_page_by_id(page_id)
        assert page is not None
        assert page.get('id') == page_id

        # Verify it's tracked for cleanup
        confluence_resources = [r for r in factory._created_resources if r.service == "confluence"]
        assert len(confluence_resources) >= 1

    @skip_if_no_real_api("Real API testing not configured")
    def test_shared_credentials_consistency(self, config):
        """Test that shared credentials are used consistently."""
        # Both services should use the same email
        assert config.jira.username == config.confluence.username

        # URLs should be related (Confluence = Jira + /wiki)
        base_url = config.jira.url
        expected_confluence_url = f"{base_url.rstrip('/')}/wiki"
        assert config.confluence.url == expected_confluence_url

    @skip_if_no_real_api("Real API testing not configured")
    def test_token_measurement_infrastructure(self):
        """Test that token measurement infrastructure is available."""
        try:
            from .token_measurement import TokenCounter, TokenUsageMeasurement

            # Test TokenCounter
            counter = TokenCounter()
            tokens = counter.count_tokens("This is a test string for token counting")
            assert isinstance(tokens, int)
            assert tokens > 0

            # Test TokenUsageMeasurement
            measurement = TokenUsageMeasurement()
            assert measurement is not None

            logger.info(f"Token counting works: {tokens} tokens counted")
        except ImportError as e:
            pytest.fail(f"Token measurement infrastructure not available: {e}")

    @skip_if_no_real_api("Real API testing not configured")
    def test_environment_variable_fallback(self):
        """Test that environment variable fallback system works."""
        import os

        # Verify that our fallback variables are set
        assert os.getenv('ATLASSIAN_URL') is not None
        assert os.getenv('ATLASSIAN_EMAIL') is not None
        assert os.getenv('ATLASSIAN_API_TOKEN') is not None

        # Verify project/space settings
        assert os.getenv('JIRA_PROJECT') is not None
        assert os.getenv('CONFLUENCE_SPACE') is not None

        logger.info("Environment variable fallback system working correctly")