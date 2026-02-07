from apps.accounts.managers import ProfileManager
from django.core.validators import RegexValidator
from django.db import models
from utils.base_models import BaseModel


class Profile(BaseModel):
    objects = ProfileManager()
    user = models.OneToOneField(
        to="accounts.User",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    biography = models.TextField(blank=True)
    location = models.CharField(blank=True)
    occupation = models.CharField(blank=True)
    skills = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)

    is_public = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile(user={self.user.id})"


class SocialMediaProfile(BaseModel):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        GITHUB = "github", "GitHub"
        INSTAGRAM = "instagram", "Instagram"
        LINKEDIN = "linkedin", "LinkedIn"
        TIKTOK = "tiktok", "TikTok"
        TWITTER = "twitter", "Twitter"
        X = "x", "X"
        YOUTUBE = "youtube", "YouTube"

    profile = models.ForeignKey(
        to=Profile,
        on_delete=models.CASCADE,
        related_name="social_media",
    )
    platform = models.CharField(choices=Platform.choices)
    url = models.URLField(
        validators=[
            RegexValidator(
                regex=r"^https://(www\.)?(github\.com|twitter\.com|x\.com|linkedin\.com|instagram\.com|facebook\.com|youtube\.com|tiktok\.com)/.+$",
            )
        ]
    )

    class Meta:
        unique_together = [["profile", "url"]]
        indexes = [models.Index(fields=["profile", "platform"])]

    def __str__(self):
        return (
            f"SocialMediaProfile(profile={self.profile.id}, platform={self.platform})"
        )
