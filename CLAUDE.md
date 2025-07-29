# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- **Install dependencies**: `uv sync --frozen --all-extras --dev`
- **Activate virtual environment**: `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate.ps1` (Windows)
- **Install pre-commit hooks**: `pre-commit install`

### Testing
- **Run all tests**: `uv run pytest`
- **Run tests with coverage**: `uv run pytest --cov=src/mcp_atlassian --cov-report=term-missing`
- **Run specific test**: `uv run pytest tests/path/to/test_file.py::test_function_name`
- **Skip real API tests**: `uv run pytest -k "not test_real_api_validation"`

### Code Quality
- **Run all pre-commit checks**: `pre-commit run --all-files`
- **Format code with Ruff**: `uv run ruff format`
- **Lint code with Ruff**: `uv run ruff check --fix`
- **Type checking with MyPy**: `uv run mypy`

### Running the Server
- **Standard MCP server**: `uv run mcp-atlassian`
- **With environment file**: `uv run mcp-atlassian --env-file .env`
- **With verbose logging**: `uv run mcp-atlassian -vv`
- **OAuth setup wizard**: `uv run mcp-atlassian --oauth-setup -v`
- **HTTP transport (SSE)**: `uv run mcp-atlassian --transport sse --port 9000`
- **HTTP transport (streamable)**: `uv run mcp-atlassian --transport streamable-http --port 9000`

## Architecture Overview

### Core Structure
This is a Model Context Protocol (MCP) server that provides AI assistants with access to Atlassian products (Jira and Confluence). The codebase is organized into several key components:

- **`src/mcp_atlassian/servers/`** - FastMCP server implementations
  - `main.py` - Main server orchestration with tool filtering and user auth middleware
  - `jira.py` - Jira-specific MCP server
  - `confluence.py` - Confluence-specific MCP server
  - `context.py` - Shared application context and state management

- **`src/mcp_atlassian/{jira,confluence}/`** - Service-specific implementations
  - `client.py` - API client wrappers around atlassian-python-api
  - `config.py` - Configuration management with environment variable handling
  - Service modules for specific operations (issues, pages, search, etc.)

- **`src/mcp_atlassian/models/`** - Pydantic data models for API responses
  - Separate subdirectories for Jira and Confluence models
  - `base.py` - Common base classes and utilities

- **`src/mcp_atlassian/utils/`** - Shared utilities
  - `oauth.py` & `oauth_setup.py` - OAuth 2.0 authentication flow
  - `environment.py` - Environment variable processing
  - `logging.py` - Centralized logging configuration
  - `tools.py` - Tool filtering and enablement logic

### Authentication Architecture
Supports multiple authentication methods with automatic detection:
1. **API Token** (Cloud) - Username + API token
2. **Personal Access Token** (Server/DC) - PAT-based auth
3. **OAuth 2.0** (Cloud) - Standard OAuth flow with refresh tokens
4. **BYOT OAuth** (Cloud) - Bring Your Own Token for external token management
5. **Multi-user HTTP** - Per-request authentication via headers

### Transport Layer
- **STDIO** - Standard MCP stdio transport for IDE integration
- **SSE** - Server-Sent Events for HTTP-based communication
- **Streamable HTTP** - HTTP transport with request/response pattern
- **Multi-tenant Support** - Per-request authentication for multi-user scenarios

### Key Design Principles
- **Service Isolation**: Jira and Confluence are implemented as separate mounted sub-servers
- **Configuration-driven**: All settings configurable via environment variables or CLI flags
- **Tool Filtering**: Granular control over which tools are available based on auth, read-only mode, and explicit enablement
- **Error Resilience**: Graceful degradation when services are unavailable or misconfigured
- **Security-first**: Credential masking in logs, secure token storage, SSL verification

## Important Implementation Notes

### Code Style
- Line length: 88 characters (Ruff formatting)
- Type annotations required for all public functions
- Google-style docstrings for public APIs
- Union types with pipe syntax: `str | None`
- Modern collection types: `list[str]`, `dict[str, Any]`

### Testing Approach
- **Unit tests**: Mock external API calls using `tests/fixtures/`
- **Integration tests**: Test MCP protocol compliance and cross-service functionality
- **Real API tests**: Optional tests requiring actual Atlassian credentials (skip by default)
- **Fixtures**: Shared mock data in `tests/fixtures/{jira,confluence}_mocks.py`

### Configuration Management
- Environment variables take precedence over CLI flags
- Config classes (`JiraConfig`, `ConfluenceConfig`) handle validation and defaults
- Service availability determined by both URL presence and auth configuration
- Proxy and custom header support for enterprise environments

### FastMCP Integration
- Custom `AtlassianMCP` class extends FastMCP with tool filtering
- Lifespan context manages service initialization and cleanup
- User token middleware handles per-request authentication
- Health check endpoints for monitoring (`/healthz`)

### Build and Deployment
- Uses `uv` for dependency management and virtual environments
- Docker-based distribution with multi-architecture support
- Pre-commit hooks ensure code quality before commits
- Semantic versioning with automated releases via GitHub Actions