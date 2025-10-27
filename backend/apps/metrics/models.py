from django.db import models
from utils.base_models import BaseModel


class PostMetric(BaseModel):
    class Providers(models.TextChoices):
        FACEBOOK = "FACEBOOK", "Facebook"
        INSTAGRAM = "INSTAGRAM", "Instagram"
        X = "X", "X"
        YOUTUBE = "YOUTUBE", "Youtube"

    post = models.ForeignKey(
        to="content.Post",
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    provider = models.CharField(max_length=30, choices=Providers.choices)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Post Metrics"
        indexes = [
            models.Index(fields=["post", "provider", "-updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["post", "provider"], name="unique_post_provider_metric"
            )
        ]
