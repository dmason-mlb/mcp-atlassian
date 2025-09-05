"""Token benchmarking system for MCP Atlassian tools.

This package provides comprehensive token analysis and benchmarking capabilities
to measure and compare token usage between the current MCP tool registration
architecture and the proposed meta-tools approach.

Key Components:
- TokenCounter: Core token counting using tiktoken
- AnalyzeCurrent: Analysis of existing @mcp.tool decorators
- AnalyzeMetaTools: Analysis of meta-tool token usage
- RunBenchmark: Main benchmarking orchestrator

Usage:
    python -m optimization.benchmarks.run_benchmark
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "MCP Atlassian Optimization Team"

# Core exports
from .token_counter import TokenCounter
from .analyze_current import CurrentToolsAnalyzer
from .analyze_meta_tools import MetaToolsAnalyzer

__all__ = [
    "TokenCounter",
    "CurrentToolsAnalyzer", 
    "MetaToolsAnalyzer",
]