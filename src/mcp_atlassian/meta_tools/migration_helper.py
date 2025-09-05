"""Migration helper for smooth transition from legacy tools to meta-tools.

This module provides utilities to translate legacy tool calls to their meta-tool
equivalents, track usage patterns, and provide learning feedback to users during
the transition period.

Reference: optimization/docs/MCP_TOKEN_OPTIMIZATION_PLAN_v2.md section 4.2
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from .errors import MetaToolError
from .resource_manager import ResourceManager
from .schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)


class MigrationResult:
    """Result of a migration helper operation."""

    def __init__(
        self,
        result: str,
        meta_tool_call: Dict[str, Any],
        legacy_tool_name: str,
        migration_guidance: Dict[str, Any],
        execution_time: float,
    ):
        self.result = result
        self.meta_tool_call = meta_tool_call
        self.legacy_tool_name = legacy_tool_name
        self.migration_guidance = migration_guidance
        self.execution_time = execution_time


class UsageAnalytics:
    """Track usage patterns for migration analytics."""

    def __init__(self):
        self.usage_data: Dict[str, Any] = {
            "session_start": datetime.now(timezone.utc).isoformat(),
            "legacy_calls": {},
            "migration_success_rate": 0.0,
            "common_patterns": [],
            "error_patterns": [],
        }

    def track_legacy_call(
        self,
        tool_name: str,
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Track a legacy tool call."""
        if tool_name not in self.usage_data["legacy_calls"]:
            self.usage_data["legacy_calls"][tool_name] = {
                "count": 0,
                "success_count": 0,
                "total_time": 0.0,
                "errors": [],
            }

        call_data = self.usage_data["legacy_calls"][tool_name]
        call_data["count"] += 1
        call_data["total_time"] += execution_time

        if success:
            call_data["success_count"] += 1
        elif error_message:
            call_data["errors"].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": error_message,
                }
            )

        # Update success rate
        total_calls = sum(
            data["count"] for data in self.usage_data["legacy_calls"].values()
        )
        total_success = sum(
            data["success_count"] for data in self.usage_data["legacy_calls"].values()
        )
        self.usage_data["migration_success_rate"] = (
            total_success / total_calls if total_calls > 0 else 0.0
        )

    def get_most_used_tools(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get the most frequently used legacy tools."""
        tool_usage = [
            (tool, data["count"])
            for tool, data in self.usage_data["legacy_calls"].items()
        ]
        return sorted(tool_usage, key=lambda x: x[1], reverse=True)[:limit]

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get a summary of usage analytics."""
        most_used = self.get_most_used_tools(5)
        total_calls = sum(
            data["count"] for data in self.usage_data["legacy_calls"].values()
        )

        return {
            "session_duration": (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(
                    self.usage_data["session_start"].replace("Z", "+00:00")
                )
            ).total_seconds(),
            "total_legacy_calls": total_calls,
            "unique_tools_used": len(self.usage_data["legacy_calls"]),
            "success_rate": self.usage_data["migration_success_rate"],
            "most_used_tools": most_used,
            "avg_execution_time": (
                sum(
                    data["total_time"]
                    for data in self.usage_data["legacy_calls"].values()
                )
                / total_calls
                if total_calls > 0
                else 0.0
            ),
        }


class MigrationHelper:
    """Helper class for migrating from legacy tools to meta-tools."""

    def __init__(self):
        self.resource_manager = ResourceManager()
        self.schema_discovery = SchemaDiscovery()
        self.analytics = UsageAnalytics()
        self._mappings: Optional[Dict[str, Any]] = None
        self._mappings_loaded = False

    def _load_mappings(self) -> Dict[str, Any]:
        """Load legacy tool mappings from JSON configuration."""
        if self._mappings_loaded:
            return self._mappings or {}

        mappings_path = (
            Path(__file__).parent.parent.parent.parent
            / "optimization"
            / "migration"
            / "legacy_mappings.json"
        )

        try:
            if mappings_path.exists():
                with open(mappings_path, "r", encoding="utf-8") as f:
                    self._mappings = json.load(f)
                logger.debug(f"Loaded legacy mappings from {mappings_path}")
            else:
                logger.warning(
                    f"Legacy mappings file not found at {mappings_path}, using empty mappings"
                )
                self._mappings = {"jira": {}, "confluence": {}}
        except Exception as e:
            logger.error(f"Failed to load legacy mappings: {e}", exc_info=True)
            self._mappings = {"jira": {}, "confluence": {}}

        self._mappings_loaded = True
        return self._mappings or {}

    def _get_service_from_tool_name(self, tool_name: str) -> str:
        """Determine service (jira/confluence) from tool name patterns."""
        # Jira-specific patterns
        jira_patterns = [
            "issue",
            "project",
            "sprint",
            "epic",
            "board",
            "worklog",
            "transition",
            "version",
            "component",
            "link",
            "attachment",
            "comment",
            "jira",
            "agile",
            "changelog",
        ]

        # Confluence-specific patterns
        confluence_patterns = ["page", "space", "confluence", "content", "label"]

        tool_lower = tool_name.lower()

        for pattern in jira_patterns:
            if pattern in tool_lower:
                return "jira"

        for pattern in confluence_patterns:
            if pattern in tool_lower:
                return "confluence"

        # Default to jira for unknown patterns (most tools are Jira)
        logger.warning(
            f"Could not determine service for tool '{tool_name}', defaulting to jira"
        )
        return "jira"

    def _transform_parameters(
        self, legacy_params: Dict[str, Any], mapping_config: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Transform legacy parameters to meta-tool format.

        Returns:
            Tuple of (resource_manager_params, additional_options)
        """
        param_mapping = mapping_config.get("parameter_mapping", {})
        resource_params = {}
        options = {}

        # Handle direct parameter mappings
        for legacy_param, meta_param in param_mapping.items():
            if legacy_param in legacy_params:
                if isinstance(meta_param, dict):
                    # Complex mapping with transformation
                    if "target" in meta_param:
                        if meta_param["target"] == "data":
                            if "data" not in resource_params:
                                resource_params["data"] = {}
                            resource_params["data"][
                                meta_param.get("field", legacy_param)
                            ] = legacy_params[legacy_param]
                        elif meta_param["target"] == "options":
                            options[meta_param.get("field", legacy_param)] = (
                                legacy_params[legacy_param]
                            )
                        else:
                            resource_params[meta_param["target"]] = legacy_params[
                                legacy_param
                            ]
                else:
                    # Simple mapping
                    resource_params[meta_param] = legacy_params[legacy_param]

        # Handle special cases for common legacy parameters
        self._handle_common_parameter_patterns(
            legacy_params, resource_params, options, mapping_config
        )

        return resource_params, options

    def _handle_common_parameter_patterns(
        self,
        legacy_params: Dict[str, Any],
        resource_params: Dict[str, Any],
        options: Dict[str, Any],
        mapping_config: Dict[str, Any],
    ) -> None:
        """Handle common parameter transformation patterns."""

        # Handle additional_fields parameter common in many legacy tools
        if "additional_fields" in legacy_params:
            if "data" not in resource_params:
                resource_params["data"] = {}

            additional = legacy_params["additional_fields"]
            if isinstance(additional, dict):
                resource_params["data"].update(additional)
            elif isinstance(additional, str):
                try:
                    parsed = json.loads(additional)
                    if isinstance(parsed, dict):
                        resource_params["data"].update(parsed)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not parse additional_fields JSON: {additional}"
                    )

        # Handle fields parameter for GET operations
        if "fields" in legacy_params:
            options["fields"] = legacy_params["fields"]

        # Handle expand parameter
        if "expand" in legacy_params:
            options["expand"] = legacy_params["expand"]

        # Handle pagination parameters
        for param in ["start_at", "max_results", "limit"]:
            if param in legacy_params:
                options[param] = legacy_params[param]

        # Handle components parameter (comma-separated string to list)
        if "components" in legacy_params and isinstance(
            legacy_params["components"], str
        ):
            if "data" not in resource_params:
                resource_params["data"] = {}
            components_list = [
                comp.strip()
                for comp in legacy_params["components"].split(",")
                if comp.strip()
            ]
            resource_params["data"]["components"] = [
                {"name": comp} for comp in components_list
            ]

    def translate_legacy_call(
        self, legacy_tool_name: str, legacy_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate a legacy tool call to meta-tool format.

        Args:
            legacy_tool_name: Name of the legacy tool
            legacy_parameters: Parameters for the legacy tool call

        Returns:
            Dictionary containing the translated meta-tool call information
        """
        mappings = self._load_mappings()
        service = self._get_service_from_tool_name(legacy_tool_name)

        # Look up mapping configuration
        service_mappings = mappings.get(service, {})
        mapping_config = service_mappings.get(legacy_tool_name)

        if not mapping_config:
            raise MetaToolError(
                error_code=f"{service.upper()}_MIGRATION_MAPPING_NOT_FOUND",
                message=f"No migration mapping found for legacy tool '{legacy_tool_name}'",
                suggestions=[
                    f"Check if '{legacy_tool_name}' is a valid legacy tool name",
                    "Ensure legacy_mappings.json is properly configured",
                    f"Consider using the {service} meta-tools directly",
                ],
            )

        # Transform parameters
        resource_params, options = self._transform_parameters(
            legacy_parameters, mapping_config
        )

        # Build the meta-tool call
        meta_tool_call = {
            "tool": mapping_config["meta_tool"],
            "parameters": {
                "service": service,
                "resource": mapping_config["resource"],
                "operation": mapping_config["operation"],
                **resource_params,
            },
        }

        if options:
            meta_tool_call["parameters"]["options"] = options

        # Add dry_run if specified in legacy parameters
        if legacy_parameters.get("dry_run", False):
            meta_tool_call["parameters"]["dry_run"] = True

        return meta_tool_call

    def _generate_migration_guidance(
        self,
        legacy_tool_name: str,
        meta_tool_call: Dict[str, Any],
        execution_time: float,
    ) -> Dict[str, Any]:
        """Generate learning feedback for the migration."""

        return {
            "legacy_tool": legacy_tool_name,
            "meta_tool_equivalent": meta_tool_call,
            "learning_note": f"Use the meta-tool call shown above for future operations instead of '{legacy_tool_name}'",
            "benefits": [
                "Reduced token usage in model context",
                "Consistent parameter structure across all operations",
                "Enhanced error handling and dry-run capabilities",
                "Better performance and caching",
            ],
            "execution_time": f"{execution_time:.3f}s",
            "next_steps": [
                "Try using the meta-tool directly next time",
                "Use schema_discovery tool to understand parameter structure",
                "Check the capabilities tool for all available operations",
            ],
        }

    async def migrate_legacy_call(
        self, ctx: Any, legacy_tool_name: str, legacy_parameters: Dict[str, Any]
    ) -> MigrationResult:
        """Execute a legacy tool call via meta-tool translation.

        Args:
            ctx: The FastMCP context
            legacy_tool_name: Name of the legacy tool to execute
            legacy_parameters: Parameters for the legacy tool

        Returns:
            MigrationResult containing the execution result and migration guidance
        """
        start_time = time.time()
        success = False
        error_message = None

        try:
            # Translate the legacy call
            meta_tool_call = self.translate_legacy_call(
                legacy_tool_name, legacy_parameters
            )

            # Execute the meta-tool call
            meta_tool_name = meta_tool_call["tool"]
            meta_params = meta_tool_call["parameters"]

            if meta_tool_name == "resource_manager":
                result = await self.resource_manager.execute_operation(
                    ctx, **meta_params
                )
            elif meta_tool_name == "schema_discovery":
                result = await self.schema_discovery.get_resource_schema(
                    ctx, **meta_params
                )
            else:
                raise MetaToolError(
                    error_code="MIGRATION_UNSUPPORTED_META_TOOL",
                    message=f"Unsupported meta-tool in migration: {meta_tool_name}",
                    suggestions=["Check migration mapping configuration"],
                )

            success = True
            execution_time = time.time() - start_time

            # Generate migration guidance
            migration_guidance = self._generate_migration_guidance(
                legacy_tool_name, meta_tool_call, execution_time
            )

            # Track usage analytics
            self.analytics.track_legacy_call(legacy_tool_name, success, execution_time)

            return MigrationResult(
                result=result,
                meta_tool_call=meta_tool_call,
                legacy_tool_name=legacy_tool_name,
                migration_guidance=migration_guidance,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Track failed migration
            self.analytics.track_legacy_call(
                legacy_tool_name, success, execution_time, error_message
            )

            logger.error(f"Migration failed for {legacy_tool_name}: {e}", exc_info=True)
            raise

    def get_migration_guidance(self, legacy_tool_name: str) -> Dict[str, Any]:
        """Get migration guidance for a specific legacy tool without execution.

        Args:
            legacy_tool_name: Name of the legacy tool

        Returns:
            Dictionary with migration guidance and examples
        """
        mappings = self._load_mappings()
        service = self._get_service_from_tool_name(legacy_tool_name)
        mapping_config = mappings.get(service, {}).get(legacy_tool_name)

        if not mapping_config:
            return {
                "error": f"No migration path found for '{legacy_tool_name}'",
                "available_tools": list(mappings.get(service, {}).keys()),
                "suggestion": f"Use {service} meta-tools directly for new operations",
            }

        return {
            "legacy_tool": legacy_tool_name,
            "meta_tool": mapping_config["meta_tool"],
            "resource": mapping_config["resource"],
            "operation": mapping_config["operation"],
            "parameter_mapping": mapping_config.get("parameter_mapping", {}),
            "examples": mapping_config.get("examples", {}),
            "migration_notes": mapping_config.get("notes", ""),
            "service": service,
        }

    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get current usage analytics."""
        return self.analytics.get_analytics_summary()

    def list_available_migrations(
        self, service: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List all available legacy tools that can be migrated.

        Args:
            service: Optional service filter ("jira" or "confluence")

        Returns:
            Dictionary mapping services to lists of legacy tool names
        """
        mappings = self._load_mappings()

        if service:
            return {service: list(mappings.get(service, {}).keys())}

        return {
            service_name: list(service_mappings.keys())
            for service_name, service_mappings in mappings.items()
        }


# Global instance for use by MCP tools
_migration_helper: Optional[MigrationHelper] = None


def get_migration_helper() -> MigrationHelper:
    """Get the global migration helper instance."""
    global _migration_helper
    if _migration_helper is None:
        _migration_helper = MigrationHelper()
    return _migration_helper
