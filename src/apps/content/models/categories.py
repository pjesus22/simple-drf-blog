from django.db import models

from apps.content.mixins import SlugMixin
from utils.base_models import BaseModel


class Category(SlugMixin, BaseModel):
    name = models.CharField(unique=True, max_length=106)
    slug = models.SlugField(unique=True, blank=True, max_length=128)
    description = models.TextField(blank=True)
    slug_source_field = "name"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
