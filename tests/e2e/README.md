# E2E Testing for MCP Atlassian

End-to-end tests for the MCP Atlassian server using pytest and MCP tool calls. These tests validate MCP tool functionality through direct API interactions and browser-based visual verification for ADF (Atlassian Document Format) rendering.

## Architecture

This test suite uses a **hybrid approach**:

- **API-first testing**: Direct MCP tool calls via streamable HTTP transport for fast, reliable validation
- **Browser-based visual verification**: Playwright integration for ADF formatting validation in actual Atlassian interfaces
- **Resource tracking**: Automatic cleanup of created test resources
- **Comprehensive coverage**: Tests across Jira issues, Confluence pages, search, cross-service integration, and error handling

## Prerequisites

- **Python 3.10+** with `uv` for package management
- **Node.js 18+** for Playwright browser automation (visual tests only)
- **Access to Atlassian instance** (Cloud or Server/DC)
- **Valid MCP server configuration** in repo root `.env` file

## Quick Start

### From Repo Root (Required Setup)
```bash
# 1. Ensure dependencies are installed at repo level
uv sync --frozen --all-extras --dev

# 2. Configure environment variables in repo root .env
cp .env.example .env
# Edit .env with your Atlassian URLs and credentials
```

### From This Directory
```bash
# 3. Install test dependencies
npm run prep

# 4. Set up browser authentication for visual tests (required once)
npm run auth

# 5. Create test data
npm run seed

# 6. Run tests
npm run test

# 7. Clean up when done
npm run clean
```

## Available Scripts

| Script | Command | Description | When to Use |
|--------|---------|-------------|-------------|
| **prep** | `playwright install --with-deps && pip install -r requirements-test.txt` | Install Playwright browsers and Python dependencies | First time setup, CI environments |
| **start-server** | `cd ../.. && uv run mcp-atlassian --transport streamable-http --port 9001` | Start MCP server for development | When debugging test issues |
| **seed** | `./seed-with-server.sh` | Create test data with server auto-start/stop | Before running tests |
| **seed:direct** | `uv run python seed/seed.py` | Create test data (requires server running) | When server is already running |
| **test** | `pytest -v` | Run all tests | Main test execution |
| **test:api** | `pytest -v -m api` | Run API-only tests (fast) | Quick validation, CI |
| **test:visual** | `pytest -v -m visual --browser chromium` | Run browser-based visual tests | ADF formatting validation |
| **test:adf** | `pytest -v -m adf` | Run ADF formatting tests | ADF-specific validation |
| **test:jira** | `pytest -v -m jira` | Run Jira-specific tests | Jira functionality testing |
| **test:confluence** | `pytest -v -m confluence` | Run Confluence-specific tests | Confluence functionality testing |
| **test:parallel** | `pytest -v -n auto` | Run tests in parallel | Faster execution |
| **clean** | `uv run python cleanup/cleanup.py` | Remove test data and artifacts | After testing, CI cleanup |
| **auth** | `node manual-login.js` | Interactive authentication setup | Initial setup, auth refresh |
| **auth-setup** | `node manual-login.js` | Interactive authentication setup (alias) | Alternative to auth command |
| **test:smoke** | `pytest -v -m smoke` | Run smoke tests for basic functionality | Quick health checks |
| **test:slow** | `pytest -v -m slow` | Run longer-running tests | Comprehensive validation |

## Test Categories

### Test Markers
Tests are organized using pytest markers defined in `pytest.ini`:

- `@pytest.mark.api` - API-based MCP tool tests (fast)
- `@pytest.mark.visual` - Browser-based visual verification tests (slower)
- `@pytest.mark.adf` - ADF formatting and conversion tests
- `@pytest.mark.jira` - Jira-specific functionality
- `@pytest.mark.confluence` - Confluence-specific functionality
- `@pytest.mark.integration` - Cross-service integration tests
- `@pytest.mark.error_handling` - Error scenario tests
- `@pytest.mark.performance` - Performance and bulk operation tests
- `@pytest.mark.smoke` - Smoke tests for basic functionality
- `@pytest.mark.slow` - Tests that take longer to run

### Test Organization

| Test File | Focus | Test Types |
|-----------|-------|------------|
| `test_connectivity.py` | Basic MCP server connection and tool availability | API |
| `test_jira_issues.py` | Jira issue CRUD, comments, transitions, linking | API |
| `test_confluence_pages.py` | Confluence page CRUD, comments, labels, hierarchy | API |
| `test_adf_visual.py` | ADF formatting visual verification | Visual + ADF |
| `test_search_functionality.py` | JQL queries, CQL searches, field searches | API |
| `test_integration_error_handling.py` | Cross-service integration, error handling | API |

## Authentication Setup

**Required for visual tests:** The `npm run auth` command opens a browser for manual login:

1. Run the authentication command:
   ```bash
   npm run auth
   ```

2. **Browser opens automatically** - Log in to your Atlassian account

3. **Wait for dashboard** to fully load (important!)

4. **Press ENTER** in the terminal when ready

5. **Authentication saved** to `storageState.json` for all visual tests

The authentication state persists across test runs. Re-run `npm run auth` if you encounter login redirects during visual tests.

## Environment Configuration

Tests load environment variables from the **repo root `.env` file**:

| Variable | Description | Example |
|----------|-------------|---------|
| `ATLASSIAN_URL` | Your Atlassian instance base URL | `https://company.atlassian.net` |
| `JIRA_PROJECT` | Project key for test issues | `FTEST` |
| `CONFLUENCE_SPACE` | Space ID for test pages | `655361` |
| `MCP_URL` | MCP server URL for tests | `http://localhost:9001` |

## Test Configuration

The test suite is configured through `pytest.ini` with the following key settings:

### Required Plugins
- **pytest-asyncio**: Enables async test functions and fixtures
- **pytest-playwright**: Browser automation integration
- **pytest-xdist**: Parallel test execution support

### Browser Configuration  
- **Default browser**: Chromium (specified in pytest.ini)
- **Asyncio mode**: Automatic async handling for all tests
- **Visual testing**: Playwright integration with screenshot capabilities

### Test Output
- **Strict markers**: All test markers must be defined
- **Duration tracking**: Shows 10 slowest tests after each run  
- **Short traceback**: Concise error output for faster debugging

## Test Structure

### Base Test Classes

- **`MCPBaseTest`** - Common functionality for all tests
  - Resource tracking and cleanup
  - Response validation utilities
  - Test data generation helpers
  - Error assertion patterns

- **`MCPJiraTest`** - Jira-specific test base
  - Issue creation and management
  - Jira-specific validation patterns

- **`MCPConfluenceTest`** - Confluence-specific test base
  - Page creation and management
  - Confluence-specific validation patterns

### Validation Utilities

- **`validators.py`** - API response validation
  - ADF structure validation
  - Response format checking
  - Error response detection

- **`visual_validators.py`** - Browser-based validation
  - ADF element visual verification
  - Screenshot comparison capabilities
  - Interactive element validation

### Test Data Management

- **`test_fixtures.py`** - Test data templates and management
  - Rich ADF content templates
  - Resource lifecycle tracking
  - Cleanup coordination

- **`conftest.py`** - Pytest configuration and fixtures
  - MCP client session management
  - Browser context configuration
  - Environment validation

## Development Workflow

### Running Tests During Development

```bash
# Quick API-only tests (fast feedback)
npm run test:api

# Visual ADF validation (slower)
npm run test:visual

# Specific test categories
npm run test:jira
npm run test:confluence
npm run test:adf
npm run test:smoke

# Run single test file
pytest -v tests/test_connectivity.py

# Run specific test method
pytest -v tests/test_jira_issues.py::TestJiraIssueCreation::test_create_basic_task

# Run with verbose output and no capture
pytest -v -s tests/test_connectivity.py
```

### Debugging Tests

```bash
# Run with Python debugger
pytest -v --pdb tests/test_connectivity.py

# Run visual tests with headed browser
pytest -v -m visual --headed tests/test_adf_visual.py

# Run single visual test with debugging
pytest -v -s tests/test_adf_visual.py::TestADFVisualFormatting::test_jira_issue_adf_description_rendering
```

### Manual Server Testing
```bash
# Start server manually for debugging
npm run start-server

# In another terminal - create seed data
npm run seed:direct

# Run tests with existing server
npm run test:api

# Clean up
npm run clean
```

## Project Structure

```
tests/e2e/
├── package.json                 # npm scripts and Playwright dependencies
├── pytest.ini                   # pytest configuration and test markers
├── requirements-test.txt         # Python test dependencies
├── conftest.py                   # pytest fixtures and configuration
├── mcp_client.py                 # MCP client implementation
├── test_fixtures.py              # Test data management
├── validators.py                 # API response validation utilities
├── visual_validators.py          # Browser-based validation utilities
├── tests/                        # Test specifications
│   ├── base_test.py             # Base test classes
│   ├── test_connectivity.py     # Basic connectivity tests
│   ├── test_jira_issues.py      # Jira issue functionality
│   ├── test_confluence_pages.py # Confluence page functionality
│   ├── test_adf_visual.py       # ADF visual verification
│   ├── test_search_functionality.py # Search capabilities
│   └── test_integration_error_handling.py # Integration & errors
├── seed/
│   └── seed.py                  # Test data creation via MCP server
├── cleanup/
│   └── cleanup.py               # Test data removal
├── manual-login.js              # Interactive authentication setup
├── seed-with-server.sh          # Automated seed with server lifecycle
├── storageState.json            # Saved authentication state (git-ignored)
├── playwright-report/          # HTML test reports
└── test-results/               # Test artifacts (screenshots, videos)
```

## Troubleshooting

### MCP Connection Issues
- **Connection refused**: Ensure MCP server is running on correct port (9001)
- **Tool not found**: Verify MCP server has Jira/Confluence tools loaded
- **Authentication failed**: Check `.env` credentials and server configuration

### Test Data Issues
- **No test data found**: Run `npm run seed` to create fresh test data
- **Seed script fails**: Check that `.env` has valid credentials and URLs
- **Resource cleanup errors**: Check cleanup logs and manually remove test resources if needed

### Visual Test Issues
- **Browser authentication failures**: Re-run `npm run auth` to refresh session
- **ADF elements not found**: Check that deployment type detection is working correctly
- **Visual assertion failures**: Review screenshots in `test-results/` directory

### Environment Issues
- **Missing environment variables**: Ensure repo root `.env` file exists and is configured
- **Wrong URLs**: Verify URLs point to your correct Atlassian instances
- **Network timeouts**: Check network connectivity to Atlassian instances

## Test Artifacts

### Reports and Results
- **Pytest output**: Detailed test results with pass/fail status
- **HTML Report**: `playwright-report/index.html` (for visual tests)
- **Screenshots**: `test-results/` (visual test failures)
- **Videos**: `test-results/` (visual test failures)

### Generated Data
- **Authentication**: `storageState.json` (browser session state for visual tests)
- **Test URLs**: `.artifacts/seed.json` (created by seed script)
- **Resource tracking**: Automatic cleanup of created test resources

## CI Integration

The test suite supports CI environments with:
- **Fast API tests**: Run with `npm run test:api` for quick feedback
- **Parallel execution**: Use `npm run test:parallel` for speed
- **Selective testing**: Use markers to run specific test categories
- **Cleanup automation**: Automatic resource cleanup after test runs
- **Artifact collection**: Screenshots and logs for debugging failures

## Performance Characteristics

### Test Execution Times
- **API tests**: ~2-5 seconds per test (fast feedback)
- **Visual tests**: ~10-30 seconds per test (browser automation)
- **Integration tests**: ~5-15 seconds per test (multiple operations)
- **Full suite**: ~5-15 minutes depending on parallelization

### Resource Usage
- **Test data**: Minimal resources created with descriptive names
- **Cleanup**: Automatic tracking and removal of all test resources
- **Browser memory**: Visual tests use single browser context per session

## ADF Testing Strategy

The test suite validates ADF (Atlassian Document Format) through:

1. **API Response Validation**: Verify ADF structure and content in MCP responses
2. **Visual Verification**: Use browser automation to verify ADF renders correctly
3. **Cross-platform Consistency**: Ensure ADF works identically in Jira and Confluence
4. **Performance Testing**: Validate ADF conversion performance with complex content

This comprehensive approach ensures the MCP Atlassian server correctly generates and processes ADF content for all supported Atlassian deployment types.