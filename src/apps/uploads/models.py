import uuid

from django.core.validators import RegexValidator
from django.db import models
from utils.base_models import BaseModel

from apps.uploads.managers import UploadManager
from apps.uploads.storage import get_media_storage
from apps.uploads.utils import get_upload_path


class Upload(BaseModel):
    class Purpose(models.TextChoices):
        AVATAR = "avatar", "Avatar"
        THUMBNAIL = "thumbnail", "Thumbnail"
        ATTACHMENT = "attachment", "Attachment"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        INHERIT = "inherit", "Inherit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to=get_upload_path,
        storage=get_media_storage,
        max_length=512,
    )
    uploaded_by = models.ForeignKey(
        to="accounts.User",
        on_delete=models.CASCADE,
        related_name="uploads",
    )
    original_filename = models.CharField(max_length=256)
    mime_type = models.CharField(max_length=128)
    hash_sha256 = models.CharField(
        max_length=64,
        editable=False,
        validators=[RegexValidator(r"^[a-fA-F0-9]{64}$")],
        db_index=True,
    )
    size = models.PositiveIntegerField(editable=False)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    purpose = models.CharField(
        max_length=32,
        choices=Purpose.choices,
        default=Purpose.ATTACHMENT,
    )
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.INHERIT,
        db_index=True,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = UploadManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hash_sha256"]),
            models.Index(fields=["uploaded_by", "created_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.purpose}"
