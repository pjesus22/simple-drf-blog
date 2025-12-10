from django.db import models
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

    def __str__(self):
        return f"EditorProfile (ID: {self.id})"


class SocialLink(BaseModel):
    profile = models.ForeignKey(
        to=EditorProfile,
        on_delete=models.CASCADE,
        related_name="social_links",
    )
    name = models.CharField(max_length=64)
    url = models.URLField()

    def __str__(self):
        return f"{self.name} - {self.url}"
