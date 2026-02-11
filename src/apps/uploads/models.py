import uuid

from django.core.validators import RegexValidator
from django.db import models
from utils.base_models import BaseModel

from .utils import get_upload_path


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
    file = models.FileField(upload_to=get_upload_path, max_length=250)
    uploaded_by = models.ForeignKey(
        to="accounts.User",
        on_delete=models.CASCADE,
        related_name="uploads",
    )
    original_filename = models.CharField(max_length=250)
    mime_type = models.CharField(max_length=100)
    hash_sha256 = models.CharField(
        max_length=64,
        editable=False,
        unique=True,
        validators=[RegexValidator(r"^[a-fA-F0-9]{64}$")],
    )
    size = models.PositiveIntegerField(editable=False)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.ATTACHMENT,
    )
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.INHERIT,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hash_sha256"]),
            models.Index(fields=["uploaded_by", "created_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.purpose}"
