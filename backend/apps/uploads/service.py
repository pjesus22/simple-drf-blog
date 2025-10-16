import os
from typing import Optional, Type

from apps.users.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.utils import timezone

from .utils import FileProcessor


class UploadService:
    """
    Service layer for handling file uploads and metadata processing
    """

    def __init__(
        self,
        uploaded_by: User,
        upload_model: Type[models.Model],
        purpose: Optional[str] = None,
    ):
        self.uploaded_by = uploaded_by
        self.purpose = purpose or "uploads"
        self.upload_model = upload_model

    def create_upload(
        self, file: UploadedFile, subdir: Optional[str] = None
    ) -> models.Model:
        """
        Creates a new upload instance, processes metadata, and saves it.
        """
        if not file:
            raise ValidationError("A file must be provided to create an upload")

        filename = os.path.basename(file.name)
        final_subdir = subdir or self.purpose
        timestamp = timezone.now().strftime("%Y%m%d")
        file.name = os.path.join(final_subdir, timestamp, filename)

        upload, _ = self.upload_model.objects.get_or_create(
            file=file,
            uploaded_by=self.uploaded_by,
            purpose=self.purpose,
        )

        self.update_metadata(upload)
        upload.save()
        return upload

    @staticmethod
    def update_metadata(upload: models.Model) -> None:
        """
        Processes and updates metadata for a given upload instance.
        """
        if not getattr(upload, "file", None):
            raise ValidationError("No file provided for metadata extraction.")

        try:
            processor = FileProcessor(
                file_obj=upload.file,
                file_name=upload.file.name,
            )
            meta = processor.process()

            upload.mime_type = meta["mime_type"]
            upload.hash_md5 = meta["hash_md5"]
            upload.size = meta["size"]
            upload.original_filename = meta["original_filename"]
            upload.file_type = meta["file_type"]

            if "width" in meta:
                upload.width = meta["width"]
                upload.height = meta["height"]

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected error processing file: {e}")
