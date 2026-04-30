from django.dispatch import receiver

from apps.metrics.tasks import process_post_view_event

from .signals import post_view_signal


@receiver(post_view_signal)
def handle_post_view(sender, event, **kwargs):
    process_post_view_event.delay(
        {
            "post_id": event.post_id,
            "ip": event.ip,
            "user_agent": event.user_agent[:256],
            "referer": event.referer,
            "user_id": event.user_id,
        }
    )
