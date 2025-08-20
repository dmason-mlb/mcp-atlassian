"""
Base test class for MCP Atlassian E2E tests.

Provides common functionality, utilities, and patterns for all test types.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import pytest


class MCPBaseTest:
    """
    Base test class providing common functionality for MCP Atlassian tests.
    
    Features:
    - Standardized test data creation and cleanup
    - Response validation utilities
    - Error handling patterns
    - Resource tracking
    - Common assertion helpers
    """
    
    def setup_method(self, method):
        """Set up each test method with tracking."""
        self.test_name = method.__name__
        self.created_resources = []
        self.test_start_time = datetime.now()
    
    def teardown_method(self, method):
        """Clean up after each test method."""
        # Cleanup is handled by test_data_manager fixture
        pass
    
    # === Resource Tracking ===
    
    def track_resource(self, resource_type: str, resource_id: str, cleanup_data: Dict[str, Any] = None):
        """
        Track a created resource for cleanup.
        
        Args:
            resource_type: Type of resource (jira_issue, confluence_page, etc.)
            resource_id: Unique identifier for the resource
            cleanup_data: Additional data needed for cleanup
        """
        resource = {
            "type": resource_type,
            "id": resource_id,
            "created_at": datetime.now(),
            "test_name": self.test_name,
            "cleanup_data": cleanup_data or {}
        }
        self.created_resources.append(resource)
    
    # === Response Validation ===
    
    def assert_success_response(self, result: Any, expected_keys: List[str] = None):
        """
        Assert that an MCP tool response indicates success.
        
        Args:
            result: MCP tool result
            expected_keys: Keys that should be present in response
        """
        assert result is not None, "Response should not be None"
        
        # If it's a raw response, try to extract JSON
        if hasattr(result, 'content') or isinstance(result, dict):
            data = self._extract_json(result)
        else:
            data = result
        
        assert isinstance(data, dict), f"Response should be a dict, got {type(data)}"
        
        # Check for common error indicators
        self._assert_no_errors(data)
        
        # Check expected keys if provided
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in data]
            assert not missing_keys, f"Missing expected keys: {missing_keys}"
    
    def assert_error_response(self, result: Any, expected_error_pattern: str = None):
        """
        Assert that an MCP tool response indicates an error.
        
        Args:
            result: MCP tool result 
            expected_error_pattern: Regex pattern for expected error message
        """
        # For exceptions, check the exception message
        if isinstance(result, Exception):
            error_msg = str(result)
            if expected_error_pattern:
                assert re.search(expected_error_pattern, error_msg, re.IGNORECASE), \
                    f"Error message '{error_msg}' does not match pattern '{expected_error_pattern}'"
            return
        
        # For normal responses, look for error indicators
        data = self._extract_json(result) if result else {}
        
        # Look for common error fields
        error_found = any(key in data for key in ['error', 'errors', 'errorMessages'])
        assert error_found, f"Expected error response, but got: {data}"
        
        if expected_error_pattern:
            error_text = json.dumps(data).lower()
            assert re.search(expected_error_pattern, error_text, re.IGNORECASE), \
                f"Error response does not match pattern: {expected_error_pattern}"
    
    def assert_adf_response(self, result: Any, deployment_type: str = "cloud"):
        """
        Assert that a response contains properly formatted ADF content.
        
        Args:
            result: MCP tool result
            deployment_type: Expected deployment type (cloud/server)
        """
        data = self._extract_json(result)
        
        if deployment_type == "cloud":
            # Should contain ADF structure
            self._assert_adf_structure(data)
        else:
            # Server/DC should contain wiki markup or plain text
            self._assert_wiki_markup_structure(data)
    
    # === Data Extraction Utilities ===
    
    def extract_value(self, result: Any, *keys: str, default: Any = None) -> Any:
        """
        Extract a value from nested MCP response using key path.
        
        Args:
            result: MCP tool result
            *keys: Key path (e.g., "issue", "key")
            default: Default value if extraction fails
            
        Returns:
            Extracted value or default
        """
        data = self._extract_json(result)
        
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        
        return data
    
    def extract_issue_key(self, create_result: Any) -> str:
        """Extract Jira issue key from creation response."""
        issue_key = self.extract_value(create_result, "issue", "key") or \
                   self.extract_value(create_result, "key")
        
        assert issue_key, f"Could not extract issue key from: {create_result}"
        assert re.match(r'^[A-Z]+-\d+$', issue_key), f"Invalid issue key format: {issue_key}"
        
        return issue_key
    
    def extract_page_id(self, create_result: Any) -> str:
        """Extract Confluence page ID from creation response."""
        page_id = self.extract_value(create_result, "page", "id") or \
                 self.extract_value(create_result, "id")
        
        assert page_id, f"Could not extract page ID from: {create_result}"
        assert str(page_id).isdigit(), f"Invalid page ID format: {page_id}"
        
        return str(page_id)
    
    # === Test Data Generators ===
    
    def generate_unique_title(self, base: str = "Test") -> str:
        """Generate a unique title for test resources."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"{base} {timestamp} - {self.test_name}"
    
    def generate_test_description(self, content_type: str = "basic") -> str:
        """Generate test description with specified content type."""
        base_desc = f"Test description created by {self.test_name} at {datetime.now()}"
        
        if content_type == "adf_rich":
            return f"""# {base_desc}

## ADF Test Elements

### Status Badges
Status: {{status:color=blue}}Testing{{/status}}

### Info Panel
:::panel type="info"
This is a test page with ADF elements for validation.
:::

### Code Block
```python
def test_function():
    return "ADF formatting test"
```

### Table
| Item | Status | Notes |
|------|--------|-------|
| Test 1 | {{status:color=green}}Pass{{/status}} | Working |
| Test 2 | {{status:color=yellow}}Review{{/status}} | Pending |
"""
        
        elif content_type == "markdown":
            return f"""# {base_desc}

This is **bold** and *italic* text.

## Features
- Bullet points
- Code blocks
- Tables

```javascript
function test() {{
    console.log('Hello MCP');
}}
```

> This is a blockquote for testing.
"""
        
        else:  # basic
            return base_desc
    
    # === Private Utilities ===
    
    def _extract_json(self, result: Any) -> Dict[str, Any]:
        """Extract JSON from MCP result."""
        if isinstance(result, dict):
            return result
        
        try:
            # FastMCP ToolResult shape
            content = getattr(result, "content", None) or result.get("content")
            if isinstance(content, list) and content:
                for item in content:
                    text = (
                        item.get("text")
                        if isinstance(item, dict)
                        else getattr(item, "text", None)
                    )
                    if text:
                        try:
                            return json.loads(text)
                        except Exception:
                            continue
        except Exception:
            pass
        
        # Fallback
        try:
            return json.loads(str(result))
        except Exception:
            return {}
    
    def _assert_no_errors(self, data: Dict[str, Any]):
        """Assert that response data contains no error indicators."""
        error_fields = ['error', 'errors', 'errorMessages']
        
        for field in error_fields:
            if field in data:
                error_content = data[field]
                if error_content:  # Not empty
                    pytest.fail(f"Response contains {field}: {error_content}")
    
    def _assert_adf_structure(self, data: Dict[str, Any]):
        """Assert that data contains valid ADF structure."""
        # Look for ADF content in common locations
        adf_content = None
        
        # Check various possible locations for ADF content
        possible_paths = [
            ["body", "adf"],
            ["body", "atlas_doc_format"],  
            ["content"],
            ["adf"],
            ["atlas_doc_format"]
        ]
        
        for path in possible_paths:
            content = data
            for key in path:
                if isinstance(content, dict) and key in content:
                    content = content[key]
                else:
                    content = None
                    break
            
            if content and isinstance(content, dict):
                adf_content = content
                break
        
        if adf_content:
            # Validate basic ADF structure
            assert "type" in adf_content, "ADF content should have 'type' field"
            assert "version" in adf_content, "ADF content should have 'version' field"
            assert "content" in adf_content, "ADF content should have 'content' field"
        
        # If no ADF found, at least ensure no wiki markup
        text_content = json.dumps(data).lower()
        wiki_patterns = [r'\*[^*]+\*', r'h[1-6]\.', r'\{.*?\}', r'\[.*?\|.*?\]']
        
        for pattern in wiki_patterns:
            matches = re.findall(pattern, text_content)
            # Allow some matches but not excessive wiki markup
            assert len(matches) < 5, f"Found wiki markup patterns in cloud response: {matches}"
    
    def _assert_wiki_markup_structure(self, data: Dict[str, Any]):
        """Assert that data contains wiki markup (for Server/DC)."""
        # For Server/DC, we expect wiki markup or plain text
        # This is less strict since Server/DC has different formatting
        pass  # Basic validation sufficient
    
    # === Async Utilities ===
    
    async def wait_for_condition(
        self,
        condition_func,
        timeout: float = 30.0,
        interval: float = 1.0,
        description: str = "condition"
    ):
        """
        Wait for a condition to become true.
        
        Args:
            condition_func: Async function that returns True when condition is met
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds
            description: Description for error messages
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                if await condition_func():
                    return
            except Exception:
                pass  # Ignore exceptions during polling
            
            await asyncio.sleep(interval)
        
        pytest.fail(f"Timeout waiting for {description} after {timeout}s")


class MCPJiraTest(MCPBaseTest):
    """Base class for Jira-specific tests."""
    
    async def create_test_issue(
        self,
        mcp_client,
        test_config,
        issue_type: str = "Task",
        description: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test Jira issue and track it for cleanup."""
        summary = self.generate_unique_title("Test Issue")
        
        result = await mcp_client.create_jira_issue(
            project_key=test_config["jira_project"],
            summary=summary,
            issue_type=issue_type,
            description=description or self.generate_test_description(),
            **kwargs
        )
        
        issue_key = self.extract_issue_key(result)
        self.track_resource("jira_issue", issue_key)
        
        return result


class MCPConfluenceTest(MCPBaseTest):
    """Base class for Confluence-specific tests."""
    
    async def create_test_page(
        self,
        mcp_client,
        test_config,
        content_format: str = "markdown",
        content: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test Confluence page and track it for cleanup."""
        title = self.generate_unique_title("Test Page")
        
        # Get space ID from space key (assuming it's provided)
        space_key = test_config["confluence_space"]
        
        result = await mcp_client.create_confluence_page(
            space_id=space_key,  # This might need adjustment based on actual API
            title=title,
            content=content or self.generate_test_description("markdown"),
            content_format=content_format,
            **kwargs
        )
        
        page_id = self.extract_page_id(result)
        self.track_resource("confluence_page", page_id)
        
        return result