"""
Test fixtures and data management for MCP Atlassian E2E tests.

This module provides:
- Test data lifecycle management
- Resource cleanup and tracking
- Test isolation utilities
- Data validation helpers
"""

import os
from datetime import datetime
from typing import Any

from mcp_client import MCPClient


class TestDataManager:
    """
    Manages test data lifecycle for E2E tests.

    Provides:
    - Resource creation and tracking
    - Automatic cleanup after tests
    - Test isolation through unique labeling
    - Data validation utilities
    """

    def __init__(self, mcp_client: MCPClient, config: dict[str, Any]):
        """
        Initialize test data manager.

        Args:
            mcp_client: MCP client instance
            config: Test configuration
        """
        self.client = mcp_client
        self.config = config

        # Generate unique test session identifier with clear datestamp
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        self.test_session = f"mcp-test-{date_str}-{time_str}-{os.getpid()}"
        self.test_label = config.get("test_label", self.test_session)

        # Track created resources for cleanup
        self.created_issues: set[str] = set()
        self.created_pages: set[str] = set()
        self.created_comments: dict[str, list[str]] = {}  # resource_id -> comment_ids
        self.created_attachments: list[str] = []

        # Test data templates
        self.test_data = self._initialize_test_data()

    def _initialize_test_data(self) -> dict[str, Any]:
        """Initialize test data templates."""
        return {
            "basic_issue": {
                "summary": f"[{self.test_session}] Basic Test Issue",
                "description": """# Basic Test Issue

This is a **test issue** created via MCP tools for validation.

## Test Content
- Basic markdown formatting
- *Italic text* and **bold text**
- `Inline code` elements

## Lists
1. Ordered item 1
2. Ordered item 2
   - Nested bullet
   - Another nested item

## Code Block
```python
def test_function():
    print("Testing MCP functionality")
    return True
```

> This is a blockquote for testing ADF conversion.

---

*Created by MCP E2E test suite*""",
                "issue_type": "Task",
                "additional_fields": {
                    "labels": [self.test_label, "mcp-test", "automation"]
                },
            },
            "rich_issue": {
                "summary": f"[{self.test_session}] Rich ADF Formatting Test",
                "description": """# Comprehensive ADF Formatting Test

## ADF-Specific Elements

### Panels
:::panel type="info"
**Information Panel**: This panel tests ADF-specific formatting elements.
:::

:::panel type="warning"
**Warning Panel**: Testing with *italic* and **bold** text inside panels.
:::

:::panel type="success"
**Success Panel**:
- Testing lists inside panels
- Multiple items with formatting
- Nested content validation
:::

:::panel type="error"
**Error Panel**: Testing error panel with `inline code` elements.
:::

### Status Badges
Current Status: {status:color=blue}In Progress{/status}
Completion: {status:color=green}Done{/status}
Issues: {status:color=red}Blocked{/status}
Review: {status:color=yellow}Under Review{/status}

### Dates and Timestamps
Created: {date:2025-01-20}
Due Date: {date:2025-02-15}
Completed: {date:2025-03-01}

### Expand/Collapse Sections
:::expand title="Click to expand detailed information"
This content is inside an expandable section for testing purposes.

#### Subsection Content
Testing nested content within expand sections:
- Item 1 with **bold** text
- Item 2 with *italic* text
- Item 3 with `inline code`

```javascript
function expandTest() {
  console.log('Testing expand section functionality');
  return {status: 'expanded'};
}
```
:::

### Complex Tables
| Feature | Status | Completion | Notes |
|---------|--------|------------|-------|
| Issue Creation | {status:color=green}Complete{/status} | 100% | Working correctly |
| ADF Conversion | {status:color=blue}Testing{/status} | 80% | Currently validating |
| Panel Rendering | {status:color=yellow}Review{/status} | 90% | Needs verification |
| Status Badges | {status:color=green}Complete{/status} | 100% | All colors working |

### Links and References
[External Documentation](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/)

### Nested Complex Content
1. **Phase 1**: Initial Setup
   :::panel type="note"
   Configure all required settings before proceeding with the test execution.
   :::

2. **Phase 2**: Execute Validation
   ```bash
   pytest tests/ -v --tb=short
   ```
   Status: {status:color=blue}Running{/status}

3. **Phase 3**: Verify Results
   :::expand title="Expected Test Results"
   - All formatting elements render correctly
   - No ADF conversion errors
   - Visual elements display properly
   - Interactive components function as expected
   :::

---

## Metadata
- **Test Session**: {test_session}
- **Created**: {date:2025-01-20}
- **Framework**: MCP E2E Testing Suite
- **Status**: {status:color=green}Ready for Validation{/status}
""".replace("{test_session}", self.test_session),
                "issue_type": "Story",
                "additional_fields": {
                    "priority": {"name": "High"},
                    "labels": [
                        self.test_label,
                        "mcp-test",
                        "adf-validation",
                        "rich-formatting",
                    ],
                },
            },
            "basic_page": {
                "title": f"[{self.test_session}] Basic Test Page",
                "content": """# MCP Testing Documentation

This page was created via **MCP tools** to validate Confluence integration.

## Purpose
Testing the following functionality:
- Page creation via MCP
- Markdown to ADF conversion
- Content formatting and rendering

## Test Elements

### Text Formatting
**Bold text**, *italic text*, ~~strikethrough~~, `inline code`

### Lists
1. Ordered item 1
2. Ordered item 2
   - Nested unordered item
   - Another nested item

### Code Block
```python
def test_mcp_integration():
    print('Testing MCP Confluence integration')
    return {'status': 'success', 'test_session': '{test_session}'}
```

### Blockquote
> This is a test blockquote to validate ADF conversion and rendering in Confluence.

### Table
| Component | Status | Notes |
|-----------|--------|-------|
| Page Creation | ✅ | Working |
| Content Rendering | 🔄 | Testing |
| ADF Conversion | ✅ | Validated |

---

*Created via MCP tools for testing purposes*
*Test Session: {test_session}*
""".replace("{test_session}", self.test_session),
                "content_format": "markdown",
            },
            "rich_page": {
                "title": f"[{self.test_session}] Advanced ADF Elements Test",
                "content": """# Advanced MCP ADF Test Page

## ADF-Specific Elements Testing

### Information Panels
:::panel type="info"
**Information Panel**: This panel tests ADF-specific formatting that should render as a native Confluence info panel with proper styling.
:::

:::panel type="warning"
**Warning Panel**: Testing warning panel with *italic* and **bold** text inside, including `inline code` elements.
:::

:::panel type="success"
**Success Panel**:
- Testing lists inside panels
- Multiple items with various formatting
- Validation of nested content structures
:::

:::panel type="error"
**Error Panel**: Testing error panel with complex content and `code` elements for comprehensive validation.
:::

### Status Badge Collection
Project Status: {status:color=blue}In Progress{/status}
Quality Gate: {status:color=green}Passed{/status}
Build Status: {status:color=red}Failed{/status}
Review Status: {status:color=yellow}Pending{/status}
Deployment: {status:color=purple}Scheduled{/status}

### Date and Time Elements
Project Start: {date:2025-01-20}
Milestone 1: {date:2025-02-15}
Release Date: {date:2025-03-01}
Review Due: {date:2025-02-28}

### Expandable Content Sections
:::expand title="Technical Implementation Details"
This expandable section contains detailed technical information about the implementation.

#### Architecture Overview
The system uses a hybrid approach:
- API-first testing for comprehensive validation
- Browser-based verification for visual elements
- Automated cleanup and resource management

#### Code Examples
```typescript
interface TestResult {
  status: 'pass' | 'fail' | 'skip';
  message: string;
  metadata: Record<string, any>;
}

function validateADFElement(element: ADFNode): TestResult {
  // Validation logic here
  return { status: 'pass', message: 'Element validated', metadata: {} };
}
```

#### Configuration
| Setting | Value | Description |
|---------|-------|-------------|
| Test Timeout | 30s | Maximum test execution time |
| Retry Count | 3 | Number of retry attempts |
| Parallel Execution | Yes | Run tests concurrently |
:::

:::expand title="Test Results and Metrics"
### Performance Metrics
- Page Load Time: < 2 seconds
- ADF Conversion: < 100ms
- API Response: < 500ms

### Coverage Statistics
| Test Category | Coverage | Status |
|---------------|----------|--------|
| API Tools | 95% | {status:color=green}Complete{/status} |
| ADF Elements | 90% | {status:color=blue}In Progress{/status} |
| Visual Tests | 85% | {status:color=yellow}Pending{/status} |
| Error Scenarios | 80% | {status:color=orange}Planned{/status} |
:::

### Complex Table with Mixed Content
| Feature | Implementation | Status | Priority | Due Date |
|---------|----------------|---------|----------|----------|
| Issue Creation | {status:color=green}✅ Complete{/status} | Production Ready | High | {date:2025-01-15} |
| Page Management | {status:color=blue}🔄 Testing{/status} | Under Review | High | {date:2025-01-25} |
| Search Functions | {status:color=yellow}⏳ Planned{/status} | Design Phase | Medium | {date:2025-02-01} |
| Error Handling | {status:color=red}❌ Blocked{/status} | Needs Requirements | Low | {date:2025-02-15} |

### Links and External References
- [Atlassian Developer Documentation](https://developer.atlassian.com/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Pytest Documentation](https://docs.pytest.org/)

### Multi-Level Nested Content
1. **Phase 1: Foundation**
   :::panel type="note"
   **Setup Requirements**:
   - Environment configuration validated
   - Authentication credentials verified
   - MCP server connectivity established
   :::

   Progress: {status:color=green}Complete{/status}

2. **Phase 2: Core Implementation**
   :::expand title="Implementation Tasks"
   - API client development
   - Test framework setup
   - Data management utilities
   - Validation helpers
   :::

   Status: {status:color=blue}In Progress{/status}
   Due: {date:2025-01-30}

3. **Phase 3: Advanced Features**
   :::panel type="warning"
   **Attention Required**: Complex ADF elements need thorough testing across different browsers and deployment types.
   :::

   Timeline: {status:color=yellow}Under Review{/status}

---

## Test Session Metadata
- **Session ID**: {test_session}
- **Framework**: MCP E2E Testing Suite v1.0
- **Created**: {date:2025-01-20}
- **Last Updated**: {date:2025-01-21}
- **Status**: {status:color=green}Ready for Comprehensive Testing{/status}
""".replace("{test_session}", self.test_session),
                "content_format": "markdown",
                "enable_heading_anchors": True,
            },
        }

    async def create_test_issue(
        self,
        template: str = "basic_issue",
        project_key: str | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a test Jira issue.

        Args:
            template: Template name to use
            project_key: Project key (uses config if not provided)
            custom_fields: Additional fields to override

        Returns:
            Created issue data
        """
        if template not in self.test_data:
            raise ValueError(f"Unknown template: {template}")

        issue_data = self.test_data[template].copy()

        # Override project key
        if not project_key:
            project_key = self.config["jira_project"]

        # Apply custom fields
        if custom_fields:
            issue_data.update(custom_fields)

        # Ensure test labeling
        if "additional_fields" not in issue_data:
            issue_data["additional_fields"] = {}
        if "labels" not in issue_data["additional_fields"]:
            issue_data["additional_fields"]["labels"] = []

        # Add test session label
        labels = issue_data["additional_fields"]["labels"]
        if self.test_label not in labels:
            labels.append(self.test_label)

        # Create issue
        result = await self.client.create_jira_issue(
            project_key=project_key, **issue_data
        )

        # Track for cleanup
        issue_key = self.client.extract_value(result, "key")
        if issue_key:
            self.created_issues.add(issue_key)

        return result

    async def create_test_page(
        self,
        template: str = "basic_page",
        space_id: str | None = None,
        parent_id: str | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a test Confluence page.

        Args:
            template: Template name to use
            space_id: Space ID (uses config if not provided)
            parent_id: Parent page ID
            custom_fields: Additional fields to override

        Returns:
            Created page data
        """
        if template not in self.test_data:
            raise ValueError(f"Unknown template: {template}")

        page_data = self.test_data[template].copy()

        # Override space ID
        if not space_id:
            space_id = self.config["confluence_space"]

        # Apply custom fields
        if custom_fields:
            page_data.update(custom_fields)

        # Create page
        result = await self.client.create_confluence_page(
            space_id=space_id, parent_id=parent_id, **page_data
        )

        # Track for cleanup
        page_data_result = self.client.extract_json(result)
        page_id = (
            page_data_result.get("page", {}).get("id")
            or page_data_result.get("id")
            or page_data_result.get("page_id")
            or page_data_result.get("data", {}).get("id")
        )

        if page_id:
            self.created_pages.add(str(page_id))

            # Add test label
            try:
                await self.client.add_confluence_label(str(page_id), self.test_label)
            except Exception:
                pass  # Label addition is optional

        return result

    async def add_test_comment(
        self,
        resource_type: str,
        resource_id: str,
        content: str | None = None,
        comment_type: str = "basic",
    ) -> dict[str, Any]:
        """
        Add a test comment to a resource.

        Args:
            resource_type: Type of resource ("jira" or "confluence")
            resource_id: Resource ID (issue key or page ID)
            content: Comment content (auto-generated if not provided)
            comment_type: Type of comment ("basic" or "rich")

        Returns:
            Comment data
        """
        if not content:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if comment_type == "rich":
                content = f"""## Test Comment - {timestamp}

This comment was added via **MCP tools** for validation testing.

### Test Information
- **Session**: {self.test_session}
- **Timestamp**: {timestamp}
- **Comment Type**: Rich formatting test

### Formatting Tests
- **Bold text** validation
- *Italic text* validation
- `Inline code` validation
- [Link test](https://example.com)

### Status Check
Current test status: {{status:color=blue}}Testing{{/status}}

### Code Example
```python
def test_comment():
    return {{
        'status': 'success',
        'session': '{self.test_session}',
        'timestamp': '{timestamp}'
    }}
```

*Automated test comment generated by MCP E2E suite*"""
            else:
                content = f"""# Test Comment - {timestamp}

This is a **test comment** added via MCP tools.

- Session: {self.test_session}
- Type: {comment_type}
- Resource: {resource_id}

`Automated test comment`"""

        # Add comment based on resource type
        if resource_type.lower() == "jira":
            result = await self.client.add_jira_comment(resource_id, content)
        elif resource_type.lower() == "confluence":
            result = await self.client.add_confluence_comment(resource_id, content)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

        # Track for cleanup (comments are usually cleaned up with parent resource)
        if resource_id not in self.created_comments:
            self.created_comments[resource_id] = []

        comment_data = self.client.extract_json(result)
        comment_id = comment_data.get("id")
        if comment_id:
            self.created_comments[resource_id].append(str(comment_id))

        return result

    def get_test_url(self, resource_type: str, resource_id: str) -> str:
        """
        Get the URL for a test resource.

        Args:
            resource_type: Type of resource ("jira" or "confluence")
            resource_id: Resource ID

        Returns:
            Resource URL
        """
        if resource_type.lower() == "jira":
            base_url = self.config["jira_base"]
            return f"{base_url}/browse/{resource_id}"
        elif resource_type.lower() == "confluence":
            base_url = self.config["confluence_base"]
            space_id = self.config["confluence_space"]
            return f"{base_url}/spaces/{space_id}/pages/{resource_id}"
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    async def cleanup(self) -> dict[str, Any]:
        """
        Clean up all created test resources.

        Returns:
            Cleanup summary
        """
        cleanup_summary = {
            "issues_deleted": 0,
            "pages_deleted": 0,
            "errors": [],
            "skipped": [],
        }

        # Clean up Jira issues
        for issue_key in self.created_issues.copy():
            try:
                # Try to delete the issue via MCP tools
                result = await self.client.call_tool(
                    "jira_delete_issue", {"issue_key": issue_key}
                )
                cleanup_summary["issues_deleted"] += 1
                self.created_issues.remove(issue_key)
                print(f"Deleted Jira issue: {issue_key}")
            except Exception as e:
                error_msg = str(e).lower()
                if "not found" in error_msg or "does not exist" in error_msg:
                    # Issue already deleted or doesn't exist
                    self.created_issues.remove(issue_key)
                    cleanup_summary["skipped"].append(
                        f"Issue {issue_key} already deleted"
                    )
                else:
                    cleanup_summary["errors"].append(
                        f"Failed to delete issue {issue_key}: {e}"
                    )

        # Clean up Confluence pages
        for page_id in self.created_pages.copy():
            try:
                # Try to delete the page via MCP tools
                result = await self.client.call_tool(
                    "confluence_pages_delete_page", {"page_id": page_id}
                )
                cleanup_summary["pages_deleted"] += 1
                self.created_pages.remove(page_id)
                print(f"Deleted Confluence page: {page_id}")
            except Exception as e:
                error_msg = str(e).lower()
                if "not found" in error_msg or "does not exist" in error_msg:
                    # Page already deleted or doesn't exist
                    self.created_pages.remove(page_id)
                    cleanup_summary["skipped"].append(f"Page {page_id} already deleted")
                else:
                    cleanup_summary["errors"].append(
                        f"Failed to delete page {page_id}: {e}"
                    )

        return cleanup_summary

    def get_resource_summary(self) -> dict[str, Any]:
        """
        Get summary of created resources.

        Returns:
            Resource summary
        """
        return {
            "test_session": self.test_session,
            "test_label": self.test_label,
            "created_issues": list(self.created_issues),
            "created_pages": list(self.created_pages),
            "created_comments": dict(self.created_comments),
            "total_resources": len(self.created_issues) + len(self.created_pages),
        }


class TestContentValidator:
    """
    Validates test content and responses.
    """

    @staticmethod
    def validate_issue_creation(result: dict[str, Any]) -> bool:
        """Validate Jira issue creation result."""
        return "key" in result and result["key"] and isinstance(result["key"], str)

    @staticmethod
    def validate_page_creation(result: dict[str, Any]) -> bool:
        """Validate Confluence page creation result."""
        page_data = result.get("page", result)
        return "id" in page_data and page_data["id"] and "title" in page_data

    @staticmethod
    def validate_adf_structure(adf_content: Any) -> bool:
        """Validate ADF structure basics."""
        if not isinstance(adf_content, dict):
            return False

        return (
            "type" in adf_content
            and adf_content["type"] == "doc"
            and "content" in adf_content
            and isinstance(adf_content["content"], list)
        )

    @staticmethod
    def contains_adf_element(adf_content: dict[str, Any], element_type: str) -> bool:
        """Check if ADF content contains specific element type."""

        def search_content(content):
            if isinstance(content, dict):
                if content.get("type") == element_type:
                    return True
                if "content" in content:
                    return search_content(content["content"])
            elif isinstance(content, list):
                return any(search_content(item) for item in content)
            return False

        return search_content(adf_content)
