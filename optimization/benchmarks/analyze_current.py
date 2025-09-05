"""Analyzer for current MCP tool registrations.

This module scans the existing codebase to find all @mcp.tool decorated functions,
extract their complete definitions, and analyze their token usage.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .token_counter import TokenCounter, TokenBreakdown

logger = logging.getLogger(__name__)


@dataclass 
class ToolInfo:
    """Information about a single MCP tool."""
    
    name: str
    module_path: str
    relative_path: str
    service: str  # 'jira' or 'confluence'
    tags: set[str]
    function_def: str
    tokens: TokenBreakdown
    decorator_name: str  # e.g., 'jira_mcp', 'pages_mcp'
    line_number: int


@dataclass
class ModuleAnalysis:
    """Analysis results for a single module."""
    
    module_path: str
    relative_path: str
    service: str
    tool_count: int
    total_tokens: int
    tools: list[ToolInfo]


@dataclass
class CurrentToolsAnalysis:
    """Complete analysis of current MCP tools."""
    
    total_tools: int
    total_tokens: int
    by_service: dict[str, dict[str, Any]]
    by_module: dict[str, ModuleAnalysis]
    tools: list[ToolInfo]
    encoding_name: str


class CurrentToolsAnalyzer:
    """Analyzer for existing MCP tool registrations."""
    
    def __init__(self, base_path: str | Path | None = None):
        """Initialize the analyzer.
        
        Args:
            base_path: Base path to the project. If None, assumes current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.servers_path = self.base_path / "src" / "mcp_atlassian" / "servers"
        self.token_counter = TokenCounter()
        
    def analyze(self) -> CurrentToolsAnalysis:
        """Analyze all current MCP tools.
        
        Returns:
            Complete analysis of current tool registrations
        """
        logger.info("Starting analysis of current MCP tools...")
        logger.info(f"Scanning directory: {self.servers_path}")
        
        tools: list[ToolInfo] = []
        modules: dict[str, ModuleAnalysis] = {}
        
        # Scan all Python files in servers directory
        py_files = list(self.servers_path.rglob("*.py"))
        logger.info(f"Found {len(py_files)} Python files to analyze")
        
        for py_file in py_files:
            if py_file.name.startswith("__"):
                continue
                
            logger.debug(f"Analyzing file: {py_file}")
            try:
                module_tools = self._analyze_module(py_file)
                logger.info(f"Found {len(module_tools)} tools in {py_file.name}")
                tools.extend(module_tools)
                
                if module_tools:
                    relative_path = str(py_file.relative_to(self.base_path))
                    service = self._determine_service(relative_path)
                    
                    modules[relative_path] = ModuleAnalysis(
                        module_path=str(py_file),
                        relative_path=relative_path,
                        service=service,
                        tool_count=len(module_tools),
                        total_tokens=sum(tool.tokens.total for tool in module_tools),
                        tools=module_tools
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")
                continue
        
        # Aggregate results
        total_tokens = sum(tool.tokens.total for tool in tools)
        by_service = self._aggregate_by_service(tools)
        
        logger.info(f"Analysis complete: {len(tools)} tools, {total_tokens} tokens")
        
        return CurrentToolsAnalysis(
            total_tools=len(tools),
            total_tokens=total_tokens,
            by_service=by_service,
            by_module=modules,
            tools=tools,
            encoding_name=self.token_counter.encoding_name
        )
    
    def _analyze_module(self, py_file: Path) -> list[ToolInfo]:
        """Analyze a single Python module for MCP tools.
        
        Args:
            py_file: Path to the Python file
            
        Returns:
            List of ToolInfo objects found in the module
        """
        try:
            with py_file.open("r", encoding="utf-8") as f:
                content = f.read()
                
            tree = ast.parse(content)
            tools = []
            
            functions_found = 0
            tools_found = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions_found += 1
                    tool_info = self._extract_tool_info(node, content, py_file)
                    if tool_info:
                        tools_found += 1
                        tools.append(tool_info)
            
            if functions_found > 0:
                logger.debug(f"In {py_file.name}: {functions_found} functions found, {tools_found} tools found")
            
            return tools
            
        except Exception as e:
            logger.error(f"Error parsing {py_file}: {e}")
            return []
    
    def _extract_tool_info(
        self, 
        func_node: ast.FunctionDef | ast.AsyncFunctionDef, 
        module_content: str, 
        py_file: Path
    ) -> ToolInfo | None:
        """Extract tool information from a function node.
        
        Args:
            func_node: AST function definition node
            module_content: Complete module source code
            py_file: Path to the Python file
            
        Returns:
            ToolInfo if this is an MCP tool, None otherwise
        """
        # Check if this function has an MCP tool decorator
        mcp_decorator = None
        decorator_name = None
        tags = set()
        
        # Debug: log decorators found
        if func_node.decorator_list:
            logger.debug(f"Function {func_node.name} has {len(func_node.decorator_list)} decorators")
        
        for decorator in func_node.decorator_list:
            # Handle @xxx_mcp.tool() decorator calls  
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    logger.debug(f"Found call decorator: {decorator.func.value.id if hasattr(decorator.func.value, 'id') else 'unknown'}.{decorator.func.attr}")
                    if (decorator.func.attr == "tool" and 
                        hasattr(decorator.func.value, "id")):
                        decorator_name = decorator.func.value.id
                        mcp_decorator = decorator
                        logger.debug(f"Matched MCP tool decorator: {decorator_name}.tool")
                        
                        # Extract tags from decorator arguments
                        for keyword in decorator.keywords:
                            if keyword.arg == "tags" and isinstance(keyword.value, (ast.Set, ast.List)):
                                for elt in keyword.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        tags.add(elt.value)
                        break
            # Handle @xxx_mcp.tool (without parentheses) - less common but possible
            elif isinstance(decorator, ast.Attribute):
                logger.debug(f"Found attribute decorator: {decorator.value.id if hasattr(decorator.value, 'id') else 'unknown'}.{decorator.attr}")
                if decorator.attr == "tool" and hasattr(decorator.value, "id"):
                    decorator_name = decorator.value.id
                    mcp_decorator = decorator
                    logger.debug(f"Matched MCP tool decorator: {decorator_name}.tool")
                    break
        
        if not mcp_decorator or not decorator_name:
            return None
        
        # Extract the complete function definition
        func_def = self._extract_function_source(func_node, module_content)
        if not func_def:
            return None
        
        # Count tokens
        tokens = self.token_counter.count_tool_definition_tokens(func_def)
        
        # Determine service and relative path
        relative_path = str(py_file.relative_to(self.base_path))
        service = self._determine_service(relative_path)
        
        return ToolInfo(
            name=func_node.name,
            module_path=str(py_file),
            relative_path=relative_path,
            service=service,
            tags=tags,
            function_def=func_def,
            tokens=tokens,
            decorator_name=decorator_name,
            line_number=func_node.lineno
        )
    
    def _extract_function_source(self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, module_content: str) -> str:
        """Extract the complete source code for a function including decorators.
        
        Args:
            func_node: AST function definition node
            module_content: Complete module source code
            
        Returns:
            Complete function source code or empty string if extraction fails
        """
        try:
            lines = module_content.splitlines()
            
            # Find the start line (including decorators)
            start_line = func_node.lineno - 1
            if func_node.decorator_list:
                start_line = func_node.decorator_list[0].lineno - 1
            
            # Find the end line (this is tricky with AST)
            # We'll use a heuristic based on the next function or class
            end_line = len(lines)
            
            # Look for the next function/class definition at the same indentation level
            func_indent = len(lines[func_node.lineno - 1]) - len(lines[func_node.lineno - 1].lstrip())
            
            for i in range(func_node.lineno, len(lines)):
                line = lines[i]
                if line.strip() and not line.startswith(' ' * (func_indent + 1)):
                    # Found a line at the same or lesser indentation level
                    if line.strip().startswith(('def ', 'class ', '@')) and not line.startswith(' ' * (func_indent + 1)):
                        end_line = i
                        break
            
            # Extract the function source
            func_lines = lines[start_line:end_line]
            return "\n".join(func_lines)
            
        except Exception as e:
            logger.error(f"Failed to extract function source: {e}")
            return ""
    
    def _determine_service(self, relative_path: str) -> str:
        """Determine the service (jira/confluence) from the relative path.
        
        Args:
            relative_path: Relative path to the module
            
        Returns:
            'jira', 'confluence', or 'unknown'
        """
        if "confluence" in relative_path:
            return "confluence"
        elif "jira" in relative_path:
            return "jira"
        else:
            return "unknown"
    
    def _aggregate_by_service(self, tools: list[ToolInfo]) -> dict[str, dict[str, Any]]:
        """Aggregate tool statistics by service.
        
        Args:
            tools: List of all tool information
            
        Returns:
            Dictionary with service-level aggregations
        """
        by_service: dict[str, dict[str, Any]] = {}
        
        for tool in tools:
            if tool.service not in by_service:
                by_service[tool.service] = {
                    "tool_count": 0,
                    "total_tokens": 0,
                    "tools": [],
                    "avg_tokens_per_tool": 0.0,
                    "token_breakdown": {
                        "signature": 0,
                        "docstring": 0, 
                        "parameters": 0,
                        "decorators": 0
                    }
                }
            
            service_data = by_service[tool.service]
            service_data["tool_count"] += 1
            service_data["total_tokens"] += tool.tokens.total
            service_data["tools"].append({
                "name": tool.name,
                "module": tool.relative_path,
                "tokens": tool.tokens.total,
                "tags": list(tool.tags)
            })
            
            # Update token breakdown
            breakdown = service_data["token_breakdown"]
            breakdown["signature"] += tool.tokens.signature
            breakdown["docstring"] += tool.tokens.docstring
            breakdown["parameters"] += tool.tokens.parameters
            breakdown["decorators"] += tool.tokens.decorators
        
        # Calculate averages
        for service_data in by_service.values():
            if service_data["tool_count"] > 0:
                service_data["avg_tokens_per_tool"] = (
                    service_data["total_tokens"] / service_data["tool_count"]
                )
        
        return by_service