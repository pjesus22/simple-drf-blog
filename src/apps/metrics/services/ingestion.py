from apps.metrics.models import MetricEvent

from .deduplication import is_duplicate


def ingest_event(event_type: str, event_data: dict) -> None:
    if is_duplicate(event_data, event_type):
        return

    MetricEvent.objects.create(
        event_type=event_type,
        metadata=event_data,
    )
