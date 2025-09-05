# Suggested Development Commands

## Environment Setup
- **Install dependencies**: `uv sync --frozen --all-extras --dev`
- **Activate virtual environment**: `source .venv/bin/activate` (macOS/Linux)
- **Install pre-commit hooks**: `pre-commit install`

## Testing Commands
- **Run all tests**: `uv run pytest`
- **Run tests with coverage**: `uv run pytest --cov=src/mcp_atlassian --cov-report=term-missing`
- **Run specific test**: `uv run pytest tests/path/to/test_file.py::test_function_name`
- **Skip real API tests**: `uv run pytest -k "not test_real_api_validation"`

## Code Quality (Run After Changes)
- **Run all pre-commit checks**: `pre-commit run --all-files`
- **Format code with Ruff**: `uv run ruff format`
- **Lint code with Ruff**: `uv run ruff check --fix`
- **Type checking with MyPy**: `uv run mypy`

## Running the Server
- **Standard MCP server**: `uv run mcp-atlassian`
- **With environment file**: `uv run mcp-atlassian --env-file .env`
- **With verbose logging**: `uv run mcp-atlassian -vv`
- **OAuth setup wizard**: `uv run mcp-atlassian --oauth-setup -v`
- **HTTP transport (SSE)**: `uv run mcp-atlassian --transport sse --port 9000`

## Debug Scripts (Available in Root Directory)
- **Debug ADF conversion**: `python debug_confluence_formats.py`
- **Simple Confluence testing**: `python debug_confluence_simple.py`
- **Page creation testing**: `python debug_page_creation.py`
- **V2 adapter testing**: `python debug_v2_adapter.py`
- **Test data creation**: `python create_seed_data.py`

## End-to-End Testing
- **Install Playwright dependencies**: `cd tests/e2e && npm run prep`
- **Seed test data**: `cd tests/e2e && npm run seed`
- **Run e2e tests**: `cd tests/e2e && npm run test`
- **Clean test data**: `cd tests/e2e && npm run clean`

## System Commands (macOS/Darwin)
- **List files**: `ls -la`
- **Find files**: `find . -name "*.py" -type f`
- **Search in files**: `grep -r "pattern" src/`
- **Git status**: `git status`
- **Git diff**: `git diff`