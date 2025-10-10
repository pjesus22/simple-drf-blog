from django.db import models
from utils.base_models import BaseModel

from .profiles import EditorProfile


class SocialLink(BaseModel):
    class Providers(models.TextChoices):
        FACEBOOK = "FACEBOOK", "Facebook"
        INSTAGRAM = "INSTAGRAM", "Instagram"
        SNAPCHAT = "SNAPCHAT", "Snapchat"
        TELEGRAM = "TELEGRAM", "Telegram"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        X = "X", "X"
        YOUTUBE = "YOUTUBE", "Youtube"
        OTHER = "OTHER", "Other"

    profile = models.ForeignKey(
        to=EditorProfile,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=30, choices=Providers.choices)
    username = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return f"{self.provider.title()} - @{self.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "username", "profile"],
                name="unique_social_per_provider",
            )
        ]
