"""Issue creation operations mixin for Jira client."""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ...exceptions import MCPAtlassianAuthenticationError
from ...models.jira import JiraIssue
from ...utils import parse_date
from ..client import JiraClient
from ..protocols import (
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    ProjectsOperationsProto,
    UsersOperationsProto,
)

logger = logging.getLogger("mcp-jira")


class IssueCreationMixin(
    JiraClient,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    ProjectsOperationsProto,
    UsersOperationsProto,
):
    """Mixin for Jira issue creation operations."""

    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        description: str = "",
        assignee: str | None = None,
        components: list[str] | None = None,
        **kwargs: Any,
    ) -> JiraIssue:
        """
        Create a Jira issue.

        Args:
            project_key: The project key
            summary: Issue summary
            issue_type: Type of issue (e.g. 'Task', 'Bug', 'Story')
            description: Issue description (Markdown format)
            assignee: Assignee username or email
            components: List of component names
            **kwargs: Additional fields. Special fields:
                - parent: Parent issue key for subtasks
                - epic_link: Epic key to link this issue to
                - epic_name: Epic name (required for Epic issues)
                - labels: List of labels or comma-separated string
                - priority: Priority name (e.g. 'High', 'Medium')
                - additional_fields: Dict or JSON string of custom fields

        Returns:
            JiraIssue model representing the created issue

        Raises:
            Exception: If there is an error creating the issue
        """
        try:
            # Validate required fields
            if not project_key:
                raise ValueError("Project key is required")
            if not summary:
                raise ValueError("Summary is required")
            if not issue_type:
                raise ValueError("Issue type is required")

            # Initialize basic fields
            fields = {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type},
            }

            # Add description if provided
            if description:
                # Bypass conflicting _markdown_to_jira resolution by calling the
                # formatting router directly and requesting string output for ADF
                description_content = self.markdown_to_jira(
                    description, return_raw_adf=False
                )
                fields["description"] = description_content

            # Handle components
            if components:
                fields["components"] = [{"name": comp} for comp in components]

            # Handle assignee
            if assignee:
                try:
                    account_id = self._get_account_id(assignee)
                    self._add_assignee_to_fields(fields, account_id)
                except ValueError as e:
                    logger.warning(f"Could not set assignee: {str(e)}")

            # Handle Epic-specific logic
            if self._is_epic_issue_type(issue_type):
                self._prepare_epic_fields(fields, summary, kwargs)
            else:
                # Handle parent/subtask logic for non-Epic issues
                self._prepare_parent_fields(fields, kwargs)

            # Process additional fields from kwargs
            self._process_additional_fields(fields, kwargs)

            # Create the issue
            result = self.jira.create_issue(fields=fields)
            if not isinstance(result, dict):
                msg = f"Unexpected return value type from `jira.create_issue`: {type(result)}"
                logger.error(msg)
                raise TypeError(msg)

            # Fetch the created issue to return a fully populated JiraIssue model
            created_key = result.get("key") or result.get("id")
            if created_key:
                try:
                    issue_data = self.jira.get_issue(created_key)
                    if isinstance(issue_data, dict):
                        return JiraIssue.from_api_response(issue_data)
                except Exception:  # noqa: BLE001
                    logger.debug("Failed to retrieve created issue %s for enrichment", created_key)
            return JiraIssue.from_api_response(result)

        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Jira API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                self._handle_create_issue_error(http_err, issue_type)
                raise
        except Exception as e:
            self._handle_create_issue_error(e, issue_type)
            raise

    def _is_epic_issue_type(self, issue_type: str) -> bool:
        """
        Check if an issue type is an Epic, handling localized names.

        Args:
            issue_type: The issue type name to check

        Returns:
            True if the issue type is an Epic, False otherwise
        """
        # Common Epic names in different languages
        epic_names = {
            "epic",  # English
            "에픽",  # Korean
            "エピック",  # Japanese
            "史诗",  # Chinese (Simplified)
            "史詩",  # Chinese (Traditional)
            "épica",  # Spanish/Portuguese
            "épique",  # French
            "epik",  # Turkish
            "эпик",  # Russian
            "епік",  # Ukrainian
        }

        return issue_type.lower() in epic_names or "epic" in issue_type.lower()

    def _find_epic_issue_type_name(self, project_key: str) -> str | None:
        """
        Find the actual Epic issue type name for a project.

        Args:
            project_key: The project key

        Returns:
            The Epic issue type name if found, None otherwise
        """
        try:
            issue_types = self.get_project_issue_types(project_key)
            for issue_type in issue_types:
                type_name = issue_type.get("name", "")
                if self._is_epic_issue_type(type_name):
                    return type_name
            return None
        except Exception as e:
            logger.warning(f"Could not get issue types for project {project_key}: {e}")
            return None

    def _find_subtask_issue_type_name(self, project_key: str) -> str | None:
        """
        Find the actual Subtask issue type name for a project.

        Args:
            project_key: The project key

        Returns:
            The Subtask issue type name if found, None otherwise
        """
        try:
            issue_types = self.get_project_issue_types(project_key)
            for issue_type in issue_types:
                # Check the subtask field - this is the most reliable way
                if issue_type.get("subtask", False):
                    return issue_type.get("name")
            return None
        except Exception as e:
            logger.warning(f"Could not get issue types for project {project_key}: {e}")
            return None

    def _prepare_epic_fields(
        self, fields: dict[str, Any], summary: str, kwargs: dict[str, Any]
    ) -> None:
        """
        Prepare fields for epic creation.

        This method delegates to the prepare_epic_fields method in EpicsMixin.

        Args:
            fields: The fields dictionary to update
            summary: The epic summary
            kwargs: Additional fields from the user
        """
        # Extract project_key from fields if available
        project_key = None
        if "project" in fields:
            if isinstance(fields["project"], dict):
                project_key = fields["project"].get("key")
            elif isinstance(fields["project"], str):
                project_key = fields["project"]

        # Delegate to EpicsMixin.prepare_epic_fields with project_key
        # Since JiraFetcher inherits from both IssuesMixin and EpicsMixin,
        # this will correctly use the prepare_epic_fields method from EpicsMixin
        # which implements the two-step Epic creation approach
        self.prepare_epic_fields(fields, summary, kwargs, project_key)

    def _prepare_parent_fields(
        self, fields: dict[str, Any], kwargs: dict[str, Any]
    ) -> None:
        """
        Prepare fields for parent relationship.

        Args:
            fields: The fields dictionary to update
            kwargs: Additional fields from the user

        Raises:
            ValueError: If parent issue key is not specified for a subtask
        """
        if "parent" in kwargs:
            parent_key = kwargs.get("parent")
            if parent_key:
                fields["parent"] = {"key": parent_key}
            # Remove parent from kwargs to avoid double processing
            kwargs.pop("parent", None)
        elif "issuetype" in fields and fields["issuetype"]["name"].lower() in (
            "subtask",
            "sub-task",
        ):
            # Only raise error if issue type is subtask and parent is missing
            raise ValueError(
                "Issue type is a sub-task but parent issue key or id not specified. Please provide a 'parent' parameter with the parent issue key."
            )

    def _add_assignee_to_fields(self, fields: dict[str, Any], assignee: str) -> None:
        """
        Add assignee to issue fields.

        Args:
            fields: The fields dictionary to update
            assignee: The assignee account ID
        """
        # Cloud instance uses accountId
        if self.config.is_cloud:
            fields["assignee"] = {"accountId": assignee}
        else:
            # Server/DC might use name instead of accountId
            fields["assignee"] = {"name": assignee}

    def _process_additional_fields(
        self, fields: dict[str, Any], kwargs: dict[str, Any]
    ) -> None:
        """
        Processes keyword arguments to add standard or custom fields to the issue fields dictionary.
        Uses the dynamic field map from FieldsMixin to identify field IDs.

        Args:
            fields: The fields dictionary to update
            kwargs: Additional fields provided via **kwargs
        """
        # Ensure field map is loaded/cached
        field_map = (
            self._generate_field_map()
        )  # Ensure map is ready (method from FieldsMixin)
        if not field_map:
            logger.error(
                "Could not generate field map. Cannot process additional fields."
            )
            return

        # Handle special 'additional_fields' parameter
        if "additional_fields" in kwargs:
            import json
            additional = kwargs.pop("additional_fields")
            
            # Parse JSON string if needed
            if isinstance(additional, str):
                try:
                    additional = json.loads(additional)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse additional_fields JSON: {e}")
                    additional = {}
            
            # Merge additional fields into kwargs
            if isinstance(additional, dict):
                kwargs.update(additional)
            else:
                logger.warning(f"additional_fields must be a dict or JSON string, got {type(additional)}")

        # Process each kwarg
        # Iterate over a copy to allow modification of the original kwargs if needed elsewhere
        for key, value in kwargs.copy().items():
            # Skip keys used internally for epic/parent handling or explicitly handled args like assignee/components
            if key.startswith("__epic_") or key in ("parent", "assignee", "components", "additional_fields"):
                continue

            normalized_key = key.lower()
            api_field_id = None

            # 1. Check if key is a known field name in the map
            if normalized_key in field_map:
                api_field_id = field_map[normalized_key]
                logger.debug(
                    f"Identified field '{key}' as '{api_field_id}' via name map."
                )

            # 2. Check if key is a direct custom field ID
            elif key.startswith("customfield_"):
                api_field_id = key
                logger.debug(f"Identified field '{key}' as direct custom field ID.")

            # 3. Check if key is a standard system field ID (like 'summary', 'priority')
            elif key in field_map:  # Check original case for system fields
                api_field_id = field_map[key]
                logger.debug(f"Identified field '{key}' as standard system field ID.")

            if api_field_id:
                # Get the full field definition for formatting context if needed
                field_definition = self.get_field_by_id(
                    api_field_id
                )  # From FieldsMixin
                formatted_value = self._format_field_value_for_write(
                    api_field_id, value, field_definition
                )
                if formatted_value is not None:  # Only add if formatting didn't fail
                    fields[api_field_id] = formatted_value
                    logger.debug(
                        f"Added field '{api_field_id}' from kwarg '{key}': {formatted_value}"
                    )
                else:
                    logger.warning(
                        f"Skipping field '{key}' due to formatting error or invalid value."
                    )
            else:
                # 4. Unrecognized key - log a warning and skip
                logger.warning(
                    f"Ignoring unrecognized field '{key}' passed via kwargs."
                )

    def _format_field_value_for_write(
        self, field_id: str, value: Any, field_definition: dict | None
    ) -> Any:
        """Formats field values for the Jira API."""
        # Get schema type if definition is available
        schema_type = (
            field_definition.get("schema", {}).get("type") if field_definition else None
        )
        # Prefer name from definition if available, else use ID for logging/lookup
        field_name_for_format = (
            field_definition.get("name", field_id) if field_definition else field_id
        )

        # Example formatting rules based on standard field names (use lowercase for comparison)
        normalized_name = field_name_for_format.lower()

        if normalized_name == "priority":
            if isinstance(value, str):
                return {"name": value}
            elif isinstance(value, dict) and ("name" in value or "id" in value):
                return value  # Assume pre-formatted
            else:
                logger.warning(
                    f"Invalid format for priority field: {value}. Expected string name or dict."
                )
                return None  # Or raise error
        elif normalized_name == "labels":
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return value
            # Allow comma-separated string if passed via additional_fields JSON string
            elif isinstance(value, str):
                return [label.strip() for label in value.split(",") if label.strip()]
            else:
                logger.warning(
                    f"Invalid format for labels field: {value}. Expected list of strings or comma-separated string."
                )
                return None
        elif normalized_name in ["fixversions", "versions", "components"]:
            # These expect lists of objects, typically {"name": "..."} or {"id": "..."}
            if isinstance(value, list):
                formatted_list = []
                for item in value:
                    if isinstance(item, str):
                        formatted_list.append({"name": item})  # Convert simple strings
                    elif isinstance(item, dict) and ("name" in item or "id" in item):
                        formatted_list.append(item)  # Keep pre-formatted dicts
                    else:
                        logger.warning(
                            f"Invalid item format in {normalized_name} list: {item}"
                        )
                return formatted_list
            else:
                logger.warning(
                    f"Invalid format for {normalized_name} field: {value}. Expected list."
                )
                return None
        elif normalized_name == "reporter":
            if isinstance(value, str):
                try:
                    reporter_identifier = self._get_account_id(value)
                    if self.config.is_cloud:
                        return {"accountId": reporter_identifier}
                    else:
                        return {"name": reporter_identifier}
                except ValueError as e:
                    logger.warning(f"Could not format reporter field: {str(e)}")
                    return None
            elif isinstance(value, dict) and ("name" in value or "accountId" in value):
                return value  # Assume pre-formatted
            else:
                logger.warning(f"Invalid format for reporter field: {value}")
                return None
        # Add more formatting rules for other standard fields based on schema_type or field_id
        elif normalized_name == "duedate":
            if isinstance(value, str):  # Basic check, could add date validation
                return value
            else:
                logger.warning(
                    f"Invalid format for duedate field: {value}. Expected YYYY-MM-DD string."
                )
                return None
        elif schema_type == "datetime" and isinstance(value, str):
            # Example: Ensure datetime fields are in ISO format if needed by API
            try:
                dt = parse_date(value)  # Assuming parse_date handles various inputs
                return (
                    dt.isoformat() if dt else value
                )  # Return ISO or original if parse fails
            except Exception:
                logger.warning(
                    f"Could not parse datetime for field {field_id}: {value}"
                )
                return value  # Return original on error

        # Default: return value as is if no specific formatting needed/identified
        return value

    def _handle_create_issue_error(self, exception: Exception, issue_type: str) -> None:
        """
        Handle errors when creating an issue.

        Args:
            exception: The exception that occurred
            issue_type: The type of issue being created
        """
        error_msg = str(exception)

        # Check for specific error types
        if "epic name" in error_msg.lower() or "epicname" in error_msg.lower():
            logger.error(
                f"Error creating {issue_type}: {error_msg}. "
                "Try specifying an epic_name in the additional fields"
            )
        elif "customfield" in error_msg.lower():
            logger.error(
                f"Error creating {issue_type}: {error_msg}. "
                "This may be due to a required custom field"
            )
        else:
            logger.error(f"Error creating {issue_type}: {error_msg}")

    def _markdown_to_jira(self, markdown_text: str) -> str | dict[str, Any]:
        """Helper method to convert markdown to Jira format.

        This wraps the FormattingMixin method for convenience.

        Args:
            markdown_text: Text in Markdown format

        Returns:
            For Cloud instances: JSON string containing ADF structure (API-compatible)
            For Server/DC instances: String in Jira wiki markup format
        """
        # For issue creation, pass string payloads to adapter for compatibility
        # FormattingMixin.markdown_to_jira will return JSON string when ADF dict is produced
        return self.markdown_to_jira(markdown_text, return_raw_adf=False)