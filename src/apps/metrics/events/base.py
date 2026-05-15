from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass
class MetricEvent(ABC):
    """Base class for metric events"""

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type string (e.g., 'post_view')."""

    def get_metadata(self) -> dict:
        """Convert event to dict for storage."""
        return asdict(self)

    def validate(self) -> bool:
        """Override to add validation logic."""
        return True
