#!/usr/bin/env python3
"""Debug why body field is still missing from schema."""

import os
import sys
from pathlib import Path

# Set environment
os.environ["ATLASSIAN_URL"] = "https://your-domain.atlassian.net"
os.environ["ATLASSIAN_EMAIL"] = "user@example.com"
os.environ["ATLASSIAN_API_TOKEN"] = "ATATT3xFfGF0abcd1234efgh5678ijklmnopqrstuvwxyz"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_parameter_flow():
    """Debug the parameter optimization flow."""
    print("🔍 DEBUGGING PARAMETER OPTIMIZATION FLOW")
    print("=" * 50)

    try:
        from src.mcp_atlassian.meta_tools.parameter_optimizer import get_parameter_optimizer

        optimizer = get_parameter_optimizer()

        print("📋 Testing parameter optimizer...")

        # Test get_recommended_parameters
        recommended = optimizer.get_recommended_parameters(
            service="confluence",
            resource="page",
            operation="create"
        )

        print(f"✅ Recommended parameters: {recommended}")

        # Check fallback method directly
        print(f"\n🔍 Testing fallback parameters...")
        fallback = optimizer._get_fallback_parameters("confluence", "page", "create")
        print(f"✅ Fallback parameters: {fallback}")

        # Check if body is in any of them
        if "body" in recommended:
            print("✅ Body found in recommended parameters")
        else:
            print("❌ Body NOT found in recommended parameters")

        if "body" in fallback:
            print("✅ Body found in fallback parameters")
        else:
            print("❌ Body NOT found in fallback parameters")

        return recommended, fallback

    except Exception as e:
        print(f"❌ Error in parameter optimizer: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def debug_schema_generation():
    """Debug the schema generation process."""
    print(f"\n🔍 DEBUGGING SCHEMA GENERATION")
    print("=" * 50)

    try:
        from src.mcp_atlassian.meta_tools.schema_discovery import SchemaDiscovery

        discovery = SchemaDiscovery()

        # Manually call the optimization method to see what happens
        schema = discovery._generate_optimized_schema(
            service="confluence",
            resource="page",
            operation="create"
        )

        print(f"✅ Generated schema successfully")
        print(f"   Required fields: {schema.required}")
        print(f"   All fields: {list(schema.fields.keys())}")

        # Check required field detection
        print(f"\n🔍 Testing required field detection...")
        for field in ["space_key", "title", "body"]:
            is_required = discovery._is_field_required_optimized(field, "create")
            status = "✅" if is_required else "❌"
            print(f"   {status} {field} is required: {is_required}")

        return schema

    except Exception as e:
        print(f"❌ Error in schema generation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🐛 DEBUGGING SCHEMA DISCOVERY ISSUE")
    print("Finding out why body field is still missing")
    print("")

    # Debug parameter optimizer
    recommended, fallback = debug_parameter_flow()

    # Debug schema generation
    schema = debug_schema_generation()

    print(f"\n" + "=" * 50)
    print("🔬 ANALYSIS:")

    if "body" in fallback:
        print("✅ Fallback includes body field")
    else:
        print("❌ Fallback missing body field")

    if "body" in recommended:
        print("✅ Recommended includes body field")
    else:
        print("❌ Recommended missing body field")

    if schema and "body" in schema.fields:
        print("✅ Schema includes body field")
    else:
        print("❌ Schema missing body field")

    print("\n💡 This will help identify where the issue is!")