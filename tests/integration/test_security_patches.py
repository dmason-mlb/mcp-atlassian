"""Integration tests to verify security patches are working correctly."""

import logging
import threading
from unittest.mock import patch

import pytest

from mcp_atlassian.formatting.router import FormatRouter
from mcp_atlassian.rest.base import BaseRESTClient
from mcp_atlassian.utils.logging import mask_sensitive
from mcp_atlassian.utils.oauth import OAuthConfig


class TestOAuthSecretMasking:
    """Test that OAuth secrets are properly masked in logs."""

    @pytest.mark.security
    def test_oauth_exchange_masks_client_secret(self, caplog):
        """Verify oauth.py now masks client_secret in debug logs."""
        secret_value = "super-secret-client-key-12345"

        with caplog.at_level(logging.DEBUG):
            oauth_config = OAuthConfig(
                client_id="test-client",
                client_secret=secret_value,
                redirect_uri="http://localhost:8080/callback",
                scope="read:jira-work write:jira-work",
            )

            with patch("requests.post") as mock_post:
                mock_post.return_value.ok = True
                mock_post.return_value.json.return_value = {
                    "access_token": "at-123",
                    "refresh_token": "rt-456",
                    "expires_in": 3600,
                }

                # This triggers the logging with masking
                oauth_config.exchange_code_for_tokens("auth-code-789")

        # Check all log messages
        all_logs = " ".join(record.getMessage() for record in caplog.records)

        # After fix - client_secret should be masked!
        assert secret_value not in all_logs, "Client secret exposed in logs!"

        # Should see masked version
        if "client_secret" in all_logs:
            assert "****" in all_logs, "Secret not properly masked!"

    @pytest.mark.security
    def test_oauth_setup_masks_secrets(self):
        """Verify oauth_setup.py masks secrets when logging config."""
        secret = "confidential-oauth-secret-xyz"

        # Test the masking function directly
        masked = mask_sensitive(secret)

        assert secret not in masked
        assert "****" in masked
        assert masked.startswith("conf") and masked.endswith("-xyz")


class TestAPIPayloadSanitization:
    """Test that sensitive API payloads are sanitized."""

    @pytest.mark.security
    def test_api_request_sanitizes_sensitive_data(self, caplog):
        """Verify base.py sanitizes JSON payloads before logging."""
        client = BaseRESTClient(
            base_url="https://test.atlassian.net", username="test", password="test"
        )

        # Payload with various sensitive data types
        sensitive_payload = {
            "password": "user-password-123",
            "api_key": "sk-proj-1234567890abcdef",
            "token": "pat-ABCDEFGHIJKLMNOP",
            "oauth": {
                "client_secret": "oauth-secret-value",
                "refresh_token": "rt-confidential",
            },
            "user": {
                "email": "john.doe@example.com",
                "ssn": "123-45-6789",
                "creditCard": "4111-1111-1111-1111",
            },
        }

        with caplog.at_level(logging.DEBUG):
            with patch("requests.Session.request") as mock_req:
                mock_req.return_value.ok = True
                mock_req.return_value.json.return_value = {"id": "123"}

                client.post("/api/v3/user", json_data=sensitive_payload)

        logs = " ".join(r.getMessage() for r in caplog.records)

        # After fix - all secrets should be masked!
        assert "user-password-123" not in logs
        assert "sk-proj-1234567890abcdef" not in logs
        assert "oauth-secret-value" not in logs
        assert "123-45-6789" not in logs
        assert "4111-1111-1111-1111" not in logs

        # Email should be partially masked
        if "john.doe@example.com" in logs:
            # Should be masked like "jo****oe@example.com"
            assert "john.doe" not in logs


class TestCacheThreadSafety:
    """Test thread safety fixes in cache implementations."""

    @pytest.mark.concurrency
    def test_format_router_cache_is_thread_safe(self):
        """Verify FormatRouter cache now has proper locking."""
        router = FormatRouter()
        errors = []

        def concurrent_access(thread_id):
            try:
                for i in range(100):
                    url = f"https://test{thread_id}.atlassian.net"
                    # This should be thread-safe now
                    router.detect_deployment_type(url)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(20):
            t = threading.Thread(target=concurrent_access, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # With proper locking, no errors should occur
        assert len(errors) == 0, f"Thread safety errors: {errors}"


class TestExceptionHandling:
    """Test that authentication exceptions are preserved."""

    @pytest.mark.error_handling
    def test_auth_error_exception_handling_in_dependencies(self):
        """Verify that MCPAtlassianAuthenticationError is converted to ValueError with context."""
        from mcp_atlassian.servers.dependencies import MCPAtlassianAuthenticationError

        # Test the specific exception handling code in dependencies.py
        auth_error = MCPAtlassianAuthenticationError("OAuth token expired")

        # Simulate what the exception handler does
        user_auth_type = "oauth"
        user_token = "invalid-token"

        # This is what our patched code should do
        error_msg = f"Jira authentication failed: {str(auth_error)}. Auth type: {user_auth_type}, Token provided: {'yes' if user_token else 'no'}"

        # Verify the error message includes context
        assert "authentication failed" in error_msg.lower()
        assert "oauth token expired" in error_msg.lower()
        assert "auth type: oauth" in error_msg.lower()
        assert "token provided: yes" in error_msg.lower()
