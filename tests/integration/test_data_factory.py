"""Test data factory for creating and managing real API test resources."""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

from .config import IntegrationTestConfig, get_test_config
from src.mcp_atlassian.jira.config import JiraConfig
from src.mcp_atlassian.confluence.config import ConfluenceConfig
from src.mcp_atlassian.jira import JiraFetcher
from src.mcp_atlassian.confluence import ConfluenceFetcher

logger = logging.getLogger(__name__)


@dataclass
class TestResource:
    """Represents a test resource that was created."""
    resource_type: str  # "issue", "page", "link", etc.
    resource_id: str    # The ID or key of the resource
    service: str        # "jira" or "confluence"
    cleanup_method: str # Method to call for cleanup
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TestDataFactory:
    """Factory for creating and managing test data in real Atlassian instances."""

    def __init__(self, config: Optional[IntegrationTestConfig] = None):
        self.config = config or get_test_config()
        self._jira_client: Optional[JiraFetcher] = None
        self._confluence_client: Optional[ConfluenceFetcher] = None
        self._created_resources: List[TestResource] = []
        self._session_id = str(uuid.uuid4())[:8]

    @property
    def jira_client(self) -> JiraFetcher:
        """Get or create Jira client."""
        if self._jira_client is None:
            jira_config = JiraConfig(
                url=self.config.jira.url,
                auth_type="basic",
                username=self.config.jira.username,
                api_token=self.config.jira.api_token,
            )
            self._jira_client = JiraFetcher(config=jira_config)
        return self._jira_client

    @property
    def confluence_client(self) -> ConfluenceFetcher:
        """Get or create Confluence client."""
        if self._confluence_client is None:
            confluence_config = ConfluenceConfig(
                url=self.config.confluence.url,
                auth_type="basic",
                username=self.config.confluence.username,
                api_token=self.config.confluence.api_token,
            )
            self._confluence_client = ConfluenceFetcher(config=confluence_config)
        return self._confluence_client

    def get_test_identifier(self, base_name: str) -> str:
        """Generate a unique test identifier."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.config.test_environment.resource_prefix}{base_name}_{self._session_id}_{timestamp}"

    def create_test_issue(
        self,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        issue_type: Optional[str] = None,
        assignee: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a test issue in Jira."""
        if summary is None:
            summary = self.get_test_identifier("Test_Issue")

        if description is None:
            description = f"Test issue created by MCP Atlassian integration tests at {datetime.now()}"


        try:
            issue = self.jira_client.create_issue(
                project_key=self.config.jira.project_key,
                summary=summary,
                issue_type=issue_type or self.config.jira.issue_type,
                description=description,
                assignee=assignee or self.config.jira.assignee,
                components=[self.config.jira.component] if self.config.jira.component else None,
                **kwargs
            )
            issue_key = issue.key

            # Track for cleanup
            self._created_resources.append(TestResource(
                resource_type="issue",
                resource_id=issue_key,
                service="jira",
                cleanup_method="delete_issue",
                metadata={"summary": summary, "project": self.config.jira.project_key}
            ))

            logger.info(f"Created test issue: {issue_key}")
            return issue_key

        except Exception as e:
            logger.error(f"Failed to create test issue: {e}")
            raise

    def create_test_page(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a test page in Confluence."""
        if title is None:
            title = self.get_test_identifier("Test_Page")

        if content is None:
            content = f"""
# {title}

This is a test page created by MCP Atlassian integration tests.

**Created:** {datetime.now()}
**Session:** {self._session_id}

## Test Content

This page can be used for testing various Confluence operations:
- Content updates
- Attachments
- Comments
- Labels

Please do not modify this page manually as it will be automatically cleaned up.
            """.strip()

        page_data = {
            "space": {"key": self.config.confluence.space_key},
            "title": title,
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        # Set parent page if specified
        if parent_id or self.config.confluence.parent_page_id:
            page_data["ancestors"] = [{"id": parent_id or self.config.confluence.parent_page_id}]

        # Add any additional fields from kwargs
        page_data.update(kwargs)

        try:
            page = self.confluence_client.create_page(**page_data)
            page_id = page.id

            # Track for cleanup
            self._created_resources.append(TestResource(
                resource_type="page",
                resource_id=page_id,
                service="confluence",
                cleanup_method="delete_page",
                metadata={"title": title, "space": self.config.confluence.space_key}
            ))

            logger.info(f"Created test page: {page_id} ({title})")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create test page: {e}")
            raise

    def create_test_epic(self, epic_name: Optional[str] = None) -> str:
        """Create a test epic in Jira."""
        if epic_name is None:
            epic_name = self.get_test_identifier("Test_Epic")

        # Create epic (issue type should be Epic)
        epic_key = self.create_test_issue(
            summary=epic_name,
            description=f"Test epic for integration testing: {epic_name}",
            issue_type="Epic"
        )

        # Update the resource metadata to indicate it's an epic
        for resource in self._created_resources:
            if resource.resource_id == epic_key:
                resource.metadata["is_epic"] = True
                break

        return epic_key

    def create_multiple_test_issues(self, count: int, prefix: str = "Bulk") -> List[str]:
        """Create multiple test issues for batch testing."""
        issue_keys = []
        for i in range(count):
            summary = f"{self.get_test_identifier(prefix)}_Issue_{i+1}"
            issue_key = self.create_test_issue(summary=summary)
            issue_keys.append(issue_key)
            # Small delay to avoid rate limiting
            time.sleep(0.1)

        logger.info(f"Created {count} test issues for batch testing")
        return issue_keys

    def get_existing_test_issue(self) -> Optional[str]:
        """Get an existing test issue key if configured."""
        return self.config.jira.existing_issue

    def get_existing_test_page(self) -> Optional[str]:
        """Get an existing test page ID if configured."""
        return self.config.confluence.existing_page_id

    def get_test_epic(self) -> Optional[str]:
        """Get a test epic key (either configured or create one)."""
        if self.config.jira.epic_key:
            return self.config.jira.epic_key

        # Create a test epic
        return self.create_test_epic()

    def cleanup_all_resources(self, force: bool = False, verify: bool = True) -> None:
        """Clean up all created test resources."""
        if not self.config.test_environment.auto_cleanup and not force:
            logger.info("Auto-cleanup disabled, skipping resource cleanup")
            return

        cleanup_errors = []
        verification_errors = []

        for resource in reversed(self._created_resources):  # Clean up in reverse order
            try:
                self._cleanup_resource(resource)

                # Verify cleanup if requested
                if verify:
                    try:
                        self._verify_resource_deleted(resource)
                    except Exception as e:
                        verification_errors.append(f"Resource {resource.resource_id} still exists after cleanup: {e}")

            except Exception as e:
                cleanup_errors.append(f"Failed to cleanup {resource.resource_type} {resource.resource_id}: {e}")
                logger.error(f"Cleanup error: {e}")

        self._created_resources.clear()

        if cleanup_errors:
            logger.warning(f"Some cleanup operations failed:\n" + "\n".join(cleanup_errors))
        if verification_errors:
            logger.warning(f"Some resources not properly cleaned up:\n" + "\n".join(verification_errors))

        if not cleanup_errors and not verification_errors:
            logger.info("All test resources cleaned up successfully")

    def _cleanup_resource(self, resource: TestResource) -> None:
        """Clean up a single test resource."""
        if resource.service == "jira":
            client = self.jira_client
        elif resource.service == "confluence":
            client = self.confluence_client
        else:
            raise ValueError(f"Unknown service: {resource.service}")

        cleanup_method = getattr(client, resource.cleanup_method, None)
        if cleanup_method is None:
            raise ValueError(f"Cleanup method {resource.cleanup_method} not found on {resource.service} client")

        # Call the cleanup method with appropriate parameters
        if resource.resource_type == "issue":
            cleanup_method(issue_key=resource.resource_id)
        elif resource.resource_type == "page":
            cleanup_method(page_id=resource.resource_id)
        else:
            # Generic cleanup - just pass the resource ID
            cleanup_method(resource.resource_id)

        logger.debug(f"Cleaned up {resource.resource_type}: {resource.resource_id}")

    def _verify_resource_deleted(self, resource: TestResource) -> None:
        """Verify that a resource has been properly deleted."""
        if resource.service == "jira":
            client = self.jira_client
        elif resource.service == "confluence":
            client = self.confluence_client
        else:
            raise ValueError(f"Unknown service: {resource.service}")

        try:
            if resource.resource_type == "issue":
                # Try to get the issue - should raise exception if deleted
                client.get_issue(resource.resource_id)
                raise Exception(f"Issue {resource.resource_id} still exists")
            elif resource.resource_type == "page":
                # Try to get the page - should raise exception if deleted
                client.get_page_by_id(resource.resource_id)
                raise Exception(f"Page {resource.resource_id} still exists")
            else:
                # For other resource types, we'll assume cleanup worked
                logger.debug(f"Cannot verify deletion of {resource.resource_type} resources")

        except Exception as e:
            # If we get an exception trying to fetch the resource, that's good!
            # It means the resource was properly deleted
            if "404" in str(e) or "not found" in str(e).lower():
                logger.debug(f"Verified {resource.resource_type} {resource.resource_id} was deleted")
            else:
                # Re-raise if it's not a "not found" error
                raise

    def verify_resource_exists(self, resource: TestResource) -> bool:
        """Verify that a resource exists and can be retrieved.

        Args:
            resource: The resource to verify

        Returns:
            True if resource exists and is accessible, False otherwise
        """
        try:
            if resource.service == "jira":
                client = self.jira_client
            elif resource.service == "confluence":
                client = self.confluence_client
            else:
                return False

            if resource.resource_type == "issue":
                issue = client.get_issue(resource.resource_id)
                return issue is not None
            elif resource.resource_type == "page":
                page = client.get_page_by_id(resource.resource_id)
                return page is not None
            else:
                # For other resource types, assume they exist
                return True

        except Exception as e:
            logger.debug(f"Resource {resource.resource_id} verification failed: {e}")
            return False

    def get_created_resource_by_id(self, resource_id: str) -> TestResource | None:
        """Get a created resource by its ID."""
        for resource in self._created_resources:
            if resource.resource_id == resource_id:
                return resource
        return None

    def cleanup_existing_test_resources(self) -> None:
        """Clean up any existing test resources from previous runs."""
        if not self.config.test_environment.cleanup_on_start:
            return

        logger.info("Cleaning up existing test resources...")

        # Clean up test issues in Jira
        try:
            jql = f'summary ~ "{self.config.test_environment.resource_prefix}*" AND project = {self.config.jira.project_key}'
            search_result = self.jira_client.search_issues(jql=jql, limit=100)

            for issue in search_result.issues:
                try:
                    self.jira_client.delete_issue(issue_key=issue.key)
                    logger.debug(f"Cleaned up existing test issue: {issue.key}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup existing issue {issue.key}: {e}")

        except Exception as e:
            logger.warning(f"Failed to cleanup existing Jira test resources: {e}")

        # Clean up test pages in Confluence
        try:
            cql = f'title ~ "{self.config.test_environment.resource_prefix}*" AND space = {self.config.confluence.space_key}'
            search_results = self.confluence_client.search(cql=cql, limit=100)

            for page in search_results:
                try:
                    self.confluence_client.delete_page(page_id=page.id)
                    logger.debug(f"Cleaned up existing test page: {page.id}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup existing page {page.id}: {e}")

        except Exception as e:
            logger.warning(f"Failed to cleanup existing Confluence test resources: {e}")

        logger.info("Existing test resource cleanup completed")

    def get_created_resources(self) -> List[TestResource]:
        """Get a list of all created resources."""
        return self._created_resources.copy()

    def get_created_resources_by_type(self, resource_type: str) -> List[TestResource]:
        """Get created resources of a specific type."""
        return [r for r in self._created_resources if r.resource_type == resource_type]


# Global factory instance for test session
_test_factory: Optional[TestDataFactory] = None


def get_test_factory() -> TestDataFactory:
    """Get the global test data factory instance."""
    global _test_factory
    if _test_factory is None:
        _test_factory = TestDataFactory()
    return _test_factory


def setup_test_session():
    """Set up test session and clean up existing resources."""
    factory = get_test_factory()
    factory.cleanup_existing_test_resources()


def teardown_test_session():
    """Clean up all test resources at the end of test session."""
    global _test_factory
    if _test_factory is not None:
        _test_factory.cleanup_all_resources()
        _test_factory = None