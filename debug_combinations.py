#!/usr/bin/env python3
"""Debug the combinations registry loading."""

import os
import sys
from pathlib import Path

# Set environment
os.environ["ATLASSIAN_URL"] = "https://your-domain.atlassian.net"
os.environ["ATLASSIAN_EMAIL"] = "user@example.com"
os.environ["ATLASSIAN_API_TOKEN"] = "ATATT3xFfGF0abcd1234efgh5678ijklmnopqrstuvwxyz"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_combinations():
    """Debug the combinations registry."""
    print("🔍 DEBUGGING COMBINATIONS REGISTRY")
    print("=" * 50)

    try:
        from src.mcp_atlassian.meta_tools.parameter_optimizer import get_parameter_optimizer

        optimizer = get_parameter_optimizer()

        print("📋 Checking combinations registry...")
        combinations = optimizer.combinations
        print(f"✅ Combinations loaded: {len(combinations)} entries")

        for key, value in combinations.items():
            print(f"   {key}: {value}")

        # Check the specific key we're looking for
        resource_key = "confluence_page_operations"
        if resource_key in combinations:
            print(f"\n✅ Found {resource_key}: {combinations[resource_key]}")
        else:
            print(f"\n❌ Missing {resource_key}")

        # Check if this is why fallback isn't being used
        lookup_key = "confluence_page_operations"
        print(f"\n🔍 Testing lookup for '{lookup_key}':")
        if lookup_key in combinations:
            params = combinations[lookup_key].copy()
            print(f"✅ Found in registry: {params}")
        else:
            fallback = optimizer._get_fallback_parameters("confluence", "page", "create")
            print(f"❌ Not in registry, using fallback: {fallback}")

        return combinations

    except Exception as e:
        print(f"❌ Error checking combinations: {e}")
        import traceback
        traceback.print_exc()
        return {}

def debug_parameter_method():
    """Debug the get_recommended_parameters method step by step."""
    print(f"\n🔍 DEBUGGING get_recommended_parameters")
    print("=" * 50)

    try:
        from src.mcp_atlassian.meta_tools.parameter_optimizer import get_parameter_optimizer

        optimizer = get_parameter_optimizer()

        # Simulate the method step by step
        service = "confluence"
        resource = "page"
        operation = "create"

        resource_key = f"{service}_{resource}_operations"
        print(f"📝 Looking for resource key: {resource_key}")

        combinations = optimizer.combinations
        print(f"📋 Available combinations: {list(combinations.keys())}")

        if resource_key in combinations:
            base_params = combinations[resource_key].copy()
            print(f"✅ Found in combinations: {base_params}")
        else:
            base_params = optimizer._get_fallback_parameters(service, resource, operation)
            print(f"❌ Not found, using fallback: {base_params}")

        # Add operation-specific parameters
        print(f"\n🔧 Adding operation-specific parameters for '{operation}'...")
        if operation in ["create", "update"]:
            base_params.extend(["dry_run"])
            print(f"   Added dry_run: {base_params}")

        # Remove duplicates
        final_params = list(dict.fromkeys(base_params))
        print(f"\n📄 Final parameters: {final_params}")

        return final_params

    except Exception as e:
        print(f"❌ Error in parameter method debug: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("🐛 DEBUGGING COMBINATIONS REGISTRY ISSUE")
    print("Finding out why fallback isn't being used")
    print("")

    # Debug combinations loading
    combinations = debug_combinations()

    # Debug parameter method
    final_params = debug_parameter_method()

    print(f"\n" + "=" * 50)
    print("🔬 SUMMARY:")
    if "body" in final_params:
        print("✅ Body found in final parameters")
    else:
        print("❌ Body still missing from final parameters")

    print("💡 This should reveal why the registry override isn't working!")