from apps.metrics.models import MetricEvent

from .deduplication import is_duplicate


def ingest_post_view(event: dict):
    if is_duplicate(event):
        return

    MetricEvent.objects.create(event_type="post_view", metadata=event)
