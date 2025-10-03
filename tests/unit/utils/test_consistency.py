"""Tests for eventual consistency handling utilities."""

import time
from unittest.mock import Mock, patch

import pytest

from src.mcp_atlassian.utils.consistency import (
    ConsistencyConfig,
    ConsistencyHelper,
    IndexingDelayMessageHelper,
    get_consistency_config_from_env,
    get_consistency_config_from_jira_config,
)


class TestConsistencyConfig:
    """Test ConsistencyConfig class."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = ConsistencyConfig()
        assert config.strategy == "reconcile"
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 8.0
        assert config.backoff_factor == 2.0
        assert config.timeout == 30.0

    def test_custom_configuration(self):
        """Test custom configuration values."""
        config = ConsistencyConfig(
            strategy="hybrid",
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=1.5,
            timeout=60.0,
        )
        assert config.strategy == "hybrid"
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.backoff_factor == 1.5
        assert config.timeout == 60.0


class TestConsistencyHelper:
    """Test ConsistencyHelper class."""

    def test_none_strategy_skips_polling(self):
        """Test that 'none' strategy skips polling entirely."""
        config = ConsistencyConfig(strategy="none")
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=False)
        result = helper.poll_until_visible(check_function)

        assert result is True  # Should return True immediately
        check_function.assert_not_called()

    def test_successful_polling_immediate(self):
        """Test polling when condition is met immediately."""
        config = ConsistencyConfig(strategy="poll", max_retries=3)
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=True)
        result = helper.poll_until_visible(check_function)

        assert result is True
        check_function.assert_called_once()

    def test_successful_polling_after_retries(self):
        """Test polling when condition is met after some retries."""
        config = ConsistencyConfig(strategy="poll", max_retries=3, base_delay=0.1)
        helper = ConsistencyHelper(config)

        # Return False first 2 times, then True
        check_function = Mock(side_effect=[False, False, True])
        result = helper.poll_until_visible(check_function)

        assert result is True
        assert check_function.call_count == 3

    def test_polling_timeout_by_max_retries(self):
        """Test polling timeout due to max retries exhaustion."""
        config = ConsistencyConfig(strategy="poll", max_retries=2, base_delay=0.1)
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=False)
        result = helper.poll_until_visible(check_function)

        assert result is False
        assert check_function.call_count == 2

    def test_polling_timeout_by_duration(self):
        """Test polling timeout due to time limit."""
        config = ConsistencyConfig(strategy="poll", timeout=0.2, base_delay=0.1)
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=False)
        start_time = time.time()
        result = helper.poll_until_visible(check_function)
        duration = time.time() - start_time

        assert result is False
        # Should have timed out approximately at the configured timeout
        assert duration < 0.5  # Should not wait much longer than timeout

    def test_exponential_backoff(self):
        """Test that exponential backoff is applied correctly."""
        config = ConsistencyConfig(
            strategy="poll",
            max_retries=3,
            base_delay=0.1,
            backoff_factor=2.0,
            timeout=10.0  # Large timeout to avoid time-based termination
        )
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=False)

        with patch('time.sleep') as mock_sleep:
            result = helper.poll_until_visible(check_function)

        assert result is False
        # Should have slept with exponential backoff
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert len(sleep_calls) == 2  # max_retries - 1
        assert sleep_calls[0] == 0.1  # base_delay
        assert sleep_calls[1] == 0.2  # base_delay * backoff_factor

    def test_max_delay_limit(self):
        """Test that delays are capped at max_delay."""
        config = ConsistencyConfig(
            strategy="poll",
            max_retries=5,
            base_delay=2.0,
            max_delay=3.0,
            backoff_factor=2.0,
            timeout=60.0
        )
        helper = ConsistencyHelper(config)

        check_function = Mock(return_value=False)

        with patch('time.sleep') as mock_sleep:
            result = helper.poll_until_visible(check_function)

        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        # All delays should be capped at max_delay
        for delay in sleep_calls:
            assert delay <= 3.0

    def test_polling_exception_handling(self):
        """Test that exceptions in check function are handled gracefully."""
        config = ConsistencyConfig(strategy="poll", max_retries=3, base_delay=0.1)
        helper = ConsistencyHelper(config)

        check_function = Mock(side_effect=[Exception("Test error"), Exception("Another error"), True])
        result = helper.poll_until_visible(check_function)

        assert result is True
        assert check_function.call_count == 3


class TestIssueVisibilityChecker:
    """Test issue visibility checker functionality."""

    def test_create_issue_visibility_checker_reconcile_strategy(self):
        """Test visibility checker with reconcile strategy."""
        config = ConsistencyConfig(strategy="reconcile")
        helper = ConsistencyHelper(config)

        # Mock search function
        mock_search_result = Mock()
        mock_search_result.issues = [Mock(key="TEST-123")]
        search_function = Mock(return_value=mock_search_result)

        checker = helper.create_issue_visibility_checker(search_function, "TEST-123")
        result = checker()

        assert result is True
        search_function.assert_called_once_with("key = TEST-123", ["TEST-123"])

    def test_create_issue_visibility_checker_poll_strategy(self):
        """Test visibility checker with poll strategy."""
        config = ConsistencyConfig(strategy="poll")
        helper = ConsistencyHelper(config)

        # Mock search function
        mock_search_result = Mock()
        mock_search_result.issues = [Mock(key="TEST-123")]
        search_function = Mock(return_value=mock_search_result)

        checker = helper.create_issue_visibility_checker(search_function, "TEST-123")
        result = checker()

        assert result is True
        search_function.assert_called_once_with("key = TEST-123", None)

    def test_issue_not_found_in_search_results(self):
        """Test when issue is not found in search results."""
        config = ConsistencyConfig(strategy="poll")
        helper = ConsistencyHelper(config)

        # Mock search function returning empty results
        mock_search_result = Mock()
        mock_search_result.issues = []
        search_function = Mock(return_value=mock_search_result)

        checker = helper.create_issue_visibility_checker(search_function, "TEST-123")
        result = checker()

        assert result is False

    def test_search_function_exception(self):
        """Test handling of search function exceptions."""
        config = ConsistencyConfig(strategy="poll")
        helper = ConsistencyHelper(config)

        search_function = Mock(side_effect=Exception("Search failed"))

        checker = helper.create_issue_visibility_checker(search_function, "TEST-123")
        result = checker()

        assert result is False


class TestHybridIssueChecker:
    """Test hybrid issue checker functionality."""

    def test_hybrid_checker_direct_access_success(self):
        """Test hybrid checker when direct access succeeds."""
        config = ConsistencyConfig(strategy="hybrid")
        helper = ConsistencyHelper(config)

        get_issue_function = Mock(return_value={"key": "TEST-123"})
        search_function = Mock()

        checker = helper.create_hybrid_issue_checker(get_issue_function, search_function, "TEST-123")
        result = checker()

        assert result is True
        get_issue_function.assert_called_once_with("TEST-123")
        search_function.assert_not_called()  # Should not fall back to search

    def test_hybrid_checker_fallback_to_search(self):
        """Test hybrid checker falling back to search when direct access fails."""
        config = ConsistencyConfig(strategy="hybrid")
        helper = ConsistencyHelper(config)

        get_issue_function = Mock(side_effect=Exception("Direct access failed"))
        mock_search_result = Mock()
        mock_search_result.issues = [Mock(key="TEST-123")]
        search_function = Mock(return_value=mock_search_result)

        checker = helper.create_hybrid_issue_checker(get_issue_function, search_function, "TEST-123")
        result = checker()

        assert result is True
        get_issue_function.assert_called_once_with("TEST-123")
        search_function.assert_called_once()

    def test_hybrid_checker_both_methods_fail(self):
        """Test hybrid checker when both direct access and search fail."""
        config = ConsistencyConfig(strategy="hybrid")
        helper = ConsistencyHelper(config)

        get_issue_function = Mock(side_effect=Exception("Direct access failed"))
        search_function = Mock(return_value=Mock(issues=[]))

        checker = helper.create_hybrid_issue_checker(get_issue_function, search_function, "TEST-123")
        result = checker()

        assert result is False


class TestIndexingDelayMessageHelper:
    """Test IndexingDelayMessageHelper class."""

    def test_create_search_delay_message_cloud(self):
        """Test search delay message for Cloud instances."""
        message = IndexingDelayMessageHelper.create_search_delay_message(
            operation="search",
            issue_key="TEST-123",
            jql="project = TEST",
            is_cloud=True,
        )

        assert "indexing delays in Jira Cloud" in message
        assert "TEST-123" in message
        assert "Suggestions:" in message
        assert "reconcileIssues" in message

    def test_create_search_delay_message_server(self):
        """Test search delay message for Server/DC instances."""
        message = IndexingDelayMessageHelper.create_search_delay_message(
            operation="search",
            is_cloud=False,
        )

        assert "check your query and permissions" in message
        assert "indexing delays" not in message

    def test_create_not_found_message_recently_created(self):
        """Test not found message for recently created resources."""
        message = IndexingDelayMessageHelper.create_not_found_message(
            resource_type="issue",
            resource_key="TEST-123",
            operation="update",
            is_cloud=True,
            recently_created=True,
        )

        assert "recently created" in message
        assert "indexing delays" in message
        assert "Suggestions:" in message
        assert "reconcileIssues" in message

    def test_create_not_found_message_server(self):
        """Test not found message for Server/DC instances."""
        message = IndexingDelayMessageHelper.create_not_found_message(
            resource_type="issue",
            resource_key="TEST-123",
            operation="update",
            is_cloud=False,
        )

        assert "check the key and your permissions" in message
        assert "indexing delays" not in message

    def test_create_timeout_message_cloud(self):
        """Test timeout message for Cloud instances."""
        message = IndexingDelayMessageHelper.create_timeout_message(
            operation="consistency check",
            duration=30.5,
            is_cloud=True,
        )

        assert "30.5s" in message
        assert "indexing consistency" in message
        assert "Suggestions:" in message
        assert "JIRA_CONSISTENCY_TIMEOUT" in message

    def test_create_timeout_message_server(self):
        """Test timeout message for Server/DC instances."""
        message = IndexingDelayMessageHelper.create_timeout_message(
            operation="consistency check",
            duration=30.5,
            is_cloud=False,
        )

        assert "30.5s" in message
        assert "network connection" in message
        assert "indexing" not in message

    def test_create_general_delay_warning_cloud(self):
        """Test general delay warning for Cloud instances."""
        message = IndexingDelayMessageHelper.create_general_delay_warning(
            is_cloud=True,
            operation="search",
        )

        assert "eventual consistency" in message
        assert "search operations" in message
        assert "hybrid strategy" in message

    def test_create_general_delay_warning_server(self):
        """Test general delay warning for Server/DC instances."""
        message = IndexingDelayMessageHelper.create_general_delay_warning(
            is_cloud=False,
        )

        assert message == ""


class TestConfigurationHelpers:
    """Test configuration helper functions."""

    @patch.dict('os.environ', {
        'JIRA_CONSISTENCY_STRATEGY': 'poll',
        'JIRA_CONSISTENCY_MAX_RETRIES': '3',
        'JIRA_CONSISTENCY_BASE_DELAY': '1.0',
        'JIRA_CONSISTENCY_MAX_DELAY': '10.0',
        'JIRA_CONSISTENCY_BACKOFF_FACTOR': '1.5',
        'JIRA_CONSISTENCY_TIMEOUT': '60.0',
    })
    def test_get_consistency_config_from_env(self):
        """Test getting configuration from environment variables."""
        config = get_consistency_config_from_env()

        assert config.strategy == "poll"
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.backoff_factor == 1.5
        assert config.timeout == 60.0

    @patch.dict('os.environ', {})
    def test_get_consistency_config_from_env_defaults(self):
        """Test getting configuration from environment with defaults."""
        config = get_consistency_config_from_env()

        assert config.strategy == "hybrid"  # Default updated to hybrid
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 8.0
        assert config.backoff_factor == 2.0
        assert config.timeout == 30.0

    def test_get_consistency_config_from_jira_config(self):
        """Test getting configuration from JiraConfig object."""
        # Mock JiraConfig object
        jira_config = Mock()
        jira_config.consistency_strategy = "hybrid"
        jira_config.consistency_max_retries = 7
        jira_config.consistency_base_delay = 0.2
        jira_config.consistency_max_delay = 5.0
        jira_config.consistency_backoff_factor = 1.8
        jira_config.consistency_timeout = 45.0

        config = get_consistency_config_from_jira_config(jira_config)

        assert config.strategy == "hybrid"
        assert config.max_retries == 7
        assert config.base_delay == 0.2
        assert config.max_delay == 5.0
        assert config.backoff_factor == 1.8
        assert config.timeout == 45.0