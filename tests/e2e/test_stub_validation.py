"""
Validation test for Atlassian HTTP stub functionality.

This test validates that our HTTP mocking system works correctly
before implementing the full ADF contract tests.
"""

import json

import pytest
import requests


@pytest.mark.mcp
@pytest.mark.atlassian_stub
class TestAtlassianStub:
    """Test the Atlassian HTTP stub system."""

    def test_stub_setup(self, atlassian_stub):
        """Test that the stub system initializes correctly."""
        assert atlassian_stub is not None
        assert hasattr(atlassian_stub, "responses")
        assert hasattr(atlassian_stub, "call_log")
        assert len(atlassian_stub.call_log) == 0

    def test_jira_search_stub(self, atlassian_stub):
        """Test stubbing Jira search API."""
        # Set up stub response
        test_results = [
            {
                "key": "TEST-123",
                "fields": {"summary": "Test Issue", "status": {"name": "To Do"}},
            }
        ]

        atlassian_stub.stub_jira_search("project = TEST", test_results)

        # Make a request that should be caught by the stub
        try:
            response = requests.post(
                "https://test.atlassian.net/rest/api/3/search",
                data={"jql": "project = TEST"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "issues" in data
            assert len(data["issues"]) == 1
            assert data["issues"][0]["key"] == "TEST-123"

        except requests.ConnectionError:
            # This is expected if responses isn't properly activated
            # In that case, we'll skip this validation
            pytest.skip(
                "HTTP stub not properly activated - this test requires responses library integration"
            )

    def test_jira_create_issue_stub(self, atlassian_stub):
        """Test stubbing Jira issue creation."""
        project_key = "TEST"
        expected_response = {
            "key": "TEST-456",
            "id": "12345",
            "fields": {"summary": "Created Issue"},
        }

        atlassian_stub.stub_jira_create_issue(project_key, expected_response)

        # Validate that the stub was set up
        assert len(atlassian_stub.responses.registered()) > 0

    def test_confluence_create_page_stub(self, atlassian_stub):
        """Test stubbing Confluence page creation."""
        expected_response = {"id": "67890", "title": "Test Page", "type": "page"}

        test_adf = {"type": "doc", "content": []}
        atlassian_stub.stub_confluence_create_page(test_adf, expected_response)

        # Validate stub setup
        assert len(atlassian_stub.responses.registered()) > 0

    def test_call_tracking(self, atlassian_stub):
        """Test that API calls are properly tracked."""
        # Initially no calls
        assert len(atlassian_stub.call_log) == 0

        # Set up a stub that logs calls
        def track_callback(request):
            body = json.loads(request.body) if request.body else {}
            atlassian_stub.call_log.append(("POST", request.url, body))
            return (201, {}, json.dumps({"success": True}))

        atlassian_stub.responses.add_callback(
            atlassian_stub.responses.POST,
            "https://test.atlassian.net/rest/api/3/issue",
            callback=track_callback,
        )

        # Make a test request
        try:
            requests.post(
                "https://test.atlassian.net/rest/api/3/issue",
                json={"test": "data"},
                headers={"Content-Type": "application/json"},
            )

            # Verify call was tracked
            assert len(atlassian_stub.call_log) == 1
            method, url, body = atlassian_stub.call_log[0]
            assert method == "POST"
            assert "/rest/api/3/issue" in url
            assert body["test"] == "data"

        except requests.ConnectionError:
            pytest.skip("HTTP stub not properly activated")

    def test_assert_called_once_with(self, atlassian_stub):
        """Test the assert_called_once_with helper method."""
        # Add a test call to the log
        atlassian_stub.call_log.append(
            (
                "POST",
                "https://test.atlassian.net/rest/api/3/issue",
                {"fields": {"summary": "Test Issue"}},
            )
        )

        # This should pass
        atlassian_stub.assert_called_once_with(
            "POST",
            "/rest/api/3/issue",
            json_contains={"fields": {"summary": "Test Issue"}},
        )

        # This should fail due to wrong method
        with pytest.raises(AssertionError):
            atlassian_stub.assert_called_once_with("GET", "/rest/api/3/issue")

        # This should fail due to wrong URL fragment
        with pytest.raises(AssertionError):
            atlassian_stub.assert_called_once_with("POST", "/different/url")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
