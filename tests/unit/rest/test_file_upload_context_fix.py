"""Test file upload context manager fix in JiraV3Client."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from mcp_atlassian.rest.jira_v3 import JiraV3Client


class TestFileUploadContextFix:
    """Test cases for file upload context manager fix."""

    @pytest.fixture
    def jira_client(self):
        """Create a JiraV3Client for testing."""
        client = JiraV3Client(
            base_url="https://test.atlassian.net",
            auth_type="basic",
            username="test",
            password="test",
        )
        return client

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for upload testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test file content")
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_successful_file_upload_with_context_manager(self, jira_client, temp_file):
        """Test that file upload uses context manager correctly."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "12345", "filename": "test.txt"}]
        mock_response.raise_for_status.return_value = None

        with patch.object(
            jira_client.session, "post", return_value=mock_response
        ) as mock_post:
            result = jira_client.add_attachment("TEST-123", temp_file)

            # Verify the request was made
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Check that URL is correct
            expected_url = (
                f"{jira_client.base_url}/rest/api/3/issue/TEST-123/attachments"
            )
            assert call_args[0][0] == expected_url

            # Check that files parameter has correct structure
            files = call_args[1]["files"]
            assert "file" in files
            filename, file_handle, mime_type = files["file"]
            assert filename == os.path.basename(temp_file)
            assert mime_type == "text/plain"

            # Verify headers
            headers = call_args[1]["headers"]
            assert headers["X-Atlassian-Token"] == "no-check"
            assert headers["Content-Type"] is None

            # Verify response
            assert result == [{"id": "12345", "filename": "test.txt"}]

    def test_file_not_found_error(self, jira_client):
        """Test that FileNotFoundError is raised for non-existent files."""
        non_existent_file = "/path/to/non/existent/file.txt"

        with pytest.raises(FileNotFoundError, match="File not found"):
            jira_client.add_attachment("TEST-123", non_existent_file)

    def test_file_handle_closed_after_upload(self, jira_client, temp_file):
        """Test that file handle is properly closed after upload."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "12345"}]
        mock_response.raise_for_status.return_value = None

        # Track file handle state
        original_open = open
        file_handle_refs = []

        def tracking_open(*args, **kwargs):
            handle = original_open(*args, **kwargs)
            file_handle_refs.append(handle)
            return handle

        with patch("builtins.open", side_effect=tracking_open):
            with patch.object(jira_client.session, "post", return_value=mock_response):
                jira_client.add_attachment("TEST-123", temp_file)

        # Verify file handles were opened and are now closed
        assert len(file_handle_refs) == 1
        assert file_handle_refs[0].closed

    def test_file_handle_closed_on_exception(self, jira_client, temp_file):
        """Test that file handle is properly closed even when upload fails."""
        # Track file handle state
        original_open = open
        file_handle_refs = []

        def tracking_open(*args, **kwargs):
            handle = original_open(*args, **kwargs)
            file_handle_refs.append(handle)
            return handle

        # Mock session.post to raise an exception
        with patch("builtins.open", side_effect=tracking_open):
            with patch.object(
                jira_client.session, "post", side_effect=Exception("Upload failed")
            ):
                with pytest.raises(Exception, match="Upload failed"):
                    jira_client.add_attachment("TEST-123", temp_file)

        # Verify file handle was opened and is now closed despite exception
        assert len(file_handle_refs) == 1
        assert file_handle_refs[0].closed

    def test_mime_type_detection(self, jira_client):
        """Test MIME type detection for different file types."""
        test_files = [
            ("test.txt", "text/plain"),
            ("test.json", "application/json"),
            ("test.pdf", "application/pdf"),
            ("test.png", "image/png"),
            ("unknown_extension", "application/octet-stream"),
        ]

        for filename, expected_mime in test_files:
            with tempfile.NamedTemporaryFile(
                suffix=f".{filename.split('.')[-1]}" if "." in filename else "",
                delete=False,
            ) as f:
                f.write(b"test content")
                temp_path = f.name

            try:
                # Mock successful response
                mock_response = MagicMock()
                mock_response.json.return_value = [{"id": "12345"}]
                mock_response.raise_for_status.return_value = None

                with patch.object(
                    jira_client.session, "post", return_value=mock_response
                ) as mock_post:
                    jira_client.add_attachment("TEST-123", temp_path)

                    # Check MIME type in files parameter
                    files = mock_post.call_args[1]["files"]
                    _, _, mime_type = files["file"]
                    assert mime_type == expected_mime

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
