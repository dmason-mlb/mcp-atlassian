"""Schema discovery for meta-tools with LRU caching and conversation hints."""

import json
import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..models.confluence.page import ConfluencePage
from ..models.jira.issue import JiraIssue
from .parameter_optimizer import get_parameter_optimizer, OptimizedParameter

logger = logging.getLogger(__name__)

Service = Literal["jira", "confluence"]
Operation = Literal["create", "update", "get", "delete", "add"]


class SchemaCache:
    """LRU cache with TTL and conversation hints."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []
        self._conversation_hints: dict[
            str, int
        ] = {}  # Track access count per conversation

    def get(self, key: str) -> Any | None:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            # Expired, remove from cache
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        # Update conversation hint
        self._conversation_hints[key] = self._conversation_hints.get(key, 0) + 1

        return value

    def put(self, key: str, value: Any) -> None:
        """Store value in cache with LRU eviction."""
        current_time = time.time()

        # If cache is full and key is new, evict LRU item
        if len(self._cache) >= self.max_size and key not in self._cache:
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]
            if lru_key in self._conversation_hints:
                del self._conversation_hints[lru_key]

        # Store the value
        self._cache[key] = (value, current_time)

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def get_conversation_hints(self) -> dict[str, int]:
        """Get conversation access hints for optimization."""
        return self._conversation_hints.copy()

    def clear_conversation_hints(self) -> None:
        """Clear conversation hints (call at conversation end)."""
        self._conversation_hints.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_count": sum(self._conversation_hints.values()),
            "unique_keys": len(self._conversation_hints),
            "ttl_seconds": self.ttl_seconds,
        }


class MinimalSchema(BaseModel):
    """Minimal schema representation for efficient token usage."""

    required: list[str] = Field(description="Required field names")
    fields: dict[str, str] = Field(description="Field name to type:description mapping")
    examples: dict[str, dict[str, Any]] = Field(description="Usage examples")
    cache_key: str = Field(description="Version-specific cache key")
    cache_hint: str = Field(description="Conversation caching hint")


class SchemaDiscovery:
    """Discovers and caches minimal schemas for meta-tool operations."""

    def __init__(self, cache_size: int = 256, cache_ttl: int = 3600):
        self.cache = SchemaCache(cache_size, cache_ttl)
        self.schema_dir = Path(__file__).parent / "schemas"
        self._ensure_schema_dir()

    def _ensure_schema_dir(self) -> None:
        """Ensure schema directory structure exists."""
        self.schema_dir.mkdir(exist_ok=True)
        (self.schema_dir / "jira").mkdir(exist_ok=True)
        (self.schema_dir / "confluence").mkdir(exist_ok=True)

    def get_resource_schema(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema:
        """Get minimal schema for a specific resource operation.

        Args:
            service: Target service ("jira" or "confluence")
            resource: Resource type (e.g., "issue", "page", "comment")
            operation: Operation type (e.g., "create", "update", "get")

        Returns:
            MinimalSchema with compact field definitions and examples
        """
        cache_key = f"{service}_{resource}_{operation}_v2"  # v2 for parameter optimization

        # Try cache first
        cached_schema = self.cache.get(cache_key)
        if cached_schema:
            logger.debug(f"Schema cache hit for {cache_key}")
            return cached_schema

        # Generate schema with parameter optimization
        schema = self._generate_optimized_schema(service, resource, operation)
        schema.cache_key = cache_key
        schema.cache_hint = "Valid for this conversation"

        # Cache the result
        self.cache.put(cache_key, schema)
        logger.debug(f"Generated and cached optimized schema for {cache_key}")

        return schema

    def _generate_optimized_schema(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema:
        """Generate schema using parameter optimization for minimal token usage."""
        optimizer = get_parameter_optimizer()
        
        # Get recommended parameters for this operation
        recommended_params = optimizer.get_recommended_parameters(
            service=service,
            resource=resource,
            operation=operation
        )
        
        # Optimize each parameter
        optimized_fields = {}
        required_fields = []
        
        for param_name in recommended_params:
            # Determine if parameter is required
            is_required = self._is_field_required_optimized(param_name, operation)
            
            # Optimize the parameter
            opt_param = optimizer.optimize_parameter(
                param_name=param_name,
                required=is_required
            )
            
            # Create compact field definition
            field_def = opt_param.type_info
            if opt_param.description:
                field_def = f"{opt_param.type_info}:{opt_param.description}"
            if not is_required:
                field_def = f"{field_def}:optional"
                
            optimized_fields[param_name] = field_def
            
            if is_required:
                required_fields.append(param_name)
        
        # Generate optimized examples with context defaults
        examples = self._generate_optimized_examples(
            service, resource, operation, required_fields, optimizer
        )
        
        return MinimalSchema(
            required=required_fields,
            fields=optimized_fields,
            examples=examples,
            cache_key="",  # Will be set by caller
            cache_hint="",  # Will be set by caller
        )

    def _is_field_required_optimized(self, field_name: str, operation: Operation) -> bool:
        """Determine if a field is required using optimized logic."""
        # Key required fields by operation
        required_patterns = {
            "create": ["summary", "title", "project_key", "space_key", "issue_key"],
            "update": ["issue_key", "page_id", "title"],
            "get": ["issue_key", "page_id"],
            "delete": ["issue_key", "page_id"],
            "add": ["issue_key", "page_id", "comment"],
            "search": ["jql", "cql"]
        }
        
        return field_name in required_patterns.get(operation, [])
    
    def _generate_optimized_examples(
        self,
        service: Service,
        resource: str,
        operation: Operation,
        required_fields: list[str],
        optimizer
    ) -> dict[str, dict[str, Any]]:
        """Generate optimized examples with smart defaults."""
        examples = {}
        
        # Create minimal example with only required fields
        minimal = {}
        for field in required_fields:
            param_def = optimizer.get_parameter_definition(field)
            if param_def and "example" in param_def:
                minimal[field] = param_def["example"]
            else:
                minimal[field] = self._get_field_example(field, service)
        
        if minimal:
            examples["minimal"] = minimal
        
        # Create complete example with context defaults
        complete = minimal.copy()
        complete.update(optimizer.apply_context_defaults(
            service=service,
            resource=resource,
            operation=operation,
            parameters=complete
        ))
        
        if len(complete) > len(minimal):
            examples["with_defaults"] = complete
            
        return examples

    def _get_field_example(self, field_name: str, service: Service) -> str:
        """Get example value for a field."""
        examples = {
            "issue_key": "PROJ-123",
            "project_key": "PROJ", 
            "page_id": "123456",
            "title": "Example Page",
            "summary": "Example issue summary",
            "jql": "project = PROJ AND status = Open",
            "cql": "space = SPACE AND type = page",
            "comment": "Example comment",
            "space_key": "SPACE"
        }
        return examples.get(field_name, f"<{field_name}_value>")

    def _generate_schema(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema:
        """Generate minimal schema from models and predefined schemas."""
        # First try to load from JSON schema files
        json_schema = self._load_json_schema(service, resource, operation)
        if json_schema:
            return json_schema

        # Fall back to dynamic generation from Pydantic models
        return self._generate_from_model(service, resource, operation)

    def _load_json_schema(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema | None:
        """Load schema from JSON file if available."""
        schema_file = self.schema_dir / service / f"{resource}.json"
        if not schema_file.exists():
            return None

        try:
            with open(schema_file) as f:
                schemas = json.load(f)

            operation_schema = schemas.get(operation)
            if not operation_schema:
                return None

            return MinimalSchema(**operation_schema)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load schema from {schema_file}: {e}")
            return None

    def _generate_from_model(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema:
        """Generate schema dynamically from Pydantic models."""
        # Map resource types to model classes
        model_map = {
            ("jira", "issue"): JiraIssue,
            ("confluence", "page"): ConfluencePage,
        }

        model_class = model_map.get((service, resource))
        if not model_class:
            return self._get_fallback_schema(service, resource, operation)

        return self._extract_schema_from_model(model_class, operation)

    def _extract_schema_from_model(
        self,
        model_class: type[BaseModel],
        operation: Operation,
    ) -> MinimalSchema:
        """Extract minimal schema from Pydantic model."""
        model_fields = model_class.model_fields

        # Determine required fields based on operation
        required_fields = []
        field_definitions = {}

        for field_name, field_info in model_fields.items():
            # Skip internal fields
            if field_name.startswith("_"):
                continue

            # Determine if field is required for this operation
            is_required = self._is_field_required(field_name, operation)

            # Get field type and description
            field_type = self._get_field_type(field_info)
            description = field_info.description or "No description"

            # Create compact field definition
            field_def = f"{field_type}:{description[:50]}..."
            if not is_required:
                field_def = f"{field_type}:optional:{description[:40]}..."

            field_definitions[field_name] = field_def

            if is_required:
                required_fields.append(field_name)

        # Generate examples
        examples = self._generate_examples(
            operation, required_fields, field_definitions
        )

        return MinimalSchema(
            required=required_fields,
            fields=field_definitions,
            examples=examples,
            cache_key="",  # Will be set by caller
            cache_hint="",  # Will be set by caller
        )

    def _is_field_required(self, field_name: str, operation: Operation) -> bool:
        """Determine if a field is required for a specific operation."""
        # Common required fields by operation
        required_by_operation = {
            "create": {
                # Jira issue creation
                "project",
                "project_key",
                "summary",
                "issue_type",
                "issuetype",
                # Confluence page creation
                "space",
                "space_id",
                "title",
                "body",
                "content",
            },
            "update": {
                # Generally fewer required fields for updates
                "id",
                "key",
                "title",
                "body",
            },
            "add": {
                # For comments, worklogs, etc.
                "body",
                "content",
                "time_spent",
            },
        }

        return field_name in required_by_operation.get(operation, set())

    def _get_field_type(self, field_info: Any) -> str:
        """Extract simplified field type."""
        # This is a simplified type extraction
        # In a real implementation, you'd want more sophisticated type analysis
        if hasattr(field_info, "annotation"):
            annotation = field_info.annotation
            if annotation == str:
                return "string"
            elif annotation == int:
                return "integer"
            elif annotation == bool:
                return "boolean"
            elif hasattr(annotation, "__origin__"):
                if annotation.__origin__ == list:
                    return "array"
                elif annotation.__origin__ == dict:
                    return "object"

        return "any"

    def _generate_examples(
        self,
        operation: Operation,
        required_fields: list[str],
        field_definitions: dict[str, str],
    ) -> dict[str, dict[str, Any]]:
        """Generate usage examples for the schema."""
        examples = {}

        if operation == "create":
            # Minimal example with just required fields
            minimal = {}
            for field in required_fields:
                if "project" in field.lower():
                    minimal[field] = "PROJ"
                elif field == "summary":
                    minimal[field] = "Brief description"
                elif "type" in field.lower():
                    minimal[field] = "Task"
                elif field == "title":
                    minimal[field] = "Page title"
                elif field in ["body", "content"]:
                    minimal[field] = "Content here"
                elif "space" in field.lower():
                    minimal[field] = "SPACE"
                else:
                    minimal[field] = "value"

            examples["minimal"] = minimal

            # Complete example with common optional fields
            complete = minimal.copy()
            complete.update(
                {
                    "description": "Detailed description",
                    "assignee": "user@example.com",
                    "priority": "Medium",
                    "labels": ["tag1", "tag2"],
                }
            )
            examples["complete"] = complete

        elif operation == "update":
            examples["minimal"] = {"title": "Updated title"}
            examples["complete"] = {
                "title": "Updated title",
                "body": "Updated content",
                "assignee": "user@example.com",
            }

        return examples

    def _get_fallback_schema(
        self,
        service: Service,
        resource: str,
        operation: Operation,
    ) -> MinimalSchema:
        """Provide fallback schema when model is not available."""
        # Basic fallback schemas
        fallback_schemas = {
            ("jira", "comment", "add"): MinimalSchema(
                required=["body"],
                fields={"body": "string:Comment text content"},
                examples={
                    "minimal": {"body": "This is a comment"},
                    "complete": {"body": "This is a detailed comment with context"},
                },
                cache_key="",
                cache_hint="",
            ),
            ("jira", "worklog", "add"): MinimalSchema(
                required=["time_spent"],
                fields={
                    "time_spent": "string:Time spent (e.g., '2h 30m', '4d')",
                    "comment": "string:optional:Work description",
                },
                examples={
                    "minimal": {"time_spent": "2h"},
                    "complete": {"time_spent": "2h 30m", "comment": "Fixed bug #123"},
                },
                cache_key="",
                cache_hint="",
            ),
        }

        key = (service, resource, operation)
        if key in fallback_schemas:
            return fallback_schemas[key]

        # Ultimate fallback
        return MinimalSchema(
            required=[],
            fields={"data": "object:Resource-specific data"},
            examples={
                "minimal": {"data": "value"},
                "complete": {"data": "value", "options": {}},
            },
            cache_key="",
            cache_hint="",
        )

    @lru_cache(maxsize=128)
    def get_capabilities(self, service: Service | None = None) -> dict[str, Any]:
        """Get comprehensive capabilities overview in minimal tokens."""
        if service:
            return self._get_service_capabilities(service)

        return {
            "jira": self._get_service_capabilities("jira"),
            "confluence": self._get_service_capabilities("confluence"),
        }

    def _get_service_capabilities(self, service: Service) -> dict[str, Any]:
        """Get capabilities for a specific service."""
        capabilities = {
            "jira": {
                "resources": [
                    "issue",
                    "comment",
                    "worklog",
                    "attachment",
                    "link",
                    "sprint",
                    "version",
                ],
                "operations": {
                    "issue": {
                        "create": "Create new issue with summary, description, type",
                        "update": "Modify existing issue fields",
                        "get": "Retrieve issue details by key",
                        "delete": "Delete issue permanently",
                    },
                    "comment": {
                        "add": "Add comment to issue",
                        "get": "Retrieve comment details",
                        "update": "Edit existing comment",
                        "delete": "Remove comment",
                    },
                    "worklog": {
                        "add": "Log work time on issue",
                        "get": "Retrieve worklog entries",
                        "update": "Edit worklog entry",
                        "delete": "Remove worklog entry",
                    },
                },
                "common_patterns": [
                    "Create issue: resource_manager(service='jira', resource='issue', operation='create', data={...})",
                    "Add comment: resource_manager(service='jira', resource='comment', operation='add', identifier='ISSUE-123', data={'body': 'text'})",
                ],
            },
            "confluence": {
                "resources": ["page", "comment", "label", "space"],
                "operations": {
                    "page": {
                        "create": "Create new page with title, body, space",
                        "update": "Update page content and title",
                        "get": "Retrieve page by ID",
                        "delete": "Delete page permanently",
                    },
                    "comment": {
                        "add": "Add comment to page",
                        "get": "Retrieve comment details",
                        "update": "Edit existing comment",
                        "delete": "Remove comment",
                    },
                },
                "common_patterns": [
                    "Create page: resource_manager(service='confluence', resource='page', operation='create', data={'space_id': 'SPACE', 'title': 'Title', 'body': 'Content'})",
                ],
            },
        }

        return capabilities.get(service, {})

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for monitoring."""
        return self.cache.stats()

    def clear_conversation_hints(self) -> None:
        """Clear conversation hints (call at conversation end)."""
        self.cache.clear_conversation_hints()


# Global instance for easy access
schema_discovery = SchemaDiscovery()
