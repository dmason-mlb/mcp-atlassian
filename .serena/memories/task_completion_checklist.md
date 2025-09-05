# Task Completion Checklist

When completing any development task in this project, ensure you run these commands in order:

## 1. Code Quality Checks (REQUIRED)
Run these commands after any code changes:

```bash
# Format code
uv run ruff format

# Fix linting issues
uv run ruff check --fix

# Type checking
uv run mypy

# OR run all pre-commit checks at once
pre-commit run --all-files
```

## 2. Testing (REQUIRED)
Verify your changes don't break existing functionality:

```bash
# Run all tests
uv run pytest

# Run with coverage to ensure adequate test coverage
uv run pytest --cov=src/mcp_atlassian --cov-report=term-missing

# Run specific tests if needed
uv run pytest tests/path/to/relevant/test_file.py
```

## 3. Integration Testing (If Applicable)
For API-related changes or new features:

```bash
# Skip real API tests during development
uv run pytest -k "not test_real_api_validation"

# Test ADF formatting if working on formatting
uv run pytest tests/unit/formatting/ -v
```

## 4. Manual Testing (For Server Changes)
If you modified server functionality:

```bash
# Test basic server startup
uv run mcp-atlassian --help

# Test with verbose logging
uv run mcp-atlassian -vv

# Test specific debug scripts if relevant
python debug_confluence_formats.py  # For ADF changes
python debug_v2_adapter.py          # For API adapter changes
```

## 5. Documentation Updates (If Applicable)
- Update docstrings if you added/modified public APIs
- Update CLAUDE.md if you added new commands or workflows
- Update type annotations if function signatures changed

## IMPORTANT NOTES
- **NEVER commit without running code quality checks first**
- **All tests must pass before considering task complete**
- **Type checking errors must be resolved**
- **Follow the existing code patterns and conventions**
- **Use the debug scripts to validate specific functionality**