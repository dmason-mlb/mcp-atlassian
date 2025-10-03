"""Configuration management for real API integration tests."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class JiraTestConfig:
    """Configuration for Jira testing."""
    url: str
    username: Optional[str] = None
    api_token: Optional[str] = None
    pat: Optional[str] = None
    project_key: str = "TEST"
    issue_type: str = "Task"
    epic_key: Optional[str] = None
    existing_issue: Optional[str] = None
    assignee: Optional[str] = None
    component: Optional[str] = None


@dataclass
class ConfluenceTestConfig:
    """Configuration for Confluence testing."""
    url: str
    username: Optional[str] = None
    api_token: Optional[str] = None
    pat: Optional[str] = None
    space_key: str = "TEST"
    parent_page_id: Optional[str] = None
    existing_page_id: Optional[str] = None


@dataclass
class TestEnvironmentConfig:
    """Overall test environment configuration."""
    enabled: bool = False
    timeouts: Dict[str, int] = None
    resource_prefix: str = "MCPTEST_"
    auto_cleanup: bool = True
    max_test_resources: int = 50
    cleanup_on_start: bool = True
    cleanup_on_end: bool = True
    cleanup_on_failure: bool = False

    def __post_init__(self):
        if self.timeouts is None:
            self.timeouts = {"default": 30, "upload": 120, "batch": 180}


@dataclass
class IntegrationTestConfig:
    """Complete integration test configuration."""
    test_environment: TestEnvironmentConfig
    jira: JiraTestConfig
    confluence: ConfluenceTestConfig


class ConfigurationError(Exception):
    """Raised when test configuration is invalid or missing."""
    pass


class TestConfigLoader:
    """Loads and validates test configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent / "test_config.yaml"
        self._config: Optional[IntegrationTestConfig] = None
        self._load_env_file()

    def _load_env_file(self) -> None:
        """Load environment variables from .env file if it exists."""
        # Look for .env file in project root
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            logger.info(f"Loading environment variables from {env_file}")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Only set if not already in environment (don't override)
                            if key not in os.environ:
                                os.environ[key] = value
            except Exception as e:
                logger.warning(f"Could not load .env file: {e}")
        else:
            logger.debug(f"No .env file found at {env_file}")

    def load_config(self, environment: str = "development") -> IntegrationTestConfig:
        """Load configuration for the specified environment."""
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")

        # Apply environment-specific overrides
        if environment in raw_config.get("environments", {}):
            env_overrides = raw_config["environments"][environment]
            raw_config = self._merge_configs(raw_config, env_overrides)

        # Expand environment variables
        expanded_config = self._expand_environment_variables(raw_config)

        # Validate and create config objects
        return self._create_config_objects(expanded_config)

    def _merge_configs(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        for key, value in overrides.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _expand_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively expand environment variables in configuration."""
        def expand_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                expanded = os.getenv(env_var)

                # Add fallback logic for shared Atlassian credentials
                if expanded is None:
                    expanded = self._get_fallback_value(env_var)

                if expanded is None:
                    logger.warning(f"Environment variable {env_var} not set and no fallback available")
                return expanded
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            else:
                return value

        return expand_value(config)

    def _get_fallback_value(self, env_var: str) -> Optional[str]:
        """Get fallback value for environment variables using shared Atlassian credentials."""
        fallback_mapping = {
            # Jira URL fallbacks
            "JIRA_TEST_URL": os.getenv("ATLASSIAN_URL"),
            "JIRA_URL": os.getenv("ATLASSIAN_URL"),

            # Confluence URL fallbacks (append /wiki to base URL)
            "CONFLUENCE_TEST_URL": self._get_confluence_url_fallback(),
            "CONFLUENCE_URL": self._get_confluence_url_fallback(),

            # Username fallbacks
            "JIRA_TEST_USERNAME": os.getenv("ATLASSIAN_EMAIL"),
            "JIRA_USERNAME": os.getenv("ATLASSIAN_EMAIL"),
            "CONFLUENCE_TEST_USERNAME": os.getenv("ATLASSIAN_EMAIL"),
            "CONFLUENCE_USERNAME": os.getenv("ATLASSIAN_EMAIL"),

            # API Token fallbacks
            "JIRA_TEST_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
            "JIRA_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
            "CONFLUENCE_TEST_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),
            "CONFLUENCE_API_TOKEN": os.getenv("ATLASSIAN_API_TOKEN"),

            # Project and space fallbacks
            "JIRA_TEST_PROJECT": os.getenv("JIRA_PROJECT"),
            "CONFLUENCE_TEST_SPACE": os.getenv("CONFLUENCE_SPACE"),
        }

        fallback = fallback_mapping.get(env_var)
        if fallback:
            logger.info(f"Using fallback value for {env_var}")
        return fallback

    def _get_confluence_url_fallback(self) -> Optional[str]:
        """Get Confluence URL by appending /wiki to ATLASSIAN_URL."""
        base_url = os.getenv("ATLASSIAN_URL")
        if base_url:
            # Ensure we don't double-append /wiki
            if base_url.endswith("/wiki"):
                return base_url
            else:
                return f"{base_url.rstrip('/')}/wiki"
        return None

    def _create_config_objects(self, config: Dict[str, Any]) -> IntegrationTestConfig:
        """Create typed configuration objects from raw configuration."""
        try:
            # Test environment config
            test_env_data = config.get("test_environment", {})
            test_data_mgmt = config.get("test_data_management", {})
            test_env_config = TestEnvironmentConfig(
                enabled=test_env_data.get("enabled", False),
                timeouts=test_env_data.get("timeouts", {}),
                resource_prefix=test_data_mgmt.get("resource_prefix", "MCPTEST_"),
                auto_cleanup=test_data_mgmt.get("auto_cleanup", True),
                max_test_resources=test_data_mgmt.get("max_test_resources", 50),
                cleanup_on_start=test_data_mgmt.get("cleanup_on_start", True),
                cleanup_on_end=test_data_mgmt.get("cleanup_on_end", True),
                cleanup_on_failure=test_data_mgmt.get("cleanup_on_failure", False),
            )

            # Jira config
            jira_data = config.get("jira", {})
            jira_auth = jira_data.get("auth", {})
            jira_test_data = jira_data.get("test_data", {})
            jira_config = JiraTestConfig(
                url=jira_data.get("url"),
                username=jira_auth.get("username"),
                api_token=jira_auth.get("api_token"),
                pat=jira_auth.get("pat"),
                project_key=jira_test_data.get("project_key", "TEST"),
                issue_type=jira_test_data.get("issue_type", "Task"),
                epic_key=jira_test_data.get("epic_key"),
                existing_issue=jira_test_data.get("existing_issue"),
                assignee=jira_test_data.get("assignee"),
                component=jira_test_data.get("component"),
            )

            # Confluence config
            confluence_data = config.get("confluence", {})
            confluence_auth = confluence_data.get("auth", {})
            confluence_test_data = confluence_data.get("test_data", {})
            confluence_config = ConfluenceTestConfig(
                url=confluence_data.get("url"),
                username=confluence_auth.get("username"),
                api_token=confluence_auth.get("api_token"),
                pat=confluence_auth.get("pat"),
                space_key=confluence_test_data.get("space_key", "TEST"),
                parent_page_id=confluence_test_data.get("parent_page_id"),
                existing_page_id=confluence_test_data.get("existing_page_id"),
            )

            return IntegrationTestConfig(
                test_environment=test_env_config,
                jira=jira_config,
                confluence=confluence_config,
            )

        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}")

    def validate_config(self, config: IntegrationTestConfig) -> None:
        """Validate that configuration is complete and valid."""
        errors = []

        if not config.test_environment.enabled:
            errors.append("Test environment is not enabled. Set test_environment.enabled=true")

        # Validate Jira config
        if not config.jira.url:
            errors.append("Jira URL is required")

        if not (config.jira.api_token or config.jira.pat):
            errors.append("Jira authentication required (api_token or pat)")

        if config.jira.api_token and not config.jira.username:
            errors.append("Jira username required when using api_token")

        # Validate Confluence config
        if not config.confluence.url:
            errors.append("Confluence URL is required")

        if not (config.confluence.api_token or config.confluence.pat):
            errors.append("Confluence authentication required (api_token or pat)")

        if config.confluence.api_token and not config.confluence.username:
            errors.append("Confluence username required when using api_token")

        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))


def get_test_config(environment: str = None) -> IntegrationTestConfig:
    """Get test configuration for the specified environment."""
    if environment is None:
        environment = os.getenv("TEST_ENVIRONMENT", "development")

    loader = TestConfigLoader()
    config = loader.load_config(environment)
    loader.validate_config(config)
    return config


def is_real_api_testing_enabled() -> bool:
    """Check if real API testing is enabled."""
    try:
        config = get_test_config()
        return config.test_environment.enabled
    except ConfigurationError:
        return False


def skip_if_no_real_api(reason: str = "Real API testing not configured"):
    """Decorator to skip tests if real API testing is not enabled."""
    import pytest

    return pytest.mark.skipif(
        not is_real_api_testing_enabled(),
        reason=reason
    )