"""Utilities for handling eventual consistency in Jira Cloud."""

import asyncio
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ConsistencyConfig:
    """Configuration for eventual consistency handling."""

    def __init__(
        self,
        strategy: str = "reconcile",  # "reconcile", "poll", "hybrid", "none"
        max_retries: int = 5,
        base_delay: float = 0.5,
        max_delay: float = 8.0,
        backoff_factor: float = 2.0,
        timeout: float = 30.0,
    ):
        """Initialize consistency configuration.

        Args:
            strategy: Strategy to use ("reconcile", "poll", "hybrid", "none")
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Exponential backoff factor
            timeout: Total timeout for all retries in seconds
        """
        self.strategy = strategy
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.timeout = timeout


class ConsistencyHelper:
    """Helper class for handling eventual consistency issues."""

    def __init__(self, config: ConsistencyConfig | None = None):
        """Initialize the consistency helper.

        Args:
            config: Configuration for consistency handling
        """
        self.config = config or ConsistencyConfig()

    def poll_until_visible(
        self,
        check_function: Callable[[], bool],
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> bool:
        """Poll until a condition is met or timeout/retries are exceeded.

        Args:
            check_function: Function that returns True when condition is met
            timeout: Override timeout from config
            max_retries: Override max_retries from config

        Returns:
            True if condition was met, False if timed out or exhausted retries
        """
        if self.config.strategy == "none":
            return True  # Skip polling

        timeout = timeout or self.config.timeout
        max_retries = max_retries or self.config.max_retries

        start_time = time.time()
        attempt = 0
        delay = self.config.base_delay

        while attempt < max_retries:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                # Enhanced timeout message with suggestions
                timeout_msg = IndexingDelayMessageHelper.create_timeout_message(
                    operation="consistency polling",
                    duration=elapsed,
                    is_cloud=True
                )
                logger.warning(f"Polling timed out: {timeout_msg}")
                return False

            try:
                if check_function():
                    if attempt > 0:
                        logger.info(f"Condition met after {attempt} retries in {elapsed:.2f}s")
                    return True
            except Exception as e:
                logger.debug(f"Polling check failed on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:  # Don't sleep after the last attempt
                sleep_time = min(delay, self.config.max_delay)
                remaining_time = timeout - elapsed
                sleep_time = min(sleep_time, remaining_time)

                if sleep_time > 0:
                    logger.debug(f"Polling attempt {attempt + 1} failed, sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    delay *= self.config.backoff_factor
                else:
                    break

            attempt += 1

        elapsed = time.time() - start_time
        logger.warning(f"Polling failed after {attempt} attempts in {elapsed:.2f}s")
        return False

    async def async_poll_until_visible(
        self,
        check_function: Callable[[], bool],
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> bool:
        """Async version of poll_until_visible.

        Args:
            check_function: Function that returns True when condition is met
            timeout: Override timeout from config
            max_retries: Override max_retries from config

        Returns:
            True if condition was met, False if timed out or exhausted retries
        """
        if self.config.strategy == "none":
            return True  # Skip polling

        timeout = timeout or self.config.timeout
        max_retries = max_retries or self.config.max_retries

        start_time = time.time()
        attempt = 0
        delay = self.config.base_delay

        while attempt < max_retries:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                # Enhanced timeout message with suggestions
                timeout_msg = IndexingDelayMessageHelper.create_timeout_message(
                    operation="async consistency polling",
                    duration=elapsed,
                    is_cloud=True
                )
                logger.warning(f"Async polling timed out: {timeout_msg}")
                return False

            try:
                if check_function():
                    if attempt > 0:
                        logger.info(f"Condition met after {attempt} retries in {elapsed:.2f}s")
                    return True
            except Exception as e:
                logger.debug(f"Async polling check failed on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:  # Don't sleep after the last attempt
                sleep_time = min(delay, self.config.max_delay)
                remaining_time = timeout - elapsed
                sleep_time = min(sleep_time, remaining_time)

                if sleep_time > 0:
                    logger.debug(f"Async polling attempt {attempt + 1} failed, sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
                    delay *= self.config.backoff_factor
                else:
                    break

            attempt += 1

        elapsed = time.time() - start_time
        logger.warning(f"Async polling failed after {attempt} attempts in {elapsed:.2f}s")
        return False

    def create_issue_visibility_checker(
        self,
        search_function: Callable[[str, list[str] | None], Any],
        issue_key: str,
    ) -> Callable[[], bool]:
        """Create a function to check if an issue is visible in search results.

        Args:
            search_function: Function to search for issues (should accept JQL and reconcile_issues)
            issue_key: The issue key to search for

        Returns:
            Function that returns True if issue is found in search results
        """
        def check_visibility() -> bool:
            try:
                jql = f"key = {issue_key}"

                if self.config.strategy == "reconcile":
                    # Use reconcileIssues parameter for read-after-write consistency
                    result = search_function(jql, [issue_key])
                else:
                    # Use regular search for polling strategy
                    result = search_function(jql, None)

                # Check if the issue is found in results
                if hasattr(result, 'issues'):
                    issues = result.issues
                elif isinstance(result, dict) and 'issues' in result:
                    issues = result['issues']
                elif isinstance(result, list):
                    issues = result
                else:
                    logger.debug(f"Unexpected search result format: {type(result)}")
                    return False

                # Look for our issue in the results
                for issue in issues:
                    if isinstance(issue, dict):
                        found_key = issue.get('key')
                    else:
                        found_key = getattr(issue, 'key', None)

                    if found_key == issue_key:
                        logger.debug(f"Issue {issue_key} found in search results")
                        return True

                logger.debug(f"Issue {issue_key} not found in search results")
                return False

            except Exception as e:
                logger.debug(f"Error checking issue visibility: {e}")
                return False

        return check_visibility

    def create_hybrid_issue_checker(
        self,
        get_issue_function: Callable[[str], Any],
        search_function: Callable[[str, list[str] | None], Any],
        issue_key: str,
    ) -> Callable[[], bool]:
        """Create a hybrid function that uses direct issue access and falls back to search.

        The hybrid approach first tries to access the issue directly via GET API
        (which bypasses search index), and falls back to search-based validation
        if direct access fails.

        Args:
            get_issue_function: Function to get issue directly by key
            search_function: Function to search for issues
            issue_key: The issue key to check

        Returns:
            Function that returns True if issue is accessible via either method
        """
        def check_hybrid_visibility() -> bool:
            # Strategy 1: Direct issue access (bypasses search index)
            try:
                logger.debug(f"Attempting direct access to issue {issue_key}")
                issue = get_issue_function(issue_key)
                if issue:
                    logger.debug(f"Issue {issue_key} accessible via direct API")
                    return True
            except Exception as e:
                logger.debug(f"Direct access to issue {issue_key} failed: {e}")

            # Strategy 2: Fall back to search-based checking
            logger.debug(f"Falling back to search-based verification for issue {issue_key}")
            search_checker = self.create_issue_visibility_checker(search_function, issue_key)
            return search_checker()

        return check_hybrid_visibility


def get_consistency_config_from_env() -> ConsistencyConfig:
    """Get consistency configuration from environment variables.

    Returns:
        ConsistencyConfig configured from environment variables
    """
    import os

    def get_env_bool(key: str, default: bool) -> bool:
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default

    def get_env_float(key: str, default: float) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def get_env_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    return ConsistencyConfig(
        strategy=os.getenv("JIRA_CONSISTENCY_STRATEGY", "hybrid"),
        max_retries=get_env_int("JIRA_CONSISTENCY_MAX_RETRIES", 5),
        base_delay=get_env_float("JIRA_CONSISTENCY_BASE_DELAY", 0.5),
        max_delay=get_env_float("JIRA_CONSISTENCY_MAX_DELAY", 8.0),
        backoff_factor=get_env_float("JIRA_CONSISTENCY_BACKOFF_FACTOR", 2.0),
        timeout=get_env_float("JIRA_CONSISTENCY_TIMEOUT", 30.0),
    )


class IndexingDelayMessageHelper:
    """Helper class for generating informative error messages about indexing delays."""

    @staticmethod
    def create_search_delay_message(
        operation: str,
        issue_key: str | None = None,
        jql: str | None = None,
        is_cloud: bool = True,
    ) -> str:
        """Create a helpful error message for search operations that may be affected by indexing delays.

        Args:
            operation: The operation being performed (e.g., "search", "update", "link")
            issue_key: The issue key that might be affected by delays
            jql: The JQL query that returned no results
            is_cloud: Whether this is a Jira Cloud instance

        Returns:
            A helpful error message with suggestions for dealing with indexing delays
        """
        if not is_cloud:
            # Server/DC instances don't have the same indexing delay issues
            return f"Operation '{operation}' failed. Please check your query and permissions."

        base_message = f"Operation '{operation}' completed but may be affected by indexing delays in Jira Cloud."

        suggestions = []

        if issue_key:
            suggestions.extend([
                f"• The issue {issue_key} may have been created/updated but not yet indexed for search",
                f"• Try accessing the issue directly via its key rather than through search",
                "• Wait a few seconds and retry the operation"
            ])

        if jql:
            suggestions.extend([
                "• The JQL query may be correct but returns no results due to indexing delays",
                "• Try using the reconcileIssues parameter in search operations",
                "• Consider using direct issue access instead of JQL search when possible"
            ])

        suggestions.extend([
            "• This is normal behavior in Jira Cloud and typically resolves within seconds",
            "• For immediate consistency, consider using direct API endpoints instead of search",
            "• Configure JIRA_CONSISTENCY_STRATEGY=hybrid to automatically handle such delays"
        ])

        if suggestions:
            return f"{base_message}\n\nSuggestions:\n" + "\n".join(suggestions)

        return base_message

    @staticmethod
    def create_not_found_message(
        resource_type: str,
        resource_key: str,
        operation: str,
        is_cloud: bool = True,
        recently_created: bool = False,
    ) -> str:
        """Create a helpful error message for 'not found' errors that may be due to indexing delays.

        Args:
            resource_type: Type of resource (e.g., "issue", "page")
            resource_key: Key/identifier of the resource
            operation: The operation being performed
            is_cloud: Whether this is a Jira Cloud instance
            recently_created: Whether the resource was recently created

        Returns:
            A helpful error message with suggestions
        """
        if not is_cloud:
            return f"{resource_type.capitalize()} '{resource_key}' not found for operation '{operation}'. Please check the key and your permissions."

        base_message = f"{resource_type.capitalize()} '{resource_key}' not found for operation '{operation}'."

        if recently_created:
            base_message += f" This {resource_type} may have been recently created and not yet available due to indexing delays in Jira Cloud."

            suggestions = [
                f"• The {resource_type} '{resource_key}' may exist but not be indexed yet",
                "• Try accessing it directly by key rather than through search",
                "• Wait a few seconds and retry the operation",
                "• Use reconcileIssues parameter in search operations",
                "• Configure JIRA_CONSISTENCY_STRATEGY=hybrid for better handling of such scenarios"
            ]

            return f"{base_message}\n\nSuggestions:\n" + "\n".join(suggestions)

        return f"{base_message} Please check the key and your permissions."

    @staticmethod
    def create_timeout_message(
        operation: str,
        duration: float,
        is_cloud: bool = True,
    ) -> str:
        """Create a helpful error message for operations that timeout due to consistency checking.

        Args:
            operation: The operation that timed out
            duration: How long the operation took
            is_cloud: Whether this is a Jira Cloud instance

        Returns:
            A helpful error message with suggestions
        """
        if not is_cloud:
            return f"Operation '{operation}' timed out after {duration:.1f}s. Please check your network connection and try again."

        base_message = f"Operation '{operation}' timed out after {duration:.1f}s while waiting for indexing consistency."

        suggestions = [
            "• The operation may have completed successfully but indexing is delayed",
            "• Try accessing the resource directly by key to verify completion",
            "• Consider increasing JIRA_CONSISTENCY_TIMEOUT if this happens frequently",
            "• Use JIRA_CONSISTENCY_STRATEGY=none to disable consistency checking",
            "• This is typically due to higher than normal indexing delays in Jira Cloud"
        ]

        return f"{base_message}\n\nSuggestions:\n" + "\n".join(suggestions)

    @staticmethod
    def create_general_delay_warning(
        is_cloud: bool = True,
        operation: str | None = None,
    ) -> str:
        """Create a general warning message about potential indexing delays.

        Args:
            is_cloud: Whether this is a Jira Cloud instance
            operation: Optional operation context

        Returns:
            A warning message about potential delays
        """
        if not is_cloud:
            return ""

        base = "Note: Jira Cloud uses eventual consistency - "
        if operation:
            base += f"{operation} operations may experience brief indexing delays."
        else:
            base += "operations may experience brief indexing delays."

        return f"{base} Use hybrid strategy or direct API access for immediate consistency if needed."


def get_consistency_config_from_jira_config(jira_config) -> ConsistencyConfig:
    """Get consistency configuration from a JiraConfig object.

    Args:
        jira_config: JiraConfig instance with consistency settings

    Returns:
        ConsistencyConfig configured from JiraConfig
    """
    return ConsistencyConfig(
        strategy=jira_config.consistency_strategy,
        max_retries=jira_config.consistency_max_retries,
        base_delay=jira_config.consistency_base_delay,
        max_delay=jira_config.consistency_max_delay,
        backoff_factor=jira_config.consistency_backoff_factor,
        timeout=jira_config.consistency_timeout,
    )