"""Parameter optimization system for MCP Atlassian meta-tools.

This module provides intelligent parameter handling to reduce token usage by:
1. Shared parameter definitions through common registry
2. Context-aware defaults based on operation types
3. Parameter validation and transformation
4. Integration with existing schema discovery system
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Type definitions
Service = Literal["jira", "confluence"]
Operation = Literal["get", "create", "update", "delete", "add", "search"]
Resource = str


class ParameterDefinition(TypedDict):
    """Type definition for parameter metadata."""
    type: str | list[str]
    description: str
    pattern: str | None
    minimum: int | None
    maximum: int | None
    default: Any | None
    example: str | None
    usage_count: int


class OptimizedParameter(BaseModel):
    """Optimized parameter with reduced description and smart defaults."""
    name: str
    type_info: str
    description: str
    default: Any | None = None
    required: bool = False
    validation: dict[str, Any] | None = None


class ParameterOptimizer:
    """Core parameter optimization engine."""

    def __init__(self) -> None:
        """Initialize parameter optimizer with common registry."""
        self._registry: dict[str, ParameterDefinition] | None = None
        self._context_defaults: dict[str, dict[str, Any]] | None = None
        self._combinations: dict[str, list[str]] | None = None

    @property
    def registry(self) -> dict[str, ParameterDefinition]:
        """Lazy-loaded parameter registry."""
        if self._registry is None:
            self._load_registry()
        return self._registry

    @property
    def context_defaults(self) -> dict[str, dict[str, Any]]:
        """Lazy-loaded context defaults."""
        if self._context_defaults is None:
            self._load_registry()
        return self._context_defaults

    @property
    def combinations(self) -> dict[str, list[str]]:
        """Lazy-loaded parameter combinations."""
        if self._combinations is None:
            self._load_registry()
        return self._combinations

    def _load_registry(self) -> None:
        """Load common parameters registry from JSON file."""
        registry_path = Path(__file__).parent / "common_params.json"
        
        try:
            with registry_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                
            self._registry = data["common_parameters"]
            self._context_defaults = data["context_defaults"]
            self._combinations = data["parameter_combinations"]
            
            logger.debug(
                f"Loaded parameter registry: {len(self._registry)} common parameters, "
                f"{len(self._context_defaults)} context patterns, "
                f"{len(self._combinations)} combinations"
            )
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load parameter registry: {e}")
            # Fallback to empty registries
            self._registry = {}
            self._context_defaults = {}
            self._combinations = {}

    def get_parameter_definition(self, param_name: str) -> ParameterDefinition | None:
        """Get parameter definition from registry.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Parameter definition or None if not found
        """
        return self.registry.get(param_name)

    def optimize_parameter(
        self,
        param_name: str,
        original_description: str | None = None,
        param_type: str = "string",
        required: bool = False
    ) -> OptimizedParameter:
        """Optimize a single parameter using registry definitions.
        
        Args:
            param_name: Parameter name
            original_description: Original verbose description (for fallback)
            param_type: Parameter type
            required: Whether parameter is required
            
        Returns:
            Optimized parameter with reduced description
        """
        # Check if parameter exists in registry
        registry_def = self.get_parameter_definition(param_name)
        
        if registry_def:
            # Use optimized definition from registry
            return OptimizedParameter(
                name=param_name,
                type_info=self._format_type(registry_def["type"]),
                description=registry_def["description"],
                default=registry_def.get("default"),
                required=required,
                validation=self._extract_validation(registry_def)
            )
        else:
            # Fallback: create minimal description from original
            optimized_desc = self._minimize_description(
                original_description or f"{param_name.replace('_', ' ').title()}"
            )
            
            return OptimizedParameter(
                name=param_name,
                type_info=param_type,
                description=optimized_desc,
                required=required
            )

    def apply_context_defaults(
        self,
        service: Service,
        resource: Resource,
        operation: Operation,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply intelligent defaults based on operation context.
        
        Args:
            service: Target service (jira/confluence)
            resource: Resource type (issue, page, etc.)
            operation: Operation type (get, create, etc.)
            parameters: Current parameter values
            
        Returns:
            Parameters with context-aware defaults applied
        """
        optimized_params = parameters.copy()
        
        # Apply operation-specific defaults
        operation_key = f"{operation}_operations"
        if operation_key in self.context_defaults:
            defaults = self.context_defaults[operation_key]
            for key, default_value in defaults.items():
                if key not in optimized_params:
                    optimized_params[key] = default_value
                    
        # Apply service+resource specific defaults
        resource_key = f"{service}_{resource}_operations"
        if resource_key in self.combinations:
            # Set reasonable defaults for this combination
            if operation == "search":
                optimized_params.setdefault("limit", 25)
                optimized_params.setdefault("start_at", 0)
                if service == "jira":
                    optimized_params.setdefault("fields", "summary,status,assignee")
            elif operation == "get" and service == "jira":
                optimized_params.setdefault("expand", "changelog,comments")
                optimized_params.setdefault("comment_limit", 10)
            elif operation in ["create", "update"]:
                optimized_params.setdefault("dry_run", False)
                
        logger.debug(
            f"Applied context defaults for {service}.{resource}.{operation}: "
            f"{len(optimized_params) - len(parameters)} defaults added"
        )
        
        return optimized_params

    def get_recommended_parameters(
        self,
        service: Service,
        resource: Resource,
        operation: Operation
    ) -> list[str]:
        """Get recommended parameters for a specific operation.
        
        Args:
            service: Target service 
            resource: Resource type
            operation: Operation type
            
        Returns:
            List of recommended parameter names
        """
        # Check for specific resource combination
        resource_key = f"{service}_{resource}_operations"
        if resource_key in self.combinations:
            base_params = self.combinations[resource_key].copy()
        else:
            # Use generic operation parameters
            base_params = []
            
        # Add operation-specific parameters
        if operation == "search":
            base_params.extend(["limit", "start_at"])
            if service == "jira":
                base_params.append("jql")
            elif service == "confluence":
                base_params.append("cql")
        elif operation in ["create", "update"]:
            base_params.extend(["dry_run"])
        elif operation == "get":
            base_params.extend(["fields", "expand"])
            
        # Remove duplicates while preserving order
        return list(dict.fromkeys(base_params))

    def get_parameter_schema_ref(self, param_name: str) -> dict[str, str] | None:
        """Get JSON Schema $ref for a common parameter.
        
        Args:
            param_name: Parameter name
            
        Returns:
            Schema reference dict or None if not a common parameter
        """
        if param_name in self.registry:
            return {"$ref": f"#/$defs/common_parameters/{param_name}"}
        return None

    def calculate_token_savings(self, original_params: list[str]) -> dict[str, Any]:
        """Calculate estimated token savings from optimization.
        
        Args:
            original_params: List of parameter names before optimization
            
        Returns:
            Token savings metrics
        """
        original_tokens = 0
        optimized_tokens = 0
        common_params = 0
        
        for param in original_params:
            # Estimate original token cost (verbose description)
            original_tokens += 15  # Average verbose description length
            
            if param in self.registry:
                # Common parameter - minimal tokens
                optimized_tokens += 5  # Short description
                common_params += 1
            else:
                # Non-common parameter - moderate savings
                optimized_tokens += 8  # Minimized description
                
        return {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "token_savings": original_tokens - optimized_tokens,
            "savings_percentage": (
                (original_tokens - optimized_tokens) / original_tokens * 100
                if original_tokens > 0 else 0
            ),
            "common_parameters": common_params,
            "total_parameters": len(original_params)
        }

    @staticmethod
    def _format_type(type_info: str | list[str]) -> str:
        """Format type information for display."""
        if isinstance(type_info, list):
            return " | ".join(type_info)
        return type_info

    @staticmethod
    def _extract_validation(registry_def: ParameterDefinition) -> dict[str, Any] | None:
        """Extract validation rules from registry definition."""
        validation = {}
        
        if "pattern" in registry_def and registry_def["pattern"]:
            validation["pattern"] = registry_def["pattern"]
        if "minimum" in registry_def and registry_def["minimum"] is not None:
            validation["minimum"] = registry_def["minimum"]  
        if "maximum" in registry_def and registry_def["maximum"] is not None:
            validation["maximum"] = registry_def["maximum"]
            
        return validation if validation else None

    @staticmethod
    def _minimize_description(original: str) -> str:
        """Minimize a verbose parameter description.
        
        Args:
            original: Original verbose description
            
        Returns:
            Minimized description
        """
        # Remove examples in parentheses
        desc = original.split("(")[0].strip()
        
        # Remove common prefixes
        prefixes = ["(Optional) ", "Optional ", "The ", "A "]
        for prefix in prefixes:
            if desc.startswith(prefix):
                desc = desc[len(prefix):]
                break
                
        # Capitalize first letter
        if desc and not desc[0].isupper():
            desc = desc[0].upper() + desc[1:]
            
        # Remove trailing punctuation except periods
        desc = desc.rstrip(",;:")
        
        return desc


# Global optimizer instance for reuse
_optimizer_instance: ParameterOptimizer | None = None


def get_parameter_optimizer() -> ParameterOptimizer:
    """Get global parameter optimizer instance.
    
    Returns:
        Shared ParameterOptimizer instance
    """
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = ParameterOptimizer()
    return _optimizer_instance


@lru_cache(maxsize=128)
def optimize_tool_parameters(
    service: Service,
    resource: Resource, 
    operation: Operation,
    parameter_names: tuple[str, ...]
) -> list[OptimizedParameter]:
    """Cached parameter optimization for tools.
    
    Args:
        service: Target service
        resource: Resource type  
        operation: Operation type
        parameter_names: Parameter names as tuple (for caching)
        
    Returns:
        List of optimized parameters
    """
    optimizer = get_parameter_optimizer()
    
    optimized = []
    for param_name in parameter_names:
        # Determine if parameter is required based on common patterns
        required = param_name in ["issue_key", "project_key", "page_id", "summary", "title"]
        
        opt_param = optimizer.optimize_parameter(
            param_name=param_name,
            required=required
        )
        optimized.append(opt_param)
        
    logger.debug(
        f"Optimized {len(parameter_names)} parameters for {service}.{resource}.{operation}"
    )
    
    return optimized


# Export key functions and classes
__all__ = [
    "ParameterOptimizer",
    "OptimizedParameter", 
    "get_parameter_optimizer",
    "optimize_tool_parameters"
]