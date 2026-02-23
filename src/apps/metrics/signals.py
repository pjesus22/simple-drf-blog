from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.metrics.models import MetricEvent


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    MetricEvent.objects.create(
        event_type=MetricEvent.EventType.LOGIN,
        user=user,
        metadata={
            "ip": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
        },
    )


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    MetricEvent.objects.create(
        event_type=MetricEvent.EventType.LOGIN_FAILED,
        metadata={
            "ip": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
            "username": credentials.get("username"),
        },
    )


@receiver(post_save, sender="uploads.Upload")
def on_created_upload(sender, instance, created, **kwargs):
    if not created:
        return

    MetricEvent.objects.create(
        event_type=MetricEvent.EventType.UPLOAD_CREATED,
        user=instance.uploaded_by,
        metadata={
            "upload_id": instance.id,
            "purpose": instance.purpose,
            "size": instance.size,
            "mime_type": instance.mime_type,
        },
    )
