from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from utils.base_models import BaseModel
from utils.text_tools import generate_slug


class Post(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
        DELETED = "deleted", "Deleted"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    author = models.ForeignKey(
        to="accounts.User",
        on_delete=models.CASCADE,
        related_name="posts",
    )
    category = models.ForeignKey(
        to="Category",
        on_delete=models.CASCADE,
        related_name="posts",
        null=False,
        blank=False,
    )
    tags = models.ManyToManyField(
        to="Tag",
        related_name="posts",
        blank=True,
    )
    title = models.CharField(max_length=100, blank=False, null=False)
    slug = models.SlugField(max_length=120, null=False, unique=True)
    content = models.TextField(blank=True)
    attachments = models.ManyToManyField(
        to="uploads.Upload",
        related_name="post_attachments",
        blank=True,
    )
    summary = models.CharField(blank=True, max_length=250)
    thumbnail = models.OneToOneField(
        to="uploads.Upload",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="post_thumbnail",
    )
    published_at = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self):
        return self.title

    def clean(self):
        self.slug = slugify(self.slug) if self.slug else generate_slug(self, self.title)
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT

    @property
    def is_archived(self):
        return self.status == self.Status.ARCHIVED

    @property
    def is_deleted(self):
        return self.status == self.Status.DELETED

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
        ]
