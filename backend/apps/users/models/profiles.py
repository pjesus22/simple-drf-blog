from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from utils.base_models import BaseModel

from .users import Editor


class EditorProfile(BaseModel):
    user = models.OneToOneField(
        to=Editor,
        on_delete=models.CASCADE,
        related_name="editor_profile",
    )
    biography = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(signal=post_save, sender=Editor)
def create_editor_profile(sender, instance, created, **kwargs):
    if created:
        EditorProfile.objects.get_or_create(user=instance)


class SocialAccounts(BaseModel):
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
    url = models.URLField(unique=True)

    def __str__(self):
        return f"{self.username} {self.provider}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "username", "profile"],
                name="unique_social_per_provider",
            )
        ]
