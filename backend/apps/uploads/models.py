from apps.users.models import User
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from utils.base_models import BaseModel

from .utils import get_upload_path


class Upload(BaseModel):
    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    class Purpose(models.TextChoices):
        AVATARS = "avatars", "Avatars"
        THUMBNAILS = "thumbnails", "Thumbnails"
        ATTACHMENTS = "attachments", "Attachments"

    file = models.FileField(
        upload_to=get_upload_path,
        max_length=250,
        blank=False,
        null=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "jpg",
                    "jpeg",
                    "png",
                    "gif",
                    "mp4",
                    "mov",
                    "avi",
                    "mp3",
                    "wav",
                    "doc",
                    "docx",
                    "pdf",
                ]
            )
        ],
    )
    uploaded_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploads",
    )
    original_filename = models.CharField(max_length=250, blank=True)
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
    )
    mime_type = models.CharField(max_length=100, blank=True)
    hash_md5 = models.CharField(
        max_length=32,
        blank=True,
        editable=False,
        validators=[RegexValidator(r"^[a-fA-F0-9]{32}$")],
    )
    size = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    purpose = models.CharField(
        max_length=20,
        choices=Purpose.choices,
        default=Purpose.ATTACHMENTS,
    )

    def __str__(self):
        return f"{self.original_filename} ({self.mime_type})"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["file_type"]),
            models.Index(fields=["uploaded_by", "created_at"]),
            models.Index(fields=["hash_md5"]),
        ]
