# Context Optimization Plan for MCP Atlassian

## Problem Statement

The MCP Atlassian codebase has several files over 1,000 lines that are causing frequent auto-compact loops and context limit issues when working with Claude Code. The largest files are:

1. `src/mcp_atlassian/servers/jira.py` (1,657 lines)
2. `src/mcp_atlassian/jira/issues.py` (1,596 lines) 
3. `src/mcp_atlassian/rest/adapters.py` (1,078 lines)
4. `src/mcp_atlassian/formatting/adf_plugins.py` (1,018 lines)

## Refactoring Strategy Considering FastMCP Constraints

Based on the analysis in `docs/REFACTOR_LIMITATIONS.md`, FastMCP imposes specific constraints that limit how we can refactor server files. However, business logic and supporting files have more flexibility.

## Priority 1: Split Large Server Files (Within FastMCP Constraints)

### `src/mcp_atlassian/servers/jira.py` (1,657 lines) - **HIGHEST PRIORITY**

**Problem**: Monolithic file with 30+ tool definitions causing severe context issues.

**FastMCP-Compatible Solution**: Split by logical tool groups while maintaining decorator requirements.

**Proposed Structure**:
```
src/mcp_atlassian/servers/jira/
├── __init__.py                 # Main server instance and imports
├── core_tools.py              # Basic CRUD operations (get_issue, create_issue, etc.)
├── search_tools.py            # Search and JQL operations  
├── workflow_tools.py          # Status transitions, worklogs, comments
├── project_tools.py           # Project and version management
├── epic_tools.py              # Epic-specific operations
├── agile_tools.py             # Board, sprint operations
└── management_tools.py        # Links, attachments, advanced operations
```

**Implementation Approach**:
1. Each file defines its own tools with decorators: `@jira_mcp.tool()`
2. Main `__init__.py` imports all tool modules to register decorators
3. Maintains FastMCP's module-level decorator discovery
4. Each file ~200-300 lines max

**Benefits**:
- Reduces context load from 1,657 lines to ~200-300 lines per file
- Maintains FastMCP compatibility 
- Logical organization for development

### Similar Approach for Confluence Server (if applicable)

Apply same pattern to confluence server files if they exist and are large.

## Priority 2: Refactor Business Logic Files (More Flexibility)

### `src/mcp_atlassian/jira/issues.py` (1,596 lines) - **HIGH PRIORITY**

**Problem**: Massive IssuesMixin class with complex business logic.

**Proposed Solution**: Extract specialized mixins and utility modules.

**Proposed Structure**:
```
src/mcp_atlassian/jira/issues/
├── __init__.py                # Main IssuesMixin combining all
├── core.py                   # Basic CRUD operations
├── fields.py                 # Field processing and validation  
├── search.py                 # Search and JQL operations
├── batch.py                  # Batch operations
├── epic.py                   # Epic link operations
├── transitions.py            # Status and workflow operations
└── validation.py             # Input validation utilities
```

**Implementation Approach**:
1. Extract logical groups into separate mixin classes
2. Main IssuesMixin inherits from all specialized mixins
3. Maintains existing public interface for server compatibility
4. Each file ~200-300 lines max

### `src/mcp_atlassian/jira/epics.py` (946 lines)

**Proposed Solution**: Split into Epic operations and Epic data management.

**Structure**:
```
src/mcp_atlassian/jira/epics/
├── __init__.py               # Main EpicMixin
├── operations.py             # Epic CRUD operations
└── hierarchy.py              # Epic-issue relationships
```

## Priority 3: Split Supporting Infrastructure

### `src/mcp_atlassian/rest/adapters.py` (1,078 lines) - **MEDIUM PRIORITY**

**Problem**: Large adapter file handling multiple services.

**Proposed Solution**: Split by service type.

**Structure**:
```
src/mcp_atlassian/rest/adapters/
├── __init__.py               # Common base classes
├── jira.py                   # Jira-specific adapters
├── confluence.py             # Confluence-specific adapters
└── common.py                 # Shared utilities
```

### `src/mcp_atlassian/formatting/adf_plugins.py` (1,018 lines) - **MEDIUM PRIORITY** 

**Problem**: Monolithic plugin system file.

**Proposed Solution**: Split into individual plugin files.

**Structure**:
```
src/mcp_atlassian/formatting/plugins/
├── __init__.py               # Plugin registry
├── panel.py                  # Panel plugin
├── media.py                  # Media plugin  
├── expand.py                 # Expand plugin
├── status.py                 # Status plugin
├── date.py                   # Date plugin
├── mention.py                # Mention plugin
├── emoji.py                  # Emoji plugin
└── layout.py                 # Layout plugin
```

## Priority 4: Optimize Test Files

### Large Test Files (>1000 lines each)
- `tests/unit/models/test_jira_models.py` (1,946 lines)
- `tests/unit/jira/test_issues.py` (1,698 lines)  
- `tests/test_real_api_validation.py` (1,479 lines)
- `tests/unit/servers/test_jira_server.py` (1,150 lines)

**Proposed Solution**: Split test files by functional area.

**Example for `test_jira_models.py`**:
```
tests/unit/models/jira/
├── test_issue_models.py      # Issue-related models
├── test_project_models.py    # Project-related models  
├── test_user_models.py       # User-related models
└── test_workflow_models.py   # Workflow-related models
```

## Implementation Plan

### Phase 1: Critical Server Files (Weeks 1-2)
1. **Split `jira.py` server file** - Highest impact on context limits
2. Test tool discovery and functionality after split
3. Update imports and registration in main server

### Phase 2: Business Logic (Weeks 3-4)  
1. **Refactor `issues.py` IssuesMixin** - Second highest impact
2. Extract logical mixins while preserving public interface
3. Ensure server compatibility maintained

### Phase 3: Infrastructure (Weeks 5-6)
1. Split REST adapters by service
2. Modularize ADF plugin system  
3. Update imports across codebase

### Phase 4: Test Optimization (Weeks 7-8)
1. Split oversized test files by functional area
2. Maintain test coverage and organization
3. Update CI/CD test discovery

## Expected Benefits

### Context Efficiency
- **Primary files reduced from 1,600+ lines to ~250 lines each**
- Claude Code should rarely hit context limits on individual files
- Auto-compact loops should be dramatically reduced

### Development Experience  
- Easier to navigate and understand code
- Better separation of concerns
- Reduced merge conflicts
- Improved maintainability

### FastMCP Compatibility
- All proposed changes maintain FastMCP decorator requirements
- Server tool registration unchanged from client perspective
- Business logic interfaces preserved

## Risk Mitigation

### Potential Issues
1. **Import complexity**: More files means more imports to manage
2. **Tool registration**: FastMCP decorator discovery might be affected
3. **Circular dependencies**: Need careful dependency management

### Mitigation Strategies
1. Use clear import patterns and `__init__.py` files
2. Test tool registration thoroughly after splits
3. Design modules with clean dependency graphs
4. Maintain comprehensive test coverage during refactoring

## Success Metrics

1. **Context Usage**: No individual file over 500 lines (target: 300 lines max)
2. **Claude Code Performance**: Elimination of auto-compact loops during normal development
3. **Functionality**: All existing MCP tools continue to work identically
4. **Test Coverage**: Maintain 100% of existing test coverage
5. **Build Performance**: No regression in build/test times

## Conclusion

This refactoring plan prioritizes the largest context-consuming files while respecting FastMCP's architectural constraints. The server file split should provide immediate relief from context limits, while the business logic refactoring will improve long-term maintainability.

The key insight is that FastMCP constrains how we organize *tool definitions* but gives us flexibility in organizing *business logic*. By splitting large server files into logical tool groups and extracting business logic into focused modules, we can dramatically reduce context usage while maintaining full functionality.