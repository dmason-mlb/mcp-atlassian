# MCP Atlassian Tool Test Suite

This document defines a comprehensive test suite for the MCP Atlassian server tools, focusing on actual MCP functionality rather than browser UI validation. These tests ensure that all tools work correctly with proper data formatting, ADF conversion, and API interactions.

## Environment Configuration

Tests use the following environment variables from `.env`:
- `JIRA_PROJECT=FTEST` - Test project for Jira issues
- `CONFLUENCE_SPACE=~911651470` - Test space for Confluence pages
- `ATLASSIAN_URL=https://baseball.atlassian.net` - Base Atlassian instance
- `MCP_URL=http://localhost:9001/mcp` - MCP server endpoint

## Test Categories

### 1. Jira Issues Tests

#### 1.1 Issue Creation Tests (`test_jira_issue_creation`)
Test comprehensive issue creation with various formatted content:

**Basic Issue Creation:**
```json
{
  "tool": "jira_issues_create_issue",
  "input": {
    "project_key": "FTEST",
    "summary": "MCP Test Issue - Basic Creation",
    "issue_type": "Task",
    "description": "# Basic Test Issue\n\nThis is a **test issue** created via MCP with *formatted* content:\n\n- Bullet point 1\n- Bullet point 2\n  - Nested bullet\n\n```python\nprint('Hello MCP')\n```\n\n> This is a blockquote for testing ADF conversion.",
    "assignee": "douglas.mason@mlb.com"
  }
}
```

**Rich Formatted Issue Creation:**
```json
{
  "tool": "jira_issues_create_issue",
  "input": {
    "project_key": "FTEST",
    "summary": "MCP Test - Rich Formatting Elements",
    "issue_type": "Story",
    "description": "# Comprehensive Formatting Test\n\n## Text Formatting\n**Bold text**, *italic text*, ~~strikethrough~~, `inline code`\n\n## Lists\n1. Ordered list item 1\n2. Ordered list item 2\n   - Nested unordered\n   - Another nested item\n\n## Code Blocks\n```javascript\nfunction testMCP() {\n  console.log('Testing MCP functionality');\n  return true;\n}\n```\n\n## Tables\n| Column 1 | Column 2 | Column 3 |\n|----------|----------|----------|\n| Cell 1   | Cell 2   | Cell 3   |\n| Data A   | Data B   | Data C   |\n\n## ADF-Specific Elements\n:::panel type=\"info\"\nThis is an info panel with **formatted content**.\n:::\n\n{status:color=green}In Progress{/status}\n\nDue date: {date:2025-02-15}\n\n## Links\n[External Link](https://example.com)\n\n## Blockquotes\n> Important note about this feature\n> with multiple lines",
    "additional_fields": {
      "priority": {"name": "High"},
      "labels": ["mcp-test", "formatting", "adf"]
    }
  }
}
```

**Epic Creation:**
```json
{
  "tool": "jira_issues_create_issue",
  "input": {
    "project_key": "FTEST",
    "summary": "MCP Test Epic - Feature Development",
    "issue_type": "Epic",
    "description": "# Epic: MCP Integration Testing\n\n## Objectives\n- Test all MCP tools\n- Validate ADF conversion\n- Ensure proper formatting\n\n## Success Criteria\n:::panel type=\"success\"\n- [ ] All tools function correctly\n- [ ] ADF rendering works\n- [ ] Error handling is robust\n:::\n\n## Timeline\nTarget completion: {date:2025-03-01}",
    "additional_fields": {
      "customfield_10011": "MCP-EPIC-001"
    }
  }
}
```

#### 1.2 Issue Update Tests (`test_jira_issue_updates`)

**Basic Field Updates:**
```json
{
  "tool": "jira_issues_update_issue",
  "input": {
    "issue_key": "{created_issue_key}",
    "fields": {
      "summary": "UPDATED: MCP Test Issue - Modified Title",
      "priority": {"name": "Critical"},
      "labels": ["mcp-test", "updated", "priority-changed"]
    }
  }
}
```

**Description Update with Rich Content:**
```json
{
  "tool": "jira_issues_update_issue",
  "input": {
    "issue_key": "{created_issue_key}",
    "fields": {
      "description": "# UPDATED Description\n\n## What Changed\n- Updated via MCP tool\n- Added new formatting elements\n- Testing update functionality\n\n## New Content\n:::panel type=\"warning\"\n**Important Update**: This issue has been modified through MCP testing.\n:::\n\n### Progress Update\n{status:color=blue}Under Review{/status}\n\n### Code Changes\n```diff\n- old functionality\n+ new MCP integration\n```\n\n### Next Steps\n1. ✅ Create issue via MCP\n2. ✅ Update issue description\n3. 🔄 Add comments\n4. ⏳ Test transitions"
    }
  }
}
```

#### 1.3 Comment Tests (`test_jira_comments`)

**Basic Comment:**
```json
{
  "tool": "jira_issues_add_comment",
  "input": {
    "issue_key": "{created_issue_key}",
    "comment": "# MCP Test Comment\n\nThis comment was added via **MCP tools** to validate:\n\n- Comment creation functionality\n- Markdown to ADF conversion\n- Rich text rendering\n\n`Testing inline code` in comments."
  }
}
```

**Rich Formatted Comment:**
```json
{
  "tool": "jira_issues_add_comment",
  "input": {
    "issue_key": "{created_issue_key}",
    "comment": "## Progress Update via MCP\n\n### Current Status\n{status:color=green}Completed{/status}\n\n### Test Results\n| Test Case | Result | Notes |\n|-----------|--------|-------|\n| Issue Creation | ✅ Pass | Created successfully |\n| Description Format | ✅ Pass | ADF conversion working |\n| Comment Creation | 🔄 Testing | Currently validating |\n\n### Next Actions\n:::panel type=\"note\"\n1. Validate all formatting elements\n2. Test error scenarios\n3. Verify cleanup procedures\n:::\n\n### Code Reference\n```bash\n# MCP tool usage\nmcp-atlassian jira_issues_add_comment --issue-key FTEST-123\n```\n\n**Assigned to:** @douglas.mason@mlb.com\n**Due:** {date:2025-02-20}"
  }
}
```

#### 1.4 Issue Transition Tests (`test_jira_transitions`)

**Get Available Transitions:**
```json
{
  "tool": "jira_management_get_transitions",
  "input": {
    "issue_key": "{created_issue_key}"
  }
}
```

**Transition with Comment:**
```json
{
  "tool": "jira_issues_transition_issue",
  "input": {
    "issue_key": "{created_issue_key}",
    "transition_id": "{transition_id}",
    "comment": "## Status Change via MCP\n\nTransitioning issue through MCP tools to validate:\n\n- Transition functionality\n- Comment addition during transition\n- Workflow state management\n\n:::panel type=\"info\"\n**Automated Change**: This transition was performed by MCP testing suite.\n:::\n\n### Validation Steps\n1. ✅ Retrieved available transitions\n2. ✅ Selected appropriate transition\n3. 🔄 Executing transition with comment\n\n{status:color=blue}In Progress{/status}"
  }
}
```

#### 1.5 Issue Linking Tests (`test_jira_linking`)

**Link to Epic:**
```json
{
  "tool": "jira_management_link_to_epic",
  "input": {
    "issue_key": "{created_issue_key}",
    "epic_key": "{created_epic_key}"
  }
}
```

**Create Issue Link:**
```json
{
  "tool": "jira_management_create_issue_link",
  "input": {
    "link_type": "Relates",
    "inward_issue_key": "{created_issue_key}",
    "outward_issue_key": "{related_issue_key}",
    "comment": "**Linked via MCP Tools**\n\nThis link was created to test:\n- Issue linking functionality\n- Relationship management\n- MCP tool integration\n\n:::panel type=\"note\"\nBoth issues are part of the MCP testing suite.\n:::"
  }
}
```

**Create Remote Link:**
```json
{
  "tool": "jira_management_create_remote_issue_link",
  "input": {
    "issue_key": "{created_issue_key}",
    "url": "https://confluence.baseball.atlassian.net/wiki/spaces/~911651470/pages/{confluence_page_id}",
    "title": "Related Confluence Documentation",
    "summary": "Link to Confluence page created during MCP testing",
    "relationship": "documentation"
  }
}
```

#### 1.6 Search Tests (`test_jira_search`)

**Basic JQL Search:**
```json
{
  "tool": "jira_search_search",
  "input": {
    "jql": "project = FTEST AND labels = mcp-test ORDER BY created DESC",
    "fields": "summary,status,assignee,labels,created",
    "limit": 10
  }
}
```

**Advanced JQL Search:**
```json
{
  "tool": "jira_search_search",
  "input": {
    "jql": "project = FTEST AND (labels = mcp-test OR summary ~ 'MCP Test') AND created >= -1d ORDER BY priority DESC, created DESC",
    "fields": "*all",
    "expand": "renderedFields,changelog"
  }
}
```

### 2. Confluence Pages Tests

#### 2.1 Page Creation Tests (`test_confluence_page_creation`)

**Basic Page Creation:**
```json
{
  "tool": "confluence_pages_create_page",
  "input": {
    "space_id": "~911651470",
    "title": "MCP Test Page - Basic Creation",
    "content": "# MCP Testing Documentation\n\nThis page was created via **MCP tools** to validate Confluence integration.\n\n## Purpose\nTesting the following functionality:\n- Page creation via MCP\n- Markdown to ADF conversion\n- Content formatting and rendering\n\n## Test Content\n\n### Text Formatting\n**Bold**, *italic*, ~~strikethrough~~, `inline code`\n\n### Lists\n1. Ordered item 1\n2. Ordered item 2\n   - Nested bullet\n   - Another nested item\n\n### Code Block\n```python\ndef test_mcp_integration():\n    print('Testing MCP Confluence integration')\n    return True\n```\n\n### Blockquote\n> This is a test blockquote to validate ADF conversion and rendering in Confluence.\n\n---\n\n*Created via MCP tools for testing purposes*",
    "content_format": "markdown"
  }
}
```

**Rich Formatted Page:**
```json
{
  "tool": "confluence_pages_create_page",
  "input": {
    "space_id": "~911651470",
    "title": "MCP Test - Advanced Formatting Elements",
    "content": "# Advanced MCP Formatting Test\n\n## ADF-Specific Elements\n\n### Panels\n:::panel type=\"info\"\n**Information Panel**: This panel tests ADF-specific formatting that should render as a native Confluence info panel.\n:::\n\n:::panel type=\"warning\"\n**Warning Panel**: Testing warning panel with *italic* and **bold** text inside.\n:::\n\n:::panel type=\"success\"\n**Success Panel**: \n- Testing lists inside panels\n- Multiple items\n- With various formatting\n:::\n\n:::panel type=\"error\"\n**Error Panel**: Testing error panel with `inline code` elements.\n:::\n\n### Status Badges\nProgress: {status:color=blue}In Progress{/status}\nComplete: {status:color=green}Done{/status}\nBlocked: {status:color=red}Blocked{/status}\nReview: {status:color=yellow}Under Review{/status}\n\n### Dates\nCreated: {date:2025-01-20}\nDue: {date:2025-02-15}\nCompleted: {date:2025-03-01}\n\n### Expand/Collapse Sections\n:::expand title=\"Click to expand detailed information\"\nThis content is inside an expandable section.\n\n#### Subsection\nTesting nested content:\n- Item 1\n- Item 2\n\n```javascript\nfunction expandTest() {\n  console.log('Content inside expand section');\n}\n```\n:::\n\n### Tables\n| Feature | Status | Notes |\n|---------|--------|-------|\n| Page Creation | {status:color=green}Complete{/status} | Working correctly |\n| ADF Conversion | {status:color=blue}Testing{/status} | Currently validating |\n| Panel Rendering | {status:color=yellow}Review{/status} | Needs verification |\n| Status Badges | {status:color=green}Complete{/status} | All colors working |\n\n### Media and Links\n[External Link](https://atlassian.com)\n\n### Complex Nested Content\n1. **Step 1**: Initial setup\n   :::panel type=\"note\"\n   Make sure to configure all required settings before proceeding.\n   :::\n\n2. **Step 2**: Execute tests\n   ```bash\n   npm run test\n   ```\n   Status: {status:color=blue}Running{/status}\n\n3. **Step 3**: Validate results\n   :::expand title=\"Expected Results\"\n   - All tests should pass\n   - No formatting issues\n   - ADF elements render correctly\n   :::\n\n---\n\n## Metadata\n- **Created**: {date:2025-01-20}\n- **Author**: MCP Testing Suite\n- **Version**: 1.0\n- **Status**: {status:color=green}Ready for Review{/status}",
    "content_format": "markdown",
    "enable_heading_anchors": true
  }
}
```

**Child Page Creation:**
```json
{
  "tool": "confluence_pages_create_page",
  "input": {
    "space_id": "~911651470",
    "title": "MCP Test - Child Page",
    "content": "# Child Page Test\n\nThis is a **child page** created via MCP to test:\n\n## Hierarchy Testing\n- Parent-child relationships\n- Navigation structure\n- Content organization\n\n## Content Validation\n:::panel type=\"info\"\nThis child page validates that MCP can create proper page hierarchies in Confluence.\n:::\n\n### Test Results\n| Test | Result |\n|------|--------|\n| Child page creation | {status:color=green}Success{/status} |\n| Parent relationship | {status:color=blue}Validating{/status} |\n\n*Child of: {parent_page_title}*",
    "parent_id": "{parent_page_id}",
    "content_format": "markdown"
  }
}
```

#### 2.2 Page Update Tests (`test_confluence_page_updates`)

**Content Update:**
```json
{
  "tool": "confluence_pages_update_page",
  "input": {
    "page_id": "{created_page_id}",
    "title": "UPDATED: MCP Test Page - Modified Content",
    "content": "# UPDATED: MCP Testing Documentation\n\n:::panel type=\"warning\"\n**Page Updated**: This content was modified via MCP tools to test update functionality.\n:::\n\n## Original Purpose\nTesting Confluence integration (✅ Complete)\n\n## New Content Added\n- Page update functionality\n- Version control testing\n- Content modification validation\n\n## Update History\n| Version | Change | Date |\n|---------|--------|------|\n| 1.0 | Initial creation | {date:2025-01-20} |\n| 1.1 | Content update | {date:2025-01-21} |\n\n### Updated Test Results\n:::panel type=\"success\"\n**Update Status**: {status:color=green}Successful{/status}\n\nAll formatting elements preserved during update:\n- **Bold text** ✅\n- *Italic text* ✅\n- `Inline code` ✅\n- Panels ✅\n- Status badges ✅\n- Tables ✅\n:::\n\n### Code Example\n```python\ndef updated_function():\n    print('Page content updated successfully via MCP')\n    return {'status': 'updated', 'version': '1.1'}\n```\n\n---\n\n*Last updated via MCP tools: {date:2025-01-21}*",
    "version_comment": "Updated via MCP tools for testing page modification functionality",
    "content_format": "markdown"
  }
}
```

#### 2.3 Comment Tests (`test_confluence_comments`)

**Basic Comment:**
```json
{
  "tool": "confluence_content_add_comment",
  "input": {
    "page_id": "{created_page_id}",
    "content": "# MCP Test Comment\n\nThis comment was added via **MCP tools** to validate:\n\n- Comment creation functionality\n- Markdown formatting in comments\n- ADF conversion for comments\n\n## Comment Features Tested\n- Basic text formatting\n- Lists and structure\n- Code blocks\n\n```bash\n# Example command\nmcp-atlassian confluence_content_add_comment\n```\n\n*Comment created by MCP testing suite*"
  }
}
```

**Rich Comment:**
```json
{
  "tool": "confluence_content_add_comment",
  "input": {
    "page_id": "{created_page_id}",
    "content": "## Review Comment via MCP\n\n### Page Quality Assessment\n| Aspect | Rating | Notes |\n|--------|--------|-------|\n| Content Quality | {status:color=green}Excellent{/status} | Well structured |\n| Formatting | {status:color=green}Good{/status} | ADF conversion working |\n| Completeness | {status:color=yellow}Partial{/status} | Needs more examples |\n\n### Suggestions\n:::panel type=\"note\"\n**Improvement Areas**:\n1. Add more code examples\n2. Include troubleshooting section\n3. Add cross-references to related pages\n:::\n\n### Action Items\n- [ ] Review content structure\n- [ ] Add missing sections\n- [ ] Validate all links\n\n**Reviewer**: MCP Testing Bot  \n**Review Date**: {date:2025-01-21}  \n**Status**: {status:color=blue}Under Review{/status}"
  }
}
```

#### 2.4 Label Tests (`test_confluence_labels`)

**Add Labels:**
```json
{
  "tool": "confluence_content_add_label",
  "input": {
    "page_id": "{created_page_id}",
    "name": "mcp-test"
  }
}
```

**Additional Labels:**
```json
{
  "tool": "confluence_content_add_label",
  "input": {
    "page_id": "{created_page_id}",
    "name": "formatting-test"
  }
},
{
  "tool": "confluence_content_add_label",
  "input": {
    "page_id": "{created_page_id}",
    "name": "adf-validation"
  }
}
```

#### 2.5 Search Tests (`test_confluence_search`)

**Basic Text Search:**
```json
{
  "tool": "confluence_search_search",
  "input": {
    "query": "MCP test",
    "limit": 10,
    "spaces_filter": "~911651470"
  }
}
```

**CQL Search:**
```json
{
  "tool": "confluence_search_search",
  "input": {
    "query": "type=page AND space=~911651470 AND label=mcp-test",
    "limit": 20
  }
}
```

**Advanced CQL Search:**
```json
{
  "tool": "confluence_search_search",
  "input": {
    "query": "space=~911651470 AND (title ~ 'MCP Test' OR text ~ 'MCP tools') AND created >= '2025-01-01'",
    "limit": 50
  }
}
```

### 3. Integration Tests

#### 3.1 Cross-Service Tests (`test_cross_service_integration`)

**Jira-Confluence Linking:**
1. Create Jira issue with Confluence reference
2. Create Confluence page with Jira issue reference
3. Link them via remote issue link
4. Validate bi-directional references

**Content Consistency:**
1. Create content with identical formatting in both services
2. Validate ADF conversion consistency
3. Test formatting preservation across updates

#### 3.2 Error Handling Tests (`test_error_scenarios`)

**Invalid Parameters:**
- Test with non-existent project keys
- Test with invalid space IDs
- Test with malformed content
- Test permission restrictions

**Network Resilience:**
- Test with simulated network delays
- Test with rate limiting scenarios
- Test with authentication failures

#### 3.3 Performance Tests (`test_performance`)

**Bulk Operations:**
- Create multiple issues rapidly
- Update multiple pages simultaneously
- Test search with large result sets

**Large Content:**
- Test with very long descriptions
- Test with complex nested formatting
- Test with large tables and lists

### 4. Cleanup Tests

#### 4.1 Resource Cleanup (`test_cleanup`)
**Delete Created Resources:**
- Delete all test issues
- Delete all test pages
- Remove test comments
- Clean up labels and links

**Validation:**
- Verify all resources removed
- Check for orphaned references
- Validate space/project state

## Test Execution Strategy

### Test Dependencies
1. **Environment Setup**: Validate `.env` configuration
2. **Authentication**: Ensure valid credentials
3. **Permissions**: Verify create/edit/delete permissions
4. **Resource Availability**: Check project and space access

### Test Data Management
- Use consistent labeling (`mcp-test`, `automation`)
- Include timestamps in titles for uniqueness
- Maintain test data inventory
- Implement robust cleanup procedures

### Validation Criteria
- **Functional**: All tools execute without errors
- **Formatting**: ADF conversion works correctly
- **Content**: Rich formatting renders properly
- **Integration**: Cross-service features work
- **Performance**: Reasonable response times
- **Cleanup**: All test artifacts removed

### Reporting
- **Success Metrics**: Tool success rates, formatting accuracy
- **Performance Metrics**: Response times, throughput
- **Error Analysis**: Failure patterns, root causes
- **Coverage Report**: Tools tested, scenarios covered

## Implementation Notes

### Test Framework
- Use pytest for Python test framework
- Implement MCP client for tool invocation
- Use fixtures for environment setup
- Implement proper test isolation

### Test Categories
- **Unit Tests**: Individual tool functionality
- **Integration Tests**: Cross-service scenarios
- **End-to-End Tests**: Complete workflows
- **Performance Tests**: Load and stress testing

### Environment Management
- Support multiple environments (dev, staging, prod)
- Isolate test data from production content
- Implement proper credential management
- Support both Cloud and Server/DC deployments
