from django.db import models
from utils.base_models import BaseModel


class MetricEvent(BaseModel):
    event_type = models.CharField(max_length=64, db_index=True)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.event_type} @{self.created_at}"

    class Meta:
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["created_at"]),
        ]
