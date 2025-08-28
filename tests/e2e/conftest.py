"""
Improved pytest configuration and fixtures for MCP Atlassian E2E tests.

This module provides:
- MCP server process management
- MCP client session management with proper async handling
- Atlassian HTTP API mocking at the boundary
- Test data lifecycle management
- Environment setup and validation
"""

import asyncio
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
import requests

# Removed nest_asyncio completely to avoid conflicts with pytest-asyncio and pytest-playwright
# Both pytest-asyncio and pytest-playwright manage their own event loops
# and nest_asyncio causes "This event loop is already running" errors
# Import our custom modules
from mcp_client_fixed import MCPClientFixed
from test_fixtures import TestDataManager


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
            "jira_base_url": os.getenv("JIRA_BASE") or config["atlassian_url"],
            "confluence_base_url": os.getenv("CONFLUENCE_BASE")
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


@pytest.fixture(scope="session")
def mcp_server_process(test_config):
    """
    Start MCP server process and ensure it's responsive.

    Args:
        test_config: Test configuration with MCP URL

    Yields:
        subprocess.Popen: Running MCP server process
    """
    # Extract port from MCP URL
    mcp_url = test_config["mcp_url"]
    try:
        port = int(mcp_url.split(":")[-1].split("/")[0])
    except (ValueError, IndexError):
        port = 9001

    # Start the MCP server using the same command as package.json
    cmd = [
        "uv",
        "run",
        "mcp-atlassian",
        "--transport",
        "streamable-http",
        "--port",
        str(port),
    ]

    # Start server in project root directory
    server_process = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,  # Create new process group for clean shutdown
    )

    # Wait for server to be responsive
    max_wait = 30  # seconds
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:{port}/healthz", timeout=1)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.RequestException:
            pass
        time.sleep(0.5)

    if not server_ready:
        # Capture server output for debugging
        stdout, stderr = server_process.communicate(timeout=5)
        server_process.kill()
        pytest.fail(
            f"MCP server failed to start within {max_wait}s. Stdout: {stdout}, Stderr: {stderr}"
        )

    try:
        yield server_process
    finally:
        # Clean shutdown
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            server_process.wait(timeout=10)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.fixture(scope="function")
def mcp_client(mcp_server_process, test_config):
    """
    Create async MCP client for individual test functions.
    Skip if running visual-only tests to avoid async conflicts.

    Args:
        mcp_server_process: Running MCP server process
        test_config: Test configuration

    Returns:
        MCPClientFixed: Async MCP client instance for API tests
    """
    test_mode = os.getenv("TEST_MODE", "")
    if test_mode == "visual":
        pytest.skip("Skipping async MCP client setup for visual-only tests")


    return MCPClientFixed(test_config["mcp_url"])


@pytest.fixture(scope="function")
def sync_mcp_client(mcp_server_process, test_config):
    """
    Create synchronous MCP client wrapper for visual tests.
    Note: This is needed for visual tests and uses thread isolation to avoid event loop conflicts.

    Args:
        mcp_server_process: Running MCP server process
        test_config: Test configuration

    Returns:
        SyncMCPWrapper: Sync wrapper around MCP client for visual tests
    """
    import asyncio
    import concurrent.futures

    base_client = MCPClientFixed(test_config["mcp_url"])

    class SyncMCPWrapper:
        """Synchronous wrapper for MCP client that avoids event loop conflicts."""

        def __init__(self, async_client):
            self._async_client = async_client
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        def _run_in_thread(self, coro):
            """Run async operation in a separate thread with its own event loop."""

            def run_async():
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            future = self._executor.submit(run_async)
            return future.result(timeout=30)  # 30 second timeout

        def create_jira_issue(self, **kwargs):
            """Synchronous wrapper for create_jira_issue."""
            coro = self._async_client.create_jira_issue(**kwargs)
            return self._run_in_thread(coro)

        def create_confluence_page(self, **kwargs):
            """Synchronous wrapper for create_confluence_page."""
            coro = self._async_client.create_confluence_page(**kwargs)
            return self._run_in_thread(coro)

        def add_jira_comment(self, **kwargs):
            """Synchronous wrapper for add_jira_comment."""
            coro = self._async_client.add_jira_comment(**kwargs)
            return self._run_in_thread(coro)

        def __getattr__(self, name):
            """Delegate other sync methods directly, wrap async ones."""
            attr = getattr(self._async_client, name)
            if asyncio.iscoroutinefunction(attr):

                def sync_wrapper(*args, **kwargs):
                    coro = attr(*args, **kwargs)
                    return self._run_in_thread(coro)

                return sync_wrapper
            else:
                return attr

    return SyncMCPWrapper(base_client)


@pytest.fixture(scope="function")
def atlassian_stub():
    """
    Create Atlassian HTTP API mock for isolating MCP server tests.

    Yields:
        AtlassianStub: HTTP mock that captures outbound requests
    """
    import responses

    class AtlassianStub:
        """Mock Atlassian HTTP API responses."""

        def __init__(self):
            self.responses = responses.RequestsMock(assert_all_requests_are_fired=False)
            self.call_log = []

        def __enter__(self):
            self.responses.start()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.responses.stop()
            self.responses.reset()

        def stub_jira_search(self, jql: str, results: list[dict], total: int = None):
            """Stub Jira search API."""
            if total is None:
                total = len(results)

            response_data = {
                "issues": results,
                "total": total,
                "startAt": 0,
                "maxResults": len(results),
            }

            # Use a simple URL pattern instead of complex matchers
            self.responses.add(
                responses.POST,
                "https://test.atlassian.net/rest/api/3/search",
                json=response_data,
                status=200,
            )

        def stub_jira_create_issue(self, project_key: str, returns: dict):
            """Stub Jira issue creation."""

            def callback(request):
                body = json.loads(request.body)
                self.call_log.append(("POST", request.url, body))
                return (201, {}, json.dumps(returns))

            self.responses.add_callback(
                responses.POST,
                f"https://{project_key.lower()}.atlassian.net/rest/api/3/issue",
                callback=callback,
            )

        def stub_confluence_create_page(self, adf: dict, returns: dict):
            """Stub Confluence page creation."""

            def callback(request):
                body = json.loads(request.body)
                self.call_log.append(("POST", request.url, body))
                return (201, {}, json.dumps(returns))

            self.responses.add_callback(
                responses.POST,
                "https://test.atlassian.net/wiki/api/v2/pages",
                callback=callback,
            )

        def assert_called_once_with(
            self, method: str, url_fragment: str, json_contains: dict = None
        ):
            """Assert that a specific API call was made."""
            matching_calls = [
                (m, u, b)
                for m, u, b in self.call_log
                if m == method and url_fragment in u
            ]

            assert len(matching_calls) == 1, (
                f"Expected 1 call matching {method} {url_fragment}, got {len(matching_calls)}"
            )

            if json_contains:
                _, _, body = matching_calls[0]
                for key, expected_value in json_contains.items():
                    assert key in body, f"Expected key '{key}' in request body"
                    assert body[key] == expected_value, (
                        f"Expected {key}={expected_value}, got {body[key]}"
                    )

    with AtlassianStub() as stub:
        yield stub


@pytest.fixture(scope="function")
def sample_test_data():
    """
    Provide sample test data for consistent testing.

    Returns:
        Dict containing various test content and data
    """
    return {
        "jira_issue": {
            "key": "TEST-123",
            "id": "12345",
            "fields": {
                "summary": "Test Issue",
                "description": "Test description",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
            },
        },
        "confluence_page": {
            "id": "67890",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Test content</p>"}},
            "space": {"key": "TEST"},
        },
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
        "adf_content": """# Advanced ADF Test Content

## ADF-Specific Elements

### Panels
:::panel type="info"
**Information Panel**: This tests ADF-specific formatting.
:::

### Status Badges
Progress: {status:color=blue}In Progress{/status}
Complete: {status:color=green}Done{/status}

### Dates
Created: {date:2025-01-20}
Due: {date:2025-02-15}
""",
    }


# Test markers for pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "mcp: MCP server contract tests (default, fast)")
    config.addinivalue_line(
        "markers", "atlassian_stub: Tests with mocked Atlassian API responses"
    )
    config.addinivalue_line(
        "markers",
        "ui_smoke: Optional browser-based visual verification tests (excluded by default)",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add mcp marker to non-visual tests by default
        if "ui_smoke" not in [mark.name for mark in item.iter_markers()]:
            item.add_marker(pytest.mark.mcp)

        # Add atlassian_stub marker if atlassian_stub fixture is used
        if "atlassian_stub" in item.fixturenames:
            item.add_marker(pytest.mark.atlassian_stub)

        # Add markers based on file names
        if "adf" in item.module.__name__:
            item.add_marker(pytest.mark.adf)
        if "jira" in item.module.__name__:
            item.add_marker(pytest.mark.jira)
        if "confluence" in item.module.__name__:
            item.add_marker(pytest.mark.confluence)


# No custom event_loop fixture - let pytest-asyncio and playwright handle their own loops


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


@pytest.fixture(scope="function")
def test_data_manager(mcp_client, test_config):
    """
    Create test data manager for individual test functions.

    Args:
        mcp_client: MCP client instance
        test_config: Test configuration

    Yields:
        TestDataManager: Test data management instance
    """
    import concurrent.futures

    def _run_async_cleanup(manager):
        """Run async cleanup in separate thread to avoid event loop conflicts."""

        def run_cleanup():
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(manager.cleanup())
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_cleanup)
            return future.result(timeout=30)  # 30 second timeout

    manager = TestDataManager(mcp_client, test_config)
    try:
        yield manager
    finally:
        # Cleanup after test
        try:
            cleanup_summary = _run_async_cleanup(manager)
            if cleanup_summary:
                total_deleted = cleanup_summary.get(
                    "issues_deleted", 0
                ) + cleanup_summary.get("pages_deleted", 0)
                if total_deleted > 0:
                    print(
                        f"\nTest cleanup completed: {total_deleted} resources deleted"
                    )
                if cleanup_summary.get("errors"):
                    print(f"Cleanup errors: {cleanup_summary['errors']}")
        except Exception as e:
            print(f"Error during test cleanup: {e}")


# === Playwright Fixtures for Visual Tests ===


@pytest.fixture(scope="session")
def browser_context_args(test_config):
    """
    Configure browser context for visual verification tests.
    Skip if running MCP-only tests to avoid Playwright dependencies.

    Args:
        test_config: Test configuration

    Returns:
        Dict: Browser context configuration
    """
    test_mode = os.getenv("TEST_MODE", "")
    if test_mode == "mcp":
        pytest.skip("Skipping browser context setup for MCP-only tests")

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
    Skip if running MCP-only tests to avoid Playwright dependencies.

    Args:
        page: Playwright page fixture
        test_config: Test configuration

    Yields:
        Page: Authenticated Playwright page
    """
    test_mode = os.getenv("TEST_MODE", "")
    if test_mode == "mcp":
        pytest.skip("Skipping Playwright page setup for MCP-only tests")

    # If no storage state, may need manual authentication
    storage_state_path = Path(__file__).parent / "storageState.json"
    if not storage_state_path.exists():
        pytest.skip("No authentication state found. Run 'npm run auth' first.")

    yield page
