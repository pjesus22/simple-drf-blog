from .base import MetricEvent
from .signals import metric_event_signal


class EventBus:
    """Central event bus for all metric events"""

    @staticmethod
    def send(event: MetricEvent) -> None:
        if not event.validate():
            return

        metric_event_signal.send(sender=event.event_type, event=event)
