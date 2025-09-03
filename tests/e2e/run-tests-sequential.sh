#!/bin/bash

# Sequential E2E Test Runner
# Runs MCP contract tests first, then Playwright visual tests
# This prevents event loop conflicts between pytest-asyncio and pytest-playwright

set -e  # Exit on any command failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE} MCP Atlassian E2E Test Suite (Sequential)${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Initialize counters
mcp_exit_code=0
visual_exit_code=0
total_tests=0
total_passed=0
total_failed=0

# Step 1: Run MCP Contract Tests
echo -e "${BLUE}[1/2] Running MCP Contract Tests...${NC}"
echo -e "${YELLOW}Using pytest-mcp.ini configuration${NC}"
echo

export TEST_MODE="mcp"
pytest -c pytest-mcp.ini -v
mcp_exit_code=$?
if [ $mcp_exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ MCP contract tests PASSED${NC}"
else
    echo -e "${RED}❌ MCP contract tests FAILED${NC}"
fi

echo
echo -e "${BLUE}========================================${NC}"
echo

# Step 2: Run Playwright Visual Tests
echo -e "${BLUE}[2/2] Running Playwright Visual Tests...${NC}"
echo -e "${YELLOW}Using pytest-visual.ini configuration${NC}"
echo

export TEST_MODE="visual"
pytest -c pytest-visual.ini -v
visual_exit_code=$?
if [ $visual_exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Playwright visual tests PASSED${NC}"
else
    echo -e "${RED}❌ Playwright visual tests FAILED${NC}"
fi

echo
echo -e "${BLUE}========================================${NC}"

# Final summary
echo -e "${BLUE} Test Execution Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $mcp_exit_code -eq 0 ]; then
    echo -e "MCP Contract Tests:    ${GREEN}PASSED${NC}"
else
    echo -e "MCP Contract Tests:    ${RED}FAILED (exit code: $mcp_exit_code)${NC}"
fi

if [ $visual_exit_code -eq 0 ]; then
    echo -e "Playwright Visual Tests: ${GREEN}PASSED${NC}"
else
    echo -e "Playwright Visual Tests: ${RED}FAILED (exit code: $visual_exit_code)${NC}"
fi

echo
echo -e "${BLUE}Reports:${NC}"
echo -e "  MCP Report:    .artifacts/mcp-report.html"
echo -e "  Visual Report: .artifacts/visual-report.html"
echo

# Determine overall exit code
overall_exit_code=0
if [ $mcp_exit_code -ne 0 ] || [ $visual_exit_code -ne 0 ]; then
    overall_exit_code=1
    echo -e "${RED}Overall Result: FAILED${NC}"
else
    echo -e "${GREEN}Overall Result: PASSED${NC}"
fi

# Clean up environment
unset TEST_MODE

echo -e "${BLUE}========================================${NC}"
exit $overall_exit_code