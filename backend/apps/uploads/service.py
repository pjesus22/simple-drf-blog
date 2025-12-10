import os
from typing import Optional

from apps.users.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .models import Upload
from .utils import FileProcessor


class UploadService:
    """Service layer for handling file uploads, metadata processing and
    deduplication."""

    def __init__(
        self,
        uploaded_by: User,
        purpose: Optional[str] = None,
    ):
        self.uploaded_by = uploaded_by
        self.purpose = purpose or Upload.Purpose.ATTACHMENTS

        if self.purpose not in Upload.Purpose.values:
            raise ValidationError(
                {"purpose": [f"Value '{self.purpose}' is not a valid choice."]}
            )

    @transaction.atomic
    def create_upload(self, file: UploadedFile) -> Upload:
        """Creates a new upload instance."""
        if not file:
            raise ValidationError("A file must be provided to create an upload")

        try:
            processor = FileProcessor(file_obj=file, file_name=file.name)
            meta = processor.process()
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error processing file metadata: {e}")

        existing_upload = Upload.objects.filter(hash_md5=meta["hash_md5"]).first()

        if existing_upload and os.path.exists(existing_upload.file.path):
            file_to_save = existing_upload.file
        else:
            file_to_save = file

        upload = Upload.objects.create(
            file=file_to_save,
            uploaded_by=self.uploaded_by,
            purpose=self.purpose,
            mime_type=meta["mime_type"],
            hash_md5=meta["hash_md5"],
            size=meta["size"],
            original_filename=meta["original_filename"],
            file_type=meta["file_type"],
            width=meta.get("width"),
            height=meta.get("height"),
        )

        return upload

    @staticmethod
    def update_metadata(upload: Upload) -> Upload:
        """Utility to re-process metadata for an existing upload.

        Destined for migrations or fixing corrupted data.
        """
        if not upload.file:
            raise ValidationError("No file provided for metadata extraction.")
        try:
            processor = FileProcessor(file_obj=upload.file, file_name=upload.file.name)
            meta = processor.process()

            upload.mime_type = meta["mime_type"]
            upload.hash_md5 = meta["hash_md5"]
            upload.size = meta["size"]
            upload.original_filename = meta["original_filename"]
            upload.file_type = meta["file_type"]
            upload.width = meta.get("width")
            upload.height = meta.get("height")

            upload.save()

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected error processing file: {e}")

        return upload
