from django.db import models
from utils.base_models import BaseModel


class PostMetric(BaseModel):
    post = models.OneToOneField(
        "content.Post", on_delete=models.CASCADE, related_name="metrics"
    )
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Post Metrics"
