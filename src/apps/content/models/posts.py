from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from utils.base_models import BaseModel
from utils.text_tools import generate_slug

from apps.content.managers import PostManager


class Post(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
        DELETED = "deleted", "Deleted"

    objects = PostManager()

    status = models.CharField(
        max_length=32,
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
    title = models.CharField(max_length=106, blank=False, null=False)
    slug = models.SlugField(max_length=128, null=False, unique=True)
    content = models.TextField(blank=True)
    attachments = models.ManyToManyField(
        to="uploads.Upload",
        related_name="post_attachments",
        blank=True,
    )
    summary = models.CharField(blank=True, max_length=256)
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
        super().clean()

        self.slug = slugify(self.slug) if self.slug else generate_slug(self, self.title)

        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()

        if self.status == self.Status.PUBLISHED and self._state.adding is False:
            old_status = Post.objects.with_deleted().get(pk=self.pk).status
            if old_status in [self.Status.ARCHIVED, self.Status.DELETED]:
                raise ValidationError(
                    f"Cannot publish a post from {old_status} status."
                    f"Restore to draft first."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def publish(self):
        if self.status == self.Status.DELETED:
            raise ValidationError("Cannot publish a deleted post. Restore it first.")

        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def archive(self):
        if self.status == self.Status.DELETED:
            raise ValidationError("Cannot archive a deleted post. Restore it first.")

        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status", "updated_at"])

    def soft_delete(self):
        if self.status == self.Status.DELETED:
            raise ValidationError("This post is already deleted.")

        self.status = self.Status.DELETED
        self.save(update_fields=["status", "updated_at"])

    def restore(self):
        if self.status != self.Status.DELETED:
            raise ValidationError("Only deleted posts can be restored.")

        self.status = self.Status.DRAFT
        self.save(update_fields=["status", "updated_at"])

    def change_status(self, new_status):
        if self.status == self.Status.DELETED:
            raise ValidationError("Cannot change status of a deleted post.")

        if new_status.lower() not in self.Status.values:
            raise ValidationError(f"Invalid status: {new_status}")

        transition_rules = {
            self.Status.DRAFT: [self.Status.PUBLISHED, self.Status.DELETED],
            self.Status.PUBLISHED: [self.Status.ARCHIVED, self.Status.DELETED],
            self.Status.ARCHIVED: [self.Status.DRAFT, self.Status.DELETED],
        }

        if new_status not in transition_rules.get(self.status, []):
            raise ValidationError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        if new_status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()

        self.status = new_status
        update_fields = ["status", "updated_at"]
        if new_status == self.Status.PUBLISHED:
            update_fields.append("published_at")

        self.save(update_fields=update_fields)

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
