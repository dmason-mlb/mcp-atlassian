"""Error handling for meta-tools."""

from __future__ import annotations

from typing import Any


class MetaToolError(Exception):
    """Structured error for meta-tool operations with enhanced context."""

    def __init__(
        self,
        error_code: str,
        user_message: str,
        api_endpoint: str | None = None,
        suggestions: list[str] | None = None,
        original_error: Exception | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MetaToolError with structured error information.

        Args:
            error_code: Unique error code (e.g., "JIRA_ISSUE_NOT_FOUND")
            user_message: Human-friendly error message
            api_endpoint: API endpoint that failed (e.g., "/rest/api/3/issue/KEY-123")
            suggestions: List of possible fixes or next steps
            original_error: The underlying exception that caused this error
            context: Additional context information for debugging
        """
        self.error_code = error_code
        self.user_message = user_message
        self.api_endpoint = api_endpoint
        self.suggestions = suggestions or []
        self.original_error = original_error
        self.context = context or {}

        # Construct the exception message
        message_parts = [f"[{error_code}] {user_message}"]

        if api_endpoint:
            message_parts.append(f"API: {api_endpoint}")

        if suggestions:
            message_parts.append(f"Suggestions: {', '.join(suggestions)}")

        super().__init__(" | ".join(message_parts))

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary format for JSON serialization."""
        return {
            "error_code": self.error_code,
            "user_message": self.user_message,
            "api_endpoint": self.api_endpoint,
            "suggestions": self.suggestions,
            "original_error": str(self.original_error) if self.original_error else None,
            "context": self.context,
        }

    @classmethod
    def from_exception(
        cls,
        error: Exception,
        error_code: str,
        user_message: str | None = None,
        api_endpoint: str | None = None,
        suggestions: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> MetaToolError:
        """Create MetaToolError from an existing exception.

        Args:
            error: The original exception
            error_code: Unique error code for this error type
            user_message: Override message (defaults to str(error))
            api_endpoint: API endpoint that failed
            suggestions: List of suggested fixes
            context: Additional context

        Returns:
            MetaToolError instance wrapping the original error
        """
        # Ensure context is initialized
        if context is None:
            context = {}

        # Extract detailed error information from Atlassian API exceptions
        error_str = str(error)
        error_type = type(error).__name__

        # Try to parse structured error details from API validation errors
        # Format from base.py: "Validation error: field1: msg1; field2: msg2"
        api_error_details = {}

        if "ValidationError" in error_type or "Validation error:" in error_str:
            # Extract the part after "Validation error:"
            if "Validation error:" in error_str:
                details_str = error_str.split("Validation error:", 1)[1].strip()

                # Split by semicolon to get individual error messages
                error_parts = [part.strip() for part in details_str.split(";") if part.strip()]

                if error_parts:
                    # First, check if we have field-level errors (format: "field: message")
                    field_errors = {}
                    general_errors = []

                    for part in error_parts:
                        if ":" in part and not part.startswith("http"):
                            # Likely a field error
                            field, msg = part.split(":", 1)
                            field_errors[field.strip()] = msg.strip()
                        else:
                            # General error message
                            general_errors.append(part)

                    if field_errors:
                        api_error_details["field_errors"] = field_errors
                    if general_errors:
                        api_error_details["error_messages"] = general_errors

        # Add API error details to context if we found any
        if api_error_details:
            context["api_error_details"] = api_error_details

        # Add original error type for debugging
        context["original_error_type"] = error_type
        context["raw_error_message"] = error_str

        return cls(
            error_code=error_code,
            user_message=user_message or str(error),
            api_endpoint=api_endpoint,
            suggestions=suggestions,
            original_error=error,
            context=context,
        )
