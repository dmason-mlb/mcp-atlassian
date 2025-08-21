#!/bin/bash
set -e

# Navigate to project root
cd "$(dirname "$0")/../.."

echo "Starting MCP server on port 9001..."
uv run mcp-atlassian --transport streamable-http --port 9001 &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "Shutting down MCP server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Wait for server to be ready
echo "Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:9001/healthz > /dev/null 2>&1; then
        echo "Server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Server did not start within 30 seconds"
        exit 1
    fi
    echo "Waiting... ($i/30)"
    sleep 1
done

# Check if server is still running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Server failed to start"
    exit 1
fi

echo "Running seed script..."
cd tests/e2e
uv run python seed/seed.py

echo "Seed completed successfully"