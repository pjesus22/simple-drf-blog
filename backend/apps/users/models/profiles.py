from django.core.validators import RegexValidator
from django.db import models
from utils.base_models import BaseModel

from .users import Editor


class EditorProfile(BaseModel):
    user = models.OneToOneField(
        to=Editor,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    biography = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"EditorProfile (ID: {self.id})"


class SocialLink(BaseModel):
    profile = models.ForeignKey(
        to=EditorProfile,
        on_delete=models.CASCADE,
        related_name="social_links",
    )
    name = models.CharField(
        max_length=64,
        choices=[
            ("facebook", "Facebook"),
            ("github", "GitHub"),
            ("instagram", "Instagram"),
            ("linkedin", "LinkedIn"),
            ("tiktok", "TikTok"),
            ("twitter", "Twitter"),
            ("x", "X"),
            ("youtube", "YouTube"),
        ],
    )
    url = models.URLField(
        validators=[
            RegexValidator(
                regex=r"^https://(www\.)?(github\.com|twitter\.com|x\.com|linkedin\.com|instagram\.com|facebook\.com|youtube\.com|tiktok\.com)/.+$",
            ),
        ],
    )

    def __str__(self):
        return f"{self.name} - {self.url}"

    class Meta:
        unique_together = [["profile", "url"]]
        indexes = [
            models.Index(fields=["profile", "name"]),
        ]
