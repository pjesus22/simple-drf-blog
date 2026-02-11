from django.db import models
from django.utils.text import slugify
from utils.base_models import BaseModel
from utils.text_tools import generate_slug


class Tag(BaseModel):
    name = models.CharField(unique=True, max_length=50)
    slug = models.SlugField(unique=True, blank=True, max_length=60)

    def __str__(self):
        return self.name

    def clean(self):
        self.slug = slugify(self.slug) if self.slug else generate_slug(self, self.name)
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["name"]
