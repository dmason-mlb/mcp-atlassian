# MCP Atlassian Refactoring Analysis

## Overview

This analysis identifies the top files causing Claude Code context limit issues and provides prioritized refactoring recommendations to optimize the codebase for AI-assisted development.

## File Size Analysis

### Largest Files by Lines
| File | Lines | Characters | Priority |
|------|-------|------------|----------|
| `src/mcp_atlassian/servers/jira.py` | 1,657 | 56,239 | 🔥 Critical |
| `src/mcp_atlassian/jira/issues.py` | 1,596 | 63,364 | 🔥 Critical |
| `src/mcp_atlassian/rest/adapters.py` | 1,076 | 31,972 | 🔵 Medium |
| `src/mcp_atlassian/formatting/adf_plugins.py` | 1,018 | 32,633 | 🔶 High |
| `src/mcp_atlassian/jira/epics.py` | 946 | 40,839 | 🔵 Medium |
| `src/mcp_atlassian/formatting/adf_ast.py` | 879 | 32,123 | 🔶 High |
| `src/mcp_atlassian/rest/jira_v3.py` | 801 | 22,171 | 🔵 Medium |
| `src/mcp_atlassian/models/jira/issue.py` | 799 | 30,309 | 🔵 Medium |
| `src/mcp_atlassian/formatting/adf_enhanced.py` | 791 | 28,212 | 🔶 High |
| `src/mcp_atlassian/formatting/adf.py` | 776 | 29,568 | 🔶 High |

### Complexity Analysis
- **`servers/jira.py`**: 32 FastMCP tool definitions in a single file
- **Formatting module**: 4 overlapping ADF implementations (~120KB total)
- **Issues module**: Single massive mixin with all issue operations

## 🔥 Critical Priority Refactoring

### 1. Split `servers/jira.py` (1,657 lines → ~400 lines each)

**Current Problem**: Monolithic file with 32 FastMCP tool definitions

**Proposed Structure**:
```
servers/jira/
├── __init__.py          # Re-export all tools
├── issues.py           # Issue CRUD operations (8 tools)
├── search.py           # Search and field operations (6 tools)
├── agile.py            # Boards, sprints, epics (10 tools)
└── management.py       # Projects, users, transitions (8 tools)
```

**Expected Impact**: 75% reduction in file size, allows loading only relevant tool groups

### 2. Refactor `jira/issues.py` (1,596 lines → ~400 lines each)

**Current Problem**: Massive `IssuesMixin` with all issue operations

**Proposed Structure**:
```python
# Extract specialized mixins:
class IssueCreationMixin     # create_issue, batch_create
class IssueUpdateMixin       # update_issue, transition_issue  
class IssueSearchMixin       # search, get_issue, get_transitions
class IssueLinkingMixin      # link operations, epic linking
```

**Expected Impact**: 70% reduction in individual file sizes

## 🔶 High Priority Refactoring

### 3. Consolidate Formatting Module

**Current Problem**: 4 overlapping ADF implementations causing confusion
- `adf_plugins.py` (1,018 lines)
- `adf_ast.py` (879 lines) - Most modern implementation
- `adf_enhanced.py` (791 lines) - Deprecated
- `adf.py` (776 lines) - Deprecated

**Recommended Action**:
1. **Keep**: `adf_ast.py` as primary implementation
2. **Migrate**: Required features from deprecated files
3. **Remove**: `adf.py` and `adf_enhanced.py`
4. **Consolidate**: Plugin system into main AST implementation

**Expected Impact**: 50% reduction in formatting module size, eliminates confusion

### 4. Split `servers/confluence.py` (746 lines)

**Current Problem**: Same monolithic pattern as jira.py

**Proposed Structure**:
```
servers/confluence/
├── __init__.py
├── pages.py            # Page CRUD operations
├── search.py           # Search and user operations  
└── management.py       # Spaces, comments, labels
```

## 🔵 Medium Priority Refactoring

### 5. REST Adapters Refactoring
- **File**: `rest/adapters.py` (1,076 lines)
- **Action**: Split by service type and operation category
- **Expected Impact**: Better separation of concerns

### 6. Model Consolidation
- **Files**: `models/jira/issue.py` (799 lines), `models/jira/common.py` (583 lines)
- **Action**: Extract specialized model files by domain area
- **Expected Impact**: More focused model definitions

## Implementation Strategy

### Phase 1: Server Module Splitting (Week 1-2)
1. Create new directory structures
2. Extract tool functions to appropriate modules
3. Update imports in `__init__.py` files
4. Verify all tools are still accessible

### Phase 2: Formatting Consolidation (Week 3)
1. Audit feature differences between implementations
2. Migrate essential features to `adf_ast.py`
3. Update all imports to use consolidated module
4. Remove deprecated files

### Phase 3: Business Logic Refactoring (Week 4-5)
1. Split `jira/issues.py` into specialized mixins
2. Update inheritance chains
3. Verify functionality preservation

### Phase 4: Model and Infrastructure (Week 6)
1. Split large model files
2. Refactor REST adapters
3. Final optimization pass

## Expected Benefits

### Context Usage Reduction
- **75% reduction** in auto-compact frequency
- **60% smaller** individual file loading
- **Better modularity** for focused development

### Development Experience
- Faster Claude Code responses
- More targeted code analysis
- Reduced cognitive load when working on specific features
- Better parallel development capabilities

### Code Quality
- Improved separation of concerns
- Better testability through smaller modules
- Reduced merge conflicts
- Clearer architectural boundaries

## Risk Mitigation

### Testing Strategy
- Run full test suite after each phase
- Maintain integration test coverage
- Verify MCP protocol compliance
- Test all FastMCP tool registrations

### Backward Compatibility
- Preserve all public APIs through re-exports
- Maintain existing import paths during transition
- Document any breaking changes
- Provide migration guide if needed

## Success Metrics

- [ ] Largest file under 800 lines
- [ ] No single file consuming >30KB context
- [ ] 75% reduction in Claude Code auto-compact events
- [ ] All existing tests passing
- [ ] No breaking changes to public API

---

*Analysis completed: August 6, 2025*
*Files analyzed: 100+ Python files*
*Total codebase size: ~15,000 lines*