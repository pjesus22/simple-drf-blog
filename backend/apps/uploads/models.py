from apps.users.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from utils.base_models import BaseModel
from utils.file_tools import FileProcessor


class Upload(BaseModel):
    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    file = models.FileField(
        upload_to="uploads/%Y/%m/%d/",
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

    def __str__(self):
        return f"{self.original_filename} ({self.mime_type})"

    def _update_metadata(self):
        try:
            processor = FileProcessor(file_obj=self.file, file_name=self.file.name)
            meta = processor.process()

            self.mime_type = meta["mime_type"]
            self.hash_md5 = meta["hash_md5"]
            self.size = meta["size"]
            self.original_filename = meta["original_filename"]
            self.file_type = meta["file_type"]

            if "width" in meta:
                self.width = meta["width"]
                self.height = meta["height"]

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected error processing file: {e}")

    def save(self, *args, **kwargs):
        if self.file and (not self.pk or self._state.adding or not self.hash_md5):
            self._update_metadata()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["file_type"]),
            models.Index(fields=["uploaded_by", "created_at"]),
            models.Index(fields=["hash_md5"]),
        ]
