import os
from typing import Optional

from apps.accounts.models import User
from apps.uploads.exceptions import InvalidFileError, InvalidPurposeError
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
            raise InvalidPurposeError(f"Value '{self.purpose}' is not a valid choice.")

    @transaction.atomic
    def create_upload(self, file: UploadedFile) -> Upload:
        """Creates a new upload instance."""
        if not file:
            raise InvalidFileError("A file must be provided.")

        processor = FileProcessor(file_obj=file, file_name=file.name)
        meta = processor.process()

        existing = Upload.objects.filter(hash_sha256=meta["hash_sha256"]).first()

        file_to_save = (
            existing.file if existing and os.path.exists(existing.file.path) else file
        )

        return Upload.objects.create(
            file=file_to_save,
            uploaded_by=self.uploaded_by,
            purpose=self.purpose,
            mime_type=meta["mime_type"],
            hash_sha256=meta["hash_sha256"],
            size=meta["size"],
            original_filename=meta["original_filename"],
            file_type=meta["file_type"],
            width=meta.get("width"),
            height=meta.get("height"),
        )

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
            upload.hash_sha256 = meta["hash_sha256"]
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
