from django.db import models
from utils.base_models import BaseModel

from apps.content.mixins import SlugMixin


class Tag(SlugMixin, BaseModel):
    name = models.CharField(unique=True, max_length=53)
    slug = models.SlugField(unique=True, blank=True, max_length=64)
    slug_source_field = "name"

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
