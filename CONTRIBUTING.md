# Contributing to MCP Atlassian

Thank you for your interest in contributing to MCP Atlassian! This Model Context Protocol server enables AI assistants to interact with Atlassian products (Jira and Confluence) securely and contextually. We welcome contributions in the form of bug reports, feature requests, documentation improvements, code changes, and tests.

## Quick Start for Contributors

1. **Prerequisites**: Python 3.10+, [UV package manager](https://docs.astral.sh/uv/getting-started/installation/)
2. **Fork & Clone**: Fork this repository and clone your fork
3. **Install Dependencies**: `uv sync --frozen --all-extras --dev`
4. **Setup Environment**: Copy `.env.example` to `.env` with your Atlassian credentials
5. **Install Hooks**: `pre-commit install`
6. **Run Tests**: `uv run pytest -k "not test_real_api_validation"`

## Development Environment Setup

### Local Development

1. **Install UV**: Follow the [UV installation guide](https://docs.astral.sh/uv/getting-started/installation/)

2. **Fork and Clone**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/mcp-atlassian.git
   cd mcp-atlassian
   git remote add upstream https://github.com/dmason-mlb/mcp-atlassian.git
   ```

3. **Install Dependencies**:
   ```bash
   uv sync --frozen --all-extras --dev
   ```

4. **Activate Virtual Environment**:
   ```bash
   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate.ps1
   ```

5. **Setup Pre-commit Hooks**:
   ```bash
   pre-commit install
   ```

6. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Atlassian instance details
   ```

### Docker Development

For containerized development:

```bash
docker build -t mcp-atlassian .
docker run -it --env-file .env mcp-atlassian
```

### VS Code DevContainer

1. Open project in VS Code
2. Install "Dev Containers" extension
3. Use "Reopen in Container" command
4. Add to `.vscode/settings.json`:
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
     "[python]": {
       "editor.defaultFormatter": "charliermarsh.ruff",
       "editor.formatOnSave": true
     }
   }
   ```

## Quality Gates & Testing

### Code Quality Commands

| Command | Purpose |
|---------|---------|
| `pre-commit run --all-files` | Run all quality checks |
| `uv run ruff format` | Format code |
| `uv run ruff check --fix` | Lint and auto-fix issues |
| `uv run mypy` | Type checking |

### Testing Commands

| Command | Purpose |
|---------|---------|
| `uv run pytest` | Run all tests |
| `uv run pytest --cov=src/mcp_atlassian --cov-report=term-missing` | Run with coverage |
| `uv run pytest -k "not test_real_api_validation"` | Skip API tests (CI default) |
| `uv run pytest tests/unit/` | Unit tests only |
| `uv run pytest tests/integration/` | Integration tests |

### End-to-End Testing

E2E tests use Playwright and require additional setup:

```bash
cd tests/e2e

# Install dependencies
npm run prep

# Seed test data (requires configured .env)
npm run seed

# Run E2E tests
npm run test

# Run specific test categories
npm run test:jira        # Jira-specific tests
npm run test:confluence  # Confluence-specific tests
npm run test:adf        # ADF format tests
npm run test:visual     # Visual regression tests

# Clean up test data
npm run clean
```

## Local MCP Server Development

### Running the Server

| Transport | Command | Use Case |
|-----------|---------|-----------|
| STDIO | `uv run mcp-atlassian` | IDE integration (Claude Desktop, etc.) |
| HTTP (SSE) | `uv run mcp-atlassian --transport sse --port 9000` | Web clients |
| HTTP (Streamable) | `uv run mcp-atlassian --transport streamable-http --port 9000` | Custom integrations |

### OAuth Setup

For OAuth authentication setup:

```bash
uv run mcp-atlassian --oauth-setup -v
```

### Debug Scripts

Useful debugging tools in the root directory:

| Script | Purpose |
|--------|---------|
| `python debug_confluence_formats.py` | Test ADF conversion |
| `python debug_confluence_simple.py` | Basic Confluence testing |
| `python debug_page_creation.py` | Page creation testing |
| `python debug_v2_adapter.py` | V2 adapter testing |
| `python create_seed_data.py` | Generate test data |

## Branching & Commits

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make Changes** following the code style guidelines below

3. **Commit Changes**:
   - Use clear, concise commit messages
   - Reference issues when applicable: `Fixes #123`
   - Follow the existing commit style (no strict conventional commits required)

## Code Style Guidelines

### Formatting & Linting
- **Line Length**: 88 characters (Ruff default)
- **Formatter**: Ruff (replaces Black)
- **Linter**: Ruff with comprehensive rule set
- **Type Checker**: MyPy (configured in `.pre-commit-config.yaml`)

### Code Standards
- **Type Annotations**: Required for all public functions
- **Import Style**: Use `from __future__ import annotations` for forward references
- **Union Types**: Use pipe syntax `str | None` (Python 3.10+)
- **Collections**: Use built-in generics `list[str]`, `dict[str, Any]`

### Documentation
Add Google-style docstrings to all public APIs:

```python
def create_issue(summary: str, issue_type: str, project_key: str) -> dict[str, Any]:
    """Create a new Jira issue.

    Args:
        summary: The issue title/summary.
        issue_type: Issue type (Bug, Task, Story, etc.).
        project_key: Jira project key (e.g., 'PROJ').

    Returns:
        Dictionary containing the created issue data.

    Raises:
        ValueError: If project_key is invalid.
        JiraError: If issue creation fails.
    """
```

## Pull Request Process

1. **Fill PR Template**: Provide clear description, testing details, checklist completion
2. **Ensure CI Passes**: All GitHub Actions workflows must pass
3. **Code Review**: Address feedback from maintainers
4. **Merge Requirements**:
   - All quality checks passing
   - Up-to-date with main branch
   - Approved by maintainer

### Required CI Checks
- **Tests**: Python 3.10, 3.11, 3.12 matrix
- **Linting**: Pre-commit hooks (ruff, mypy, various checks)
- **Coverage**: Maintained or improved test coverage

## Architecture Overview

### Core Components
- **MCP Server**: FastMCP-based server with tool filtering and auth middleware
- **Service Layers**: Separate Jira and Confluence service implementations
- **Format Router**: Automatic Cloud/Server detection with ADF/wiki markup conversion
- **Authentication**: OAuth 2.0, API tokens, PAT, BYOT support
- **Transport**: STDIO, SSE, HTTP with multi-tenant capabilities

### Key Directories
```
src/mcp_atlassian/
├── servers/           # MCP server implementations
├── jira/             # Jira service layer
├── confluence/       # Confluence service layer
├── formatting/       # ADF conversion and routing
├── models/           # Pydantic data models
├── rest/             # REST API adapters
└── utils/            # Shared utilities

tests/
├── unit/             # Unit tests with mocks
├── integration/      # Integration tests
└── e2e/              # End-to-end Playwright tests
```

## Issue Reports

When reporting bugs:

1. **Use Bug Report Template**: Available in GitHub Issues
2. **Minimal Reproduction**: Provide steps to reproduce
3. **Environment Details**: Python version, OS, Atlassian instance type
4. **Logs**: Include relevant error messages (mask sensitive data)
5. **Expected vs Actual**: Clear description of the problem

## Release Process

Releases use semantic versioning and are managed by maintainers:

- **PATCH**: Bug fixes, documentation updates
- **MINOR**: New features, backwards-compatible changes
- **MAJOR**: Breaking API changes

Version management is automated through `uv-dynamic-versioning` based on Git tags.

## Security

For security vulnerabilities:

1. **Do NOT** open public issues for security problems
2. **Contact maintainers directly** through GitHub Security tab or repository owner
3. **Provide details**: Vulnerability description, impact, reproduction steps
4. **Responsible disclosure**: Allow time for fixes before public disclosure

## Attribution & License

This project is licensed under the MIT License. Contributions are welcome under the same license terms. All contributors will be acknowledged in release notes and project documentation.

---

**Thank you for contributing to MCP Atlassian!** Your contributions help make AI-Atlassian integration more powerful and accessible for everyone.
