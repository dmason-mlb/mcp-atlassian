"""Issue update operations mixin for Jira client."""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ...exceptions import MCPAtlassianAuthenticationError
from ...models.jira import JiraIssue
from ..client import JiraClient
from ..protocols import (
    AttachmentsOperationsProto,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    UsersOperationsProto,
)

logger = logging.getLogger("mcp-jira")


class IssueUpdateMixin(
    JiraClient,
    AttachmentsOperationsProto,
    EpicOperationsProto,
    FieldsOperationsProto,
    IssueOperationsProto,
    UsersOperationsProto,
):
    """Mixin for Jira issue update operations."""

    def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any] | None = None,
        **kwargs: Any,  # noqa: ANN401 - Dynamic field types are necessary for Jira API
    ) -> JiraIssue:
        """
        Update a Jira issue.

        Args:
            issue_key: The key of the issue to update
            fields: Dictionary of fields to update
            **kwargs: Additional fields to update. Special fields include:
                - attachments: List of file paths to upload as attachments
                - status: New status for the issue (handled via transitions)
                - assignee: New assignee for the issue

        Returns:
            JiraIssue model representing the updated issue

        Raises:
            Exception: If there is an error updating the issue
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("[DEBUG] JiraIssueService.update_issue called with:")
            logger.debug(f"[DEBUG]   issue_key: '{issue_key}'")
            logger.debug(f"[DEBUG]   fields: {list(fields.keys()) if fields else 'None'}")
            logger.debug(f"[DEBUG]   kwargs: {list(kwargs.keys()) if kwargs else 'None'}")

        try:
            # Validate required fields
            if not issue_key:
                raise ValueError("Issue key is required")

            # STRUCTURAL FIX: Unify inputs to eliminate double processing
            # Start with fields parameter, then merge in kwargs
            update_fields = fields.copy() if fields else {}
            attachments_result = None

            # Extract special kwargs that need separate handling (don't modify original kwargs)
            status_value = kwargs.get("status")
            attachments_value = kwargs.get("attachments")

            # Merge kwargs into update_fields, excluding special fields (kwargs override fields)
            for key, value in kwargs.items():
                if key not in ["status", "attachments"]:
                    update_fields[key] = value

            logger.debug(f"[DEBUG] Unified update_fields: {list(update_fields.keys())}")

            # Handle status changes first (they require special processing)
            if status_value is not None:
                # Status changes are handled separately via transitions
                # Add status to fields so _update_issue_with_status can find it
                update_fields["status"] = status_value
                return self._update_issue_with_status(issue_key, update_fields)

            # SINGLE PROCESSING PATH: Convert description from Markdown to Jira format if present
            if "description" in update_fields:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("[DEBUG] Processing description field...")
                    logger.debug(
                        f"[DEBUG] Original description: {update_fields['description'][:200]}..."
                    )

                description_content = self.markdown_to_jira(
                    update_fields["description"], return_raw_adf=True
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("[DEBUG] Description content after conversion:")
                    logger.debug(f"[DEBUG]   Type: {type(description_content)}")
                    logger.debug(
                        f"[DEBUG]   Is dict: {isinstance(description_content, dict)}"
                    )
                    logger.debug(f"[DEBUG]   Is str: {isinstance(description_content, str)}")
                    logger.debug(
                        f"[DEBUG]   Content preview: {str(description_content)[:300]}..."
                )

                # Handle both ADF (dict) and wiki markup (str) formats
                # With the new REST client, ADF is passed as-is (dict)
                update_fields["description"] = description_content

            # Handle assignee updates with special processing
            if "assignee" in update_fields:
                assignee_value = update_fields["assignee"]
                if assignee_value is None or assignee_value == "":
                    update_fields["assignee"] = None
                else:
                    try:
                        account_id = self._get_account_id(assignee_value)
                        self._add_assignee_to_fields(update_fields, account_id)
                    except ValueError as e:
                        logger.warning(f"Could not update assignee: {str(e)}")
                        # Remove invalid assignee to prevent API errors
                        update_fields.pop("assignee", None)

            # Process any remaining fields that need additional processing
            # (Note: description and assignee are already handled above)
            fields_to_process = {
                k: v
                for k, v in update_fields.items()
                if k not in ["description", "assignee", "status"]
            }
            if fields_to_process:
                self._process_additional_fields(update_fields, fields_to_process)

            # Update the issue fields
            if update_fields:
                self.jira.update_issue(
                    issue_key=issue_key, fields=update_fields, update=None
                )

            # Handle attachments if provided
            if attachments_value and isinstance(attachments_value, list | tuple):
                try:
                    attachments_result = self.upload_attachments(
                        issue_key, attachments_value
                    )
                    logger.info(
                        f"Uploaded attachments to {issue_key}: {attachments_result}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error uploading attachments to {issue_key}: {str(e)}"
                    )
                    # Continue with the update even if attachments fail
            elif attachments_value:
                logger.warning(f"Invalid attachments value: {attachments_value}")

            # Get the updated issue data and convert to JiraIssue model
            issue_data = self.jira.get_issue(issue_key)
            if not isinstance(issue_data, dict):
                msg = f"Unexpected return value type from `jira.get_issue`: {type(issue_data)}"
                logger.error(msg)
                raise TypeError(msg)
            issue = JiraIssue.from_api_response(issue_data)

            # Add attachment results to the response if available
            if attachments_result:
                issue.custom_fields["attachment_results"] = attachments_result

            return issue

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error updating issue {issue_key}: {error_msg}")
            raise ValueError(f"Failed to update issue {issue_key}: {error_msg}") from e

    def _update_issue_with_status(
        self, issue_key: str, fields: dict[str, Any]
    ) -> JiraIssue:
        """
        Update an issue with a status change.

        Args:
            issue_key: The key of the issue to update
            fields: Dictionary of fields to update

        Returns:
            JiraIssue model representing the updated issue

        Raises:
            Exception: If there is an error updating the issue
        """
        # Extract status from fields and remove it for the standard update
        status = fields.pop("status", None)

        # First update any fields if needed
        if fields:
            self.jira.update_issue(issue_key=issue_key, fields=fields)  # type: ignore[call-arg]

        # If no status change is requested, return the issue
        if not status:
            issue_data = self.jira.get_issue(issue_key)
            if not isinstance(issue_data, dict):
                msg = f"Unexpected return value type from `jira.get_issue`: {type(issue_data)}"
                logger.error(msg)
                raise TypeError(msg)
            return JiraIssue.from_api_response(issue_data)

        # Get available transitions (uses TransitionsMixin's normalized implementation)
        transitions = self.get_available_transitions(issue_key)  # type: ignore[attr-defined]

        # Extract status name or ID depending on what we received
        status_name = None
        status_id = None

        # Handle different input formats for status
        if isinstance(status, dict):
            # Dictionary format: {"name": "In Progress"} or {"id": "123"}
            status_name = status.get("name")
            status_id = status.get("id")
        elif isinstance(status, str):
            # String format: could be a name or an ID
            if status.isdigit():
                status_id = status
            else:
                status_name = status
        elif isinstance(status, int):
            # Integer format: must be an ID
            status_id = str(status)
        else:
            # Unknown format
            logger.warning(
                f"Unrecognized status format: {status} (type: {type(status)})"
            )
            status_name = str(status)

        # Log what we're searching for
        if status_name:
            logger.info(f"Looking for transition to status name: '{status_name}'")
        if status_id:
            logger.info(f"Looking for transition with ID: '{status_id}'")

        # Find the appropriate transition
        transition_id = None
        for transition in transitions:
            # TransitionsMixin returns normalized transitions with 'to_status' field
            transition_status_name = transition.get("to_status", "")

            # Match by name (case-insensitive)
            if (
                status_name
                and transition_status_name
                and transition_status_name.lower() == status_name.lower()
            ):
                transition_id = transition.get("id")
                logger.info(
                    f"Found transition ID {transition_id} matching status name '{status_name}'"
                )
                break

            # Direct transition ID match (if status is actually a transition ID)
            if status_id and str(transition.get("id", "")) == str(status_id):
                transition_id = transition.get("id")
                logger.info(f"Using direct transition ID {transition_id}")
                break

        if not transition_id:
            # Build list of available statuses from normalized transitions
            available_statuses = []
            for t in transitions:
                # Include transition name and target status if available
                transition_name = t.get("name", "")
                to_status = t.get("to_status", "")
                if to_status:
                    available_statuses.append(f"{transition_name} -> {to_status}")
                elif transition_name:
                    available_statuses.append(transition_name)

            available_statuses_str = (
                ", ".join(available_statuses) if available_statuses else "None found"
            )
            error_msg = (
                f"Could not find transition to status '{status}'. "
                f"Available transitions: {available_statuses_str}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Perform the transition
        logger.info(f"Performing transition with ID {transition_id}")
        self.jira.set_issue_status_by_transition_id(
            issue_key=issue_key,
            transition_id=(
                int(transition_id)
                if isinstance(transition_id, str) and transition_id.isdigit()
                else transition_id
            ),
        )

        # Get the updated issue data
        issue_data = self.jira.get_issue(issue_key)
        if not isinstance(issue_data, dict):
            msg = f"Unexpected return value type from `jira.get_issue`: {type(issue_data)}"
            logger.error(msg)
            raise TypeError(msg)
        return JiraIssue.from_api_response(issue_data)

    def _markdown_to_jira(self, markdown_text: str) -> str | dict[str, Any]:
        """Helper method to convert markdown to Jira format.

        This wraps the FormattingMixin method for convenience.

        Args:
            markdown_text: Text in Markdown format

        Returns:
            For Cloud instances: Dictionary containing ADF JSON structure
            For Server/DC instances: String in Jira wiki markup format
        """
        return self.markdown_to_jira(markdown_text, return_raw_adf=True)

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

        # Process each kwarg
        # Iterate over a copy to allow modification of the original kwargs if needed elsewhere
        for key, value in kwargs.copy().items():
            # Skip keys used internally for epic/parent handling or explicitly handled args like assignee/components
            if key.startswith("__epic_") or key in ("parent", "assignee", "components"):
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
                from ...utils import parse_date
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