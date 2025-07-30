"""ADF Schema Validation Module.

This module provides validation for Atlassian Document Format (ADF) JSON structures
against the official ADF schema.
"""

import json
import logging
import os
from typing import Any, Optional
from functools import lru_cache

try:
    import jsonschema
    from jsonschema import Draft7Validator, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback for type hints

logger = logging.getLogger(__name__)


class ADFValidator:
    """Validates ADF documents against the official schema."""
    
    # Official ADF schema URL
    ADF_SCHEMA_URL = "http://go.atlassian.com/adf-json-schema"
    
    # Validation levels
    VALIDATION_OFF = "off"
    VALIDATION_WARN = "warn"
    VALIDATION_ERROR = "error"
    
    def __init__(self, validation_level: str = VALIDATION_WARN) -> None:
        """
        Initialize the ADF validator.
        
        Args:
            validation_level: Validation level - off, warn, or error
        """
        self.validation_level = validation_level.lower()
        self._schema: Optional[dict[str, Any]] = None
        self._validator: Optional[Any] = None
        
        if not JSONSCHEMA_AVAILABLE and self.validation_level != self.VALIDATION_OFF:
            logger.warning(
                "jsonschema library not available. Install with: pip install jsonschema. "
                "ADF validation will be disabled."
            )
            self.validation_level = self.VALIDATION_OFF
    
    @property
    @lru_cache(maxsize=1)
    def schema(self) -> Optional[dict[str, Any]]:
        """Get the ADF schema, loading from file or URL if needed."""
        if self._schema is not None:
            return self._schema
            
        # Try to load from local file first
        schema_file = os.path.join(
            os.path.dirname(__file__), 
            "schemas", 
            "adf-schema.json"
        )
        
        if os.path.exists(schema_file):
            try:
                with open(schema_file, 'r') as f:
                    self._schema = json.load(f)
                logger.info(f"Loaded ADF schema from {schema_file}")
                return self._schema
            except Exception as e:
                logger.error(f"Failed to load schema from file: {e}")
        
        # For now, use a simplified schema
        # In production, this would fetch from ADF_SCHEMA_URL
        self._schema = self._get_simplified_schema()
        return self._schema
    
    def _get_simplified_schema(self) -> dict[str, Any]:
        """Get a simplified ADF schema for basic validation."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "type", "content"],
            "properties": {
                "version": {"const": 1},
                "type": {"const": "doc"},
                "content": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/block_node"}
                }
            },
            "definitions": {
                "block_node": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "enum": [
                                "paragraph", "heading", "bulletList", "orderedList",
                                "codeBlock", "blockquote", "table", "rule", "panel",
                                "expand", "nestedExpand", "mediaGroup", "mediaSingle",
                                "layout"
                            ]
                        },
                        "content": {"type": "array"},
                        "attrs": {"type": "object"}
                    }
                },
                "inline_node": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "enum": [
                                "text", "hardBreak", "emoji", "mention", 
                                "date", "status", "media", "inlineCard"
                            ]
                        },
                        "text": {"type": "string"},
                        "marks": {"type": "array"},
                        "attrs": {"type": "object"}
                    }
                },
                "mark": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "enum": [
                                "strong", "em", "code", "strike", "underline",
                                "link", "textColor", "backgroundColor", "subsup"
                            ]
                        },
                        "attrs": {"type": "object"}
                    }
                }
            }
        }
    
    def validate(self, adf_document: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate an ADF document against the schema.
        
        Args:
            adf_document: The ADF document to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if self.validation_level == self.VALIDATION_OFF:
            return True, []
        
        if not JSONSCHEMA_AVAILABLE:
            return True, ["Validation skipped - jsonschema not available"]
        
        schema = self.schema
        if not schema:
            return True, ["Validation skipped - schema not available"]
        
        try:
            # Create validator if not exists
            if self._validator is None:
                self._validator = Draft7Validator(schema)
            
            # Validate and collect errors
            errors = list(self._validator.iter_errors(adf_document))
            
            if not errors:
                return True, []
            
            # Format error messages
            error_messages = []
            for error in errors:
                path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                error_messages.append(f"{path}: {error.message}")
            
            # Handle based on validation level
            if self.validation_level == self.VALIDATION_WARN:
                for msg in error_messages:
                    logger.warning(f"ADF validation warning: {msg}")
                return True, error_messages  # Still return True for warnings
            else:  # VALIDATION_ERROR
                for msg in error_messages:
                    logger.error(f"ADF validation error: {msg}")
                return False, error_messages
                
        except Exception as e:
            error_msg = f"Validation failed with exception: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_marks(self, marks: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """
        Validate mark combinations according to ADF rules.
        
        Args:
            marks: List of mark objects
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not marks:
            return True, []
        
        errors = []
        mark_types = [mark.get("type") for mark in marks]
        
        # Check for invalid combinations
        if "code" in mark_types:
            # Code can only combine with link
            invalid_with_code = set(mark_types) - {"code", "link"}
            if invalid_with_code:
                errors.append(
                    f"'code' mark cannot be combined with: {', '.join(invalid_with_code)}"
                )
        
        if "textColor" in mark_types:
            # textColor cannot combine with code or link
            if "code" in mark_types or "link" in mark_types:
                errors.append(
                    "'textColor' mark cannot be combined with 'code' or 'link'"
                )
        
        if "backgroundColor" in mark_types:
            # backgroundColor cannot combine with code
            if "code" in mark_types:
                errors.append(
                    "'backgroundColor' mark cannot be combined with 'code'"
                )
        
        return len(errors) == 0, errors


def get_validation_level() -> str:
    """Get the validation level from environment."""
    level = os.getenv("ATLASSIAN_ADF_VALIDATION_LEVEL", ADFValidator.VALIDATION_WARN)
    if level.lower() not in [ADFValidator.VALIDATION_OFF, 
                            ADFValidator.VALIDATION_WARN, 
                            ADFValidator.VALIDATION_ERROR]:
        logger.warning(
            f"Invalid validation level '{level}'. Using 'warn'. "
            f"Valid options: off, warn, error"
        )
        return ADFValidator.VALIDATION_WARN
    return level.lower()