# Codebase Structure and Architecture

## Top-Level Directory Organization

```
src/mcp_atlassian/
├── __init__.py                 # Main entry point and CLI setup
├── __main__.py                 # Module execution entry
├── exceptions.py               # Custom exception classes
├── servers/                    # FastMCP server implementations
├── jira/                       # Jira service implementation
├── confluence/                 # Confluence service implementation
├── models/                     # Pydantic data models
├── utils/                      # Shared utilities
├── formatting/                 # ADF and markup conversion
├── preprocessing/              # Request/response preprocessing
├── rest/                       # REST API client abstractions
└── attic/                      # Deprecated/legacy code
```

## Core Architecture Components

### Server Layer (`servers/`)
- **main.py**: Main server orchestration with middleware
- **jira.py**: Jira-specific MCP server with tool registration
- **confluence.py**: Confluence-specific MCP server
- **context.py**: Shared application context and state management
- **dependencies.py**: Dependency injection setup

### Service Implementation (`jira/`, `confluence/`)
- **client.py**: API client wrapper around atlassian-python-api  
- **config.py**: Environment-based configuration management
- **Service modules**: issues.py, pages.py, search.py, etc.
- **mixins/**: Reusable functionality (CRUD operations, field handling)

### Data Models (`models/`)
- **base.py**: Common base classes and utilities
- **jira/**: Jira-specific Pydantic models (Issue, Project, Comment, etc.)
- **confluence/**: Confluence-specific models (Page, Space, Comment, etc.)
- **constants.py**: Shared constants and enums

### Utilities (`utils/`)
- **oauth.py/oauth_setup.py**: OAuth 2.0 authentication flow
- **environment.py**: Environment variable processing
- **logging.py**: Centralized logging configuration
- **tools.py**: Tool filtering and enablement logic
- **lifecycle.py**: Application lifecycle management

### Format Conversion (`formatting/`)
- **router.py**: Central format routing (Cloud vs Server/DC detection)
- **adf_ast.py**: Modern AST-based ADF converter using mistune
- **adf_plugins.py**: Plugin system for ADF node types
- **adf_validator.py**: ADF schema validation

### REST Layer (`rest/`)
- **adapters.py**: Version-agnostic API adapters
- **jira_adapter.py**: Jira API version handling (v2/v3)
- **confluence_adapter.py**: Confluence API version handling (v1/v2)
- **base.py**: Common REST client functionality

## Key Design Patterns

### Service Isolation
- Jira and Confluence are completely separate services
- No cross-service dependencies in service modules
- Shared functionality extracted to utils/ and models/base.py

### Configuration-Driven Architecture  
- All settings via environment variables or CLI flags
- Automatic service availability detection
- Auth method auto-detection based on available credentials

### Plugin System (ADF)
- Extensible ADF node conversion via plugins
- Automatic plugin registration
- Categorized plugins: block, inline, layout, media

### Middleware Pattern
- Tool filtering middleware for access control
- Per-request authentication for multi-tenant usage
- Preprocessing pipeline for request/response handling

### Adapter Pattern (REST)
- Version-agnostic API access through adapters
- Graceful handling of API version differences
- Centralized authentication and error handling