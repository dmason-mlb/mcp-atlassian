"""
ADF formatting visual verification tests.

Tests that ADF content is properly formatted and displayed in browser interfaces
for both Jira and Confluence. Uses Playwright for visual validation.
"""

import pytest
from playwright.async_api import Page, expect

from ..tests.base_test import MCPBaseTest
from ..visual_validators import ADFVisualValidator


class TestADFVisualFormatting(MCPBaseTest):
    """
    Visual verification tests for ADF formatting in browser interfaces.
    
    These tests create content with ADF elements and verify they render correctly
    in the actual Jira and Confluence web interfaces.
    """

    @pytest.mark.visual
    @pytest.mark.adf
    async def test_jira_issue_adf_description_rendering(
        self, mcp_client, test_config, browser_context
    ):
        """Test that ADF-formatted Jira issue descriptions render correctly."""
        # Create issue with rich ADF content
        adf_description = """# ADF Test Issue Description

## Status Elements
Status: {status:color=green}In Progress{/status}
Priority: {status:color=red}High{/status}

## Panel Information
:::panel type="info"
This issue contains **ADF elements** for visual validation testing.
The panel should render with proper styling and formatting.
:::

## Code and Formatting
Here's some `inline code` and a **bold statement** with *italic emphasis*.

```python
def validate_adf_rendering():
    return "ADF formatting should be visible"
```

## Lists and Structure
1. **Ordered list item** with formatting
2. Second item with `code`
3. Final item with [link text](https://example.com)

- Bullet point with **bold**
- Another bullet with *italic*
- Final bullet with {status:color=blue}Status{/status}

## Table with Status
| Component | Status | Notes |
|-----------|--------|-------|
| Frontend | {status:color=green}Complete{/status} | All tests passing |
| Backend | {status:color=yellow}In Review{/status} | Code review pending |
| Database | {status:color=red}Blocked{/status} | Migration issues |

## Expand Section
:::expand title="Click to expand technical details"
This section contains additional technical information that should be collapsible.

### Nested Content
- Technical details
- Implementation notes
- **Bold technical terms**
:::

## Date and Time
Due date: {date:2025-03-15}
Last updated: {date:2025-01-20}
"""

        # Create the issue
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("ADF Visual Test Issue"),
            issue_type="Task",
            description=adf_description
        )
        
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
        
        # Navigate to issue and validate ADF rendering
        page = await browser_context.new_page()
        validator = ADFVisualValidator()
        
        validation_result = await validator.validate_jira_issue_description(
            page, issue_key, test_config
        )
        
        assert validation_result.is_valid, f"ADF validation failed: {validation_result.errors}"
        assert validation_result.elements_found > 5, "Should find multiple ADF elements"
        
        await page.close()

    @pytest.mark.visual
    @pytest.mark.adf
    async def test_confluence_page_adf_content_rendering(
        self, mcp_client, test_config, browser_context
    ):
        """Test that ADF-formatted Confluence page content renders correctly."""
        # Create page with comprehensive ADF content
        adf_content = """# ADF Visual Validation Page

## Overview Panel
:::panel type="note"
This Confluence page demonstrates **ADF rendering** across various element types.
All formatting should appear correctly in the browser interface.
:::

## Status Indicators
Project status: {status:color=green}Active{/status}
Review status: {status:color=yellow}Pending{/status}
Deployment: {status:color=blue}Scheduled{/status}

## Rich Text Formatting
This paragraph contains **bold text**, *italic text*, `inline code`, and ~~strikethrough~~.

### Code Blocks
```javascript
// JavaScript code example
function testADFRendering(element) {
    console.log('Validating ADF element:', element);
    return element.isVisible();
}
```

```python
# Python code example
def validate_adf_elements():
    elements = find_all_adf_elements()
    return all(element.is_displayed() for element in elements)
```

## Interactive Elements

### Expandable Section
:::expand title="Technical Implementation Details"
This expandable section contains detailed technical information about ADF implementation.

#### Nested Lists
1. **ADF Parser**: Handles document structure
   - Block elements (headings, paragraphs, panels)
   - Inline elements (bold, italic, code, status)
   - Media elements (images, videos, attachments)

2. **Renderer**: Converts ADF to HTML
   - Maintains semantic structure
   - Preserves interactive elements
   - Handles custom Atlassian elements

3. **Validator**: Ensures ADF compliance
   - Schema validation
   - Element relationship validation
   - Performance optimization
:::

### Warning Panel
:::panel type="warning"
**Important Note**: ADF elements should render consistently across different browsers
and screen sizes. This warning panel tests the visual styling.
:::

## Data Tables
| Element Type | ADF Node | Visual Test | Status |
|--------------|----------|-------------|--------|
| Panel | `panel` | Background color | {status:color=green}Pass{/status} |
| Status | `status` | Inline badge | {status:color=green}Pass{/status} |
| Code Block | `codeBlock` | Syntax highlighting | {status:color=yellow}Review{/status} |
| Expand | `expand` | Collapsible section | {status:color=blue}Testing{/status} |

## Media and Links
Here's an [external link](https://developer.atlassian.com/cloud/confluence/adf/) to the ADF documentation.

## Date Information
Created: {date:2025-01-20}
Review due: {date:2025-02-15}
Next milestone: {date:2025-03-01}

## Final Validation Panel
:::panel type="success"
If you can see this green success panel with **bold text** and proper formatting,
the ADF visual rendering is working correctly!
:::
"""

        # Create the page
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=self.generate_unique_title("ADF Visual Validation Page"),
            content=adf_content,
            content_format="markdown"
        )
        
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
        
        # Navigate to page and validate ADF rendering
        page = await browser_context.new_page()
        validator = ADFVisualValidator()
        
        validation_result = await validator.validate_confluence_page_content(
            page, page_id, test_config
        )
        
        assert validation_result.is_valid, f"ADF validation failed: {validation_result.errors}"
        assert validation_result.elements_found > 8, "Should find many ADF elements"
        
        # Validate specific ADF element types
        assert "panel" in validation_result.element_types, "Should find panel elements"
        assert "status" in validation_result.element_types, "Should find status elements"
        assert "expand" in validation_result.element_types, "Should find expand elements"
        
        await page.close()

    @pytest.mark.visual
    @pytest.mark.adf
    async def test_jira_comment_adf_formatting(
        self, mcp_client, test_config, browser_context
    ):
        """Test ADF formatting in Jira comments."""
        # First create a test issue
        issue_result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Issue for Comment ADF Test"),
            issue_type="Task",
            description="Issue created for testing ADF in comments"
        )
        
        issue_key = self.extract_issue_key(issue_result)
        self.track_resource("jira_issue", issue_key)
        
        # Add comment with ADF formatting
        adf_comment = """## Comment with ADF Elements

This comment demonstrates ADF formatting in Jira comments:

### Status Updates
Current: {status:color=blue}In Progress{/status}
Next: {status:color=green}Ready for Review{/status}

### Code Reference
```bash
# Run the test command
npm run test:adf
```

### Important Notes
:::panel type="info"
**ADF Comment Test**: This panel should render properly within the comment context.
:::

**Bold conclusion**: ADF elements should work in comments too!
"""

        comment_result = await mcp_client.add_jira_comment(
            issue_key=issue_key,
            comment=adf_comment
        )
        
        self.assert_success_response(comment_result)
        
        # Navigate and validate comment ADF rendering
        page = await browser_context.new_page()
        validator = ADFVisualValidator()
        
        # Navigate to the issue to view the comment
        jira_base_url = test_config["jira_base_url"]
        await page.goto(f"{jira_base_url}/browse/{issue_key}")
        await page.wait_for_load_state("networkidle")
        
        # Wait for comments section to load
        await page.wait_for_selector("[data-testid='issue.views.issue-base.foundation.summary.comment']", timeout=10000)
        
        # Validate that ADF elements are rendered in the comment
        comment_section = page.locator("[data-testid='issue.views.issue-base.foundation.summary.comment']")
        
        # Check for status elements in comment
        status_elements = comment_section.locator("[data-testid='status-lozenge']")
        await expect(status_elements).to_have_count_greater_than(0)
        
        # Check for code block in comment
        code_elements = comment_section.locator("code, pre")
        await expect(code_elements).to_have_count_greater_than(0)
        
        # Check for panel in comment (if supported)
        panel_elements = comment_section.locator("[data-panel-type]")
        # Note: Panels might not be supported in comments, so this is optional
        
        await page.close()

    @pytest.mark.visual
    @pytest.mark.adf
    async def test_cross_platform_adf_consistency(
        self, mcp_client, test_config, browser_context
    ):
        """Test that ADF renders consistently across Jira and Confluence."""
        # Use identical ADF content in both platforms
        shared_adf_content = """# Cross-Platform ADF Test

## Status Consistency Test
Status: {status:color=purple}Cross-Platform{/status}

## Panel Consistency
:::panel type="info"
This **identical content** should render consistently in both Jira and Confluence.
Testing cross-platform ADF compatibility.
:::

## Code Consistency
```json
{
  "test": "cross-platform",
  "platforms": ["jira", "confluence"],
  "status": "validating"
}
```

## Format Elements
- **Bold text** consistency
- *Italic text* consistency  
- `Code text` consistency
- ~~Strikethrough~~ consistency

## Date Consistency
Test date: {date:2025-01-20}
"""

        # Create Jira issue with shared content
        jira_result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=self.generate_unique_title("Cross-Platform ADF Test Issue"),
            issue_type="Task",
            description=shared_adf_content
        )
        
        issue_key = self.extract_issue_key(jira_result)
        self.track_resource("jira_issue", issue_key)
        
        # Create Confluence page with shared content
        confluence_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=self.generate_unique_title("Cross-Platform ADF Test Page"),
            content=shared_adf_content,
            content_format="markdown"
        )
        
        page_id = self.extract_page_id(confluence_result)
        self.track_resource("confluence_page", page_id)
        
        # Visual validation for both platforms
        page = await browser_context.new_page()
        validator = ADFVisualValidator()
        
        # Validate Jira rendering
        jira_validation = await validator.validate_jira_issue_description(
            page, issue_key, test_config
        )
        
        # Validate Confluence rendering  
        confluence_validation = await validator.validate_confluence_page_content(
            page, page_id, test_config
        )
        
        # Compare consistency
        assert jira_validation.is_valid, f"Jira ADF validation failed: {jira_validation.errors}"
        assert confluence_validation.is_valid, f"Confluence ADF validation failed: {confluence_validation.errors}"
        
        # Check that similar element types were found in both platforms
        common_types = set(jira_validation.element_types) & set(confluence_validation.element_types)
        assert len(common_types) >= 2, f"Should find common ADF elements across platforms, found: {common_types}"
        
        await page.close()

    @pytest.mark.visual
    @pytest.mark.adf
    async def test_adf_performance_visual_validation(
        self, mcp_client, test_config, browser_context
    ):
        """Test ADF rendering performance with complex content."""
        # Create complex ADF content to test performance
        complex_adf = """# Performance Test Page

## Multiple Panels
""" + "\n\n".join([
    f""":::panel type="{'info' if i % 4 == 0 else 'note' if i % 4 == 1 else 'warning' if i % 4 == 2 else 'success'}"
Panel {i+1}: This is test panel content with **bold** and *italic* text.
Status: {{status:color={'green' if i % 3 == 0 else 'yellow' if i % 3 == 1 else 'blue'}}}Panel {i+1}{{/status}}
:::""" for i in range(5)
]) + """

## Multiple Status Elements
""" + " | ".join([
    f"{{status:color={'red' if i % 4 == 0 else 'green' if i % 4 == 1 else 'blue' if i % 4 == 2 else 'yellow'}}}Status {i+1}{{/status}}"
    for i in range(10)
]) + """

## Complex Table
| ID | Name | Status | Priority | Assignee | Due Date |
|----|------|--------|----------|----------|----------|
""" + "\n".join([
    f"| {i+1} | Task {i+1} | {{status:color={'green' if i % 3 == 0 else 'yellow' if i % 3 == 1 else 'red'}}}{'Complete' if i % 3 == 0 else 'In Progress' if i % 3 == 1 else 'Blocked'}{{/status}} | {'High' if i % 2 == 0 else 'Medium'} | User{i+1} | {{date:2025-0{(i % 9) + 1}-{(i % 28) + 1:02d}}} |"
    for i in range(8)
]) + """

## Multiple Expand Sections
""" + "\n\n".join([
    f""":::expand title="Expand Section {i+1}"
Content for section {i+1} with **formatting** and `code`.

```python
def section_{i+1}():
    return "Section {i+1} content"
```
:::""" for i in range(4)
])

        # Create page with complex content
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=self.generate_unique_title("ADF Performance Test Page"),
            content=complex_adf,
            content_format="markdown"
        )
        
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
        
        # Validate with performance timing
        page = await browser_context.new_page()
        validator = ADFVisualValidator()
        
        import time
        start_time = time.time()
        
        validation_result = await validator.validate_confluence_page_content(
            page, page_id, test_config
        )
        
        end_time = time.time()
        validation_duration = end_time - start_time
        
        # Performance assertions
        assert validation_duration < 30.0, f"ADF validation took too long: {validation_duration:.2f}s"
        assert validation_result.is_valid, f"Complex ADF validation failed: {validation_result.errors}"
        assert validation_result.elements_found > 20, f"Should find many elements, found: {validation_result.elements_found}"
        
        # Verify specific element counts
        panel_count = validation_result.element_counts.get("panel", 0)
        status_count = validation_result.element_counts.get("status", 0)
        expand_count = validation_result.element_counts.get("expand", 0)
        
        assert panel_count >= 5, f"Should find multiple panels, found: {panel_count}"
        assert status_count >= 10, f"Should find multiple status elements, found: {status_count}"
        assert expand_count >= 4, f"Should find multiple expand sections, found: {expand_count}"
        
        await page.close()