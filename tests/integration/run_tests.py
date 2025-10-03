#!/usr/bin/env python3
"""Test runner for MCP Atlassian real API integration tests."""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_setup():
    """Run the setup script to validate configuration and create test resources."""
    print("🚀 Running integration test setup...")
    setup_script = Path(__file__).parent / "setup_integration_tests.py"
    result = subprocess.run([sys.executable, str(setup_script), "--all"], capture_output=False)
    return result.returncode == 0


def run_tests(test_filter=None, verbose=False, log_level="INFO"):
    """Run the integration tests."""
    print("🧪 Running integration tests...")

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/integration/test_meta_tools_real_api.py"]

    if test_filter:
        cmd.extend(["-k", test_filter])

    if verbose:
        cmd.append("-v")

    # Add logging configuration
    cmd.extend(["--log-cli-level", log_level])

    # Run with real-time output
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def cleanup_resources():
    """Clean up test resources."""
    print("🧹 Cleaning up test resources...")
    setup_script = Path(__file__).parent / "setup_integration_tests.py"
    result = subprocess.run([sys.executable, str(setup_script), "--cleanup"], capture_output=False)
    return result.returncode == 0


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Run MCP Atlassian real API integration tests")
    parser.add_argument("--setup", action="store_true", help="Run setup before tests")
    parser.add_argument("--cleanup", action="store_true", help="Clean up resources after tests")
    parser.add_argument("--test-filter", "-k", help="Filter tests by name/pattern")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--setup-only", action="store_true", help="Run setup only")
    parser.add_argument("--cleanup-only", action="store_true", help="Run cleanup only")
    parser.add_argument("--resource-manager", action="store_true", help="Run ResourceManager tests only")
    parser.add_argument("--all-meta-tools", action="store_true", help="Run all meta-tool tests")

    args = parser.parse_args()

    # Set environment variable for test configuration
    os.environ.setdefault("TEST_ENVIRONMENT", "development")

    success = True

    # Handle specific actions
    if args.setup_only:
        return 0 if run_setup() else 1

    if args.cleanup_only:
        return 0 if cleanup_resources() else 1

    # Build test filter
    test_filter = args.test_filter
    if args.resource_manager:
        test_filter = "TestResourceManagerRealAPI"
    elif args.all_meta_tools:
        test_filter = "RealAPI"

    # Run setup if requested
    if args.setup:
        success = run_setup()
        if not success:
            print("❌ Setup failed, aborting tests")
            return 1

    # Run tests
    if success:
        success = run_tests(test_filter, args.verbose, args.log_level)

    # Run cleanup if requested
    if args.cleanup:
        cleanup_success = cleanup_resources()
        if not cleanup_success:
            print("⚠️  Cleanup failed, but test results are still valid")

    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())