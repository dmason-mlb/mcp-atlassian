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

### Debug Scripts (Root Directory)
Several debug scripts are available for troubleshooting specific components:
- **Debug ADF conversion**: `python debug_confluence_formats.py`
- **Simple Confluence testing**: `python debug_confluence_simple.py`
- **Page creation testing**: `python debug_page_creation.py`
- **V2 adapter testing**: `python debug_v2_adapter.py`
- **Test data creation**: `python create_seed_data.py`

### End-to-End Testing
- **Install Playwright dependencies**: `cd tests/e2e && npm run prep`
- **Seed test data**: `cd tests/e2e && npm run seed`
- **Run e2e tests**: `cd tests/e2e && npm run test`
- **Clean test data**: `cd tests/e2e && npm run clean`

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

### Critical Architecture Patterns
Understanding these patterns is essential for effective development:

#### Service Layer Separation
- Jira and Confluence are implemented as completely separate services with their own clients, models, and tools
- Shared functionality lives in `utils/` and `models/base.py`
- Cross-service operations are handled at the main server level, not within individual services

#### Format Routing Architecture
- The `FormatRouter` in `src/mcp_atlassian/formatting/router.py` handles automatic detection of Cloud vs Server/DC deployments
- ADF conversion is used for Cloud instances, wiki markup for Server/DC
- Performance optimization through TTL caching and compiled regex patterns

#### Plugin System for ADF
- Extensible plugin architecture allows adding new ADF node types without modifying core conversion logic
- Plugins are categorized: block, inline, layout, media
- Registration happens automatically through the plugin registry

#### REST Client Abstraction
- `src/mcp_atlassian/rest/` provides a clean abstraction over the underlying atlassian-python-api library
- Adapters handle version-specific API differences (v2 vs v3 for Jira, v1 vs v2 for Confluence)
- Authentication detection and credential management are centralized

#### Tool Filtering and Middleware
- Tools can be dynamically enabled/disabled based on authentication, read-only mode, and explicit configuration
- Per-request authentication middleware allows multi-tenant usage
- Tool metadata and filtering logic in `utils/tools.py` enables fine-grained access control

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
- **E2E tests**: Playwright-based browser automation in `tests/e2e/` with seeding scripts
- **Coverage reports**: Available in `htmlcov/` after running coverage tests

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
- Modular server architecture: separate Jira and Confluence sub-servers in `src/mcp_atlassian/servers/`

### Build and Deployment
- Uses `uv` for dependency management and virtual environments
- Docker-based distribution with multi-architecture support
- Pre-commit hooks ensure code quality before commits
- Semantic versioning with automated releases via GitHub Actions

## Common Development Workflows

### Debugging ADF Issues
When working on ADF (Atlassian Document Format) conversion issues:
1. Use `debug_confluence_formats.py` to test format detection and conversion
2. Check deployment type detection with FormatRouter debugging commands
3. Validate ADF output using the built-in ADFValidator
4. Run ADF-specific tests: `uv run pytest tests/unit/formatting/ -v`

### Adding New MCP Tools
When adding new MCP tools to either service:
1. Define the tool in the appropriate service module (`src/mcp_atlassian/jira/` or `src/mcp_atlassian/confluence/`)
2. Add corresponding Pydantic models in `src/mcp_atlassian/models/`
3. Update the server registration in `src/mcp_atlassian/servers/{jira,confluence}.py`
4. Write unit tests with mock fixtures in `tests/fixtures/`
5. Add integration tests if API behavior is complex

### Plugin Development (ADF)
For extending ADF conversion capabilities:
1. Create new plugins in `src/mcp_atlassian/formatting/` following the plugin architecture
2. Register plugins in the `ASTBasedADFGenerator` 
3. Test with both unit tests and `debug_confluence_formats.py` script
4. Validate against real Confluence instances for ADF compliance

## ADF (Atlassian Document Format) Implementation

### Overview
The MCP Atlassian server now includes comprehensive support for ADF (Atlassian Document Format), which is required by Jira and Confluence Cloud APIs. The implementation provides automatic format detection and conversion to ensure proper rendering of markdown content.

### Format Detection and Routing
The system automatically detects deployment types and routes content accordingly:

- **Cloud instances** (*.atlassian.net, *.atlassian.com): Use ADF JSON format
- **Server/DC instances** (custom domains): Use wiki markup strings
- **Unknown deployments**: Default to wiki markup with graceful fallback

### Architecture Components

#### FormatRouter (`src/mcp_atlassian/formatting/router.py`)
Central routing system that:
- Detects deployment type from base URLs with TTL caching
- Selects appropriate formatter (ADF vs wiki markup)
- Provides performance monitoring and metrics collection
- Implements compiled regex patterns for efficient URL matching

#### ASTBasedADFGenerator (`src/mcp_atlassian/formatting/adf_ast.py`)
Modern AST-based markdown-to-ADF converter using mistune:
- Robust parsing using Abstract Syntax Tree approach
- Plugin architecture for extensible node support
- Comprehensive validation with ADFValidator
- Support for all standard markdown plus ADF extensions

#### Plugin Architecture (`src/mcp_atlassian/formatting/adf_plugins.py`)
Extensible plugin system for ADF nodes:
- Base plugin class for easy extension
- Built-in plugins: Panel, Media, Expand, Status, Date, Mention, Emoji, Layout
- Support for both block and inline node types
- See [ADF Plugin Architecture Documentation](docs/adf-plugin-architecture.md) for details

#### Legacy ADFGenerator (`src/mcp_atlassian/formatting/adf.py`) - Deprecated
Python-native markdown-to-ADF converter featuring:
- LRU caching for frequently converted patterns (256 items)
- Lazy evaluation for complex elements (tables, nested lists)
- Comprehensive error handling with graceful degradation
- Performance metrics and optimization monitoring

### Supported Markdown Elements

#### Basic Elements (Full Support)
- **Text formatting**: Bold, italic, strikethrough, underline, code
- **Headings**: H1-H6 with proper ADF structure
- **Paragraphs**: Multi-paragraph content with line breaks
- **Links**: Inline and reference-style links with href attributes

#### Lists (Optimized)
- **Unordered lists**: Bullet lists with nested support (max 10 levels)
- **Ordered lists**: Numbered lists with proper sequencing
- **Mixed nesting**: Combined bullet and numbered lists
- **Performance limits**: 100 items per list, 50 children per item

#### Code (Enhanced)
- **Inline code**: Backtick notation with proper marks
- **Code blocks**: Fenced blocks with language detection
- **Syntax highlighting**: Language-specific formatting where supported

#### Advanced Elements (Performance Optimized)
- **Tables**: Full table support with 50 row × 20 cell limits
- **Blockquotes**: Nested quote support with proper structure
- **Horizontal rules**: HR elements for content separation

#### ADF-Specific Elements (Plugin-based)
- **Panels**: Info, note, warning, success, error panels with `:::panel` syntax
- **Expand/Collapse**: Collapsible sections with `:::expand` syntax
- **Media**: Confluence media embedding with `:::media` syntax
- **Status badges**: Inline status with `{status:color=green}Text{/status}` syntax
- **Dates**: Date elements with `{date:YYYY-MM-DD}` syntax
- **Mentions**: User mentions with `@username` or `@[Full Name]` syntax
- **Emojis**: Emoji support with `:emoji_name:` syntax
- **Layouts**: Multi-column layouts with `:::layout` syntax

### Performance Characteristics

#### Optimization Features
- **Caching**: LRU cache with 256 item capacity for repeated conversions
- **Lazy evaluation**: Large tables and deep lists processed efficiently
- **Size limits**: Automatic truncation with user-friendly notices
- **Metrics collection**: Comprehensive performance monitoring

#### Benchmarks
- **Target performance**: <100ms conversion time achieved
- **Average conversion**: 15ms for typical markdown content
- **Cache hit rate**: Up to 100% for repeated content
- **Memory efficiency**: Optimized for large documents with truncation

### Error Handling and Fallback

#### Graceful Degradation Hierarchy
1. **Primary**: ADF JSON conversion for Cloud instances
2. **Fallback**: Wiki markup conversion for compatibility
3. **Ultimate**: Plain text with error context preservation

#### Error Recovery
- **Conversion failures**: Automatic fallback to previous format
- **Malformed input**: Graceful handling with partial conversion
- **Performance limits**: Truncation with explanatory messages
- **Logging**: Comprehensive error context for debugging

### Integration Points

#### Preprocessing Pipeline
- **JiraPreprocessor**: Enhanced with `enable_adf` parameter
- **ConfluencePreprocessor**: Integrated ADF support for Cloud instances
- **Backward compatibility**: Existing wiki markup preserved for Server/DC

#### Configuration
- **Automatic detection**: URL-based deployment type identification
- **Manual override**: Force format selection when needed
- **Caching**: TTL-based deployment detection (1 hour default)
- **Performance tuning**: Configurable cache sizes and limits

### Usage Examples

#### Basic ADF Conversion
```python
from mcp_atlassian.formatting.router import FormatRouter

router = FormatRouter()
result = router.convert_markdown(
    "# Heading\n\n**Bold** and *italic* text",
    "https://company.atlassian.net"
)
# Returns: {'content': {...}, 'format': 'adf', 'deployment_type': 'cloud'}
```

#### Performance Monitoring
```python
# Get comprehensive metrics
metrics = router.get_performance_metrics()
print(f"Cache hit rate: {metrics['detection_cache_hit_rate']:.1f}%")
print(f"Average conversion time: {metrics['average_conversion_time']*1000:.2f}ms")
```

#### Direct ADF Generation
```python
from mcp_atlassian.formatting.adf_ast import ASTBasedADFGenerator

generator = ASTBasedADFGenerator()
adf_result = generator.markdown_to_adf("**Bold** text with `code`")
# Returns valid ADF JSON structure
```

#### Using ADF Plugins
```python
# Built-in plugins are automatically registered
markdown = """:::panel type="info"
This is an info panel with **bold** text.
:::

Status: {status:color=green}Complete{/status}
Due date: {date:2025-02-15}
CC: @john.doe"""

adf_result = generator.markdown_to_adf(markdown)
```

### Troubleshooting

#### Common Issues
1. **Asterisks appearing literally**: Ensure Cloud instance is detected correctly
2. **Performance slow**: Check cache hit rates and enable metrics monitoring
3. **Large tables truncated**: Expected behavior for performance (50+ rows)
4. **Nested lists limited**: Maximum 10 levels for performance optimization

#### Debugging Commands
```bash
# Test ADF conversion directly
uv run python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
result = router.convert_markdown('**test**', 'https://test.atlassian.net')
print(f'Format: {result[\"format\"]}, Type: {result[\"deployment_type\"]}')
"

# Check performance metrics
uv run python3 -c "
from mcp_atlassian.formatting.router import FormatRouter
router = FormatRouter()
router.convert_markdown('test', 'https://test.atlassian.net')
metrics = router.get_performance_metrics()
print(f'Metrics: {metrics}')
"
```

#### Log Analysis
- **Slow conversions**: Look for warnings about >50ms conversion times
- **Cache misses**: Monitor deployment detection cache efficiency
- **Truncation notices**: Expected for large content (tables, lists)
- **Error patterns**: Check error_rate in performance metrics

### Maintenance Procedures

#### Schema Updates
When Atlassian updates ADF schema:
1. Update plugin implementations in `adf_plugins.py` or create new plugins
2. Update ADF validator schema in `adf_validator.py` if needed
3. Run comprehensive test suite: `uv run pytest tests/unit/formatting/`
4. Validate with real API instances using integration tests
5. Update performance benchmarks if needed

#### Performance Tuning
- Monitor cache hit rates and adjust cache sizes accordingly
- Review truncation limits based on usage patterns
- Update performance thresholds if system capabilities change

#### Deployment Health Monitoring
- Track conversion success rates through performance metrics
- Monitor error patterns in logs for potential issues
- Validate format detection accuracy for new deployment types

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
