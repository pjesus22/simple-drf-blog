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
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
