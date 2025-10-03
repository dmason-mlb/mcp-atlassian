#!/bin/bash

# MCP Atlassian Test Environment Compatibility Setup
# This script helps users who have shared Atlassian credentials in their .env file
# set up the test environment without duplicating their credentials.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

echo "🔧 MCP Atlassian Test Environment Compatibility Setup"
echo "=" * 60

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ No .env file found at $ENV_FILE"
    echo "   Please create a .env file with your Atlassian credentials first."
    exit 1
fi

echo "✅ Found .env file at $ENV_FILE"

# Source the .env file to check for shared credentials
source "$ENV_FILE"

# Check for required shared credentials
missing_vars=()

if [[ -z "$ATLASSIAN_URL" ]]; then
    missing_vars+=("ATLASSIAN_URL")
fi

if [[ -z "$ATLASSIAN_EMAIL" ]]; then
    missing_vars+=("ATLASSIAN_EMAIL")
fi

if [[ -z "$ATLASSIAN_API_TOKEN" ]]; then
    missing_vars+=("ATLASSIAN_API_TOKEN")
fi

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required shared credentials in .env file:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please add these variables to your .env file:"
    echo "ATLASSIAN_URL=https://your-domain.atlassian.net"
    echo "ATLASSIAN_EMAIL=your-email@example.com"
    echo "ATLASSIAN_API_TOKEN=your-api-token"
    exit 1
fi

echo "✅ Found shared Atlassian credentials:"
echo "   - ATLASSIAN_URL: $ATLASSIAN_URL"
echo "   - ATLASSIAN_EMAIL: $ATLASSIAN_EMAIL"
echo "   - ATLASSIAN_API_TOKEN: [MASKED]"

# Check for optional project/space configuration
if [[ -n "$JIRA_PROJECT" ]]; then
    echo "   - JIRA_PROJECT: $JIRA_PROJECT"
else
    echo "⚠️  JIRA_PROJECT not set, will use default 'TEST'"
fi

if [[ -n "$CONFLUENCE_SPACE" ]]; then
    echo "   - CONFLUENCE_SPACE: $CONFLUENCE_SPACE"
else
    echo "⚠️  CONFLUENCE_SPACE not set, will use default 'TEST'"
fi

echo ""
echo "🧪 Testing configuration compatibility..."

# Test Jira URL derivation
echo "📋 Jira Configuration:"
echo "   - URL: $ATLASSIAN_URL (using shared ATLASSIAN_URL)"
echo "   - Username: $ATLASSIAN_EMAIL (using shared ATLASSIAN_EMAIL)"
echo "   - API Token: [MASKED] (using shared ATLASSIAN_API_TOKEN)"

# Test Confluence URL derivation
CONFLUENCE_DERIVED_URL="$ATLASSIAN_URL"
if [[ ! "$CONFLUENCE_DERIVED_URL" =~ /wiki$ ]]; then
    CONFLUENCE_DERIVED_URL="${CONFLUENCE_DERIVED_URL%/}/wiki"
fi

echo "📄 Confluence Configuration:"
echo "   - URL: $CONFLUENCE_DERIVED_URL (derived from ATLASSIAN_URL + /wiki)"
echo "   - Username: $ATLASSIAN_EMAIL (using shared ATLASSIAN_EMAIL)"
echo "   - API Token: [MASKED] (using shared ATLASSIAN_API_TOKEN)"

echo ""
echo "✅ Configuration compatibility check complete!"
echo ""
echo "📖 How the fallback system works:"
echo "   1. Tests first look for specific variables (e.g., JIRA_TEST_URL)"
echo "   2. If not found, they fall back to shared credentials:"
echo "      - JIRA_TEST_URL → ATLASSIAN_URL"
echo "      - CONFLUENCE_TEST_URL → ATLASSIAN_URL + '/wiki'"
echo "      - JIRA_TEST_USERNAME → ATLASSIAN_EMAIL"
echo "      - CONFLUENCE_TEST_USERNAME → ATLASSIAN_EMAIL"
echo "      - JIRA_TEST_API_TOKEN → ATLASSIAN_API_TOKEN"
echo "      - CONFLUENCE_TEST_API_TOKEN → ATLASSIAN_API_TOKEN"
echo "      - JIRA_TEST_PROJECT → JIRA_PROJECT (or 'TEST' default)"
echo "      - CONFLUENCE_TEST_SPACE → CONFLUENCE_SPACE (or 'TEST' default)"
echo ""
echo "🚀 Ready to run tests! Use:"
echo "   python tests/integration/run_tests.py --resource-manager --verbose"
echo "   python tests/integration/measure_token_usage.py --real-api"
echo ""
echo "🔍 To validate your setup:"
echo "   python tests/integration/setup_integration_tests.py --validate-only"