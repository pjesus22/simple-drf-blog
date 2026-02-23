from django.db import models
from utils.base_models import BaseModel


class MetricEvent(BaseModel):
    class EventType(models.TextChoices):
        POST_READ = "post_read"
        LOGIN = "login"
        UPLOAD_CREATED = "upload_created"
        LOGIN_FAILED = "login_failed"

    event_type = models.CharField(
        max_length=64,
        choices=EventType.choices,
        db_index=True,
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="metrics",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.event_type} @{self.created_at} by {self.user}"

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["event_type", "created_at"])]
