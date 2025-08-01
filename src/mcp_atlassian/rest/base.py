"""Base REST client for direct API calls to Atlassian services."""

import logging
from typing import Any, Dict, Optional, Union, Literal
from urllib.parse import urljoin, urlparse
import json

import requests
from requests import Session, Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mcp_atlassian.exceptions import (
    MCPAtlassianError,
    MCPAtlassianAuthenticationError,
    MCPAtlassianNotFoundError,
    MCPAtlassianPermissionError,
    MCPAtlassianValidationError,
)

logger = logging.getLogger(__name__)


class BaseRESTClient:
    """Base REST client with authentication and session management."""
    
    def __init__(
        self,
        base_url: str,
        auth_type: Literal["basic", "pat", "oauth", "bearer"] = "basic",
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        oauth_session: Optional[Session] = None,
        verify_ssl: bool = True,
        timeout: int = 60,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ):
        """Initialize the REST client.
        
        Args:
            base_url: Base URL for the API
            auth_type: Type of authentication to use
            username: Username for basic auth
            password: Password/API token for basic auth
            token: Personal access token or bearer token
            oauth_session: Pre-configured OAuth session
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
        """
        self.base_url = base_url.rstrip("/")
        self.auth_type = auth_type
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Create session
        if oauth_session:
            self.session = oauth_session
        else:
            self.session = Session()
            
        # Configure authentication
        self._configure_auth(username, password, token)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
    def _configure_auth(
        self, 
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Configure authentication for the session."""
        if self.auth_type == "basic":
            if not username or not password:
                raise ValueError("Basic auth requires username and password")
            self.session.auth = (username, password)
            
        elif self.auth_type == "pat":
            if not token:
                raise ValueError("PAT auth requires a token")
            self.session.headers["Authorization"] = f"Bearer {token}"
            
        elif self.auth_type == "bearer":
            if not token:
                raise ValueError("Bearer auth requires a token")
            self.session.headers["Authorization"] = f"Bearer {token}"
            
        elif self.auth_type == "oauth":
            # OAuth session should already be configured
            if not hasattr(self.session, "headers") or "Authorization" not in self.session.headers:
                raise ValueError("OAuth session must be pre-configured with Authorization header")
    
    def _build_url(self, endpoint: str, absolute: bool = False) -> str:
        """Build the full URL for an endpoint.
        
        Args:
            endpoint: API endpoint
            absolute: If True, treat endpoint as absolute URL
            
        Returns:
            Full URL
        """
        if absolute or endpoint.startswith(("http://", "https://")):
            return endpoint
        
        # Remove leading slash for urljoin to work correctly
        endpoint = endpoint.lstrip("/")
        return urljoin(self.base_url + "/", endpoint)
    
    def _handle_response_error(self, response: Response) -> None:
        """Handle error responses from the API.
        
        Args:
            response: Response object
            
        Raises:
            MCPAtlassianError: Appropriate error based on status code
        """
        try:
            error_data = response.json()
            error_messages = []
            
            # Extract error messages from various formats
            if isinstance(error_data, dict):
                if "errorMessages" in error_data:
                    error_messages.extend(error_data["errorMessages"])
                if "errors" in error_data:
                    if isinstance(error_data["errors"], dict):
                        for field, msg in error_data["errors"].items():
                            error_messages.append(f"{field}: {msg}")
                    elif isinstance(error_data["errors"], list):
                        error_messages.extend(str(e) for e in error_data["errors"])
                if "message" in error_data:
                    error_messages.append(error_data["message"])
                    
            error_message = "; ".join(error_messages) if error_messages else response.text
            
        except (ValueError, json.JSONDecodeError):
            error_message = response.text or f"HTTP {response.status_code}"
        
        # Map status codes to specific exceptions
        if response.status_code == 401:
            raise MCPAtlassianAuthenticationError(f"Authentication failed: {error_message}")
        elif response.status_code == 403:
            raise MCPAtlassianPermissionError(f"Permission denied: {error_message}")
        elif response.status_code == 404:
            raise MCPAtlassianNotFoundError(f"Resource not found: {error_message}")
        elif response.status_code == 400:
            raise MCPAtlassianValidationError(f"Validation error: {error_message}")
        else:
            raise MCPAtlassianError(
                f"API request failed with status {response.status_code}: {error_message}"
            )
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON data to send
            data: Raw data to send
            headers: Additional headers
            absolute: If True, treat endpoint as absolute URL
            raw_response: If True, return raw Response object
            
        Returns:
            API response data or Response object if raw_response=True
            
        Raises:
            MCPAtlassianError: On API errors
        """
        url = self._build_url(endpoint, absolute)
        
        # Merge headers
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Log request details (with sensitive data masked)
        logger.debug(
            f"{method} {url} "
            f"(params: {params}, "
            f"json: {'<data>' if json_data else None}, "
            f"data: {'<data>' if data else None})"
        )
        
        # Log full JSON payload for debugging
        if json_data:
            import json as json_module
            logger.info(f"[DEBUG] Full JSON payload being sent to API:")
            logger.info(f"[DEBUG] {json_module.dumps(json_data, indent=2)}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                data=data,
                headers=request_headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            
            # Handle errors
            if not response.ok:
                self._handle_response_error(response)
            
            # Return raw response if requested
            if raw_response:
                return response
            
            # Return None for 204 No Content
            if response.status_code == 204:
                return None
            
            # Parse JSON response
            try:
                return response.json()
            except (ValueError, json.JSONDecodeError):
                # Return text for non-JSON responses
                return {"text": response.text}
                
        except requests.exceptions.Timeout:
            raise MCPAtlassianError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise MCPAtlassianError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise MCPAtlassianError(f"Request failed: {e}")
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a GET request."""
        return self.request(
            method="GET",
            endpoint=endpoint,
            params=params,
            headers=headers,
            absolute=absolute,
            raw_response=raw_response,
        )
    
    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a POST request."""
        return self.request(
            method="POST",
            endpoint=endpoint,
            params=params,
            json_data=json_data,
            data=data,
            headers=headers,
            absolute=absolute,
            raw_response=raw_response,
        )
    
    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a PUT request."""
        return self.request(
            method="PUT",
            endpoint=endpoint,
            params=params,
            json_data=json_data,
            data=data,
            headers=headers,
            absolute=absolute,
            raw_response=raw_response,
        )
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a DELETE request."""
        return self.request(
            method="DELETE",
            endpoint=endpoint,
            params=params,
            headers=headers,
            absolute=absolute,
            raw_response=raw_response,
        )
    
    def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        absolute: bool = False,
        raw_response: bool = False,
    ) -> Union[Dict[str, Any], Response, None]:
        """Make a PATCH request."""
        return self.request(
            method="PATCH",
            endpoint=endpoint,
            params=params,
            json_data=json_data,
            data=data,
            headers=headers,
            absolute=absolute,
            raw_response=raw_response,
        )
    
    def set_header(self, name: str, value: str) -> None:
        """Set a session header."""
        self.session.headers[name] = value
    
    def remove_header(self, name: str) -> None:
        """Remove a session header."""
        self.session.headers.pop(name, None)
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()