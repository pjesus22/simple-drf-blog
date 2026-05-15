from django.dispatch import receiver

from apps.metrics.tasks import process_metric_event

from .registry import EventRegistry
from .signals import metric_event_signal


@receiver(signal=metric_event_signal)
def handle_metric_event(sender, event, **kwargs):
    """Generic handler that routes events to their specific handlers."""
    handler = EventRegistry.get_handler(event.event_type)
    if handler:
        handler(event)


class PostViewHandler:
    def __call__(self, event):
        process_metric_event.delay(
            event_type=event.event_type,
            event_data=event.get_metadata(),
        )


# Handlers registry
EventRegistry.register_handler("post_view", PostViewHandler())
