"""Main benchmark runner for MCP Atlassian token optimization analysis.

This module orchestrates the complete benchmarking process, comparing
current tool registration with meta-tools approach and generating
comprehensive reports.

Usage:
    python -m optimization.benchmarks.run_benchmark
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    # Try importing colorama for colored terminal output
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback to no colors
    COLORS_AVAILABLE = False
    
    class Fore:
        GREEN = RED = YELLOW = BLUE = CYAN = MAGENTA = WHITE = ""
    
    class Style:
        BRIGHT = RESET_ALL = ""

from .analyze_current import CurrentToolsAnalyzer
from .analyze_meta_tools import MetaToolsAnalyzer
from .token_counter import TokenCounter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable debug logging for benchmarks
logging.getLogger("optimization.benchmarks").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Main benchmark runner that orchestrates the complete analysis."""
    
    def __init__(self, base_path: str | Path | None = None):
        """Initialize the benchmark runner.
        
        Args:
            base_path: Base path to the project. If None, assumes current working directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.output_dir = self.base_path / "optimization" / "benchmarks"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analyzers
        self.current_tools_analyzer = CurrentToolsAnalyzer(base_path)
        self.meta_tools_analyzer = MetaToolsAnalyzer(base_path)
        self.token_counter = TokenCounter()
        
    def run_complete_benchmark(self) -> dict[str, Any]:
        """Run the complete benchmarking process.
        
        Returns:
            Complete benchmark results
        """
        logger.info("Starting complete MCP Atlassian token benchmark...")
        
        # Analyze current tools
        logger.info("Analyzing current tool registrations...")
        current_analysis = self.current_tools_analyzer.analyze()
        
        # Analyze meta-tools
        logger.info("Analyzing meta-tools implementation...")
        meta_analysis = self.meta_tools_analyzer.analyze()
        
        # Generate comparison metrics
        logger.info("Computing comparison metrics...")
        comparison = self._compute_comparison_metrics(current_analysis, meta_analysis)
        
        # Compile complete results
        results = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "encoding": self.token_counter.encoding_name,
                "analysis_version": "1.0.0",
                "project_path": str(self.base_path),
            },
            "current_tools": {
                "total_tools": current_analysis.total_tools,
                "total_tokens": current_analysis.total_tokens,
                "by_service": current_analysis.by_service,
                "by_module": {
                    mod_path: {
                        "tool_count": mod_analysis.tool_count,
                        "total_tokens": mod_analysis.total_tokens,
                        "service": mod_analysis.service,
                        "tools": [
                            {
                                "name": tool.name,
                                "tokens": tool.tokens.total,
                                "tags": list(tool.tags)
                            }
                            for tool in mod_analysis.tools
                        ]
                    }
                    for mod_path, mod_analysis in current_analysis.by_module.items()
                },
                "token_breakdown": self._aggregate_token_breakdown(current_analysis),
                "detailed_tools": [
                    {
                        "name": tool.name,
                        "module": tool.relative_path,
                        "service": tool.service,
                        "tokens": {
                            "total": tool.tokens.total,
                            "signature": tool.tokens.signature,
                            "docstring": tool.tokens.docstring,
                            "parameters": tool.tokens.parameters,
                            "decorators": tool.tokens.decorators
                        },
                        "tags": list(tool.tags),
                        "line_number": tool.line_number
                    }
                    for tool in current_analysis.tools
                ]
            },
            "meta_tools": {
                "total_meta_tools": meta_analysis.total_meta_tools,
                "total_tokens": meta_analysis.total_tokens,
                "tools_consolidated": meta_analysis.traditional_tools_replaced,
                "consolidation_ratio": (
                    meta_analysis.traditional_tools_replaced / current_analysis.total_tools
                    if current_analysis.total_tools > 0 else 0
                ),
                "analysis_summary": meta_analysis.analysis_summary,
                "detailed_meta_tools": [
                    {
                        "name": meta_tool.name,
                        "module": meta_tool.relative_path,
                        "type": meta_tool.tool_type,
                        "tokens": {
                            "total": meta_tool.tokens.total,
                            "signature": meta_tool.tokens.signature,
                            "docstring": meta_tool.tokens.docstring,
                            "parameters": meta_tool.tokens.parameters,
                            "decorators": meta_tool.tokens.decorators
                        },
                        "consolidates": meta_tool.consolidates,
                        "consolidates_count": len(meta_tool.consolidates)
                    }
                    for meta_tool in meta_analysis.meta_tools
                ]
            },
            "comparison": comparison,
            "recommendations": self._generate_recommendations(comparison)
        }
        
        logger.info("Benchmark analysis complete!")
        return results
    
    def _compute_comparison_metrics(
        self, 
        current_analysis, 
        meta_analysis
    ) -> dict[str, Any]:
        """Compute detailed comparison metrics.
        
        Args:
            current_analysis: Current tools analysis results
            meta_analysis: Meta-tools analysis results
            
        Returns:
            Comparison metrics dictionary
        """
        current_tokens = current_analysis.total_tokens
        meta_tokens = meta_analysis.total_tokens
        
        # Add estimated overhead for context management
        current_overhead = self.token_counter.estimate_context_overhead(current_analysis.total_tools)
        meta_overhead = self.token_counter.estimate_context_overhead(meta_analysis.total_meta_tools)
        
        current_total = current_tokens + current_overhead
        meta_total = meta_tokens + meta_overhead
        
        token_reduction = current_total - meta_total
        reduction_percentage = (token_reduction / current_total * 100) if current_total > 0 else 0
        
        return {
            "token_analysis": {
                "current_tools_tokens": current_tokens,
                "current_overhead_tokens": current_overhead,
                "current_total_tokens": current_total,
                "meta_tools_tokens": meta_tokens,
                "meta_overhead_tokens": meta_overhead,
                "meta_total_tokens": meta_total,
                "absolute_reduction": token_reduction,
                "reduction_percentage": reduction_percentage,
                "efficiency_ratio": meta_total / current_total if current_total > 0 else 0
            },
            "tool_consolidation": {
                "original_tool_count": current_analysis.total_tools,
                "meta_tool_count": meta_analysis.total_meta_tools,
                "consolidation_factor": (
                    current_analysis.total_tools / meta_analysis.total_meta_tools
                    if meta_analysis.total_meta_tools > 0 else 0
                ),
                "tools_eliminated": current_analysis.total_tools - meta_analysis.total_meta_tools
            },
            "service_breakdown": {
                service: {
                    "original_tokens": service_data["total_tokens"],
                    "original_tool_count": service_data["tool_count"],
                    "avg_tokens_per_tool": service_data.get("avg_tokens_per_tool", 0),
                    "estimated_meta_tool_tokens": meta_tokens // len(current_analysis.by_service) if current_analysis.by_service else 0
                }
                for service, service_data in current_analysis.by_service.items()
            },
            "performance_impact": {
                "context_window_savings_percentage": reduction_percentage,
                "estimated_response_time_improvement": min(reduction_percentage * 0.5, 25),  # Conservative estimate
                "memory_efficiency_improvement": reduction_percentage * 0.3  # Estimated memory savings
            }
        }
    
    def _aggregate_token_breakdown(self, current_analysis) -> dict[str, Any]:
        """Aggregate token breakdown across all current tools.
        
        Args:
            current_analysis: Current tools analysis results
            
        Returns:
            Aggregated token breakdown
        """
        total_signature = sum(tool.tokens.signature for tool in current_analysis.tools)
        total_docstring = sum(tool.tokens.docstring for tool in current_analysis.tools)
        total_parameters = sum(tool.tokens.parameters for tool in current_analysis.tools)
        total_decorators = sum(tool.tokens.decorators for tool in current_analysis.tools)
        
        total_tokens = current_analysis.total_tokens
        
        return {
            "signature_tokens": total_signature,
            "docstring_tokens": total_docstring,
            "parameter_tokens": total_parameters,
            "decorator_tokens": total_decorators,
            "total_tokens": total_tokens,
            "breakdown_percentages": {
                "signature": (total_signature / total_tokens * 100) if total_tokens > 0 else 0,
                "docstring": (total_docstring / total_tokens * 100) if total_tokens > 0 else 0,
                "parameters": (total_parameters / total_tokens * 100) if total_tokens > 0 else 0,
                "decorators": (total_decorators / total_tokens * 100) if total_tokens > 0 else 0
            }
        }
    
    def _generate_recommendations(self, comparison: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate optimization recommendations based on comparison results.
        
        Args:
            comparison: Comparison metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        token_analysis = comparison["token_analysis"]
        reduction_percentage = token_analysis["reduction_percentage"]
        
        # High-impact recommendations
        if reduction_percentage > 60:
            recommendations.append({
                "priority": "HIGH",
                "category": "Token Optimization",
                "title": "Implement Meta-Tools Architecture",
                "description": f"Meta-tools approach reduces token usage by {reduction_percentage:.1f}%, providing significant context window savings.",
                "estimated_impact": "High - Major performance improvement",
                "implementation_effort": "Medium"
            })
        
        # Service-specific recommendations
        for service, service_data in comparison["service_breakdown"].items():
            if service_data["original_tool_count"] > 5:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Service Optimization",
                    "title": f"Consolidate {service.title()} Tools",
                    "description": f"{service.title()} service has {service_data['original_tool_count']} tools averaging {service_data['avg_tokens_per_tool']:.0f} tokens each. Consider consolidation.",
                    "estimated_impact": "Medium - Service-level efficiency",
                    "implementation_effort": "Low"
                })
        
        # Tool consolidation recommendations
        consolidation_factor = comparison["tool_consolidation"]["consolidation_factor"]
        if consolidation_factor > 10:
            recommendations.append({
                "priority": "HIGH",
                "category": "Architecture",
                "title": "High Consolidation Opportunity",
                "description": f"Current architecture has {consolidation_factor:.1f}x more tools than needed. Meta-tools provide excellent consolidation opportunity.",
                "estimated_impact": "High - Significant simplification",
                "implementation_effort": "High"
            })
        
        return recommendations
    
    def generate_reports(self, results: dict[str, Any]) -> None:
        """Generate comprehensive reports from benchmark results.
        
        Args:
            results: Complete benchmark results
        """
        # Generate JSON report
        json_report_path = self.output_dir / "baseline_report.json"
        with json_report_path.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {json_report_path}")
        
        # Generate Markdown report
        md_report_path = self.output_dir / "benchmark_report.md"
        self._generate_markdown_report(results, md_report_path)
        
        logger.info(f"Markdown report generated: {md_report_path}")
        
        # Print console summary
        self._print_console_summary(results)
    
    def _generate_markdown_report(self, results: dict[str, Any], output_path: Path) -> None:
        """Generate a comprehensive Markdown report.
        
        Args:
            results: Complete benchmark results
            output_path: Path to write the Markdown report
        """
        current = results["current_tools"]
        meta = results["meta_tools"]
        comparison = results["comparison"]["token_analysis"]
        
        md_content = f"""# MCP Atlassian Token Benchmarking Report

*Generated on {results['metadata']['timestamp']}*

## Executive Summary

This report analyzes the token usage of the current MCP Atlassian tool architecture compared to the proposed meta-tools approach.

### Key Findings

- **Current Tools**: {current['total_tools']} tools consuming {current['total_tokens']:,} tokens
- **Meta-Tools**: {meta['total_meta_tools']} meta-tools consuming {meta['total_tokens']:,} tokens  
- **Token Reduction**: {comparison['absolute_reduction']:,} tokens ({comparison['reduction_percentage']:.1f}%)
- **Efficiency Gain**: {(1/comparison['efficiency_ratio']-1)*100:.1f}% improvement in token efficiency

## Current Tool Analysis

### By Service
"""
        
        for service, service_data in current["by_service"].items():
            md_content += f"""
#### {service.title()} Service
- **Tools**: {service_data['tool_count']}
- **Total Tokens**: {service_data['total_tokens']:,}
- **Average per Tool**: {service_data['avg_tokens_per_tool']:.0f} tokens
"""
        
        md_content += f"""
### Token Breakdown
- **Function Signatures**: {current['token_breakdown']['signature_tokens']:,} tokens ({current['token_breakdown']['breakdown_percentages']['signature']:.1f}%)
- **Docstrings**: {current['token_breakdown']['docstring_tokens']:,} tokens ({current['token_breakdown']['breakdown_percentages']['docstring']:.1f}%)
- **Parameters**: {current['token_breakdown']['parameter_tokens']:,} tokens ({current['token_breakdown']['breakdown_percentages']['parameters']:.1f}%)
- **Decorators**: {current['token_breakdown']['decorator_tokens']:,} tokens ({current['token_breakdown']['breakdown_percentages']['decorators']:.1f}%)

## Meta-Tools Analysis

The meta-tools approach consolidates {current['total_tools']} individual tools into {meta['total_meta_tools']} unified interfaces:

- **Resource Manager**: Handles CRUD operations across both Jira and Confluence
- **Schema Discovery**: Dynamic schema and field discovery
- **Unified Interfaces**: Single entry points for multiple operations

## Recommendations

"""
        
        for i, rec in enumerate(results["recommendations"], 1):
            md_content += f"""
### {i}. {rec['title']} ({rec['priority']} Priority)

**Category**: {rec['category']}  
**Description**: {rec['description']}  
**Estimated Impact**: {rec['estimated_impact']}  
**Implementation Effort**: {rec['implementation_effort']}
"""
        
        md_content += f"""
## Technical Details

- **Encoding**: {results['metadata']['encoding']}
- **Analysis Version**: {results['metadata']['analysis_version']}
- **Project Path**: {results['metadata']['project_path']}
- **Report Generated**: {results['metadata']['timestamp']}
"""
        
        with output_path.open("w", encoding="utf-8") as f:
            f.write(md_content)
    
    def _print_console_summary(self, results: dict[str, Any]) -> None:
        """Print a colorized console summary.
        
        Args:
            results: Complete benchmark results
        """
        current = results["current_tools"]
        meta = results["meta_tools"]
        comparison = results["comparison"]["token_analysis"]
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}MCP Atlassian Token Benchmark Results{Style.RESET_ALL}")
        print("=" * 50)
        
        print(f"\n{Fore.YELLOW}Current Architecture:{Style.RESET_ALL}")
        print(f"  • Tools: {Fore.WHITE}{current['total_tools']}{Style.RESET_ALL}")
        print(f"  • Total Tokens: {Fore.WHITE}{current['total_tokens']:,}{Style.RESET_ALL}")
        avg_tokens = current['total_tokens'] // current['total_tools'] if current['total_tools'] > 0 else 0
        print(f"  • Average per Tool: {Fore.WHITE}{avg_tokens:.0f}{Style.RESET_ALL} tokens")
        
        print(f"\n{Fore.GREEN}Meta-Tools Architecture:{Style.RESET_ALL}")
        print(f"  • Meta-Tools: {Fore.WHITE}{meta['total_meta_tools']}{Style.RESET_ALL}")
        print(f"  • Total Tokens: {Fore.WHITE}{meta['total_tokens']:,}{Style.RESET_ALL}")
        avg_meta_tokens = meta['total_tokens'] // meta['total_meta_tools'] if meta['total_meta_tools'] > 0 else 0
        print(f"  • Average per Meta-Tool: {Fore.WHITE}{avg_meta_tokens:.0f}{Style.RESET_ALL} tokens")
        
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Optimization Results:{Style.RESET_ALL}")
        print(f"  • Token Reduction: {Fore.GREEN}{comparison['absolute_reduction']:,}{Style.RESET_ALL} tokens")
        print(f"  • Reduction Percentage: {Fore.GREEN}{comparison['reduction_percentage']:.1f}%{Style.RESET_ALL}")
        print(f"  • Efficiency Ratio: {Fore.GREEN}{1/comparison['efficiency_ratio']:.1f}x{Style.RESET_ALL} improvement")
        
        # Service breakdown
        print(f"\n{Fore.BLUE}By Service:{Style.RESET_ALL}")
        for service, service_data in current["by_service"].items():
            print(f"  • {service.title()}: {Fore.WHITE}{service_data['tool_count']}{Style.RESET_ALL} tools, "
                  f"{Fore.WHITE}{service_data['total_tokens']:,}{Style.RESET_ALL} tokens")
        
        print(f"\n{Fore.CYAN}Reports Generated:{Style.RESET_ALL}")
        print(f"  • JSON: {Fore.WHITE}optimization/benchmarks/baseline_report.json{Style.RESET_ALL}")
        print(f"  • Markdown: {Fore.WHITE}optimization/benchmarks/benchmark_report.md{Style.RESET_ALL}")
        
        print(f"\n{Style.BRIGHT}Recommendation: {Fore.GREEN}Implement meta-tools architecture for {comparison['reduction_percentage']:.0f}% token savings!{Style.RESET_ALL}\n")


def main() -> int:
    """Main entry point for the benchmark runner.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        runner = BenchmarkRunner()
        results = runner.run_complete_benchmark()
        runner.generate_reports(results)
        return 0
        
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())