"""Analyzer for meta-tools implementation.

This module analyzes the existing meta-tools in src/mcp_atlassian/meta_tools/
to understand their token usage and compare with the traditional tool approach.
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
class MetaToolInfo:
    """Information about a meta-tool."""
    
    name: str
    module_path: str
    relative_path: str
    class_name: str | None
    method_name: str | None
    function_def: str
    tokens: TokenBreakdown
    tool_type: str  # 'class_method', 'function', 'mcp_tool'
    consolidates: list[str]  # List of traditional tools this replaces


@dataclass
class MetaToolsAnalysis:
    """Complete analysis of meta-tools implementation."""
    
    total_meta_tools: int
    total_tokens: int
    meta_tools: list[MetaToolInfo]
    traditional_tools_replaced: int
    estimated_token_savings: int
    encoding_name: str
    analysis_summary: dict[str, Any]


class MetaToolsAnalyzer:
    """Analyzer for meta-tools implementation."""
    
    def __init__(self, base_path: str | Path | None = None):
        """Initialize the meta-tools analyzer.
        
        Args:
            base_path: Base path to the project. If None, assumes current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.meta_tools_path = self.base_path / "src" / "mcp_atlassian" / "meta_tools"
        self.token_counter = TokenCounter()
        
    def analyze(self) -> MetaToolsAnalysis:
        """Analyze the meta-tools implementation.
        
        Returns:
            Complete analysis of meta-tools
        """
        logger.info("Starting analysis of meta-tools...")
        
        meta_tools: list[MetaToolInfo] = []
        
        # Analyze all Python files in meta_tools directory
        for py_file in self.meta_tools_path.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.suffix != ".py":
                continue
                
            try:
                file_meta_tools = self._analyze_meta_tools_file(py_file)
                meta_tools.extend(file_meta_tools)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {py_file}: {e}")
                continue
        
        # Calculate totals and generate analysis
        total_tokens = sum(tool.tokens.total for tool in meta_tools)
        traditional_tools_replaced = self._estimate_tools_replaced(meta_tools)
        
        # Generate analysis summary
        analysis_summary = self._generate_analysis_summary(meta_tools)
        
        logger.info(f"Meta-tools analysis complete: {len(meta_tools)} meta-tools, {total_tokens} tokens")
        
        return MetaToolsAnalysis(
            total_meta_tools=len(meta_tools),
            total_tokens=total_tokens,
            meta_tools=meta_tools,
            traditional_tools_replaced=traditional_tools_replaced,
            estimated_token_savings=0,  # Will be calculated by benchmark runner
            encoding_name=self.token_counter.encoding_name,
            analysis_summary=analysis_summary
        )
    
    def _analyze_meta_tools_file(self, py_file: Path) -> list[MetaToolInfo]:
        """Analyze a single meta-tools file.
        
        Args:
            py_file: Path to the Python file
            
        Returns:
            List of MetaToolInfo objects
        """
        try:
            with py_file.open("r", encoding="utf-8") as f:
                content = f.read()
                
            tree = ast.parse(content)
            meta_tools = []
            
            # Look for class definitions (like ResourceManager)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_tools = self._analyze_meta_tool_class(node, content, py_file)
                    meta_tools.extend(class_tools)
                elif isinstance(node, ast.FunctionDef):
                    func_tool = self._analyze_meta_tool_function(node, content, py_file)
                    if func_tool:
                        meta_tools.append(func_tool)
            
            return meta_tools
            
        except Exception as e:
            logger.error(f"Error parsing {py_file}: {e}")
            return []
    
    def _analyze_meta_tool_class(
        self, 
        class_node: ast.ClassDef, 
        content: str, 
        py_file: Path
    ) -> list[MetaToolInfo]:
        """Analyze a class for meta-tool methods.
        
        Args:
            class_node: AST class definition node
            content: Complete file content
            py_file: Path to the Python file
            
        Returns:
            List of MetaToolInfo for significant methods
        """
        meta_tools = []
        
        # For classes like ResourceManager, we want to analyze key methods
        key_methods = [
            'manage_resource',  # Main entry point
            'get_resource_schema',  # Schema discovery
            'handle_crud_operation'  # Core CRUD handler
        ]
        
        for node in class_node.body:
            if (isinstance(node, ast.FunctionDef) and 
                (node.name in key_methods or 
                 node.name.startswith('_') and len(node.name) > 5)):  # Private methods with logic
                
                method_source = self._extract_method_source(node, content, class_node.name)
                if method_source:
                    tokens = self.token_counter.count_function_tokens(method_source)
                    
                    # Determine what this meta-tool replaces
                    consolidates = self._determine_consolidated_tools(class_node.name, node.name)
                    
                    meta_tool = MetaToolInfo(
                        name=f"{class_node.name}.{node.name}",
                        module_path=str(py_file),
                        relative_path=str(py_file.relative_to(self.base_path)),
                        class_name=class_node.name,
                        method_name=node.name,
                        function_def=method_source,
                        tokens=tokens,
                        tool_type="class_method",
                        consolidates=consolidates
                    )
                    
                    meta_tools.append(meta_tool)
        
        return meta_tools
    
    def _analyze_meta_tool_function(
        self,
        func_node: ast.FunctionDef,
        content: str, 
        py_file: Path
    ) -> MetaToolInfo | None:
        """Analyze a standalone function as a meta-tool.
        
        Args:
            func_node: AST function definition node
            content: Complete file content
            py_file: Path to the Python file
            
        Returns:
            MetaToolInfo if this is a significant meta-tool function
        """
        # Look for functions that could be meta-tools
        meta_tool_functions = [
            'schema_discovery',
            'dynamic_resource_handler',
            'unified_crud_handler'
        ]
        
        if func_node.name not in meta_tool_functions:
            return None
        
        func_source = self._extract_function_source_from_ast(func_node, content)
        if not func_source:
            return None
        
        tokens = self.token_counter.count_function_tokens(func_source)
        consolidates = self._determine_consolidated_tools("", func_node.name)
        
        return MetaToolInfo(
            name=func_node.name,
            module_path=str(py_file),
            relative_path=str(py_file.relative_to(self.base_path)),
            class_name=None,
            method_name=None,
            function_def=func_source,
            tokens=tokens,
            tool_type="function",
            consolidates=consolidates
        )
    
    def _extract_method_source(
        self, 
        method_node: ast.FunctionDef, 
        content: str, 
        class_name: str
    ) -> str:
        """Extract the complete source code for a class method.
        
        Args:
            method_node: AST method definition node
            content: Complete file content
            class_name: Name of the containing class
            
        Returns:
            Complete method source code
        """
        try:
            lines = content.splitlines()
            
            # Find the method start line
            start_line = method_node.lineno - 1
            
            # Find decorators if any
            if method_node.decorator_list:
                start_line = method_node.decorator_list[0].lineno - 1
            
            # Find the end line by looking for the next method/function at the same level
            method_indent = None
            for i in range(method_node.lineno - 1, len(lines)):
                line = lines[i]
                if line.strip().startswith('def '):
                    method_indent = len(line) - len(line.lstrip())
                    break
            
            if method_indent is None:
                return ""
            
            end_line = len(lines)
            for i in range(method_node.lineno, len(lines)):
                line = lines[i]
                if (line.strip() and 
                    not line.startswith(' ' * (method_indent + 1)) and
                    (line.strip().startswith('def ') or 
                     line.strip().startswith('class ') or
                     line.strip().startswith('@'))):
                    end_line = i
                    break
            
            method_lines = lines[start_line:end_line]
            return "\n".join(method_lines)
            
        except Exception as e:
            logger.error(f"Failed to extract method source: {e}")
            return ""
    
    def _extract_function_source_from_ast(self, func_node: ast.FunctionDef, content: str) -> str:
        """Extract function source using AST information.
        
        Args:
            func_node: AST function definition node
            content: Complete file content
            
        Returns:
            Complete function source code
        """
        try:
            lines = content.splitlines()
            
            start_line = func_node.lineno - 1
            if func_node.decorator_list:
                start_line = func_node.decorator_list[0].lineno - 1
            
            # Simple heuristic for end line
            end_line = len(lines)
            if hasattr(func_node, 'end_lineno') and func_node.end_lineno:
                end_line = func_node.end_lineno
            else:
                # Look for next function/class definition
                func_indent = len(lines[func_node.lineno - 1]) - len(lines[func_node.lineno - 1].lstrip())
                for i in range(func_node.lineno, len(lines)):
                    line = lines[i]
                    if (line.strip() and 
                        not line.startswith(' ' * (func_indent + 1)) and
                        (line.strip().startswith(('def ', 'class ', '@')))):
                        end_line = i
                        break
            
            func_lines = lines[start_line:end_line]
            return "\n".join(func_lines)
            
        except Exception as e:
            logger.error(f"Failed to extract function source: {e}")
            return ""
    
    def _determine_consolidated_tools(self, class_name: str, method_name: str) -> list[str]:
        """Determine which traditional tools this meta-tool consolidates.
        
        Args:
            class_name: Name of the class (if applicable)
            method_name: Name of the method/function
            
        Returns:
            List of traditional tool names that this meta-tool replaces
        """
        # Based on the ResourceManager design, map meta-tools to consolidated tools
        consolidation_map = {
            "ResourceManager.manage_resource": [
                "get_issue", "create_issue", "update_issue", "delete_issue",
                "get_page", "create_page", "update_page", "delete_page",
                "add_comment", "update_comment", "delete_comment",
                "add_worklog", "update_worklog", "delete_worklog"
            ],
            "ResourceManager.get_resource_schema": [
                "search_fields", "get_transitions", "get_link_types"
            ],
            "schema_discovery": [
                "search_fields", "get_issue", "get_page"
            ]
        }
        
        key = f"{class_name}.{method_name}" if class_name else method_name
        return consolidation_map.get(key, [])
    
    def _estimate_tools_replaced(self, meta_tools: list[MetaToolInfo]) -> int:
        """Estimate how many traditional tools are replaced by meta-tools.
        
        Args:
            meta_tools: List of meta-tools
            
        Returns:
            Estimated number of traditional tools replaced
        """
        all_consolidated = set()
        for meta_tool in meta_tools:
            all_consolidated.update(meta_tool.consolidates)
        
        return len(all_consolidated)
    
    def _generate_analysis_summary(self, meta_tools: list[MetaToolInfo]) -> dict[str, Any]:
        """Generate a summary of the meta-tools analysis.
        
        Args:
            meta_tools: List of analyzed meta-tools
            
        Returns:
            Analysis summary dictionary
        """
        by_type = {}
        by_module = {}
        
        for meta_tool in meta_tools:
            # By type
            if meta_tool.tool_type not in by_type:
                by_type[meta_tool.tool_type] = {
                    "count": 0,
                    "total_tokens": 0,
                    "tools": []
                }
            
            by_type[meta_tool.tool_type]["count"] += 1
            by_type[meta_tool.tool_type]["total_tokens"] += meta_tool.tokens.total
            by_type[meta_tool.tool_type]["tools"].append({
                "name": meta_tool.name,
                "tokens": meta_tool.tokens.total,
                "consolidates_count": len(meta_tool.consolidates)
            })
            
            # By module
            module = meta_tool.relative_path
            if module not in by_module:
                by_module[module] = {
                    "count": 0,
                    "total_tokens": 0,
                    "tools": []
                }
            
            by_module[module]["count"] += 1
            by_module[module]["total_tokens"] += meta_tool.tokens.total
            by_module[module]["tools"].append(meta_tool.name)
        
        return {
            "by_type": by_type,
            "by_module": by_module,
            "consolidation_ratio": sum(len(mt.consolidates) for mt in meta_tools) / len(meta_tools) if meta_tools else 0
        }