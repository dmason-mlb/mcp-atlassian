# MCP Atlassian

[![Run Tests](https://github.com/dmason-mlb/mcp-atlassian/actions/workflows/tests.yml/badge.svg)](https://github.com/dmason-mlb/mcp-atlassian/actions/workflows/tests.yml)
![License](https://img.shields.io/github/license/dmason-mlb/mcp-atlassian)

Model Context Protocol (MCP) server for Atlassian products (Confluence and Jira). This integration supports both Confluence & Jira Cloud and Server/Data Center deployments.

## Quick Start (60 seconds)

```bash
# 1. Install dependencies
uv sync --frozen --all-extras --dev

# 2. Get your API token (for Cloud)
# Visit: https://id.atlassian.com/manage-profile/security/api-tokens

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Run the server
uv run mcp-atlassian
```

## Prerequisites

- **Python 3.10+** installed
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Atlassian account** with appropriate permissions
- **API credentials**: API token (Cloud) or Personal Access Token (Server/DC)

## Features

### Key Capabilities
- **🔄 Unified Interface**: Single MCP server for both Jira and Confluence
- **🏗️ AST-Based Markdown Processing**: Robust markdown to ADF conversion using Abstract Syntax Tree parsing
- **🔌 Extensible Plugin Architecture**: Easy addition of custom ADF nodes through plugins
- **📝 Rich Content Support**: Full support for panels, expands, layouts, mentions, emojis, and more
- **🚀 High Performance**: LRU caching and optimized parsing for fast conversions
- **🔒 Multi-Auth Support**: API tokens, OAuth 2.0, Personal Access Tokens, and multi-user HTTP
- **🎯 Smart Format Detection**: Automatic detection of Cloud vs Server/DC deployments
- **⚡ Graceful Degradation**: Fallback from ADF → Wiki markup → Plain text as needed

### Example Usage

Ask your AI assistant to:
- **📝 Automatic Jira Updates** - "Update Jira from our meeting notes"
- **🔍 AI-Powered Confluence Search** - "Find our OKR guide in Confluence and summarize it"
- **🐛 Smart Jira Issue Filtering** - "Show me urgent bugs in PROJ project from last week"
- **📄 Content Creation & Management** - "Create a tech design doc for XYZ feature"

### Feature Demo

https://github.com/user-attachments/assets/35303504-14c6-4ae4-913b-7c25ea511c3e

<details> <summary>Confluence Demo</summary>

https://github.com/user-attachments/assets/7fe9c488-ad0c-4876-9b54-120b666bb785

</details>

### Compatibility

| Product        | Deployment Type    | Support Status              |
|----------------|--------------------|------------------------------|
| **Confluence** | Cloud              | ✅ Fully supported           |
| **Confluence** | Server/Data Center | ✅ Supported (version 6.0+)  |
| **Jira**       | Cloud              | ✅ Fully supported           |
| **Jira**       | Server/Data Center | ✅ Supported (version 8.14+) |

## Installation

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/dmason-mlb/mcp-atlassian.git
cd mcp-atlassian

# Install dependencies
uv sync --frozen --all-extras --dev

# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate.ps1  # Windows

# Set up pre-commit hooks
pre-commit install
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your credentials:

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_URL` | Jira instance URL | Yes |
| `CONFLUENCE_URL` | Confluence instance URL | Yes |
| `JIRA_USERNAME` / `JIRA_API_TOKEN` | Jira Cloud auth | For Cloud |
| `JIRA_PERSONAL_TOKEN` | Jira Server/DC auth | For Server/DC |
| `CONFLUENCE_USERNAME` / `CONFLUENCE_API_TOKEN` | Confluence Cloud auth | For Cloud |
| `CONFLUENCE_PERSONAL_TOKEN` | Confluence Server/DC auth | For Server/DC |
| `READ_ONLY_MODE` | Disable write operations | Optional |
| `ENABLED_TOOLS` | Comma-separated tool whitelist | Optional |
| `MCP_VERBOSE` | Enable verbose logging | Optional |

See [.env.example](.env.example) for all available options including proxy, OAuth, and custom headers.

### Authentication Methods

#### A. API Token (Cloud) - **Recommended**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**, name it
3. Copy the token immediately

#### B. Personal Access Token (Server/DC)
1. Go to your profile → **Personal Access Tokens**
2. Click **Create token**, set expiry
3. Copy the token immediately

#### C. OAuth 2.0 (Cloud) - **Advanced**
See the [OAuth Setup Guide](#oauth-20-configuration-example-cloud-only) for detailed instructions.

## IDE Integration

> **Configuration files location:**
> - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
> - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
> - **Linux**: `~/.config/Claude/claude_desktop_config.json`
> - **Cursor**: Settings → MCP → + Add new global MCP server

### Basic Configuration (Claude Desktop/Cursor)

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/mcp-atlassian",
        "mcp-atlassian"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@company.com",
        "CONFLUENCE_API_TOKEN": "your_confluence_api_token",
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your.email@company.com",
        "JIRA_API_TOKEN": "your_jira_api_token"
      }
    }
  }
}
```

<details>
<summary>Server/Data Center Configuration</summary>

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/mcp-atlassian",
        "mcp-atlassian"
      ],
      "env": {
        "CONFLUENCE_URL": "https://confluence.your-company.com",
        "CONFLUENCE_PERSONAL_TOKEN": "your_confluence_pat",
        "JIRA_URL": "https://jira.your-company.com",
        "JIRA_PERSONAL_TOKEN": "your_jira_pat"
      }
    }
  }
}
```

</details>

<details>
<summary>OAuth 2.0 Configuration (Cloud)</summary>
<a name="oauth-20-configuration-example-cloud-only"></a>

Run the OAuth setup wizard:
```bash
uv run mcp-atlassian --oauth-setup -v
```

Then configure your IDE:
```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uv",
      "args": [
        "run", "--directory", "/path/to/mcp-atlassian",
        "mcp-atlassian"
      ],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "ATLASSIAN_OAUTH_CLIENT_ID": "YOUR_OAUTH_APP_CLIENT_ID",
        "ATLASSIAN_OAUTH_CLIENT_SECRET": "YOUR_OAUTH_APP_CLIENT_SECRET",
        "ATLASSIAN_OAUTH_REDIRECT_URI": "http://localhost:8080/callback",
        "ATLASSIAN_OAUTH_SCOPE": "read:jira-work write:jira-work offline_access",
        "ATLASSIAN_OAUTH_CLOUD_ID": "YOUR_CLOUD_ID_FROM_SETUP_WIZARD"
      }
    }
  }
}
```

</details>

<details>
<summary>HTTP Transport (Multi-User)</summary>

Start server with HTTP transport:
```bash
uv run mcp-atlassian --transport streamable-http --port 9000
```

Configure IDE with user-specific auth:
```json
{
  "mcpServers": {
    "mcp-atlassian-service": {
      "url": "http://localhost:9000/mcp",
      "headers": {
        "Authorization": "Bearer <USER_OAUTH_TOKEN>"
      }
    }
  }
}
```

</details>

<details>
<summary>Advanced Configuration Options</summary>

- **Environment File**: Use `--env-file` flag for environment variables
- **Proxy Support**: Configure `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
- **Custom Headers**: Set `JIRA_CUSTOM_HEADERS`, `CONFLUENCE_CUSTOM_HEADERS`
- **Space/Project Filters**: Use `CONFLUENCE_SPACES_FILTER`, `JIRA_PROJECTS_FILTER`
- **Tool Filtering**: Set `ENABLED_TOOLS` to whitelist specific tools
- **Multi-Cloud OAuth**: See [Multi-Cloud OAuth Support](#multi-cloud-oauth-support)

</details>

## Available Tools

This MCP server exposes 50+ tools for comprehensive Jira and Confluence interaction.

**Quick Overview:**
- **Jira** (40+ tools): Issue management, search, agile boards, attachments, user management
- **Confluence** (11 tools): Page operations, content management, search, comments, labels

See [**TOOLSET.md**](docs/TOOLSET.md) for the complete catalog with schemas and examples.

## Development

### Commands Reference

| Command | Purpose | When to Use |
|---------|---------|-------------|
| **Python/uv Commands** |
| `uv sync --frozen --all-extras --dev` | Install all dependencies | Initial setup |
| `uv run pytest` | Run test suite | Before committing |
| `uv run pytest --cov=src/mcp_atlassian` | Run tests with coverage | CI/quality check |
| `pre-commit run --all-files` | Run all code quality checks | Before committing |
| `uv run mcp-atlassian` | Run server locally | Development testing |
| `uv run mcp-atlassian --oauth-setup` | OAuth setup wizard | Initial OAuth config |
| **E2E Test Commands** |
| `npm run prep` | Install Playwright | First time setup |
| `npm run seed` | Seed test data | Before e2e tests |
| `npm run test` | Run e2e tests | Integration testing |
| `npm run clean` | Clean test data | After testing |

### Project Structure

```
mcp-atlassian/
├── src/mcp_atlassian/         # Main source code
│   ├── servers/               # FastMCP server implementations
│   │   ├── main.py           # Main server orchestration
│   │   ├── jira/             # Jira-specific server & tools
│   │   └── confluence/       # Confluence-specific server & tools
│   ├── formatting/           # ADF/markdown conversion
│   │   ├── adf_ast.py       # AST-based ADF generator
│   │   ├── adf_plugins.py   # Plugin architecture
│   │   └── router.py        # Format detection & routing
│   ├── models/              # Pydantic data models
│   └── utils/               # Shared utilities
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data & mocks
├── e2e/                    # End-to-end tests
│   ├── tests/             # Playwright test specs
│   └── seed/              # Test data seeding
├── docs/                   # Documentation
│   └── TOOLSET.md         # Tool reference catalog
├── scripts/               # Utility scripts
├── .env.example          # Configuration template
├── pyproject.toml        # Python project config
└── smithery.yaml        # Smithery.ai deployment
```

## Testing

```bash
# Run all tests (skip real API tests)
uv run pytest -k "not test_real_api_validation"

# Run with coverage
uv run pytest --cov=src/mcp_atlassian --cov-report=term-missing

# Run specific test
uv run pytest tests/unit/formatting/test_adf_ast.py

# Run e2e tests (requires setup)
cd e2e && npm run test
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Authentication fails** | For Cloud: Use API token (not password). For Server/DC: Check PAT expiry |
| **SSL Certificate errors** | Set `JIRA_SSL_VERIFY=false` or `CONFLUENCE_SSL_VERIFY=false` for self-signed certs |
| **Permission denied** | Verify account has sufficient Atlassian permissions |
| **Python version error** | Requires Python 3.10+. Check with `python --version` |
| **uv not found** | Install uv: https://docs.astral.sh/uv/getting-started/installation/ |
| **Port already in use** | Change port with `--port` flag or `PORT` env var |
| **Custom headers not working** | Enable `MCP_VERY_VERBOSE=true` to debug header parsing |

### Debug Tools

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run --directory /path/to/mcp-atlassian mcp-atlassian

# View logs (macOS)
tail -n 20 -f ~/Library/Logs/Claude/mcp*.log

# View logs (Windows)
type %APPDATA%\Claude\logs\mcp*.log | more

# Enable debug logging
export MCP_VERY_VERBOSE=true
export MCP_LOGGING_STDOUT=true
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:
- Development setup and quality standards
- Commit conventions and PR process
- Testing requirements and CI checks
- Code style and type annotations

## Deployment Options

### Smithery.ai
Configuration available in [smithery.yaml](smithery.yaml) for automated deployment.

### Local Development
This fork is focused on local development. Install dependencies with `uv sync` and run with `uv run mcp-atlassian`.

## Security

- Never commit API tokens or credentials
- Use environment variables or secure vaults for secrets
- Enable SSL verification in production
- Review [OAuth scopes](https://developer.atlassian.com/cloud/jira/platform/scopes-for-oauth-2-3LO-and-forge-apps/) carefully
- Report security issues privately via GitHub Security tab

## License

Licensed under MIT - see [LICENSE](LICENSE) file. This is not an official Atlassian product.

## Support

- **Documentation**: [Full docs](docs/) | [Tool Reference](docs/TOOLSET.md)
- **Issues**: [GitHub Issues](https://github.com/dmason-mlb/mcp-atlassian/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dmason-mlb/mcp-atlassian/discussions)

---

*Built with ❤️ for the MCP ecosystem by [dmason-mlb](https://github.com/dmason-mlb)*
