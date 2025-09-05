# Code Style and Conventions

## Code Formatting (Ruff Configuration)
- **Line length**: 88 characters
- **Indentation**: 4 spaces (not tabs)
- **Quote style**: Double quotes preferred
- **Target Python version**: 3.10+

## Type Annotations
- **Required**: All public functions must have type annotations
- **Modern syntax**: Use pipe union syntax `str | None` instead of `Optional[str]`
- **Modern collections**: Use `list[str]`, `dict[str, Any]` instead of `List[str]`, `Dict[str, Any]`
- **Return types**: Always specify return types for functions

## Documentation
- **Docstrings**: Google-style docstrings for all public APIs
- **Module docstrings**: Brief description at top of modules
- **Class docstrings**: Purpose and key attributes
- **Method docstrings**: Args, Returns, and Raises sections where applicable

## Import Organization
- **Standard library imports first**
- **Third-party imports second**
- **Local application imports last**
- **Absolute imports preferred** over relative imports
- **Specific imports** preferred: `from module import Class` vs `import module`

## Naming Conventions
- **Classes**: PascalCase (e.g., `JiraClient`, `ConfluenceConfig`)
- **Functions/Methods**: snake_case (e.g., `get_issue`, `create_page`)
- **Variables**: snake_case (e.g., `auth_type`, `base_url`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Private members**: Leading underscore (e.g., `_field_ids_cache`)

## Error Handling
- **Custom exceptions**: Defined in `src/mcp_atlassian/exceptions.py`
- **Specific exception types**: Use `MCPAtlassianAuthenticationError` vs generic `ValueError`
- **Logging**: Use module-specific loggers with proper levels
- **Graceful degradation**: Handle API failures with fallbacks

## Class Structure
- **Type hints**: All attributes should be type-hinted at class level
- **Initialization**: Clear `__init__` methods with parameter validation
- **Configuration classes**: Use Pydantic models or dataclasses
- **Client classes**: Separate concerns (auth, API calls, preprocessing)

## File Organization Patterns
- **Service modules**: Separate files for major functionality (issues, pages, search)
- **Model definitions**: Pydantic models in `models/` subdirectories
- **Configuration**: Environment-based config classes
- **Utilities**: Shared functionality in `utils/` directory
- **Mixins**: Reusable functionality in appropriate mixin classes