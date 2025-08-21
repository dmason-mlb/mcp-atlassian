"""Issue field operations mixin for Jira client."""

import logging

from ..client import JiraClient

logger = logging.getLogger("mcp-jira")


class IssueFieldMixin(JiraClient):
    """Mixin for Jira issue field operations."""

    def _log_available_fields(self, fields: list[dict]) -> None:
        """
        Log available fields for debugging.

        Args:
            fields: List of field definitions
        """
        logger.debug("Available Jira fields:")
        for field in fields:
            logger.debug(
                f"{field.get('id')}: {field.get('name')} ({field.get('schema', {}).get('type')})"
            )

    def _process_field_for_epic_data(
        self, field: dict, field_ids: dict[str, str]
    ) -> None:
        """
        Process a field for epic-related data.

        Args:
            field: The field data to process
            field_ids: Dictionary of field IDs to update
        """
        try:
            field_id = field.get("id")
            if not field_id:
                return

            # Skip non-custom fields
            if not field_id.startswith("customfield_"):
                return

            name = field.get("name", "").lower()

            # Look for field names related to epics
            if "epic" in name:
                if "link" in name:
                    field_ids["epic_link"] = field_id
                    field_ids["Epic Link"] = field_id
                elif "name" in name:
                    field_ids["epic_name"] = field_id
                    field_ids["Epic Name"] = field_id
        except Exception as e:
            logger.warning(f"Error processing field for epic data: {str(e)}")
