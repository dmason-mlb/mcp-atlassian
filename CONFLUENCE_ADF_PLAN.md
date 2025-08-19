# Confluence ADF Migration & API Version Remediation Plan

## Overview
This plan describes the steps to migrate the MCP Atlassian server to use Confluence v2 API with ADF (Atlassian Document Format) as the default content format, while cleaning up legacy API usage.
**Scope:** Personal use only. No external rollouts. The plan doubles as a living document, updated as progress is made.

## Executive Summary
- **Primary Issue**: ConfluenceV2Client hardcodes `"representation": "storage"` in several locations.
- **Status**: ADF generation is already supported via FormatRouter. Incorrect assumption in client is preventing its use.
- **Risk Level**: Low. Changes are localized to Confluence client and adapter.
- **Server/DC Support**: To be deprecated later; current focus is Cloud (v3/v2 + ADF).

---

## A) Phase Plan

### P0: Foundation & Analysis ✅
- **Status**: Complete.
- **Deliverables**:
  - Identified hardcoded storage usage.
  - Verified ADF support in Confluence v2.
  - Determined Jira is already v3 compliant except for one v2 permission search call.

### P1: Minimal Feature Flag
- **Scope**: Add a single environment toggle for ADF.
- **Deliverables**:
  - `CONFLUENCE_USE_ADF=true|false` in config.
  - Used by ConfluenceV2Client to choose representation.
- **Zen MCP Tooling**: None required beyond light `codereview` (grok-4) to confirm consistent flag injection.
- **Status**: Pending.

### P2: ConfluenceV2Client Format Awareness
- **Scope**: Replace hardcoded `"storage"` with a format parameter.
- **Deliverables**:
  - Client methods accept `format_param`.
  - Default behavior uses ADF when `CONFLUENCE_USE_ADF=true`.
- **Zen MCP Tooling**: `precommit` (o3) before merging.
- **Status**: Pending.

### P3: Adapter Integration
- **Scope**: Connect FormatRouter to ConfluenceAdapter.
- **Deliverables**:
  - Cloud → ADF; Server/DC → storage.
  - Use feature flag for override.
- **Zen MCP Tooling**: `codereview` (grok-4) for integration safety.
- **Status**: Pending.

### P4: Validation & Risk Mitigation
- **Scope**: Integrate schema validation for ADF.
- **Deliverables**:
  - `ADFValidator` module.
  - Strict by default; override available.
- **Zen MCP Tooling**: `consensus` (o3 vs grok-4) to decide validation strictness.
- **Status**: Pending.

### P5: Cleanup & Documentation
- **Scope**: Update fixtures, remove legacy paths, document Cloud-first assumption.
- **Deliverables**:
  - Fixtures updated to use ADF.
  - Plan file (`CONFLUENCE_ADF_PLAN.md`) updated to mark completed phases.
- **Zen MCP Tooling**: `precommit` (o3) before commit.
- **Status**: Pending.

---

## B) Change Map

| File | Lines | Current | Change | Phase |
|------|-------|---------|--------|-------|
| `src/mcp_atlassian/rest/confluence_v2.py` | 127,163,361,407 | `"representation":"storage"` | Use `format_param` | P2 |
| `src/mcp_atlassian/rest/confluence_adapter.py` | 187–224, 249–287 | ADF logic exists | Connect to FormatRouter | P3 |
| `jira/users.py` | 181 | `/rest/api/2/user/permission/search` | Switch to v3 equivalent | P2 |

---

## C) Feature Flag

- **Variable**: `CONFLUENCE_USE_ADF`
- **Values**: `true|false`
- **Default**: `true` (Cloud assumption)
- **Emergency fallback**: Set to `false` to revert to storage.

---

## D) ADF Schema Validation

- **Levels**: strict | lenient | skip
- **Override**: env var `CONFLUENCE_ADF_VALIDATE=skip`
- **Errors**: raise by default; fallback to storage if override is set.

---

## E) Validation & Risk Management

- **Risks**:
  - ADF validation failures → fallback to storage.
  - Performance overhead → negligible, but can disable validation.
  - Future schema changes → update validator schema.

- **Monitoring**:
  - Log ADF vs storage decisions.
  - Log validation failures with summaries.

- **Fallback**:
  - Single flag toggle to revert entirely to storage.

---

## F) Acceptance Criteria

- Confluence client methods accept `format_param`.
- Default Cloud behavior sends `"representation":"atlas_doc_format"`.
- ADF schema validation runs unless disabled.
- Jira user permission search endpoint upgraded to v3.
- Tests pass with ADF enabled.
- One-flag fallback works.

---

## G) Open Questions

1. Should validation be strict or lenient by default? (`consensus` run pending)
2. Do we need any migration of historical storage-format content, or just focus on new writes?
3. How to best handle fixture migration (bulk rewrite vs phased)?

---

## Tests Modernized / Recovery Complete

**Date**: 2025-08-19  
**Status**: ✅ **COMPLETE**

### E2E Test Restoration
- **Confluence Tools**: All 11 Confluence tools restored and functional
- **Jira Tools**: Tool naming compatibility restored via aliases
- **E2E Seed**: Successfully runs and creates test data (FTEST-185, page 5042241547)
- **ADF Support**: Maintained throughout recovery process

### Jira Alias Addition
Added backward-compatible tool name aliases to maintain E2E compatibility:
- `issues_create_issue` → `create_issue` (alias added to maintain legacy E2E expectations)
- Missing `upload_attachment` tool restored from workflow module
- All aliases maintain Jira v3 API usage exclusively

### Recovery Validation
- ✅ Confluence v2 API + ADF patterns preserved
- ✅ Jira v3 API patterns maintained
- ✅ E2E tests functional with restored tool names
- ✅ No regressions introduced to existing functionality

---

## Implementation Notes

- **Zen MCP Integration**:
  - Use `thinkdeep` (grok-4) to evaluate fixture migration strategy.
  - Use `consensus` (o3 vs grok-4) to decide on validation strictness.
  - Use `codereview` (grok-4) for adapter integration.
  - Use `precommit` (o3) before each merge.
- **Living Plan**: This file (`CONFLUENCE_ADF_PLAN.md`) is updated each time progress is made, marking statuses as ✅ or Pending.
