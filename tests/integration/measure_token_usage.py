#!/usr/bin/env python3
"""Script to measure and compare real token usage between v1 and v2 meta-tools."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.token_measurement import TokenUsageMeasurement
from tests.integration.config import get_test_config, ConfigurationError
from tests.integration.test_data_factory import TestDataFactory


def setup_logging(log_level: str = "INFO"):
    """Set up logging for the measurement script."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("tests/logs/token_measurement.log", mode="w")
        ]
    )


def measure_tool_definitions_only(model: str) -> None:
    """Measure token usage for tool definitions only (no API calls)."""
    print("📊 Measuring tool definition token usage...")

    measurement = TokenUsageMeasurement(model=model)
    v1_tokens, v2_tokens = measurement.measure_tool_definitions_tokens()

    savings = v1_tokens - v2_tokens
    savings_pct = (savings / v1_tokens * 100) if v1_tokens > 0 else 0

    print(f"\n📈 Tool Definition Results:")
    print(f"   V1 Total Tokens: {v1_tokens:,}")
    print(f"   V2 Total Tokens: {v2_tokens:,}")
    print(f"   Token Savings: {savings:,} ({savings_pct:.1f}%)")

    # Generate a simple report
    report = {
        "measurement_type": "tool_definitions_only",
        "model": model,
        "v1_tokens": v1_tokens,
        "v2_tokens": v2_tokens,
        "savings": savings,
        "savings_percentage": savings_pct,
        "v1_tool_count": len(measurement.loader.get_v1_tool_definitions()),
        "v2_tool_count": len(measurement.loader.get_v2_tool_definitions()),
    }

    # Save report
    output_path = "tests/logs/tool_definitions_token_report.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📄 Report saved to: {output_path}")


def simulate_response_measurements(model: str) -> None:
    """Simulate response measurements with sample data (no real API calls)."""
    print("🎭 Simulating response token measurements...")

    measurement = TokenUsageMeasurement(model=model)

    # Simulate typical responses
    simulated_responses = [
        {
            "operation": "create_issue",
            "service": "jira",
            "v1_response": json.dumps({
                "success": True,
                "issue_key": "TEST-123",
                "issue": {
                    "key": "TEST-123",
                    "fields": {
                        "summary": "Test issue created",
                        "description": "This is a test issue",
                        "status": {"name": "Open"},
                        "assignee": {"emailAddress": "test@example.com"},
                        "priority": {"name": "Medium"},
                        "labels": ["test", "integration"],
                        "created": "2023-12-15T10:30:00.000Z",
                        "updated": "2023-12-15T10:30:00.000Z"
                    }
                }
            }, indent=2),
            "v2_response": json.dumps({
                "success": True,
                "service": "jira",
                "operation": "create",
                "resource_type": "issue",
                "results": {
                    "key": "TEST-123",
                    "fields": {
                        "summary": "Test issue created",
                        "description": "This is a test issue",
                        "status": {"name": "Open"},
                        "assignee": {"emailAddress": "test@example.com"},
                        "priority": {"name": "Medium"},
                        "labels": ["test", "integration"],
                        "created": "2023-12-15T10:30:00.000Z",
                        "updated": "2023-12-15T10:30:00.000Z"
                    }
                }
            }, indent=2)
        },
        {
            "operation": "search_issues",
            "service": "jira",
            "v1_response": json.dumps({
                "issues": [
                    {"key": "TEST-1", "fields": {"summary": "First issue", "status": {"name": "Open"}}},
                    {"key": "TEST-2", "fields": {"summary": "Second issue", "status": {"name": "In Progress"}}},
                    {"key": "TEST-3", "fields": {"summary": "Third issue", "status": {"name": "Done"}}}
                ],
                "total": 3,
                "startAt": 0,
                "maxResults": 50
            }, indent=2),
            "v2_response": json.dumps({
                "success": True,
                "service": "jira",
                "query_type": "jql",
                "results": {
                    "issues": [
                        {"key": "TEST-1", "fields": {"summary": "First issue", "status": {"name": "Open"}}},
                        {"key": "TEST-2", "fields": {"summary": "Second issue", "status": {"name": "In Progress"}}},
                        {"key": "TEST-3", "fields": {"summary": "Third issue", "status": {"name": "Done"}}}
                    ],
                    "total": 3,
                    "pagination": {"start": 0, "limit": 50}
                }
            }, indent=2)
        },
        {
            "operation": "create_page",
            "service": "confluence",
            "v1_response": json.dumps({
                "success": True,
                "page_id": "123456",
                "page": {
                    "id": "123456",
                    "title": "Test Page",
                    "space": {"key": "TEST", "name": "Test Space"},
                    "version": {"number": 1},
                    "body": {
                        "storage": {
                            "value": "<h1>Test Page</h1><p>This is a test page content.</p>",
                            "representation": "storage"
                        }
                    },
                    "created": "2023-12-15T10:30:00.000Z",
                    "updated": "2023-12-15T10:30:00.000Z"
                }
            }, indent=2),
            "v2_response": json.dumps({
                "success": True,
                "service": "confluence",
                "operation": "create",
                "resource_type": "page",
                "results": {
                    "id": "123456",
                    "title": "Test Page",
                    "space": {"key": "TEST", "name": "Test Space"},
                    "version": {"number": 1},
                    "content": "# Test Page\n\nThis is a test page content.",
                    "created": "2023-12-15T10:30:00.000Z",
                    "updated": "2023-12-15T10:30:00.000Z"
                }
            }, indent=2)
        },
        {
            "operation": "bulk_update",
            "service": "jira",
            "v1_response": json.dumps({
                "results": [
                    {"issue_key": "TEST-1", "success": True, "updated_fields": ["summary", "description"]},
                    {"issue_key": "TEST-2", "success": True, "updated_fields": ["summary", "assignee"]},
                    {"issue_key": "TEST-3", "success": False, "error": "Permission denied"},
                    {"issue_key": "TEST-4", "success": True, "updated_fields": ["priority", "labels"]},
                    {"issue_key": "TEST-5", "success": True, "updated_fields": ["description"]}
                ],
                "summary": {
                    "total": 5,
                    "successful": 4,
                    "failed": 1,
                    "errors": ["TEST-3: Permission denied"]
                }
            }, indent=2),
            "v2_response": json.dumps({
                "success": True,
                "service": "jira",
                "operation": "bulk_update",
                "resource_type": "issue",
                "results": [
                    {"identifier": "TEST-1", "success": True, "changes": ["summary", "description"]},
                    {"identifier": "TEST-2", "success": True, "changes": ["summary", "assignee"]},
                    {"identifier": "TEST-3", "success": False, "error": "Permission denied"},
                    {"identifier": "TEST-4", "success": True, "changes": ["priority", "labels"]},
                    {"identifier": "TEST-5", "success": True, "changes": ["description"]}
                ],
                "summary": {
                    "processed": 5,
                    "successful": 4,
                    "failed": 1,
                    "success_rate": 0.8
                }
            }, indent=2)
        }
    ]

    # Measure each simulated response
    for response_data in simulated_responses:
        measurement.measure_operation_response_tokens(
            operation=response_data["operation"],
            service=response_data["service"],
            v1_response=response_data["v1_response"],
            v2_response=response_data["v2_response"],
            metadata={"simulation": True}
        )

    # Generate comprehensive report
    report = measurement.generate_comprehensive_report()

    # Save detailed report
    output_path = "tests/logs/token_usage_report.json"
    measurement.save_report(report, output_path)

    # Create markdown summary
    markdown = measurement.create_markdown_summary(report)
    markdown_path = "tests/logs/token_usage_summary.md"
    with open(markdown_path, 'w') as f:
        f.write(markdown)

    print(f"\n📊 Simulation Results:")
    print(f"   Overall Token Savings: {report['summary']['overall_savings_percentage']:.1f}%")
    print(f"   Definition Savings: {report['summary']['definition_savings_percentage']:.1f}%")
    print(f"   Response Savings: {report['summary']['response_savings_percentage']:.1f}%")
    print(f"   📄 Detailed Report: {output_path}")
    print(f"   📝 Markdown Summary: {markdown_path}")


def measure_with_real_api(model: str) -> None:
    """Measure token usage with real API responses (requires configured environment)."""
    print("🌐 Measuring with real API responses...")

    try:
        config = get_test_config()
        if not config.test_environment.enabled:
            print("❌ Real API testing not enabled. Set test_environment.enabled=true in config.")
            return

        factory = TestDataFactory()
        measurement = TokenUsageMeasurement(model=model)

        print("   Creating test resources...")

        # Create a test issue for measurements
        test_issue_key = factory.create_test_issue(
            summary="Token Measurement Test Issue",
            description="This issue is created for token usage measurement testing."
        )

        # Create a test page for measurements
        test_page_id = factory.create_test_page(
            title="Token Measurement Test Page",
            content="# Token Measurement Test Page\n\nThis page is created for testing token usage measurements."
        )

        print(f"   Created test issue: {test_issue_key}")
        print(f"   Created test page: {test_page_id}")

        # TODO: Get actual responses from meta-tools vs individual tools
        # This would require implementing the actual comparison logic
        # For now, we'll use the simulation approach

        print("   ⚠️  Real API measurement not fully implemented yet.")
        print("   Using simulation data for now...")

        simulate_response_measurements(model)

        # Clean up test resources
        print("   Cleaning up test resources...")
        factory.cleanup_all_resources()

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        print("   Use --definitions-only to measure without API calls.")
    except Exception as e:
        print(f"❌ Error during real API measurement: {e}")
        print("   Use --definitions-only to measure without API calls.")


def main():
    """Main measurement script entry point."""
    parser = argparse.ArgumentParser(description="Measure token usage for MCP Atlassian meta-tools")
    parser.add_argument("--model", default="gpt-4", help="LLM model for token counting")
    parser.add_argument("--definitions-only", action="store_true", help="Only measure tool definitions (no API calls)")
    parser.add_argument("--simulate", action="store_true", help="Use simulated responses instead of real API")
    parser.add_argument("--real-api", action="store_true", help="Use real API responses (requires configuration)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # Create logs directory
    os.makedirs("tests/logs", exist_ok=True)
    setup_logging(args.log_level)

    print("🔢 MCP Atlassian Token Usage Measurement")
    print("=" * 50)
    print(f"Model: {args.model}")

    if args.definitions_only:
        measure_tool_definitions_only(args.model)
    elif args.real_api:
        measure_with_real_api(args.model)
    else:
        # Default to simulation
        measure_tool_definitions_only(args.model)
        simulate_response_measurements(args.model)

    print("\n✅ Token measurement completed!")


if __name__ == "__main__":
    sys.exit(main())