# E2E Testing for MCP Atlassian

This directory contains end-to-end tests for the MCP Atlassian server, validating ADF (Atlassian Document Format) rendering and functionality across Jira and Confluence.

## Quick Start

### 1. Setup
```bash
# Install Playwright dependencies
npm run prep

# Set up authentication (required once)
npm run auth
```

### 2. Create Test Data
```bash
# Generate seed data (creates Jira issues and Confluence pages)
npm run seed
```

### 3. Run Tests
```bash
# Run all E2E tests
npm run test

# Run specific browser tests
npx playwright test --project=chromium
npx playwright test --project=firefox
```

### 4. Cleanup
```bash
# Clean up test data when done
npm run clean
```

## Available Commands

| Command | Description |
|---------|-------------|
| `npm run prep` | Install Playwright browsers and dependencies |
| `npm run auth` | **Set up authentication** - Opens browser for manual login |
| `npm run seed` | Create test data (Jira issues + Confluence pages) |
| `npm run test` | Run all E2E tests across browsers |
| `npm run clean` | Remove test data and artifacts |

## Authentication Setup

The `npm run auth` command is **required** before running tests:

1. **Runs the authentication setup**:
   ```bash
   npm run auth
   ```

2. **Browser opens automatically** - Log in to your Atlassian account

3. **Wait for Jira dashboard** to fully load

4. **Press ENTER** in the terminal when ready

5. **Authentication saved** - Tests can now access Confluence/Jira pages

The authentication state is saved to `storageState.json` and will be used by all tests.

## Test Structure

- **ADF Features** (`adf-features.spec.ts`) - Tests ADF-specific elements (panels, mentions, emoji, dates, etc.)
- **Confluence Pages** (`confluence-page.spec.ts`) - Tests Confluence page rendering and navigation
- **Jira Issues** (`jira-issue.spec.ts`) - Tests Jira issue display and metadata
- **Interactive Elements** (`interactive-elements.spec.ts`) - Tests UI interactions
- **Error Scenarios** (`error-scenarios.spec.ts`) - Tests edge cases and error handling

## Configuration

Tests use environment variables from the project root `.env` file:

- `ATLASSIAN_URL` - Your Atlassian instance URL
- `JIRA_PROJECT` - Project key for test issues (e.g., "FTEST")
- `CONFLUENCE_SPACE` - Space ID for test pages (e.g., "655361")

## Troubleshooting

### Tests redirecting to login page
- Run `npm run auth` to re-authenticate
- Make sure you can see the Jira dashboard before pressing ENTER

### No test data found
- Run `npm run seed` to create fresh test data
- Check that seed.json contains both Jira and Confluence URLs

### Browser compatibility issues
- Firefox tests typically have better success rates
- Chromium tests require proper authentication setup

### Environment issues
- Check `.env` file has correct `ATLASSIAN_URL`
- Verify `JIRA_PROJECT` and `CONFLUENCE_SPACE` are accessible

## Test Results

Test results are available in:
- **HTML Report**: `playwright-report/index.html`
- **Screenshots**: `test-results/` (for failed tests)
- **Videos**: `test-results/` (for failed tests)

## Architecture

The E2E tests validate the complete workflow:
1. **MCP Server** generates markdown content
2. **ADF Conversion** transforms markdown to Atlassian Document Format
3. **Confluence v2 API** creates pages with proper storage format
4. **Browser Tests** validate visual rendering and functionality

This ensures the ADF implementation works correctly end-to-end.
