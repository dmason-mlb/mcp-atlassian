# MCP Atlassian Server - Issues to Fix

**Generated:** 2025-08-07  
**Testing Environment:** MLB Atlassian Cloud  
**Priority Levels:** 🔴 Critical | 🟡 High | 🟢 Medium | ⚪ Low

## 🔴 Critical Issues (Must Fix)

### 1. ADF Format Support Missing
**Location:** All text input operations  
**Impact:** Cannot create issues with descriptions, add comments, or use any rich text features  
**Error:** "Operation value must be an Atlassian Document (see the Atlassian Document Format)"  
**Fix Required:** Implement proper ADF document structure for all text fields  

### 2. Worklog Implementation Broken
**Location:** `jira_add_worklog` tool  
**Impact:** Cannot log time on issues  
**Error:** "'dict' object has no attribute 'to_simplified_dict'"  
**Fix Required:** Fix the worklog object serialization and ensure proper API payload structure  

### 3. Comment System Non-Functional
**Location:** `jira_add_comment` tool  
**Impact:** Cannot add comments to issues  
**Error:** "Comment body is not valid!"  
**Fix Required:** Implement ADF format for comment bodies  

## 🟡 High Priority Issues

### 4. User Resolution Failure
**Location:** `jira_get_user_profile`  
**Impact:** Cannot resolve email addresses to account IDs  
**Error:** "Could not resolve email 'douglas.mason@mlb.com' to a valid account ID"  
**Fix Required:** Implement proper user lookup mechanism for Cloud instances  

### 5. Confluence Page Creation Error
**Location:** `confluence_pages_create_page`  
**Impact:** Cannot create Confluence pages  
**Error:** Generic "Error calling tool 'create_page'"  
**Fix Required:** Debug and fix the Confluence page creation endpoint  

### 6. Story Issue Type Creation Fails
**Location:** `jira_create_issue` with Story type  
**Impact:** Cannot create Story issues with additional fields  
**Error:** Generic error when additional_fields provided  
**Fix Required:** Fix field handling for different issue types  

## 🟢 Medium Priority Issues

### 7. Transition Comments Not Supported
**Location:** `jira_transition_issue`  
**Impact:** Cannot add comments during status transitions  
**Error:** ADF validation error on comment field  
**Fix Required:** Support ADF format in transition comments  

### 8. Missing Markdown to ADF Converter
**Location:** Throughout the codebase  
**Impact:** Users must manually format ADF documents  
**Fix Required:** Add automatic markdown to ADF conversion  

### 9. Poor Error Messages
**Location:** Various tools  
**Impact:** Difficult to debug issues  
**Fix Required:** Improve error handling and provide clearer messages  

## ⚪ Low Priority Enhancements

### 10. No Batch Operations Support
**Location:** Issue operations  
**Impact:** Inefficient for bulk operations  
**Fix Required:** Add batch create/update/delete endpoints  

### 11. Missing Retry Logic
**Location:** All API calls  
**Impact:** Transient failures cause operation failures  
**Fix Required:** Implement exponential backoff retry  

### 12. No Caching Layer
**Location:** Frequently accessed data  
**Impact:** Unnecessary API calls  
**Fix Required:** Add caching for project info, user data, etc.  

## Root Cause Analysis

The primary issue is that the MCP server was likely developed against an older version of the Atlassian API or Jira Server/Data Center, which used plain text for many fields. Atlassian Cloud now requires ADF (Atlassian Document Format) for all rich text fields.

## Recommended Fix Order

1. **Implement ADF Support** - This will fix multiple issues at once
2. **Fix Worklog Implementation** - Core functionality
3. **Fix User Resolution** - Needed for many operations
4. **Add Markdown Converter** - Improve usability
5. **Improve Error Handling** - Better debugging

## Testing Requirements

After fixes are implemented:
- Re-test all failed operations
- Add unit tests for ADF conversion
- Add integration tests for Cloud API
- Document ADF requirements in README

---
*This document should be updated as issues are resolved*