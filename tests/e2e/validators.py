"""
Validation utilities for MCP Atlassian E2E tests.

Provides comprehensive validation for:
- ADF (Atlassian Document Format) responses
- API response structures
- Content formatting
- Error responses
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum


class DeploymentType(Enum):
    """Atlassian deployment types."""
    CLOUD = "cloud"
    SERVER = "server"
    DATACENTER = "datacenter"


class FormatType(Enum):
    """Content format types."""
    ADF = "adf"
    WIKI = "wiki"
    MARKDOWN = "markdown"
    STORAGE = "storage"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.details.update(other.details)


class ADFValidator:
    """Validator for ADF (Atlassian Document Format) content."""
    
    # Valid ADF node types
    VALID_NODE_TYPES = {
        # Block nodes
        "doc", "paragraph", "heading", "blockquote", "codeBlock", "rule",
        "bulletList", "orderedList", "listItem", "table", "tableRow", 
        "tableCell", "tableHeader", "expand", "panel", "media", "mediaGroup",
        "mediaSingle", "layout", "layoutSection", "layoutColumn",
        
        # Inline nodes
        "text", "hardBreak", "inlineCard", "mention", "emoji", "date",
        "status", "link", "inlineExtension",
        
        # Extension nodes
        "extension", "bodiedExtension"
    }
    
    # Valid mark types
    VALID_MARK_TYPES = {
        "strong", "em", "code", "link", "strike", "subsup", "underline",
        "textColor", "backgroundColor", "annotation"
    }
    
    def validate_adf(self, content: Union[Dict, str]) -> ValidationResult:
        """
        Validate ADF document structure.
        
        Args:
            content: ADF content as dict or JSON string
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(True, [], [], {})
        
        try:
            if isinstance(content, str):
                content = json.loads(content)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
            return result
        
        if not isinstance(content, dict):
            result.add_error(f"ADF content must be a dict, got {type(content)}")
            return result
        
        # Validate top-level structure
        self._validate_document_structure(content, result)
        
        # Validate content recursively
        if "content" in content:
            self._validate_content_array(content["content"], result)
        
        result.details["node_count"] = self._count_nodes(content)
        result.details["format_type"] = FormatType.ADF
        
        return result
    
    def _validate_document_structure(self, doc: Dict, result: ValidationResult):
        """Validate top-level document structure."""
        required_fields = ["type", "version"]
        
        for field in required_fields:
            if field not in doc:
                result.add_error(f"Missing required field: {field}")
        
        if "type" in doc and doc["type"] != "doc":
            result.add_error(f"Document type must be 'doc', got '{doc['type']}'")
        
        if "version" in doc:
            version = doc["version"]
            if not isinstance(version, int) or version < 1:
                result.add_error(f"Version must be positive integer, got {version}")
    
    def _validate_content_array(self, content: List, result: ValidationResult, path: str = ""):
        """Validate array of content nodes."""
        if not isinstance(content, list):
            result.add_error(f"Content at {path} must be array, got {type(content)}")
            return
        
        for i, node in enumerate(content):
            node_path = f"{path}[{i}]"
            self._validate_node(node, result, node_path)
    
    def _validate_node(self, node: Dict, result: ValidationResult, path: str = ""):
        """Validate individual ADF node."""
        if not isinstance(node, dict):
            result.add_error(f"Node at {path} must be dict, got {type(node)}")
            return
        
        # Check required type field
        if "type" not in node:
            result.add_error(f"Node at {path} missing required 'type' field")
            return
        
        node_type = node["type"]
        if node_type not in self.VALID_NODE_TYPES:
            result.add_warning(f"Unknown node type '{node_type}' at {path}")
        
        # Validate specific node types
        if node_type == "text":
            self._validate_text_node(node, result, path)
        elif node_type in ["heading", "paragraph", "listItem"]:
            self._validate_block_node(node, result, path)
        elif node_type == "table":
            self._validate_table_node(node, result, path)
        
        # Validate marks if present
        if "marks" in node:
            self._validate_marks(node["marks"], result, path)
        
        # Validate attributes if present
        if "attrs" in node:
            self._validate_attributes(node["attrs"], node_type, result, path)
        
        # Recursively validate content
        if "content" in node:
            self._validate_content_array(node["content"], result, f"{path}.content")
    
    def _validate_text_node(self, node: Dict, result: ValidationResult, path: str):
        """Validate text node specifics."""
        if "text" not in node:
            result.add_error(f"Text node at {path} missing 'text' field")
        
        text_content = node.get("text", "")
        if not isinstance(text_content, str):
            result.add_error(f"Text content at {path} must be string")
    
    def _validate_block_node(self, node: Dict, result: ValidationResult, path: str):
        """Validate block node specifics."""
        node_type = node["type"]
        
        # Heading nodes should have level attribute
        if node_type == "heading":
            attrs = node.get("attrs", {})
            level = attrs.get("level")
            if level is None:
                result.add_error(f"Heading at {path} missing level attribute")
            elif not isinstance(level, int) or level < 1 or level > 6:
                result.add_error(f"Heading level at {path} must be 1-6, got {level}")
    
    def _validate_table_node(self, node: Dict, result: ValidationResult, path: str):
        """Validate table node structure.""" 
        content = node.get("content", [])
        
        for i, row_node in enumerate(content):
            if not isinstance(row_node, dict):
                continue
                
            if row_node.get("type") == "tableRow":
                cells = row_node.get("content", [])
                for j, cell_node in enumerate(cells):
                    if isinstance(cell_node, dict):
                        cell_type = cell_node.get("type")
                        if cell_type not in ["tableCell", "tableHeader"]:
                            result.add_warning(f"Unexpected cell type '{cell_type}' at {path}[{i}][{j}]")
    
    def _validate_marks(self, marks: List, result: ValidationResult, path: str):
        """Validate text marks."""
        if not isinstance(marks, list):
            result.add_error(f"Marks at {path} must be array")
            return
        
        for i, mark in enumerate(marks):
            if not isinstance(mark, dict):
                result.add_error(f"Mark at {path}[{i}] must be dict")
                continue
            
            if "type" not in mark:
                result.add_error(f"Mark at {path}[{i}] missing type")
                continue
            
            mark_type = mark["type"]
            if mark_type not in self.VALID_MARK_TYPES:
                result.add_warning(f"Unknown mark type '{mark_type}' at {path}[{i}]")
    
    def _validate_attributes(self, attrs: Dict, node_type: str, result: ValidationResult, path: str):
        """Validate node attributes."""
        if not isinstance(attrs, dict):
            result.add_error(f"Attributes at {path} must be dict")
            return
        
        # Type-specific attribute validation
        if node_type == "panel":
            panel_type = attrs.get("panelType")
            valid_panel_types = ["info", "note", "warning", "error", "success"]
            if panel_type and panel_type not in valid_panel_types:
                result.add_warning(f"Unknown panel type '{panel_type}' at {path}")
        
        elif node_type == "status":
            status_attrs = ["text", "color", "localId"]
            for attr in status_attrs:
                if attr in attrs and not isinstance(attrs[attr], str):
                    result.add_error(f"Status {attr} at {path} must be string")
    
    def _count_nodes(self, content: Union[Dict, List], count: int = 0) -> int:
        """Count total nodes in ADF structure."""
        if isinstance(content, dict):
            count += 1
            if "content" in content:
                count = self._count_nodes(content["content"], count)
        elif isinstance(content, list):
            for item in content:
                count = self._count_nodes(item, count)
        
        return count


class WikiMarkupValidator:
    """Validator for wiki markup content (Server/DC)."""
    
    # Common wiki markup patterns
    WIKI_PATTERNS = {
        "heading": r"^h[1-6]\.",
        "bold": r"\*[^*]+\*",
        "italic": r"_[^_]+_", 
        "code": r"\{\{[^}]+\}\}",
        "link": r"\[[^\]]+\]",
        "list": r"^[\*#]+ ",
        "table": r"\|\|?[^|]*\|",
        "macro": r"\{[^}]+\}",
        "panel": r"\{panel[^}]*\}",
        "code_block": r"\{code[^}]*\}"
    }
    
    def validate_wiki_markup(self, content: str) -> ValidationResult:
        """
        Validate wiki markup content.
        
        Args:
            content: Wiki markup content as string
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(True, [], [], {})
        
        if not isinstance(content, str):
            result.add_error(f"Wiki markup content must be string, got {type(content)}")
            return result
        
        # Check for valid wiki markup patterns
        found_patterns = {}
        for pattern_name, pattern in self.WIKI_PATTERNS.items():
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                found_patterns[pattern_name] = len(matches)
        
        result.details["found_patterns"] = found_patterns
        result.details["format_type"] = FormatType.WIKI
        result.details["content_length"] = len(content)
        
        # Check for potential ADF leakage in wiki markup
        adf_indicators = ["\"type\":", "\"version\":", "\"content\":["]
        for indicator in adf_indicators:
            if indicator in content:
                result.add_warning(f"Found ADF-like content in wiki markup: {indicator}")
        
        return result


class ResponseValidator:
    """Validator for general MCP tool responses."""
    
    def __init__(self):
        self.adf_validator = ADFValidator()
        self.wiki_validator = WikiMarkupValidator()
    
    def validate_response(
        self,
        response: Any,
        expected_type: str = "success",
        deployment_type: DeploymentType = DeploymentType.CLOUD,
        expected_fields: List[str] = None
    ) -> ValidationResult:
        """
        Comprehensive response validation.
        
        Args:
            response: MCP tool response
            expected_type: Expected response type (success, error)
            deployment_type: Atlassian deployment type
            expected_fields: Fields that should be present
            
        Returns:
            ValidationResult with comprehensive validation
        """
        result = ValidationResult(True, [], [], {})
        
        # Extract JSON from response
        data = self._extract_json(response)
        if not data and expected_type == "success":
            result.add_error("Could not extract valid JSON from response")
            return result
        
        # Basic structure validation
        self._validate_basic_structure(data, expected_type, result)
        
        # Field presence validation
        if expected_fields:
            self._validate_required_fields(data, expected_fields, result)
        
        # Content format validation
        if expected_type == "success":
            format_result = self._validate_content_format(data, deployment_type)
            result.merge(format_result)
        
        result.details["deployment_type"] = deployment_type
        result.details["response_size"] = len(str(response))
        
        return result
    
    def validate_jira_issue_response(
        self,
        response: Any,
        operation: str = "create",
        deployment_type: DeploymentType = DeploymentType.CLOUD
    ) -> ValidationResult:
        """Validate Jira issue operation response."""
        result = ValidationResult(True, [], [], {})
        
        data = self._extract_json(response)
        
        if operation == "create":
            # Check for either flat structure (key, id) or nested structure (message, issue)
            if "issue" in data and isinstance(data.get("issue"), dict):
                # Nested structure: expect top-level "issue" and nested "key"
                required_fields = ["issue"]
                field_result = self._validate_required_fields(data, required_fields, result)
                result.merge(field_result)
                
                # Check nested issue structure
                issue_data = data.get("issue", {})
                issue_required = ["key", "id"]
                issue_result = ValidationResult(True, [], [], {})
                missing_issue_fields = [f for f in issue_required if f not in issue_data]
                if missing_issue_fields:
                    issue_result.add_error(f"Missing required fields in issue: {missing_issue_fields}")
                result.merge(issue_result)
            else:
                # Flat structure: expect key and id at top level
                required_fields = ["key", "id"]
                field_result = self._validate_required_fields(data, required_fields, result)
                result.merge(field_result)
            
            # Validate issue key format
            issue_key = data.get("key") or data.get("issue", {}).get("key")
            if issue_key:
                if not re.match(r'^[A-Z]+-\d+$', issue_key):
                    result.add_error(f"Invalid issue key format: {issue_key}")
        
        elif operation == "update":
            # Updates may have different structure
            pass
        
        elif operation == "comment":
            # Comment responses should have comment data
            if "body" not in data and "comment" not in data:
                result.add_warning("Comment response missing body/comment field")
        
        # Validate description content if present
        description_paths = [
            ["issue", "fields", "description"],
            ["fields", "description"],
            ["description"]
        ]
        
        for path in description_paths:
            desc_content = data
            for key in path:
                if isinstance(desc_content, dict) and key in desc_content:
                    desc_content = desc_content[key]
                else:
                    desc_content = None
                    break
            
            if desc_content:
                format_result = self._validate_content_format(
                    {"content": desc_content}, 
                    deployment_type
                )
                result.merge(format_result)
                break
        
        result.details["operation"] = operation
        return result
    
    def validate_confluence_page_response(
        self,
        response: Any,
        operation: str = "create",
        deployment_type: DeploymentType = DeploymentType.CLOUD
    ) -> ValidationResult:
        """Validate Confluence page operation response."""
        result = ValidationResult(True, [], [], {})
        
        data = self._extract_json(response)
        
        if operation == "create":
            # Check for either flat structure (id, title) or nested structure (message, page)
            if "page" in data and isinstance(data.get("page"), dict):
                # Nested structure: expect top-level "page" and nested "id", "title"
                required_fields = ["page"]
                field_result = self._validate_required_fields(data, required_fields, result)
                result.merge(field_result)
                
                # Check nested page structure
                page_data = data.get("page", {})
                page_required = ["id", "title"]
                page_result = ValidationResult(True, [], [], {})
                missing_page_fields = [f for f in page_required if f not in page_data]
                if missing_page_fields:
                    page_result.add_error(f"Missing required fields in page: {missing_page_fields}")
                result.merge(page_result)
                
                # Validate page ID format
                page_id = page_data.get("id")
                if page_id and not str(page_id).isdigit():
                    result.add_error(f"Invalid page ID format: {page_id}")
            else:
                # Flat structure: expect id and title at top level
                required_fields = ["id", "title"]
                field_result = self._validate_required_fields(data, required_fields, result)
                result.merge(field_result)
                
                # Validate page ID format
                page_id = data.get("id")
                if page_id and not str(page_id).isdigit():
                    result.add_error(f"Invalid page ID format: {page_id}")
        
        # Validate page content if present
        content_paths = [
            ["body", "storage", "value"],
            ["body", "atlas_doc_format"],
            ["content"]
        ]
        
        for path in content_paths:
            content = data
            for key in path:
                if isinstance(content, dict) and key in content:
                    content = content[key]
                else:
                    content = None
                    break
            
            if content:
                format_result = self._validate_content_format(
                    {"content": content},
                    deployment_type
                )
                result.merge(format_result)
                break
        
        result.details["operation"] = operation
        return result
    
    def _extract_json(self, response: Any) -> Dict[str, Any]:
        """Extract JSON from MCP response."""
        if isinstance(response, dict):
            return response
        
        try:
            # FastMCP ToolResult shape
            content = getattr(response, "content", None) or response.get("content")
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
            return json.loads(str(response))
        except Exception:
            return {}
    
    def _validate_basic_structure(
        self,
        data: Dict[str, Any],
        expected_type: str,
        result: ValidationResult
    ):
        """Validate basic response structure."""
        if expected_type == "error":
            error_indicators = ["error", "errors", "errorMessages", "message"]
            has_error = any(key in data for key in error_indicators)
            if not has_error:
                result.add_warning("Expected error response but no error indicators found")
        
        elif expected_type == "success":
            # Check for unexpected error indicators
            error_fields = ["error", "errors", "errorMessages"]
            for field in error_fields:
                if field in data and data[field]:
                    result.add_error(f"Unexpected error in success response: {data[field]}")
    
    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        result: ValidationResult
    ) -> ValidationResult:
        """Validate presence of required fields."""
        field_result = ValidationResult(True, [], [], {})
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            field_result.add_error(f"Missing required fields: {missing_fields}")
        
        field_result.details["required_fields"] = required_fields
        field_result.details["missing_fields"] = missing_fields
        
        return field_result
    
    def _validate_content_format(
        self,
        data: Dict[str, Any],
        deployment_type: DeploymentType
    ) -> ValidationResult:
        """Validate content format based on deployment type."""
        result = ValidationResult(True, [], [], {})
        
        # Look for content in various locations
        content_value = None
        content_format = None
        
        # Common content locations
        content_paths = [
            (["content"], "unknown"),
            (["body", "adf"], "adf"),
            (["body", "atlas_doc_format"], "adf"),
            (["body", "storage", "value"], "storage"),
            (["body", "wiki", "value"], "wiki"),
            (["description"], "unknown"),
            (["value"], "unknown")
        ]
        
        for path, format_hint in content_paths:
            temp_content = data
            for key in path:
                if isinstance(temp_content, dict) and key in temp_content:
                    temp_content = temp_content[key]
                else:
                    temp_content = None
                    break
            
            if temp_content is not None:
                content_value = temp_content
                content_format = format_hint
                break
        
        if content_value is None:
            result.add_warning("No content found in response")
            return result
        
        # Validate based on deployment type and content format
        if deployment_type == DeploymentType.CLOUD:
            # Cloud should use ADF
            if isinstance(content_value, dict):
                adf_result = self.adf_validator.validate_adf(content_value)
                result.merge(adf_result)
            elif isinstance(content_value, str):
                # String content in cloud might be converted
                if self._looks_like_adf_json(content_value):
                    try:
                        adf_data = json.loads(content_value)
                        adf_result = self.adf_validator.validate_adf(adf_data)
                        result.merge(adf_result)
                    except json.JSONDecodeError:
                        result.add_warning("Content looks like ADF JSON but failed to parse")
                else:
                    # Check if it's accidentally wiki markup
                    if self._looks_like_wiki_markup(content_value):
                        result.add_warning("Found wiki markup in Cloud deployment")
        
        else:  # Server/DC
            # Server/DC should use wiki markup or storage format
            if isinstance(content_value, str):
                wiki_result = self.wiki_validator.validate_wiki_markup(content_value)
                result.merge(wiki_result)
            elif isinstance(content_value, dict):
                # Might be storage format or accidentally ADF
                if self._looks_like_adf(content_value):
                    result.add_warning("Found ADF in Server/DC deployment")
        
        result.details["content_format_detected"] = content_format
        result.details["content_type"] = type(content_value).__name__
        
        return result
    
    def _looks_like_adf_json(self, content: str) -> bool:
        """Check if string content looks like ADF JSON."""
        adf_indicators = ['"type":"doc"', '"version":', '"content":[']
        return any(indicator in content for indicator in adf_indicators)
    
    def _looks_like_adf(self, content: Dict) -> bool:
        """Check if dict content looks like ADF."""
        return (
            isinstance(content, dict) and
            content.get("type") == "doc" and
            "version" in content and
            "content" in content
        )
    
    def _looks_like_wiki_markup(self, content: str) -> bool:
        """Check if string content looks like wiki markup."""
        wiki_indicators = [r'h[1-6]\.', r'\*[^*]+\*', r'\{[^}]+\}', r'\[[^\]]+\]']
        return any(re.search(pattern, content) for pattern in wiki_indicators)


# Convenience functions
def validate_adf(content: Union[Dict, str]) -> ValidationResult:
    """Validate ADF content."""
    validator = ADFValidator()
    return validator.validate_adf(content)


def validate_response(
    response: Any,
    expected_type: str = "success",
    deployment_type: DeploymentType = DeploymentType.CLOUD,
    expected_fields: List[str] = None
) -> ValidationResult:
    """Validate MCP tool response."""
    validator = ResponseValidator()
    return validator.validate_response(response, expected_type, deployment_type, expected_fields)


def validate_jira_response(
    response: Any,
    operation: str = "create",
    deployment_type: DeploymentType = DeploymentType.CLOUD
) -> ValidationResult:
    """Validate Jira operation response."""
    validator = ResponseValidator()
    return validator.validate_jira_issue_response(response, operation, deployment_type)


def validate_confluence_response(
    response: Any,
    operation: str = "create", 
    deployment_type: DeploymentType = DeploymentType.CLOUD
) -> ValidationResult:
    """Validate Confluence operation response."""
    validator = ResponseValidator()
    return validator.validate_confluence_page_response(response, operation, deployment_type)