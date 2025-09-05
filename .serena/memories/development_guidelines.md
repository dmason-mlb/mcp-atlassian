# Development Guidelines and Best Practices

## Adding New MCP Tools

### 1. Service Module Implementation
- Add tool in appropriate service module (`src/mcp_atlassian/jira/` or `src/mcp_atlassian/confluence/`)
- Follow existing patterns for error handling and logging
- Use service-specific client classes for API access

### 2. Data Models
- Add corresponding Pydantic models in `src/mcp_atlassian/models/`
- Separate models by service (jira/ vs confluence/ subdirectories)
- Inherit from base classes when appropriate

### 3. Server Registration
- Register tools in `src/mcp_atlassian/servers/{jira,confluence}.py`
- Use proper tool filtering and access control
- Add appropriate middleware if needed

### 4. Testing
- Write unit tests with mock fixtures in `tests/fixtures/`
- Add integration tests for complex API behavior
- Use existing patterns from `tests/fixtures/{jira,confluence}_mocks.py`

## Working with ADF (Atlassian Document Format)

### Format Detection
- System automatically detects Cloud vs Server/DC deployments
- Cloud instances (*.atlassian.net) use ADF JSON format
- Server/DC instances use wiki markup strings

### Adding ADF Plugins
- Create plugins in `src/mcp_atlassian/formatting/`
- Follow plugin architecture patterns from existing plugins
- Register plugins in `ASTBasedADFGenerator`
- Test with `debug_confluence_formats.py` script

### Debugging ADF Issues
```bash
# Test format detection and conversion
python debug_confluence_formats.py

# Run ADF-specific tests
uv run pytest tests/unit/formatting/ -v

# Check performance metrics
# (See CLAUDE.md for specific debugging commands)
```

## Authentication and Configuration

### Multi-Auth Support
The system supports multiple authentication methods:
1. **API Token** (Cloud): Username + API token
2. **Personal Access Token** (Server/DC): PAT-based auth
3. **OAuth 2.0** (Cloud): Standard OAuth flow
4. **BYOT OAuth** (Cloud): External token management
5. **Multi-user HTTP**: Per-request authentication

### Configuration Management
- Environment variables take precedence over CLI flags
- Config classes handle validation and defaults
- Service availability auto-detected from URL + auth config

## Code Organization Principles

### Service Separation
- Keep Jira and Confluence completely independent
- No cross-service imports in service modules
- Shared functionality in utils/ and models/base.py

### Error Handling
- Use custom exceptions from `exceptions.py`
- Implement graceful degradation for API failures
- Comprehensive logging with proper levels
- Mask sensitive information in logs

### Performance Considerations
- Use caching for expensive operations (format detection, field lookups)
- Implement size limits for large data structures (tables, lists)
- Monitor conversion performance and optimize as needed

## Testing Strategy

### Unit Tests
- Mock external API calls using fixtures
- Test business logic independently
- Focus on edge cases and error conditions

### Integration Tests  
- Test MCP protocol compliance
- Verify cross-service functionality
- Use real API tests sparingly (marked with special decorator)

### End-to-End Tests
- Playwright-based browser automation
- Seed test data scripts for consistent testing
- Clean up test data after runs

## Debugging and Troubleshooting

### Debug Scripts
Several debug scripts available in project root:
- `debug_confluence_formats.py`: ADF conversion testing
- `debug_confluence_simple.py`: Basic Confluence functionality
- `debug_page_creation.py`: Page creation workflows
- `debug_v2_adapter.py`: API adapter functionality

### Common Issues
1. **Format detection failures**: Check URL patterns and caching
2. **Authentication errors**: Verify config and credential masking
3. **Performance issues**: Monitor cache hit rates and conversion times
4. **API version mismatches**: Update adapter logic as needed