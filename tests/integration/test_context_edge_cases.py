"""
Edge case tests for context handling functionality.

This module tests edge cases and error scenarios for the context fix
that addresses the "'Server' object has no attribute 'lifespan_context'"
error from the QA report.

Tests verify:
- Handling of None/invalid server objects
- Missing attributes in server structure
- Malformed lifespan_context data
- Thread safety of context creation
- Memory management and cleanup
- Concurrent access patterns
- Error propagation and recovery
"""

import asyncio
import threading
import time
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from src.mcp_atlassian.servers.main import AtlassianMCP, get_tool_context


@pytest.mark.edge_case
@pytest.mark.integration
class TestContextEdgeCases:
    """Test suite for edge cases in context handling."""

    def test_context_with_none_server(self):
        """Test context creation with None server."""
        # This should not crash
        context = get_tool_context(None)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_missing_mcp_server(self):
        """Test context creation when server._mcp_server is missing."""
        server = MagicMock()
        del server._mcp_server

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_none_mcp_server(self):
        """Test context creation when server._mcp_server is None."""
        server = MagicMock()
        server._mcp_server = None

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_missing_request_context(self):
        """Test context creation when request_context is missing."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        del server._mcp_server.request_context

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_none_request_context(self):
        """Test context creation when request_context is None."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = None

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_missing_lifespan_context(self):
        """Test context creation when lifespan_context is missing."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        del server._mcp_server.request_context.lifespan_context

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_none_lifespan_context(self):
        """Test context creation when lifespan_context is None."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = None

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        # Should preserve None value (dependencies.py handles this correctly)
        assert context.lifespan_context is None

    def test_context_with_empty_lifespan_context(self):
        """Test context creation with empty lifespan_context."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {}

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_valid_lifespan_context(self):
        """Test context creation with valid lifespan_context."""
        app_context = {"test": "data"}
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": app_context
        }

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {"app_lifespan_context": app_context}

    def test_context_with_malformed_lifespan_context(self):
        """Test context creation with malformed lifespan_context."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        # Set lifespan_context to a non-dict value
        server._mcp_server.request_context.lifespan_context = "invalid"

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        # Should still return the value even if it's not a dict
        assert context.lifespan_context == "invalid"

    def test_context_with_invalid_server_type(self):
        """Test context creation with invalid server type."""
        # Test with various invalid types
        invalid_servers = [
            "string_server",
            123,
            [],
            {"dict": "server"},
            lambda: "function_server"
        ]

        for invalid_server in invalid_servers:
            context = get_tool_context(invalid_server)
            assert hasattr(context, 'lifespan_context')
            assert context.lifespan_context == {}

    def test_context_thread_safety(self):
        """Test that context creation is thread-safe."""
        results = []
        errors = []

        def create_context_worker(server_id: int):
            try:
                # Create different servers for each thread
                server = MagicMock()
                server._mcp_server = MagicMock()
                server._mcp_server.request_context = MagicMock()
                server._mcp_server.request_context.lifespan_context = {
                    "app_lifespan_context": {"server_id": server_id}
                }

                context = get_tool_context(server)
                results.append((server_id, context.lifespan_context))
            except Exception as e:
                errors.append((server_id, e))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_context_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Thread safety test failed with errors: {errors}"
        assert len(results) == 10, f"Expected 10 results, got {len(results)}"

        # Verify each thread got its correct context
        for server_id, lifespan_context in results:
            expected_context = {"app_lifespan_context": {"server_id": server_id}}
            assert lifespan_context == expected_context

    def test_context_memory_management(self):
        """Test that context objects don't leak memory."""
        import gc
        import weakref

        contexts = []
        weak_refs = []

        # Create many contexts
        for i in range(100):
            server = MagicMock()
            server._mcp_server = MagicMock()
            server._mcp_server.request_context = MagicMock()
            server._mcp_server.request_context.lifespan_context = {"test": f"data_{i}"}

            context = get_tool_context(server)
            contexts.append(context)
            weak_refs.append(weakref.ref(context))

        # Clear references
        del contexts
        gc.collect()

        # Check that some objects were garbage collected
        # (We can't guarantee all will be collected due to test framework overhead)
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        assert alive_count < 100, f"Memory leak detected: {alive_count}/100 contexts still alive"

    def test_context_with_exception_in_attribute_access(self):
        """Test context creation when attribute access raises exceptions."""
        class ExceptionRaisingMock:
            def __getattr__(self, name):
                if name == "request_context":
                    raise RuntimeError("Simulated attribute access error")
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        server = MagicMock()
        server._mcp_server = ExceptionRaisingMock()

        # This should not crash, should return empty context
        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context == {}

    def test_context_with_circular_references(self):
        """Test context creation with circular references in server structure."""
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()

        # Create circular reference
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": {"server": server}
        }

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert "app_lifespan_context" in context.lifespan_context
        # Should handle circular reference gracefully

    def test_context_performance_under_load(self):
        """Test context creation performance under high load."""
        import time

        start_time = time.time()

        # Create many contexts quickly
        for i in range(1000):
            server = MagicMock()
            server._mcp_server = MagicMock()
            server._mcp_server.request_context = MagicMock()
            server._mcp_server.request_context.lifespan_context = {"test": f"data_{i}"}

            context = get_tool_context(server)
            assert hasattr(context, 'lifespan_context')

        elapsed_time = time.time() - start_time

        # Should be able to create 1000 contexts in under 1 second
        assert elapsed_time < 1.0, f"Context creation too slow: {elapsed_time:.3f}s for 1000 contexts"

    def test_context_with_deeply_nested_structure(self):
        """Test context creation with deeply nested lifespan_context."""
        # Create deeply nested structure
        nested_data = {"level": 0}
        current = nested_data
        for i in range(1, 100):
            current["nested"] = {"level": i}
            current = current["nested"]

        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": nested_data
        }

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert context.lifespan_context["app_lifespan_context"]["level"] == 0

    def test_context_with_large_data_structure(self):
        """Test context creation with large data in lifespan_context."""
        # Create large data structure
        large_data = {
            "configs": {f"config_{i}": f"value_{i}" for i in range(1000)},
            "cache": {f"cache_key_{i}": f"cache_value_{i}" for i in range(1000)},
            "metadata": "x" * 10000  # Large string
        }

        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": large_data
        }

        context = get_tool_context(server)

        assert hasattr(context, 'lifespan_context')
        assert "app_lifespan_context" in context.lifespan_context
        assert len(context.lifespan_context["app_lifespan_context"]["configs"]) == 1000

    def test_context_prevents_original_error(self):
        """Test that the context fix prevents the original AttributeError."""
        # This reproduces the exact error pattern from the QA report
        server = MagicMock(spec=AtlassianMCP)
        mock_mcp_server = MagicMock()
        mock_request_context = MagicMock()
        mock_request_context.lifespan_context = {"app_lifespan_context": "test"}
        mock_mcp_server.request_context = mock_request_context
        server._mcp_server = mock_mcp_server

        # The old pattern that was failing: server._mcp_server.lifespan_context
        # This would throw: "'Server' object has no attribute 'lifespan_context'"

        # The new pattern should work:
        context = get_tool_context(server)

        # This should NOT throw AttributeError
        try:
            lifespan_ctx = context.lifespan_context
            app_ctx = lifespan_ctx.get("app_lifespan_context") if isinstance(lifespan_ctx, dict) else None
            assert app_ctx == "test"
        except AttributeError as e:
            if "lifespan_context" in str(e):
                pytest.fail(f"Original QA error still present: {e}")
            else:
                raise

    def test_context_error_isolation(self):
        """Test that context creation errors don't propagate to other contexts."""
        # Create a context that might cause issues
        problematic_server = MagicMock()
        problematic_server._mcp_server = None

        # Create a normal context
        normal_server = MagicMock()
        normal_server._mcp_server = MagicMock()
        normal_server._mcp_server.request_context = MagicMock()
        normal_server._mcp_server.request_context.lifespan_context = {"test": "data"}

        # Both should work independently
        problematic_context = get_tool_context(problematic_server)
        normal_context = get_tool_context(normal_server)

        assert problematic_context.lifespan_context == {}
        assert normal_context.lifespan_context == {"test": "data"}

    def test_context_concurrent_access(self):
        """Test concurrent access to the same server context."""
        # Create a shared server
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {"shared": "data"}

        results = []
        errors = []

        def access_context_worker():
            try:
                for _ in range(100):
                    context = get_tool_context(server)
                    assert context.lifespan_context == {"shared": "data"}
                results.append("success")
            except Exception as e:
                errors.append(e)

        # Create multiple threads accessing the same server
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_context_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Concurrent access failed: {errors}"
        assert len(results) == 5, f"Expected 5 successful workers, got {len(results)}"

    def test_context_immutability_safety(self):
        """Test that modifications to context don't affect the original server."""
        app_context = {"original": "data"}
        server = MagicMock()
        server._mcp_server = MagicMock()
        server._mcp_server.request_context = MagicMock()
        server._mcp_server.request_context.lifespan_context = {
            "app_lifespan_context": app_context
        }

        # Get context and modify it
        context = get_tool_context(server)
        context.lifespan_context["modified"] = "value"

        # Original server should be unaffected
        original_lifespan_context = server._mcp_server.request_context.lifespan_context
        assert "modified" not in original_lifespan_context
        assert original_lifespan_context == {"app_lifespan_context": app_context}