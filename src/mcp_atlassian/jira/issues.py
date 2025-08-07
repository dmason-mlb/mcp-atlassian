"""Module for Jira issue operations."""

from .mixins.batch import IssueBatchMixin
from .mixins.creation import IssueCreationMixin
from .mixins.deletion import IssueDeletionMixin
from .mixins.field import IssueFieldMixin
from .mixins.retrieval import IssueRetrievalMixin
from .mixins.transition import IssueTransitionMixin
from .mixins.update import IssueUpdateMixin


class IssuesMixin(
    IssueRetrievalMixin,
    IssueCreationMixin,
    IssueUpdateMixin,
    IssueDeletionMixin,
    IssueTransitionMixin,
    IssueBatchMixin,
    IssueFieldMixin,
):
    """Mixin for Jira issue operations combining all specialized mixins."""

    pass
