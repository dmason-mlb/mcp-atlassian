"""Configuration for integration tests."""

import pytest
import os


def pytest_configure(config):
    """Add integration and real API markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as requiring integration with real services"
    )
    config.addinivalue_line(
        "markers", "real_api: marks tests as requiring real API execution (deselect with '-m \"not real_api\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless explicitly requested and handle real API mode."""
    execution_mode = os.getenv("TEST_EXECUTION_MODE", "dry_run").lower()

    if not config.getoption("--integration", default=False):
        # Skip integration tests by default
        skip_integration = pytest.mark.skip(reason="Need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    # Skip real_api tests if not in real or hybrid mode
    if execution_mode == "dry_run":
        skip_real_api = pytest.mark.skip(reason="Real API testing disabled (TEST_EXECUTION_MODE=dry_run)")
        for item in items:
            if "real_api" in item.keywords:
                item.add_marker(skip_real_api)


def pytest_addoption(parser):
    """Add integration option to pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


@pytest.fixture(scope="session")
def execution_mode():
    """Determine execution mode for tests.

    Returns:
        str: "real", "dry_run", or "hybrid" based on environment
    """
    # Check environment variable
    mode = os.getenv("TEST_EXECUTION_MODE", "dry_run").lower()

    # Validate mode
    valid_modes = ["real", "dry_run", "hybrid"]
    if mode not in valid_modes:
        mode = "dry_run"

    return mode


@pytest.fixture(scope="session")
def real_api_enabled(execution_mode):
    """Check if real API testing is enabled."""
    return execution_mode in ["real", "hybrid"]
