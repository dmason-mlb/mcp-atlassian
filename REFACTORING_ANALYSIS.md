# MCP Atlassian Codebase Refactoring Analysis

*Analysis Date: August 7, 2025*  
*Total Python Files: 222*  
*Total Lines of Code: 67,269*

## Executive Summary

The MCP Atlassian codebase contains several large files that are contributing to context limit issues in Claude Code. The analysis identifies 15 key files that should be prioritized for refactoring, with the top 5 files alone containing over 8,000 lines of code.

## Critical Files Requiring Immediate Refactoring

### 1. `src/mcp_atlassian/servers/jira.py` (1,657 lines, 56KB)
**Issue**: Monolithic server file containing 31 MCP tool definitions
**Impact**: High - Core server functionality causes frequent context inclusion
**Recommendations**:
- **Split by functional domain**: Create separate files for each major operation type:
  - `jira/issues_tools.py` - Issue CRUD operations
  - `jira/search_tools.py` - Search and query tools  
  - `jira/agile_tools.py` - Sprint, board, epic management
  - `jira/management_tools.py` - User, project, metadata operations
- **Keep server registration**: Main server file should only contain FastMCP instance and tool registration
- **Estimated reduction**: From 1,657 lines to ~200 lines (87% reduction)

### 2. `src/mcp_atlassian/jira/issues.py` (1,596 lines, 63KB)
**Issue**: Single class with 26 methods handling all issue operations
**Impact**: High - Core business logic frequently referenced
**Recommendations**:
- **Split by operation type**:
  - `jira/issues/crud.py` - Create, read, update, delete operations
  - `jira/issues/comments.py` - Comment management
  - `jira/issues/transitions.py` - Status and workflow operations
  - `jira/issues/attachments.py` - File operations
  - `jira/issues/links.py` - Issue linking and epic management
- **Create base class**: Abstract common functionality into `BaseIssueOperations`
- **Estimated reduction**: From 1,596 lines to 4-5 files of ~300-400 lines each

### 3. `src/mcp_atlassian/formatting/adf_plugins.py` (1,018 lines, 33KB)
**Issue**: 10 plugin classes in single file with complex regex patterns
**Impact**: Medium - ADF processing frequently used
**Recommendations**:
- **Split by plugin type**:
  - `formatting/plugins/block_plugins.py` - Panel, Expand, Layout plugins
  - `formatting/plugins/inline_plugins.py` - Status, Date, Mention, Emoji plugins
  - `formatting/plugins/media_plugins.py` - Media and attachment plugins
- **Keep plugin registry**: Main file should only contain base classes and registration
- **Estimated reduction**: From 1,018 lines to 3-4 files of ~200-300 lines each

### 4. `src/mcp_atlassian/rest/adapters.py` (1,078 lines, 32KB)
**Issue**: Adapter classes with 61 methods providing backward compatibility
**Impact**: Medium - REST layer abstraction
**Recommendations**:
- **Split by service**:
  - `rest/adapters/jira_adapter.py` - Jira-specific adapter methods
  - `rest/adapters/confluence_adapter.py` - Confluence-specific adapter methods
  - `rest/adapters/base.py` - Common adapter functionality
- **Group by operation**: Within each adapter, group related operations
- **Estimated reduction**: From 1,078 lines to 3 files of ~300-400 lines each

### 5. `src/mcp_atlassian/jira/epics.py` (946 lines, 41KB)
**Issue**: Epic operations mixing different concerns
**Impact**: Medium - Agile functionality
**Recommendations**:
- **Split by concern**:
  - `jira/epics/operations.py` - Core epic CRUD operations
  - `jira/epics/hierarchy.py` - Parent-child relationship management
  - `jira/epics/linking.py` - Epic linking to stories/tasks
- **Estimated reduction**: From 946 lines to 3 files of ~300 lines each

## Test File Optimization

### Large Test Files to Refactor

1. **`tests/unit/models/test_jira_models.py`** (1,946 lines, 76KB, 68 test functions)
   - Split by model type: `test_issue_models.py`, `test_project_models.py`, `test_search_models.py`

2. **`tests/unit/jira/test_issues.py`** (1,698 lines, 65KB)
   - Split by operation: `test_issue_crud.py`, `test_issue_comments.py`, `test_issue_transitions.py`

3. **`tests/unit/servers/test_jira_server.py`** (1,150 lines, 39KB)
   - Split by tool category following the same pattern as the server refactoring

## Secondary Priority Files

### Medium Impact Files (500-900 lines)
- `src/mcp_atlassian/formatting/adf_ast.py` (879 lines) - Split AST processing by node types
- `src/mcp_atlassian/rest/jira_v3.py` (804 lines) - Split REST client by API groupings
- `src/mcp_atlassian/models/jira/issue.py` (799 lines) - Split complex models by concerns

## Implementation Strategy

### Phase 1: Core Server Refactoring (Priority 1)
1. **Week 1**: Split `servers/jira.py` into functional domains
2. **Week 2**: Refactor `jira/issues.py` into operation-specific modules
3. **Week 3**: Split ADF plugins and adapters

### Phase 2: Test Organization (Priority 2)
1. **Week 4**: Refactor large test files following new source structure
2. **Week 5**: Update test utilities and fixtures

### Phase 3: Secondary Optimizations (Priority 3)
1. **Week 6**: Address medium-impact files
2. **Week 7**: Consolidate and validate refactoring

## Expected Benefits

### Context Usage Reduction
- **Estimated 60-70% reduction** in context usage for common operations
- **Improved incremental loading** - only load relevant modules
- **Better caching efficiency** - smaller, focused files

### Development Experience
- **Easier navigation** - logical file organization
- **Reduced merge conflicts** - isolated changes
- **Faster IDE operations** - smaller file parsing

### Maintainability
- **Single responsibility** - each file has clear purpose
- **Better testability** - focused test files
- **Improved code review** - smaller, targeted changes

## Risk Mitigation

### Potential Risks
1. **Import complexity** - More files mean more imports
2. **Circular dependencies** - Risk when splitting tightly coupled code
3. **Breaking changes** - Public API modifications

### Mitigation Strategies
1. **Preserve public APIs** - Keep existing imports working via `__init__.py` files
2. **Dependency injection** - Use protocols and dependency injection to avoid circular imports
3. **Gradual migration** - Implement changes incrementally with backward compatibility
4. **Comprehensive testing** - Ensure all existing tests pass after refactoring

## File Size Targets

### Target Sizes After Refactoring
- **Server files**: 200-400 lines (tool registration only)
- **Service modules**: 300-500 lines (focused operations)
- **Model files**: 200-400 lines (related models grouped)
- **Test files**: 300-600 lines (focused test suites)
- **Plugin files**: 200-300 lines (single responsibility)

### Success Metrics
- No single file exceeds 800 lines
- Average file size under 400 lines
- Context window usage reduced by 60%+
- All existing functionality preserved
- No performance degradation

## Detailed File Analysis

### Top 15 Files by Size (Excluding Tests)
| Rank | File | Lines | Size | Impact | Recommendation |
|------|------|-------|------|---------|----------------|
| 1 | `servers/jira.py` | 1,657 | 56KB | Critical | Split into 4 domain files |
| 2 | `jira/issues.py` | 1,596 | 63KB | Critical | Split into 5 operation files |
| 3 | `rest/adapters.py` | 1,078 | 32KB | Medium | Split by service type |
| 4 | `formatting/adf_plugins.py` | 1,018 | 33KB | High | Split by plugin type |
| 5 | `jira/epics.py` | 946 | 41KB | Medium | Split by concern |
| 6 | `formatting/adf_ast.py` | 879 | 32KB | Medium | Keep as primary ADF impl |
| 7 | `rest/jira_v3.py` | 804 | 22KB | Low | Split by API grouping |
| 8 | `models/jira/issue.py` | 799 | 30KB | Low | Split by model complexity |
| 9 | `servers/confluence.py` | 746 | 25KB | Medium | Split by operation type |
| 10 | `jira/search.py` | 698 | 24KB | Low | Acceptable size |
| 11 | `confluence/pages.py` | 654 | 23KB | Low | Acceptable size |
| 12 | `models/confluence/page.py` | 612 | 21KB | Low | Acceptable size |
| 13 | `jira/boards.py` | 588 | 20KB | Low | Acceptable size |
| 14 | `models/jira/common.py` | 583 | 19KB | Low | Acceptable size |
| 15 | `confluence/search.py` | 563 | 19KB | Low | Acceptable size |

## Conclusion

This refactoring plan addresses the root cause of context limit issues by systematically breaking down large files into focused, maintainable modules. The proposed changes will significantly improve Claude Code's ability to work with the codebase while enhancing overall code quality and maintainability.

**Next Steps**: Begin with Phase 1 implementation, starting with `servers/jira.py` as it has the highest impact on context usage.