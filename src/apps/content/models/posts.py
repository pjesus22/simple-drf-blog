from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from utils.base_models import BaseModel

from apps.content.managers import PostManager, PostQueryset
from apps.content.mixins import SlugMixin


class Post(SlugMixin, BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
        DELETED = "deleted", "Deleted"

    objects = PostManager()
    all_objects = PostQueryset.as_manager()
    ALLOWED_TRANSITIONS = {
        Status.DRAFT: {Status.PUBLISHED, Status.DELETED},
        Status.PUBLISHED: {Status.ARCHIVED, Status.DELETED},
        Status.ARCHIVED: {Status.DRAFT, Status.DELETED},
        Status.DELETED: {Status.DRAFT},
    }

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
    slug = models.SlugField(max_length=128, unique=True)
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

    def transition_to(self, new_status):
        if not self.pk:
            raise ValidationError("Cannot transition an unsaved object.")

        with transaction.atomic():
            locked = (
                Post.all_objects.select_for_update()
                .only("status", "published_at")
                .get(pk=self.pk)
            )

            if new_status not in self.Status.values:
                raise ValidationError(f"Invalid status: {new_status}.")

            if new_status == locked.status:
                return

            allowed = self.ALLOWED_TRANSITIONS.get(locked.status, set())

            if new_status not in allowed:
                raise ValidationError(
                    f"Cannot transition from {locked.status} to {new_status}"
                )

            if new_status == self.Status.PUBLISHED and locked.published_at is None:
                locked.published_at = timezone.now()

            locked.status = new_status
            locked.save()
            self.refresh_from_db(fields=["status", "published_at"])

    def publish(self):
        self.transition_to(self.Status.PUBLISHED)

    def archive(self):
        self.transition_to(self.Status.ARCHIVED)

    def soft_delete(self):
        if self.is_deleted:
            raise ValidationError(message="This post is already deleted.")

        self.transition_to(self.Status.DELETED)

    def restore(self):
        if not (self.is_deleted or self.is_archived):
            raise ValidationError(message="This post is not deleted or archived.")

        self.transition_to(self.Status.DRAFT)

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
