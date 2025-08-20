"""
Comprehensive Confluence page tests for MCP Atlassian tools.

Tests cover:
- Page creation with various content formats
- Page updates and content modifications
- Comments and comment management  
- Labels and page metadata
- Page hierarchy and relationships
- Error handling and edge cases
"""

import pytest
from typing import Dict, Any, List

from tests.base_test import MCPConfluenceTest
from validators import validate_confluence_response, DeploymentType, ValidationResult


@pytest.mark.api
@pytest.mark.confluence
class TestConfluencePageCreation(MCPConfluenceTest):
    """Test Confluence page creation functionality."""
    
    async def test_create_basic_page(self, mcp_client, test_config, test_data_manager):
        """Test creating a basic page with markdown content."""
        title = self.generate_unique_title("Basic Page")
        content = self.generate_test_description("markdown")
        
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=title,
            content=content,
            content_format="markdown"
        )
        
        # Validate response
        self.assert_success_response(result, ["id", "title"])
        validation = validate_confluence_response(result, "create")
        assert validation.is_valid, f"Validation failed: {validation.errors}"
        
        # Extract and track page
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
        
        # Verify page was created with correct data
        page_data = self.extract_json(result)
        assert title in str(page_data)
    
    async def test_create_page_with_adf_content(self, mcp_client, test_config, test_data_manager):
        """Test creating a page with rich ADF content."""
        title = self.generate_unique_title("ADF Rich Page")
        content = self.generate_test_description("adf_rich")
        
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=title,
            content=content,
            content_format="markdown",  # Will be converted to ADF
            enable_heading_anchors=True
        )
        
        self.assert_success_response(result, ["id", "title"])
        
        # Validate ADF formatting in response
        validation = validate_confluence_response(result, "create", DeploymentType.CLOUD)
        assert validation.is_valid, f"ADF validation failed: {validation.errors}"
        
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
    
    async def test_create_page_with_wiki_markup(self, mcp_client, test_config, test_data_manager):
        """Test creating a page with wiki markup format."""
        title = self.generate_unique_title("Wiki Markup Page")
        
        # Wiki markup content
        content = """h1. Wiki Markup Test Page

This page contains *wiki markup* formatting.

h2. Features
* Bold text: *bold*
* Italic text: _italic_
* Code: {{monospace}}
* Links: [Atlassian|https://atlassian.com]

h3. Code Block
{code:java}
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello Confluence");
    }
}
{code}

{panel:title=Info Panel}
This is an info panel in wiki markup format.
{panel}
"""
        
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=title,
            content=content,
            content_format="wiki"
        )
        
        self.assert_success_response(result, ["id", "title"])
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
    
    async def test_create_child_page(self, mcp_client, test_config, test_data_manager):
        """Test creating a child page under a parent."""
        # Create parent page first
        parent_title = self.generate_unique_title("Parent Page")
        parent_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=parent_title,
            content="This is a parent page for testing hierarchy.",
            content_format="markdown"
        )
        
        parent_id = self.extract_page_id(parent_result)
        self.track_resource("confluence_page", parent_id)
        
        # Create child page
        child_title = self.generate_unique_title("Child Page")
        child_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=child_title,
            content="This is a child page under the parent.",
            content_format="markdown",
            parent_id=parent_id
        )
        
        self.assert_success_response(child_result, ["id", "title"])
        child_id = self.extract_page_id(child_result)
        self.track_resource("confluence_page", child_id)
    
    async def test_create_page_with_table(self, mcp_client, test_config, test_data_manager):
        """Test creating a page with complex table content."""
        title = self.generate_unique_title("Table Test Page")
        
        content = """# Table Test Page

This page contains various table formats for testing.

## Basic Table
| Name | Status | Progress |
|------|--------|----------|
| Task 1 | {status:color=green}Complete{/status} | 100% |
| Task 2 | {status:color=blue}In Progress{/status} | 75% |
| Task 3 | {status:color=red}Blocked{/status} | 25% |

## Complex Table with ADF Elements

| Feature | Description | Example |
|---------|-------------|---------|
| Panels | Info panels | :::panel type="info"<br>**Note**: This is informational<br>::: |
| Code | Code blocks | `function test() { return true; }` |
| Dates | Date formatting | Due: {date:2025-02-15} |

## Nested Content Table
| Step | Action | Result |
|------|--------|--------|
| 1 | Initialize | :::expand title="Details"<br>Setup process details here<br>::: |
| 2 | Execute | **Status**: {status:color=blue}Running{/status} |
| 3 | Validate | > Expected outcome documented |
"""
        
        result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=title,
            content=content,
            content_format="markdown"
        )
        
        self.assert_success_response(result, ["id", "title"])
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
    
    async def test_create_page_invalid_space(self, mcp_client, test_config):
        """Test creating page in invalid space."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.create_confluence_page(
                space_id="INVALID",
                title="Should Fail",
                content="This should not work",
                content_format="markdown"
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["space", "not found", "invalid"]), \
            f"Expected space-related error, got: {error_msg}"


@pytest.mark.api
@pytest.mark.confluence
class TestConfluencePageUpdates(MCPConfluenceTest):
    """Test Confluence page update functionality."""
    
    async def test_update_page_title(self, mcp_client, test_config, test_data_manager):
        """Test updating page title."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Update title
        new_title = self.generate_unique_title("Updated Title")
        original_content = self.generate_test_description("markdown")
        
        update_result = await mcp_client.update_confluence_page(
            page_id=page_id,
            title=new_title,
            content=original_content,
            content_format="markdown"
        )
        
        self.assert_success_response(update_result)
        validation = validate_confluence_response(update_result, "update")
        assert validation.is_valid, f"Update validation failed: {validation.errors}"
    
    async def test_update_page_content(self, mcp_client, test_config, test_data_manager):
        """Test updating page content with rich ADF."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        original_title = self.extract_value(create_result, "title")
        
        # Update with rich ADF content
        new_content = self.generate_test_description("adf_rich")
        update_result = await mcp_client.update_confluence_page(
            page_id=page_id,
            title=original_title or "Updated Content Page",
            content=new_content,
            content_format="markdown",
            version_comment="Updated with rich ADF content by test"
        )
        
        self.assert_success_response(update_result)
        
        # Validate ADF formatting in response
        validation = validate_confluence_response(update_result, "update", DeploymentType.CLOUD)
        assert validation.is_valid, f"ADF validation failed: {validation.errors}"
    
    async def test_update_page_with_complex_content(self, mcp_client, test_config, test_data_manager):
        """Test updating page with complex nested content."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        original_title = self.extract_value(create_result, "title")
        
        # Update with complex nested content
        complex_content = self.generate_test_description("complex_nested_content")
        update_result = await mcp_client.update_confluence_page(
            page_id=page_id,
            title=original_title or "Complex Content Page",
            content=complex_content,
            content_format="markdown"
        )
        
        self.assert_success_response(update_result)
    
    async def test_update_nonexistent_page(self, mcp_client, test_config):
        """Test updating non-existent page."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.update_confluence_page(
                page_id="999999999",
                title="Should Fail",
                content="This should not work",
                content_format="markdown"
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["not found", "does not exist", "invalid"]), \
            f"Expected page not found error, got: {error_msg}"


@pytest.mark.api
@pytest.mark.confluence
class TestConfluenceComments(MCPConfluenceTest):
    """Test Confluence comment functionality."""
    
    async def test_add_basic_comment(self, mcp_client, test_config, test_data_manager):
        """Test adding a basic comment to a page."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add comment
        comment_text = f"Basic comment added by test at {self.test_start_time}"
        comment_result = await mcp_client.add_confluence_comment(
            page_id=page_id,
            content=comment_text
        )
        
        self.assert_success_response(comment_result)
    
    async def test_add_formatted_comment(self, mcp_client, test_config, test_data_manager):
        """Test adding a formatted comment with ADF elements."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add formatted comment
        comment_text = """# Comment with Formatting

This is a **formatted comment** with various elements:

## Status Updates
- Review status: {status:color=green}Approved{/status}
- Testing status: {status:color=blue}In Progress{/status}

:::panel type="warning"
**Note**: Please review the changes carefully.
:::

### Code Reference
```python
def review_page():
    return "Comment added successfully"
```

> This comment demonstrates ADF formatting capabilities."""
        
        comment_result = await mcp_client.add_confluence_comment(
            page_id=page_id,
            content=comment_text
        )
        
        self.assert_success_response(comment_result)
    
    async def test_add_comment_with_mentions(self, mcp_client, test_config, test_data_manager):
        """Test adding comment with user mentions."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add comment with mention (generic format)
        comment_text = f"Comment with mention: @[Reviewer] please check this page at {self.test_start_time}"
        comment_result = await mcp_client.add_confluence_comment(
            page_id=page_id,
            content=comment_text
        )
        
        self.assert_success_response(comment_result)


@pytest.mark.api
@pytest.mark.confluence
class TestConfluenceLabels(MCPConfluenceTest):
    """Test Confluence label functionality."""
    
    async def test_add_single_label(self, mcp_client, test_config, test_data_manager):
        """Test adding a single label to a page."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add label
        test_label = test_config["test_label"]
        label_result = await mcp_client.add_confluence_label(
            page_id=page_id,
            name=test_label
        )
        
        self.assert_success_response(label_result)
        
        # Verify label was added
        labels_data = self.extract_json(label_result)
        assert isinstance(labels_data, (list, dict))
    
    async def test_add_multiple_labels(self, mcp_client, test_config, test_data_manager):
        """Test adding multiple labels to a page."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add multiple labels
        labels = [
            test_config["test_label"],
            "documentation",
            "testing",
            "automation"
        ]
        
        for label in labels:
            label_result = await mcp_client.add_confluence_label(
                page_id=page_id,
                name=label
            )
            self.assert_success_response(label_result)
    
    async def test_add_label_to_nonexistent_page(self, mcp_client, test_config):
        """Test adding label to non-existent page."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.add_confluence_label(
                page_id="999999999",
                name="should-fail"
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["not found", "does not exist", "invalid"]), \
            f"Expected page not found error, got: {error_msg}"


@pytest.mark.api
@pytest.mark.confluence
class TestConfluencePageHierarchy(MCPConfluenceTest):
    """Test Confluence page hierarchy functionality."""
    
    async def test_create_page_hierarchy(self, mcp_client, test_config, test_data_manager):
        """Test creating a multi-level page hierarchy."""
        # Create root page
        root_title = self.generate_unique_title("Root Page")
        root_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=root_title,
            content="# Root Page\n\nThis is the root of a page hierarchy.",
            content_format="markdown"
        )
        
        root_id = self.extract_page_id(root_result)
        self.track_resource("confluence_page", root_id)
        
        # Create level 1 child
        child1_title = self.generate_unique_title("Child Level 1")
        child1_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=child1_title,
            content="# Level 1 Child\n\nThis is a first-level child page.",
            content_format="markdown",
            parent_id=root_id
        )
        
        child1_id = self.extract_page_id(child1_result)
        self.track_resource("confluence_page", child1_id)
        
        # Create level 2 child
        child2_title = self.generate_unique_title("Child Level 2")
        child2_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=child2_title,
            content="# Level 2 Child\n\nThis is a second-level child page.",
            content_format="markdown",
            parent_id=child1_id
        )
        
        child2_id = self.extract_page_id(child2_result)
        self.track_resource("confluence_page", child2_id)
        
        # Verify all pages created successfully
        assert root_id
        assert child1_id 
        assert child2_id
    
    async def test_move_page_hierarchy(self, mcp_client, test_config, test_data_manager):
        """Test moving a page to a different parent (if supported)."""
        # Create two parent pages
        parent1_result = await self.create_test_page(
            mcp_client, test_config,
            content="# Original Parent\n\nOriginal parent page."
        )
        parent1_id = self.extract_page_id(parent1_result)
        
        parent2_result = await self.create_test_page(
            mcp_client, test_config, 
            content="# New Parent\n\nNew parent page."
        )
        parent2_id = self.extract_page_id(parent2_result)
        
        # Create child under first parent
        child_title = self.generate_unique_title("Movable Child")
        child_result = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=child_title,
            content="# Child Page\n\nThis page will be moved.",
            content_format="markdown",
            parent_id=parent1_id
        )
        
        child_id = self.extract_page_id(child_result)
        self.track_resource("confluence_page", child_id)
        
        # Note: Moving pages requires different API calls that may not be available
        # This test primarily validates the hierarchy creation works


@pytest.mark.api
@pytest.mark.confluence
@pytest.mark.error_handling
class TestConfluenceErrorHandling(MCPConfluenceTest):
    """Test error handling scenarios."""
    
    async def test_create_page_missing_title(self, mcp_client, test_config):
        """Test creating page with missing title."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title="",  # Empty title
                content="Content without title",
                content_format="markdown"
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["title", "required", "empty"]), \
            f"Expected title validation error, got: {error_msg}"
    
    async def test_create_duplicate_title_in_space(self, mcp_client, test_config, test_data_manager):
        """Test creating pages with duplicate titles."""
        duplicate_title = self.generate_unique_title("Duplicate Title Test")
        
        # Create first page
        result1 = await mcp_client.create_confluence_page(
            space_id=test_config["confluence_space"],
            title=duplicate_title,
            content="First page with this title",
            content_format="markdown"
        )
        
        page1_id = self.extract_page_id(result1)
        self.track_resource("confluence_page", page1_id)
        
        # Try to create second page with same title
        with pytest.raises(Exception) as exc_info:
            await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title=duplicate_title,
                content="Second page with same title",
                content_format="markdown"
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["already exists", "duplicate", "title"]), \
            f"Expected duplicate title error, got: {error_msg}"
    
    async def test_invalid_parent_id(self, mcp_client, test_config):
        """Test creating page with invalid parent ID."""
        with pytest.raises(Exception) as exc_info:
            await mcp_client.create_confluence_page(
                space_id=test_config["confluence_space"],
                title="Child with Invalid Parent",
                content="This should fail",
                content_format="markdown",
                parent_id="999999999"  # Invalid parent ID
            )
        
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ["parent", "not found", "invalid"]), \
            f"Expected parent validation error, got: {error_msg}"


@pytest.mark.api
@pytest.mark.confluence
@pytest.mark.performance
class TestConfluenceBulkOperations(MCPConfluenceTest):
    """Test bulk operations and performance."""
    
    async def test_create_multiple_pages(self, mcp_client, test_config, test_data_manager):
        """Test creating multiple pages efficiently."""
        page_ids = []
        
        # Create 3 test pages
        for i in range(3):
            result = await self.create_test_page(
                mcp_client, test_config,
                content=f"# Bulk Page {i+1}\n\nBulk creation test page #{i+1}"
            )
            page_id = self.extract_page_id(result)
            page_ids.append(page_id)
        
        # Verify all pages were created
        assert len(page_ids) == 3
        assert all(page_id for page_id in page_ids)
    
    async def test_batch_labels(self, mcp_client, test_config, test_data_manager):
        """Test adding multiple labels to multiple pages."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add multiple labels efficiently
        labels = [
            test_config["test_label"],
            "batch-test",
            "automation",
            "confluence-api"
        ]
        
        for label in labels:
            label_result = await mcp_client.add_confluence_label(
                page_id=page_id,
                name=label
            )
            self.assert_success_response(label_result)
    
    async def test_batch_comments(self, mcp_client, test_config, test_data_manager):
        """Test adding multiple comments to a page."""
        # Create test page
        create_result = await self.create_test_page(mcp_client, test_config)
        page_id = self.extract_page_id(create_result)
        
        # Add multiple comments
        comments = [
            "First batch comment",
            "Second comment with **formatting**", 
            "Third comment with {status:color=green}Complete{/status}",
            "Final comment with :::panel type=\"info\"\\n**Info**: Batch testing complete\\n:::"
        ]
        
        for i, comment_text in enumerate(comments):
            comment_result = await mcp_client.add_confluence_comment(
                page_id=page_id,
                content=f"{comment_text} (#{i+1})"
            )
            self.assert_success_response(comment_result)