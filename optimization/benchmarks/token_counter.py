"""Token counting utilities using OpenAI's tiktoken library.

This module provides accurate token counting for MCP tool definitions,
function signatures, docstrings, and parameter annotations using the
cl100k_base encoding that matches OpenAI's GPT models.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

try:
    import tiktoken
except ImportError as e:
    raise ImportError(
        "tiktoken is required for token counting. Install with: pip install tiktoken"
    ) from e


@dataclass
class TokenBreakdown:
    """Detailed breakdown of token counts for different components."""
    
    signature: int
    docstring: int
    parameters: int
    decorators: int
    total: int
    
    @classmethod
    def create(
        cls, 
        signature: int = 0, 
        docstring: int = 0, 
        parameters: int = 0, 
        decorators: int = 0,
        total: int | None = None
    ) -> TokenBreakdown:
        """Create a TokenBreakdown with calculated total."""
        if total is None:
            total = signature + docstring + parameters + decorators
        return TokenBreakdown(
            signature=signature,
            docstring=docstring, 
            parameters=parameters,
            decorators=decorators,
            total=total
        )


class TokenCounter:
    """Accurate token counter using OpenAI's tiktoken library."""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize the token counter.
        
        Args:
            encoding_name: The tiktoken encoding to use. Default is cl100k_base
                         which is used by GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo.
        """
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.encoding_name = encoding_name
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a given text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            The number of tokens
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def count_function_tokens(self, func_def: str) -> TokenBreakdown:
        """Count tokens for a complete function definition.
        
        Args:
            func_def: The complete function definition as a string
            
        Returns:
            TokenBreakdown with counts for different components
        """
        try:
            # Parse the function definition
            tree = ast.parse(func_def)
            if not tree.body or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Fallback to simple counting if parsing fails
                return TokenBreakdown.create(total=self.count_tokens(func_def))
                
            func_node = tree.body[0]
            
            # Extract decorators
            decorators_text = ""
            if func_node.decorator_list:
                decorators_lines = []
                for decorator in func_node.decorator_list:
                    # Reconstruct decorator text (simplified)
                    if isinstance(decorator, ast.Name):
                        decorators_lines.append(f"@{decorator.id}")
                    elif isinstance(decorator, ast.Attribute):
                        decorators_lines.append(f"@{ast.unparse(decorator)}")
                    else:
                        decorators_lines.append(f"@{ast.unparse(decorator)}")
                decorators_text = "\n".join(decorators_lines)
            
            # Extract function signature
            async_prefix = "async " if isinstance(func_node, ast.AsyncFunctionDef) else ""
            signature = f"{async_prefix}def {func_node.name}("
            args_parts = []
            
            # Regular arguments
            for arg in func_node.args.args:
                if arg.annotation:
                    args_parts.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
                else:
                    args_parts.append(arg.arg)
            
            signature += ", ".join(args_parts) + ")"
            
            # Return annotation
            if func_node.returns:
                signature += f" -> {ast.unparse(func_node.returns)}"
            
            signature += ":"
            
            # Extract docstring
            docstring = ast.get_docstring(func_node) or ""
            
            # Count tokens for each component
            decorators_tokens = self.count_tokens(decorators_text)
            signature_tokens = self.count_tokens(signature)
            docstring_tokens = self.count_tokens(docstring)
            
            # For parameters, count the detailed parameter definitions
            # This would include Field annotations, defaults, etc.
            param_details = self._extract_parameter_details(func_def)
            param_tokens = self.count_tokens(param_details)
            
            return TokenBreakdown.create(
                signature=signature_tokens,
                docstring=docstring_tokens,
                parameters=param_tokens,
                decorators=decorators_tokens
            )
            
        except Exception:
            # Fallback to simple counting if AST parsing fails
            return TokenBreakdown.create(total=self.count_tokens(func_def))
    
    def _extract_parameter_details(self, func_def: str) -> str:
        """Extract detailed parameter definitions including annotations and defaults.
        
        This captures the full parameter definitions that include Field annotations,
        type hints, default values, and descriptions.
        """
        # Look for parameter definitions with Field annotations
        field_pattern = r'(\w+):\s*Annotated\[([^\]]+)\]\s*=\s*[^,\)]*'
        matches = re.findall(field_pattern, func_def, re.MULTILINE | re.DOTALL)
        
        param_details = []
        for param_name, annotation_content in matches:
            # Extract the full parameter definition
            param_start = func_def.find(f"{param_name}:")
            if param_start == -1:
                continue
                
            # Find the end of this parameter (next parameter or end of parameters)
            remaining = func_def[param_start:]
            
            # Look for the next parameter or end of function signature
            next_param_match = re.search(r',\s*(\w+):\s*', remaining[10:])
            end_signature_match = re.search(r'\)\s*->', remaining)
            
            if next_param_match:
                param_end = param_start + 10 + next_param_match.start()
            elif end_signature_match:
                param_end = param_start + end_signature_match.start()
            else:
                param_end = len(func_def)
            
            param_def = func_def[param_start:param_end].strip().rstrip(',')
            param_details.append(param_def)
        
        return "\n".join(param_details)
    
    def count_tool_definition_tokens(self, tool_def: str) -> TokenBreakdown:
        """Count tokens for a complete MCP tool definition.
        
        This includes the decorator, function signature, docstring, and
        parameter definitions with their Field annotations.
        
        Args:
            tool_def: The complete tool definition including decorators
            
        Returns:
            TokenBreakdown with detailed component counts
        """
        return self.count_function_tokens(tool_def)
    
    def estimate_context_overhead(self, num_tools: int) -> int:
        """Estimate additional context overhead for multiple tools.
        
        Args:
            num_tools: Number of tools in the context
            
        Returns:
            Estimated overhead tokens for context management
        """
        # Empirical estimation based on MCP protocol overhead
        base_overhead = 50  # Basic MCP context
        per_tool_overhead = 10  # Tool registration overhead
        
        return base_overhead + (per_tool_overhead * num_tools)