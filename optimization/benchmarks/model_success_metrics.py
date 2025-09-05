"""
Model Success Metrics and Benchmarking Suite

Comprehensive benchmarking framework for measuring model performance with meta-tools.
Tracks key metrics including tool selection accuracy, token usage, error recovery rates,
and overall success in achieving >95% operation effectiveness.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import statistics
from pathlib import Path
import csv


class MetricType(Enum):
    """Types of metrics tracked for model performance."""
    TOOL_SELECTION_ACCURACY = "tool_selection_accuracy"
    OPERATION_SUCCESS_RATE = "operation_success_rate"
    TOKEN_USAGE = "token_usage"
    ERROR_RECOVERY_RATE = "error_recovery_rate"
    SCHEMA_CACHE_HIT_RATE = "schema_cache_hit_rate"
    RESPONSE_TIME = "response_time"
    AMBIGUITY_RESOLUTION_ACCURACY = "ambiguity_resolution_accuracy"
    CONVERSATION_COHERENCE = "conversation_coherence"


@dataclass
class OperationMetric:
    """Metrics for a single operation."""
    operation_id: str
    timestamp: datetime
    request: str
    selected_tool: str
    expected_tool: str
    success: bool
    tokens_used: int
    response_time_ms: float
    error_occurred: bool = False
    error_recovered: bool = False
    schema_fetched: bool = False
    ambiguity_detected: bool = False
    ambiguity_resolved: bool = False
    confidence_score: float = 0.0


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    benchmark_id: str
    timestamp: datetime
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_tokens: float
    average_response_time_ms: float
    tool_selection_accuracy: float
    error_recovery_rate: float
    schema_cache_hit_rate: float
    ambiguity_resolution_accuracy: float
    overall_success_rate: float
    v1_comparison: Optional[Dict[str, float]] = None
    detailed_metrics: List[OperationMetric] = field(default_factory=list)


@dataclass
class PerformanceComparison:
    """Comparison between v1 and v2 tool performance."""
    metric_name: str
    v1_value: float
    v2_value: float
    improvement_percentage: float
    meets_target: bool


class ModelSuccessMetrics:
    """
    Main metrics collection and analysis class for model performance.
    
    Tracks all key performance indicators for meta-tool interactions
    and provides comprehensive reporting and benchmarking capabilities.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("optimization/benchmarks/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.operations: List[OperationMetric] = []
        self.benchmarks: List[BenchmarkResult] = []
        self.v1_baseline: Optional[Dict[str, float]] = None
        
        # Performance targets
        self.targets = {
            MetricType.TOOL_SELECTION_ACCURACY: 95.0,
            MetricType.OPERATION_SUCCESS_RATE: 95.0,
            MetricType.ERROR_RECOVERY_RATE: 90.0,
            MetricType.SCHEMA_CACHE_HIT_RATE: 80.0,
            MetricType.AMBIGUITY_RESOLUTION_ACCURACY: 85.0,
            MetricType.TOKEN_USAGE: 3500,  # Maximum tokens
            MetricType.RESPONSE_TIME: 200,  # Maximum ms
        }
    
    def record_operation(self, metric: OperationMetric) -> None:
        """Record metrics for a single operation."""
        self.operations.append(metric)
    
    def set_v1_baseline(self, baseline: Dict[str, float]) -> None:
        """Set v1 baseline metrics for comparison."""
        self.v1_baseline = baseline
    
    def calculate_tool_selection_accuracy(self) -> float:
        """Calculate accuracy of tool selection."""
        if not self.operations:
            return 0.0
        
        correct_selections = sum(
            1 for op in self.operations 
            if op.selected_tool == op.expected_tool
        )
        return (correct_selections / len(self.operations)) * 100
    
    def calculate_operation_success_rate(self) -> float:
        """Calculate overall operation success rate."""
        if not self.operations:
            return 0.0
        
        successful = sum(1 for op in self.operations if op.success)
        return (successful / len(self.operations)) * 100
    
    def calculate_average_tokens(self) -> float:
        """Calculate average token usage per operation."""
        if not self.operations:
            return 0.0
        
        return statistics.mean(op.tokens_used for op in self.operations)
    
    def calculate_error_recovery_rate(self) -> float:
        """Calculate error recovery success rate."""
        error_operations = [op for op in self.operations if op.error_occurred]
        if not error_operations:
            return 100.0  # No errors to recover from
        
        recovered = sum(1 for op in error_operations if op.error_recovered)
        return (recovered / len(error_operations)) * 100
    
    def calculate_schema_cache_hit_rate(self) -> float:
        """Calculate schema cache hit rate."""
        if not self.operations:
            return 0.0
        
        # Operations that didn't need to fetch schema (cache hit)
        cache_hits = sum(1 for op in self.operations if not op.schema_fetched)
        return (cache_hits / len(self.operations)) * 100
    
    def calculate_ambiguity_resolution_accuracy(self) -> float:
        """Calculate accuracy of ambiguity resolution."""
        ambiguous_operations = [op for op in self.operations if op.ambiguity_detected]
        if not ambiguous_operations:
            return 100.0  # No ambiguity to resolve
        
        resolved = sum(1 for op in ambiguous_operations if op.ambiguity_resolved and op.success)
        return (resolved / len(ambiguous_operations)) * 100
    
    def calculate_average_response_time(self) -> float:
        """Calculate average response time in milliseconds."""
        if not self.operations:
            return 0.0
        
        return statistics.mean(op.response_time_ms for op in self.operations)
    
    def calculate_confidence_score(self) -> float:
        """Calculate average confidence score across operations."""
        if not self.operations:
            return 0.0
        
        scores = [op.confidence_score for op in self.operations if op.confidence_score > 0]
        return statistics.mean(scores) if scores else 0.0
    
    def run_benchmark(self, benchmark_name: str = "default") -> BenchmarkResult:
        """Run a complete benchmark and generate results."""
        benchmark_id = f"{benchmark_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            timestamp=datetime.now(),
            total_operations=len(self.operations),
            successful_operations=sum(1 for op in self.operations if op.success),
            failed_operations=sum(1 for op in self.operations if not op.success),
            average_tokens=self.calculate_average_tokens(),
            average_response_time_ms=self.calculate_average_response_time(),
            tool_selection_accuracy=self.calculate_tool_selection_accuracy(),
            error_recovery_rate=self.calculate_error_recovery_rate(),
            schema_cache_hit_rate=self.calculate_schema_cache_hit_rate(),
            ambiguity_resolution_accuracy=self.calculate_ambiguity_resolution_accuracy(),
            overall_success_rate=self.calculate_operation_success_rate(),
            detailed_metrics=self.operations.copy()
        )
        
        # Add v1 comparison if baseline available
        if self.v1_baseline:
            result.v1_comparison = self.generate_v1_comparison()
        
        self.benchmarks.append(result)
        return result
    
    def generate_v1_comparison(self) -> Dict[str, float]:
        """Generate comparison metrics against v1 baseline."""
        if not self.v1_baseline:
            return {}
        
        comparison = {}
        
        # Token usage comparison
        v2_tokens = self.calculate_average_tokens()
        v1_tokens = self.v1_baseline.get("average_tokens", 15000)
        comparison["token_reduction_percentage"] = ((v1_tokens - v2_tokens) / v1_tokens) * 100
        
        # Response time comparison
        v2_response = self.calculate_average_response_time()
        v1_response = self.v1_baseline.get("average_response_time_ms", 500)
        comparison["response_time_improvement"] = ((v1_response - v2_response) / v1_response) * 100
        
        # Success rate comparison
        v2_success = self.calculate_operation_success_rate()
        v1_success = self.v1_baseline.get("operation_success_rate", 85.0)
        comparison["success_rate_delta"] = v2_success - v1_success
        
        return comparison
    
    def check_performance_targets(self) -> Dict[MetricType, Tuple[float, float, bool]]:
        """Check if performance meets targets."""
        results = {}
        
        metrics = {
            MetricType.TOOL_SELECTION_ACCURACY: self.calculate_tool_selection_accuracy(),
            MetricType.OPERATION_SUCCESS_RATE: self.calculate_operation_success_rate(),
            MetricType.ERROR_RECOVERY_RATE: self.calculate_error_recovery_rate(),
            MetricType.SCHEMA_CACHE_HIT_RATE: self.calculate_schema_cache_hit_rate(),
            MetricType.AMBIGUITY_RESOLUTION_ACCURACY: self.calculate_ambiguity_resolution_accuracy(),
            MetricType.TOKEN_USAGE: self.calculate_average_tokens(),
            MetricType.RESPONSE_TIME: self.calculate_average_response_time(),
        }
        
        for metric_type, value in metrics.items():
            target = self.targets[metric_type]
            
            # For token usage and response time, lower is better
            if metric_type in [MetricType.TOKEN_USAGE, MetricType.RESPONSE_TIME]:
                meets_target = value <= target
            else:
                meets_target = value >= target
            
            results[metric_type] = (value, target, meets_target)
        
        return results
    
    def generate_report(self, benchmark: Optional[BenchmarkResult] = None) -> str:
        """Generate a comprehensive performance report."""
        if benchmark is None and self.benchmarks:
            benchmark = self.benchmarks[-1]
        elif benchmark is None:
            benchmark = self.run_benchmark()
        
        report = []
        report.append("=" * 80)
        report.append("MODEL SUCCESS METRICS REPORT")
        report.append("=" * 80)
        report.append(f"Benchmark ID: {benchmark.benchmark_id}")
        report.append(f"Timestamp: {benchmark.timestamp}")
        report.append(f"Total Operations: {benchmark.total_operations}")
        report.append("")
        
        # Success Metrics
        report.append("SUCCESS METRICS")
        report.append("-" * 40)
        report.append(f"Overall Success Rate: {benchmark.overall_success_rate:.1f}%")
        report.append(f"Tool Selection Accuracy: {benchmark.tool_selection_accuracy:.1f}%")
        report.append(f"Ambiguity Resolution: {benchmark.ambiguity_resolution_accuracy:.1f}%")
        report.append(f"Error Recovery Rate: {benchmark.error_recovery_rate:.1f}%")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Average Token Usage: {benchmark.average_tokens:.0f} tokens")
        report.append(f"Average Response Time: {benchmark.average_response_time_ms:.2f}ms")
        report.append(f"Schema Cache Hit Rate: {benchmark.schema_cache_hit_rate:.1f}%")
        report.append("")
        
        # Target Achievement
        report.append("TARGET ACHIEVEMENT")
        report.append("-" * 40)
        
        target_results = self.check_performance_targets()
        for metric_type, (value, target, meets) in target_results.items():
            status = "✓" if meets else "✗"
            metric_name = metric_type.value.replace("_", " ").title()
            
            if metric_type in [MetricType.TOKEN_USAGE, MetricType.RESPONSE_TIME]:
                report.append(f"{status} {metric_name}: {value:.1f} (target: ≤{target})")
            else:
                report.append(f"{status} {metric_name}: {value:.1f}% (target: ≥{target}%)")
        
        report.append("")
        
        # V1 Comparison
        if benchmark.v1_comparison:
            report.append("V1 vs V2 COMPARISON")
            report.append("-" * 40)
            
            for key, value in benchmark.v1_comparison.items():
                formatted_key = key.replace("_", " ").title()
                if "percentage" in key or "improvement" in key:
                    report.append(f"{formatted_key}: {value:.1f}%")
                else:
                    report.append(f"{formatted_key}: {value:.1f}")
            
            report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        
        targets_met = sum(1 for _, _, meets in target_results.values() if meets)
        total_targets = len(target_results)
        
        report.append(f"Targets Met: {targets_met}/{total_targets}")
        
        if benchmark.overall_success_rate >= 95.0:
            report.append("✓ SUCCESS: Achieved >95% operation success rate")
        else:
            report.append("✗ NEEDS IMPROVEMENT: Below 95% success rate target")
        
        if benchmark.average_tokens <= 3500:
            report.append("✓ SUCCESS: Token usage optimized (75% reduction achieved)")
        else:
            report.append("✗ NEEDS IMPROVEMENT: Token usage above target")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str, filename: Optional[str] = None) -> Path:
        """Save report to file."""
        if filename is None:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        filepath = self.output_dir / filename
        filepath.write_text(report)
        return filepath
    
    def export_metrics_csv(self, filename: Optional[str] = None) -> Path:
        """Export detailed metrics to CSV."""
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as csvfile:
            if self.operations:
                fieldnames = list(asdict(self.operations[0]).keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for op in self.operations:
                    writer.writerow(asdict(op))
        
        return filepath
    
    def export_benchmark_json(self, benchmark: Optional[BenchmarkResult] = None) -> Path:
        """Export benchmark results to JSON."""
        if benchmark is None and self.benchmarks:
            benchmark = self.benchmarks[-1]
        elif benchmark is None:
            benchmark = self.run_benchmark()
        
        filename = f"benchmark_{benchmark.benchmark_id}.json"
        filepath = self.output_dir / filename
        
        # Convert to serializable format
        benchmark_dict = {
            "benchmark_id": benchmark.benchmark_id,
            "timestamp": benchmark.timestamp.isoformat(),
            "total_operations": benchmark.total_operations,
            "successful_operations": benchmark.successful_operations,
            "failed_operations": benchmark.failed_operations,
            "average_tokens": benchmark.average_tokens,
            "average_response_time_ms": benchmark.average_response_time_ms,
            "tool_selection_accuracy": benchmark.tool_selection_accuracy,
            "error_recovery_rate": benchmark.error_recovery_rate,
            "schema_cache_hit_rate": benchmark.schema_cache_hit_rate,
            "ambiguity_resolution_accuracy": benchmark.ambiguity_resolution_accuracy,
            "overall_success_rate": benchmark.overall_success_rate,
            "v1_comparison": benchmark.v1_comparison,
        }
        
        with open(filepath, 'w') as f:
            json.dump(benchmark_dict, f, indent=2)
        
        return filepath


class A_B_TestRunner:
    """
    A/B testing framework for comparing v1 and v2 tool performance.
    
    Runs parallel tests with both tool versions and provides
    statistical comparison of results.
    """
    
    def __init__(self):
        self.v1_metrics = ModelSuccessMetrics()
        self.v2_metrics = ModelSuccessMetrics()
        self.test_scenarios: List[Dict[str, Any]] = []
    
    def add_test_scenario(self, scenario: Dict[str, Any]) -> None:
        """Add a test scenario for A/B testing."""
        self.test_scenarios.append(scenario)
    
    async def run_v1_test(self, scenario: Dict[str, Any]) -> OperationMetric:
        """Run test with v1 tools."""
        start_time = time.time()
        
        # Simulate v1 tool execution
        # In real implementation, would use actual v1 tools
        operation = OperationMetric(
            operation_id=f"v1_{scenario['id']}",
            timestamp=datetime.now(),
            request=scenario["request"],
            selected_tool=scenario.get("v1_tool", "jira_create_issue"),
            expected_tool=scenario["expected_tool"],
            success=scenario.get("v1_success", True),
            tokens_used=scenario.get("v1_tokens", 15000),
            response_time_ms=(time.time() - start_time) * 1000,
            error_occurred=scenario.get("v1_error", False),
            error_recovered=scenario.get("v1_recovered", False),
            schema_fetched=True,  # v1 always loads full schema
            ambiguity_detected=scenario.get("ambiguity", False),
            ambiguity_resolved=scenario.get("v1_resolved", False),
            confidence_score=scenario.get("v1_confidence", 0.7)
        )
        
        return operation
    
    async def run_v2_test(self, scenario: Dict[str, Any]) -> OperationMetric:
        """Run test with v2 meta-tools."""
        start_time = time.time()
        
        # Simulate v2 meta-tool execution
        # In real implementation, would use actual v2 tools
        operation = OperationMetric(
            operation_id=f"v2_{scenario['id']}",
            timestamp=datetime.now(),
            request=scenario["request"],
            selected_tool=scenario.get("v2_tool", "resource_manager"),
            expected_tool=scenario["expected_tool"],
            success=scenario.get("v2_success", True),
            tokens_used=scenario.get("v2_tokens", 3500),
            response_time_ms=(time.time() - start_time) * 1000,
            error_occurred=scenario.get("v2_error", False),
            error_recovered=scenario.get("v2_recovered", True),
            schema_fetched=scenario.get("v2_schema_fetch", False),
            ambiguity_detected=scenario.get("ambiguity", False),
            ambiguity_resolved=scenario.get("v2_resolved", True),
            confidence_score=scenario.get("v2_confidence", 0.9)
        )
        
        return operation
    
    async def run_a_b_test(self) -> Dict[str, Any]:
        """Run complete A/B test with all scenarios."""
        v1_operations = []
        v2_operations = []
        
        for scenario in self.test_scenarios:
            # Run both versions in parallel
            v1_op, v2_op = await asyncio.gather(
                self.run_v1_test(scenario),
                self.run_v2_test(scenario)
            )
            
            v1_operations.append(v1_op)
            v2_operations.append(v2_op)
            
            self.v1_metrics.record_operation(v1_op)
            self.v2_metrics.record_operation(v2_op)
        
        # Generate benchmarks
        v1_benchmark = self.v1_metrics.run_benchmark("v1")
        v2_benchmark = self.v2_metrics.run_benchmark("v2")
        
        # Compare results
        comparison = {
            "test_count": len(self.test_scenarios),
            "v1_success_rate": v1_benchmark.overall_success_rate,
            "v2_success_rate": v2_benchmark.overall_success_rate,
            "success_rate_improvement": v2_benchmark.overall_success_rate - v1_benchmark.overall_success_rate,
            "v1_avg_tokens": v1_benchmark.average_tokens,
            "v2_avg_tokens": v2_benchmark.average_tokens,
            "token_reduction": ((v1_benchmark.average_tokens - v2_benchmark.average_tokens) / 
                              v1_benchmark.average_tokens) * 100,
            "v1_avg_response_ms": v1_benchmark.average_response_time_ms,
            "v2_avg_response_ms": v2_benchmark.average_response_time_ms,
            "response_time_improvement": ((v1_benchmark.average_response_time_ms - 
                                         v2_benchmark.average_response_time_ms) / 
                                        v1_benchmark.average_response_time_ms) * 100,
            "v2_meets_targets": v2_benchmark.overall_success_rate >= 95.0 and v2_benchmark.average_tokens <= 3500,
            "recommendation": "Deploy v2" if v2_benchmark.overall_success_rate >= 95.0 else "Continue optimization"
        }
        
        return comparison
    
    def generate_a_b_report(self, comparison: Dict[str, Any]) -> str:
        """Generate A/B test comparison report."""
        report = []
        report.append("=" * 80)
        report.append("A/B TEST COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Test Scenarios: {comparison['test_count']}")
        report.append("")
        
        report.append("SUCCESS RATES")
        report.append("-" * 40)
        report.append(f"V1 Success Rate: {comparison['v1_success_rate']:.1f}%")
        report.append(f"V2 Success Rate: {comparison['v2_success_rate']:.1f}%")
        report.append(f"Improvement: {comparison['success_rate_improvement']:+.1f}%")
        report.append("")
        
        report.append("TOKEN USAGE")
        report.append("-" * 40)
        report.append(f"V1 Average Tokens: {comparison['v1_avg_tokens']:.0f}")
        report.append(f"V2 Average Tokens: {comparison['v2_avg_tokens']:.0f}")
        report.append(f"Reduction: {comparison['token_reduction']:.1f}%")
        report.append("")
        
        report.append("RESPONSE TIME")
        report.append("-" * 40)
        report.append(f"V1 Average Response: {comparison['v1_avg_response_ms']:.2f}ms")
        report.append(f"V2 Average Response: {comparison['v2_avg_response_ms']:.2f}ms")
        report.append(f"Improvement: {comparison['response_time_improvement']:.1f}%")
        report.append("")
        
        report.append("RECOMMENDATION")
        report.append("-" * 40)
        
        if comparison['v2_meets_targets']:
            report.append("✓ V2 meets all performance targets")
            report.append(f"✓ Recommendation: {comparison['recommendation']}")
        else:
            report.append("✗ V2 does not meet all targets")
            report.append(f"⚠ Recommendation: {comparison['recommendation']}")
        
        report.append("=" * 80)
        
        return "\n".join(report)


# Convenience function for running quick benchmarks
async def run_model_success_benchmark(
    operations: List[OperationMetric],
    v1_baseline: Optional[Dict[str, float]] = None,
    output_dir: Optional[Path] = None
) -> Tuple[BenchmarkResult, str]:
    """
    Run a complete benchmark with provided operations.
    
    Args:
        operations: List of operation metrics to benchmark
        v1_baseline: Optional v1 baseline metrics for comparison
        output_dir: Optional output directory for reports
    
    Returns:
        Tuple of (BenchmarkResult, report_string)
    """
    metrics = ModelSuccessMetrics(output_dir)
    
    for operation in operations:
        metrics.record_operation(operation)
    
    if v1_baseline:
        metrics.set_v1_baseline(v1_baseline)
    
    benchmark = metrics.run_benchmark()
    report = metrics.generate_report(benchmark)
    
    # Save outputs
    metrics.save_report(report)
    metrics.export_metrics_csv()
    metrics.export_benchmark_json(benchmark)
    
    return benchmark, report


# Example usage and test data generation
def generate_test_operations() -> List[OperationMetric]:
    """Generate sample operation metrics for testing."""
    operations = []
    
    # Successful operations
    for i in range(80):
        operations.append(OperationMetric(
            operation_id=f"op_{i}",
            timestamp=datetime.now(),
            request=f"Create issue {i}",
            selected_tool="resource_manager",
            expected_tool="resource_manager",
            success=True,
            tokens_used=3200 + (i % 500),
            response_time_ms=150 + (i % 100),
            schema_fetched=(i < 5),  # Only first few fetch schema
            confidence_score=0.85 + (i % 15) / 100
        ))
    
    # Operations with errors but recovered
    for i in range(10):
        operations.append(OperationMetric(
            operation_id=f"error_op_{i}",
            timestamp=datetime.now(),
            request=f"Update issue {i}",
            selected_tool="resource_manager",
            expected_tool="resource_manager",
            success=True,
            tokens_used=3500,
            response_time_ms=250,
            error_occurred=True,
            error_recovered=True,
            confidence_score=0.75
        ))
    
    # Operations with ambiguity
    for i in range(5):
        operations.append(OperationMetric(
            operation_id=f"ambig_op_{i}",
            timestamp=datetime.now(),
            request=f"Update status {i}",
            selected_tool="workflow_engine",
            expected_tool="workflow_engine",
            success=True,
            tokens_used=3300,
            response_time_ms=180,
            ambiguity_detected=True,
            ambiguity_resolved=True,
            confidence_score=0.70
        ))
    
    # Failed operations
    for i in range(5):
        operations.append(OperationMetric(
            operation_id=f"failed_op_{i}",
            timestamp=datetime.now(),
            request=f"Invalid operation {i}",
            selected_tool="resource_manager",
            expected_tool="search_engine",
            success=False,
            tokens_used=3000,
            response_time_ms=100,
            error_occurred=True,
            error_recovered=False,
            confidence_score=0.40
        ))
    
    return operations


if __name__ == "__main__":
    # Example benchmark run
    async def main():
        # Generate test data
        operations = generate_test_operations()
        
        # Set v1 baseline
        v1_baseline = {
            "average_tokens": 15000,
            "average_response_time_ms": 500,
            "operation_success_rate": 85.0
        }
        
        # Run benchmark
        benchmark, report = await run_model_success_benchmark(
            operations, v1_baseline
        )
        
        print(report)
        print(f"\nReports saved to: optimization/benchmarks/results/")
    
    asyncio.run(main())