from apps.users.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from utils.base_models import BaseModel

from .service import UploadService


class Upload(BaseModel):
    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    class Purpose(models.TextChoices):
        AVATAR = "avatar", "Avatar"
        THUMBNAIL = "thumbnail", "Thumbnail"
        ATTACHMENT = "attachment", "Attachment"

    file = models.FileField(
        upload_to="uploads/%Y%m%d/",
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
        to=User, on_delete=models.SET_NULL, null=True, related_name="uploads"
    )
    original_filename = models.CharField(max_length=250, blank=True)
    file_type = models.CharField(
        max_length=20, choices=FileType.choices, default=FileType.OTHER
    )
    mime_type = models.CharField(max_length=100, blank=True)
    hash_md5 = models.CharField(max_length=32, blank=True, editable=False)
    size = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    purpose = models.CharField(
        max_length=20,
        blank=True,
        choices=Purpose.choices,
        help_text="Optional: defines the purpose of this file for traceability",
    )

    def __str__(self):
        return f"{self.original_filename} ({self.mime_type})"

    def save(self, *args, **kwargs):
        if self.file and (not self.pk or self._state.adding or not self.hash_md5):
            UploadService.update_metadata(self)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["file_type"]),
            models.Index(fields=["uploaded_by", "created_at"]),
            models.Index(fields=["hash_md5"]),
        ]
