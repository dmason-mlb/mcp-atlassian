"""Test OAuth detection bug fix in ConfluenceAdapter."""

from requests import Session

from mcp_atlassian.rest.confluence_adapter import ConfluenceAdapter


class TestOAuthDetectionFix:
    """Test cases for OAuth detection logic fix."""

    def test_oauth_detection_without_authorization_header(self):
        """Test that OAuth path is not taken when Authorization header is missing."""
        session = Session()
        # Explicitly ensure no Authorization header
        if "Authorization" in session.headers:
            del session.headers["Authorization"]

        # This should NOT trigger OAuth path due to missing Authorization header
        adapter = ConfluenceAdapter(
            url="https://test.atlassian.net",
            session=session,
            username="testuser",
            password="testpass"
        )

        # Should create basic auth client since no Authorization header
        assert adapter.client.auth_type == "basic"

    def test_oauth_detection_with_authorization_header(self):
        """Test that OAuth path is taken when Authorization header is present."""
        session = Session()
        session.headers["Authorization"] = "Bearer mock-token"

        adapter = ConfluenceAdapter(
            url="https://test.atlassian.net",
            session=session,
        )

        # Should create OAuth client due to Authorization header
        assert adapter.client.auth_type == "oauth"

    def test_oauth_detection_with_empty_session_headers(self):
        """Test OAuth detection when session has no headers attribute."""
        session = Session()
        # Remove headers to test the hasattr check
        if hasattr(session, "headers"):
            delattr(session, "headers")

        adapter = ConfluenceAdapter(
            url="https://test.atlassian.net",
            session=session,
            username="testuser",
            password="testpass"
        )

        # Should fallback to basic auth when no headers attribute
        assert adapter.client.auth_type == "basic"

    def test_pat_auth_with_token(self):
        """Test that PAT auth is used when token is provided."""
        adapter = ConfluenceAdapter(
            url="https://test.atlassian.net",
            token="test-pat-token",
        )

        assert adapter.client.auth_type == "pat"

    def test_basic_auth_fallback(self):
        """Test that basic auth is used as fallback."""
        adapter = ConfluenceAdapter(
            url="https://test.atlassian.net",
            username="testuser",
            password="testpass",
        )

        assert adapter.client.auth_type == "basic"
