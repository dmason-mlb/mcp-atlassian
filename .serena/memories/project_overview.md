# MCP Atlassian Project Overview

## Project Purpose
MCP Atlassian is a Model Context Protocol (MCP) server that provides AI assistants with secure access to Atlassian products (Jira and Confluence). It bridges AI language models with Atlassian tools while maintaining data privacy and security, following Anthropic's MCP specification.

## Key Features
- **Multi-product support**: Both Jira and Confluence integration
- **Multiple authentication methods**: API tokens, Personal Access Tokens, OAuth 2.0, BYOT OAuth, Multi-user HTTP
- **Format handling**: Automatic ADF (Atlassian Document Format) conversion for Cloud instances, wiki markup for Server/DC
- **Transport flexibility**: STDIO, SSE, Streamable HTTP with multi-tenant support
- **Security-first**: Credential masking, secure token storage, SSL verification
- **Tool filtering**: Granular control over available tools based on auth and permissions

## Tech Stack
- **Language**: Python 3.10+
- **Package management**: uv (modern Python package manager)
- **MCP framework**: FastMCP (v2.3.4+) built on top of MCP (v1.8.0+)
- **Web framework**: Starlette/Uvicorn for HTTP transport
- **Data validation**: Pydantic v2.10.6+
- **HTTP client**: httpx, requests
- **Markup processing**: mistune (AST-based), markdown, beautifulsoup4
- **Authentication**: OAuth 2.0, keyring for secure storage
- **Testing**: pytest, pytest-asyncio, pytest-playwright for E2E
- **Code quality**: Ruff (linting/formatting), mypy (type checking), pre-commit hooks

## Architecture
- **Modular design**: Separate Jira and Confluence servers as FastMCP sub-servers
- **Service isolation**: Independent clients, models, and tools for each service
- **Plugin system**: Extensible ADF conversion with plugin architecture
- **Format routing**: Automatic Cloud vs Server/DC deployment detection
- **REST abstraction**: Clean abstraction over atlassian-python-api
- **Middleware**: Per-request authentication and tool filtering

## Development Environment
- **Package manager**: uv (not pip/poetry)
- **Virtual environment**: .venv managed by uv
- **Pre-commit**: Enforced code quality checks
- **Testing**: Unit, integration, and E2E tests with fixtures
- **Documentation**: Comprehensive CLAUDE.md with development workflows