"""Issue linking mixin for Jira server."""

import logging

logger = logging.getLogger(__name__)


class IssueLinkingMixin:
    """Mixin providing issue linking tools.
    
    Note: Currently empty as linking functionality is handled in the management module.
    This mixin is provided for future extensibility and maintaining the planned architecture.
    """
    pass