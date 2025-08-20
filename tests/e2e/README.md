# E2E Testing for MCP Atlassian

End-to-end tests for the MCP Atlassian server, validating ADF (Atlassian Document Format) rendering and functionality across Jira and Confluence. These tests use Playwright to verify that markdown content is properly converted to ADF and rendered correctly in actual Atlassian instances.

## Prerequisites

- **Node.js 18+** for Playwright tests
- **Python 3.10+** and `uv` for seed/cleanup scripts
- **Access to Atlassian instance** (Cloud or Server/DC)
- **Valid credentials** configured in repo root `.env` file

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
# 3. Install Playwright and browsers
npm run prep

# 4. Set up authentication (required once)
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
| **prep** | `playwright install --with-deps` | Install Playwright browsers and system dependencies | First time setup, CI environments |
| **start-server** | `cd ../.. && uv run mcp-atlassian --transport streamable-http --port 9001` | Start MCP server for development | When debugging seed/cleanup issues |
| **seed** | `./seed-with-server.sh` | Create test data with server auto-start/stop | Before running tests |
| **seed:direct** | `uv run python seed/seed.py` | Create test data (requires server running) | When server is already running |
| **test** | `REUSE_AUTH=true playwright test` | Run all E2E tests across browsers | Main test execution |
| **test:chromium** | `REUSE_AUTH=true playwright test --project=chromium` | Run tests in Chromium only | Faster testing, debugging |
| **test:firefox** | `REUSE_AUTH=true playwright test --project=firefox` | Run tests in Firefox only | Better success rates |
| **test:webkit** | `REUSE_AUTH=true playwright test --project=webkit` | Run tests in WebKit/Safari | Safari compatibility |
| **clean** | `uv run python cleanup/cleanup.py` | Remove test data and artifacts | After testing, CI cleanup |
| **auth** | `node manual-login.js` | Interactive authentication setup | Initial setup, auth refresh |
| **validate** | `node validate-env.js` | Validate environment configuration | Troubleshooting setup issues |

## Authentication Setup

**Required before running tests:** The `npm run auth` command opens a browser for manual login:

1. Run the authentication command:
   ```bash
   npm run auth
   ```

2. **Browser opens automatically** - Log in to your Atlassian account

3. **Wait for Jira dashboard** to fully load (important!)

4. **Press ENTER** in the terminal when ready

5. **Authentication saved** to `storageState.json` for all tests

The authentication state persists across test runs. Re-run `npm run auth` if you encounter login redirects.

## Environment Configuration

Tests load environment variables from the **repo root `.env` file**:

| Variable | Description | Example |
|----------|-------------|---------|
| `ATLASSIAN_URL` | Your Atlassian instance base URL | `https://company.atlassian.net` |
| `JIRA_BASE` | Jira base URL (overrides ATLASSIAN_URL) | `https://company.atlassian.net` |
| `CONFLUENCE_BASE` | Confluence base URL | `https://company.atlassian.net/wiki` |
| `JIRA_PROJECT` | Project key for test issues | `FTEST` |
| `CONFLUENCE_SPACE` | Space ID for test pages | `655361` |

## Test Structure

### Test Suites
- **`adf-features.spec.ts`** - ADF-specific elements (panels, mentions, emoji, dates, status badges)
- **`confluence-page.spec.ts`** - Confluence page rendering, navigation, and content structure
- **`jira-issue.spec.ts`** - Jira issue display, metadata, and markdown rendering
- **`interactive-elements.spec.ts`** - UI interactions, buttons, forms, and accessibility
- **`error-scenarios.spec.ts`** - Edge cases, error handling, and graceful degradation

### Browser Projects
- **Desktop**: chromium, firefox, webkit
- **Mobile**: mobile-chrome (Pixel 5), mobile-safari (iPhone 12)
- **Specialized**: tablet (iPad Pro), high-dpi, accessibility

### Test Data
- **Seed Data**: Created by `seed/seed.py` via MCP server calls
- **Templates**: Markdown templates documented in `test-data-templates.md`
- **Artifacts**: Test URLs stored in `.artifacts/seed.json`
- **Cleanup**: Removed by `cleanup/cleanup.py` after testing

## Development Workflow

### Running Tests During Development
```bash
# Quick iteration - single browser
npm run test:chromium

# Full validation - all browsers
npm run test

# Debug specific test file
npx playwright test tests/jira-issue.spec.ts --headed

# Run with debugging tools
npx playwright test --debug
```

### Manual Server Testing
```bash
# Start server manually for debugging
npm run start-server

# In another terminal - create seed data
npm run seed:direct

# Run tests with existing server
npm run test

# Clean up
npm run clean
```

## Project Structure

```
tests/e2e/
├── package.json              # npm scripts and Playwright dependencies
├── playwright.config.ts      # Playwright configuration, browser projects
├── validate-env.js          # Environment validation script
├── test-data-templates.md   # Documentation of markdown test templates
├── setup/
│   └── global-setup.ts      # Authentication and environment setup
├── tests/                   # Test specifications
│   ├── adf-features.spec.ts
│   ├── confluence-page.spec.ts
│   ├── jira-issue.spec.ts
│   ├── interactive-elements.spec.ts
│   └── error-scenarios.spec.ts
├── seed/
│   └── seed.py             # Test data creation via MCP server
├── cleanup/
│   └── cleanup.py          # Test data removal
├── manual-login.js         # Interactive authentication setup
├── seed-with-server.sh     # Automated seed with server lifecycle
├── storageState.json       # Saved authentication state (git-ignored)
├── .artifacts/
│   └── seed.json          # Generated test URLs and metadata
├── test-results/          # Test artifacts (screenshots, videos)
└── playwright-report/     # HTML test reports
```

## Troubleshooting

### Authentication Issues
- **Tests redirect to login**: Run `npm run auth` to re-authenticate
- **No cookies saved**: Ensure you see the Jira dashboard before pressing ENTER
- **Permission errors**: Verify your Atlassian account has access to configured project/space

### Test Data Issues
- **No test data found**: Run `npm run seed` to create fresh test data
- **Seed script fails**: Check that `.env` has valid credentials and URLs
- **Missing .artifacts/seed.json**: Seed script creates this file with test URLs

### Server Issues
- **Port 9001 in use**: Stop other MCP server instances or change port in scripts
- **Server won't start**: Run from repo root with `uv run mcp-atlassian --transport streamable-http --port 9001`
- **Connection refused**: Wait for server health check in `seed-with-server.sh`

### Browser Issues
- **Chromium auth failures**: Try Firefox tests first: `npm run test:firefox`
- **Headless issues**: Run with `--headed` flag for debugging
- **Video/screenshot missing**: Check `test-results/` directory after failed tests

### Environment Issues
- **Missing environment variables**: Ensure repo root `.env` file exists and is configured
- **Wrong URLs**: Verify `ATLASSIAN_URL` points to your correct instance
- **Network timeouts**: Increase timeout in `playwright.config.ts` if needed

## Test Artifacts

### Reports and Results
- **HTML Report**: `playwright-report/index.html` (viewable in browser)
- **JUnit XML**: `test-results/junit.xml` (for CI integration)
- **Screenshots**: `test-results/` (only on test failures)
- **Videos**: `test-results/` (retained on failures)

### Generated Data
- **Authentication**: `storageState.json` (browser session state)
- **Test URLs**: `.artifacts/seed.json` (created by seed script)
- **Traces**: Available for debugging with `npx playwright show-trace`

## CI Integration

The test suite supports CI environments with:
- **Parallel execution**: 2 workers in CI mode
- **Retry logic**: 2 retries on failure in CI
- **Artifact collection**: Screenshots, videos, and traces on failure
- **Multiple browsers**: Full browser matrix validation
- **Health checks**: Server readiness validation in seed scripts

## Architecture

The E2E testing validates the complete MCP Atlassian workflow:
1. **MCP Server** generates markdown content via tools
2. **ADF Conversion** transforms markdown to Atlassian Document Format
3. **Atlassian APIs** create Jira issues and Confluence pages
4. **Browser Tests** validate visual rendering and functionality in real Atlassian UI

This ensures ADF implementation works correctly end-to-end with actual Atlassian instances.