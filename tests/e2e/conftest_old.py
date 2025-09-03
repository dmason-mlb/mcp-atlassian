"""
Pytest configuration and fixtures for MCP Atlassian E2E tests.

This module provides:
- Environment setup and validation
- MCP client session management
- Test data lifecycle management
- Browser setup for visual verification tests
- Shared utilities and fixtures
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

# Note: Removed nest_asyncio.apply() to fix Playwright event loop conflicts
# Import our custom modules
from test_fixtures import TestDataManager


# Load environment from project root
def load_env_file(env_path: Path) -> None:
    """Load environment variables from .env file."""
    if not env_path.exists():
        return

    try:
        # Try python-dotenv if available
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=False)
            return
        except ImportError:
            pass

        # Fallback to manual parsing
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                # Drop inline comments
                if " #" in val:
                    val = val.split(" #", 1)[0]
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except Exception:
        pass


# Load project root .env
ROOT_DIR = Path(__file__).resolve().parents[2]
load_env_file(ROOT_DIR / ".env")

# Test configuration constants
ART_DIR = ROOT_DIR / "tests" / "e2e" / ".artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)

# Let pytest-asyncio handle event loop creation automatically


@pytest.fixture(scope="session")
def test_config() -> dict[str, str]:
    """
    Validate and provide test configuration from environment variables.

    Returns:
        Dict containing validated environment configuration

    Raises:
        pytest.skip: If required environment variables are missing
    """

    def required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            pytest.skip(f"Missing required environment variable: {name}")
        return value

    # Required variables
    config = {
        "atlassian_url": required("ATLASSIAN_URL"),
        "jira_project": required("JIRA_PROJECT"),
        "confluence_space": required("CONFLUENCE_SPACE"),
    }

    # Optional variables with defaults
    config.update(
        {
            "mcp_url": os.getenv("MCP_URL", "http://localhost:9001/mcp"),
            "jira_base": os.getenv("JIRA_BASE") or config["atlassian_url"],
            "confluence_base": os.getenv("CONFLUENCE_BASE")
            or f"{config['atlassian_url'].rstrip('/')}/wiki",
            "test_label": os.getenv("TEST_LABEL", f"mcp-test-{os.getpid()}"),
        }
    )

    # Authentication check
    auth_vars = [
        "ATLASSIAN_EMAIL",
        "ATLASSIAN_API_TOKEN",
        "ATLASSIAN_PAT",
        "JIRA_USERNAME",
        "JIRA_API_TOKEN",
        "JIRA_PERSONAL_TOKEN",
        "CONFLUENCE_USERNAME",
        "CONFLUENCE_API_TOKEN",
        "CONFLUENCE_PERSONAL_TOKEN",
        "ATLASSIAN_OAUTH_CLIENT_ID",
        "ATLASSIAN_OAUTH_CLIENT_SECRET",
    ]

    has_auth = any(os.getenv(var) for var in auth_vars)
    if not has_auth:
        pytest.skip("No authentication variables found")

    return config


@pytest.fixture(scope="function")
def mcp_client(test_config):
    """
    Create MCP client using the same pattern as the working seed script.

    Args:
        test_config: Test configuration from environment

    Returns:
        MCPClientFixed: MCP client instance that creates sessions per operation
    """
    from mcp_client_fixed import MCPClientFixed

    client = MCPClientFixed(test_config["mcp_url"])
    return client


@pytest.fixture(scope="function")
async def test_data_manager(mcp_client, test_config):
    """
    Create test data manager for individual test functions.

    Args:
        mcp_client: MCP client instance
        test_config: Test configuration

    Yields:
        TestDataManager: Test data management instance
    """

    manager = TestDataManager(mcp_client, test_config)
    yield manager

    # Cleanup after test
    await manager.cleanup()


@pytest.fixture
def test_content_fixtures():
    """
    Provide standard test content fixtures for consistent testing.

    Returns:
        Dict containing various test content templates
    """
    return {
        "basic_markdown": """# Test Content

This is **basic markdown** content for testing.

## Features
- Basic text formatting
- Lists and structure
- Code blocks

```python
def test_function():
    return "Hello MCP"
```

> This is a blockquote for testing.
""",
        "rich_adf_content": """# Advanced ADF Test Content

## ADF-Specific Elements

### Panels
:::panel type="info"
**Information Panel**: This tests ADF-specific formatting.
:::

:::panel type="warning"
**Warning Panel**: Testing with *italic* and **bold** text.
:::

### Status Badges
Progress: {status:color=blue}In Progress{/status}
Complete: {status:color=green}Done{/status}
Blocked: {status:color=red}Blocked{/status}

### Dates
Created: {date:2025-01-20}
Due: {date:2025-02-15}

### Expand Sections
:::expand title="Click to expand details"
This content is inside an expandable section.

#### Nested Content
- Item 1
- Item 2

```javascript
function expandTest() {
  console.log('Expand section test');
}
```
:::

### Tables with ADF Elements
| Feature | Status | Notes |
|---------|--------|-------|
| Creation | {status:color=green}Complete{/status} | Working |
| Updates | {status:color=blue}Testing{/status} | In progress |
| ADF | {status:color=yellow}Review{/status} | Needs validation |
""",
        "complex_nested_content": """# Complex Nested Test

## Multi-level Content

1. **Step 1**: Initial setup
   :::panel type="note"
   Configure all settings before proceeding.
   :::

2. **Step 2**: Execute process
   ```bash
   npm run test
   ```
   Status: {status:color=blue}Running{/status}

3. **Step 3**: Validate results
   :::expand title="Expected Results"
   - All tests pass
   - No formatting issues
   - ADF elements render correctly
   :::
""",
    }


# Browser-based fixtures for visual verification tests
@pytest.fixture(scope="session")
def browser_context_args(test_config):
    """
    Configure browser context for visual verification tests.

    Args:
        test_config: Test configuration

    Returns:
        Dict: Browser context configuration
    """
    storage_state_path = Path(__file__).parent / "storageState.json"

    context_args = {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

    # Use saved authentication state if available
    if storage_state_path.exists():
        context_args["storage_state"] = str(storage_state_path)

    return context_args


@pytest.fixture(scope="function")
def authenticated_page(page, test_config):
    """
    Provide an authenticated page for visual verification tests.

    Args:
        page: Playwright page fixture
        test_config: Test configuration

    Yields:
        Page: Authenticated Playwright page
    """
    # If no storage state, may need manual authentication
    storage_state_path = Path(__file__).parent / "storageState.json"
    if not storage_state_path.exists():
        pytest.skip("No authentication state found. Run 'npm run auth' first.")

    yield page


@pytest.fixture(scope="function")
def screenshot_manager():
    """
    Manage screenshot capture and comparison for visual tests.

    Yields:
        ScreenshotManager: Screenshot management utilities
    """

    class ScreenshotManager:
        def __init__(self):
            self.screenshots_dir = ART_DIR / "screenshots"
            self.screenshots_dir.mkdir(exist_ok=True)

        def capture_element(self, page, selector: str, name: str) -> Path:
            """Capture screenshot of specific element."""
            element = page.locator(selector)
            screenshot_path = self.screenshots_dir / f"{name}.png"
            element.screenshot(path=screenshot_path)
            return screenshot_path

        def capture_page(self, page, name: str) -> Path:
            """Capture full page screenshot."""
            screenshot_path = self.screenshots_dir / f"{name}_full.png"
            page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path

    yield ScreenshotManager()


# Utility functions
def extract_json_from_result(result: Any) -> dict:
    """
    Extract JSON object from MCP tool result.

    Args:
        result: MCP tool result

    Returns:
        Dict: Extracted JSON data
    """
    if isinstance(result, dict):
        return result

    try:
        # FastMCP ToolResult shape
        content = getattr(result, "content", None) or result.get("content")
        if isinstance(content, list) and content:
            for item in content:
                text = (
                    item.get("text")
                    if isinstance(item, dict)
                    else getattr(item, "text", None)
                )
                if text:
                    try:
                        return json.loads(text)
                    except Exception:
                        continue
    except Exception:
        pass

    # Fallback
    try:
        return json.loads(str(result))
    except Exception:
        return {}


# Test markers for pytest-xdist compatibility
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "api: API-based MCP tool tests (fast)")
    config.addinivalue_line(
        "markers", "visual: Browser-based visual verification tests (slower)"
    )
    config.addinivalue_line("markers", "adf: ADF formatting and conversion tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add api marker to non-visual tests by default
        if "visual" not in [mark.name for mark in item.iter_markers()]:
            item.add_marker(pytest.mark.api)

        # Add markers based on file names
        if "adf" in item.module.__name__:
            item.add_marker(pytest.mark.adf)
        if "jira" in item.module.__name__:
            item.add_marker(pytest.mark.jira)
        if "confluence" in item.module.__name__:
            item.add_marker(pytest.mark.confluence)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test execution status for screenshot capture."""
    outcome = yield
    rep = outcome.get_result()

    # Store test result on the item for later use
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def auto_screenshot_capture(request):
    """
    Automatically capture screenshots for all tests that have access to a page fixture.
    Captures screenshots regardless of test outcome (pass/fail/skip).
    """
    # Setup
    screenshots_dir = ART_DIR / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = request.node.name.replace("::", "_").replace("[", "_").replace("]", "")

    yield

    # Capture screenshot after test completion (only if page fixture exists and is valid)
    try:
        # Try to get page fixture, but don't fail if it doesn't exist
        page = request.getfixturevalue("page")
        if page is None:
            return

        # Determine test outcome
        outcome = "unknown"
        if hasattr(request.node, "rep_call"):
            if request.node.rep_call.passed:
                outcome = "passed"
            elif request.node.rep_call.failed:
                outcome = "failed"
            elif request.node.rep_call.skipped:
                outcome = "skipped"

        # Capture screenshot with timeout protection
        screenshot_name = f"{test_name}_{timestamp}_{outcome}.png"
        screenshot_path = screenshots_dir / screenshot_name

        # Use synchronous screenshot method to avoid event loop issues
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot captured: {screenshot_path}")

    except Exception as e:
        # Silently ignore screenshot failures to avoid affecting test results
        print(f"Failed to capture screenshot for {test_name}: {e}")
