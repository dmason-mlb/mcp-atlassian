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
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Generator, AsyncGenerator, List
import pytest
import signal
import requests

# Import our custom modules
from mcp_client_fixed import MCPClientFixed


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
                line = line[len("export "):].lstrip()
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
def test_config() -> Dict[str, str]:
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
    config.update({
        "mcp_url": os.getenv("MCP_URL", "http://localhost:9001/mcp"),
        "jira_base_url": os.getenv("JIRA_BASE") or config["atlassian_url"],
        "confluence_base_url": os.getenv("CONFLUENCE_BASE") or f"{config['atlassian_url'].rstrip('/')}/wiki",
        "test_label": os.getenv("TEST_LABEL", f"mcp-test-{os.getpid()}"),
    })
    
    # Authentication check
    auth_vars = [
        "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "ATLASSIAN_PAT",
        "JIRA_USERNAME", "JIRA_API_TOKEN", "JIRA_PERSONAL_TOKEN",
        "CONFLUENCE_USERNAME", "CONFLUENCE_API_TOKEN", "CONFLUENCE_PERSONAL_TOKEN",
        "ATLASSIAN_OAUTH_CLIENT_ID", "ATLASSIAN_OAUTH_CLIENT_SECRET"
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
        "uv", "run", "mcp-atlassian", 
        "--transport", "streamable-http", 
        "--port", str(port)
    ]
    
    # Start server in project root directory
    server_process = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid  # Create new process group for clean shutdown
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
        pytest.fail(f"MCP server failed to start within {max_wait}s. Stdout: {stdout}, Stderr: {stderr}")
    
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
    Create MCP client for individual test functions.
    
    Args:
        mcp_server_process: Running MCP server process
        test_config: Test configuration
        
    Returns:
        MCPClientFixed: MCP client instance
    """
    client = MCPClientFixed(test_config["mcp_url"])
    return client


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
            
        def stub_jira_search(self, jql: str, results: List[Dict], total: int = None):
            """Stub Jira search API."""
            if total is None:
                total = len(results)
                
            response_data = {
                "issues": results,
                "total": total,
                "startAt": 0,
                "maxResults": len(results)
            }
            
            # Use a simple URL pattern instead of complex matchers
            self.responses.add(
                responses.POST,
                "https://test.atlassian.net/rest/api/3/search",
                json=response_data,
                status=200
            )
            
        def stub_jira_create_issue(self, project_key: str, returns: Dict):
            """Stub Jira issue creation."""
            def callback(request):
                body = json.loads(request.body)
                self.call_log.append(("POST", request.url, body))
                return (201, {}, json.dumps(returns))
                
            self.responses.add_callback(
                responses.POST,
                f"https://{project_key.lower()}.atlassian.net/rest/api/3/issue",
                callback=callback
            )
            
        def stub_confluence_create_page(self, adf: Dict, returns: Dict):
            """Stub Confluence page creation."""
            def callback(request):
                body = json.loads(request.body)
                self.call_log.append(("POST", request.url, body))
                return (201, {}, json.dumps(returns))
                
            self.responses.add_callback(
                responses.POST,
                "https://test.atlassian.net/wiki/api/v2/pages",
                callback=callback
            )
            
        def assert_called_once_with(self, method: str, url_fragment: str, json_contains: Dict = None):
            """Assert that a specific API call was made."""
            matching_calls = [
                (m, u, b) for m, u, b in self.call_log 
                if m == method and url_fragment in u
            ]
            
            assert len(matching_calls) == 1, f"Expected 1 call matching {method} {url_fragment}, got {len(matching_calls)}"
            
            if json_contains:
                _, _, body = matching_calls[0]
                for key, expected_value in json_contains.items():
                    assert key in body, f"Expected key '{key}' in request body"
                    assert body[key] == expected_value, f"Expected {key}={expected_value}, got {body[key]}"
    
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
                "priority": {"name": "Medium"}
            }
        },
        
        "confluence_page": {
            "id": "67890",
            "title": "Test Page", 
            "body": {
                "storage": {
                    "value": "<p>Test content</p>"
                }
            },
            "space": {"key": "TEST"}
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
    config.addinivalue_line(
        "markers", "mcp: MCP server contract tests (default, fast)"
    )
    config.addinivalue_line(
        "markers", "atlassian_stub: Tests with mocked Atlassian API responses"
    )
    config.addinivalue_line(
        "markers", "ui_smoke: Optional browser-based visual verification tests (excluded by default)"
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


def extract_json_from_result(result: Any) -> Dict:
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