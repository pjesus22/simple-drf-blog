from dataclasses import dataclass
from typing import Optional

from apps.accounts.models import User
from apps.uploads.exceptions import (
    InvalidFileError,
    InvalidPurposeError,
    InvalidVisibilityError,
)
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .models import Upload
from .utils import FileProcessor


@dataclass(frozen=True)
class FileMetadata:
    mime_type: str
    hash_sha256: str
    size: int
    original_filename: str
    width: int | None = None
    height: int | None = None


class UploadService:
    """
    Service layer responsible for upload creation, deduplication
    and metadata synchronization.
    """

    def __init__(
        self,
        uploaded_by: User,
        purpose: Optional[str] = None,
        visibility: Optional[str] = None,
    ):
        self.uploaded_by = uploaded_by
        self.purpose = purpose or Upload.Purpose.ATTACHMENT
        self.visibility = visibility or Upload.Visibility.INHERIT

        self._validate_choices()

    def create_or_get_upload(self, file: UploadedFile) -> Upload:
        """Create or reuse an Upload from an uploaded file."""
        self._validate_file(file)

        metadata = self._process_file(file)

        with transaction.atomic():
            upload, _ = Upload.objects.get_or_create(
                hash_sha256=metadata.hash_sha256,
                defaults=self._build_defaults(metadata, file),
            )

        return upload

    def update_metadata(self, upload: Upload) -> Upload:
        """
        Recalculate and persist metadata derivable from the stored file.

        This is a technical repair/synchronization operation intended for
        migrations or recovery from corrupted data.

        Only metadata that can be deterministically derived from file contents
        is updated (e.g. hash, size, mime type, image dimensions).
        Semantic domain data such as `original_filename` is preserved and
        never inferred or repaired.
        """
        self._validate_file(upload.file)

        metadata = self._process_file(
            upload.file,
            file_name=upload.original_filename,
        )

        self._apply_metadata(upload, metadata)
        upload.save(
            update_fields=[
                "mime_type",
                "hash_sha256",
                "size",
                "original_filename",
                "width",
                "height",
            ]
        )

        return upload

    def _validate_choices(self) -> None:
        if self.purpose not in Upload.Purpose.values:
            raise InvalidPurposeError(f"Value '{self.purpose}' is not a valid purpose")

        if self.visibility not in Upload.Visibility.values:
            raise InvalidVisibilityError(
                f"Value '{self.visibility}' is not a valid visibility"
            )

    @staticmethod
    def _validate_file(file: UploadedFile | None) -> None:
        if not file:
            raise InvalidFileError("A file must be provided.")

    @staticmethod
    def _process_file(
        file: UploadedFile, file_name: Optional[str] = None
    ) -> FileMetadata:
        processor = FileProcessor(
            file_obj=file,
            file_name=file_name or file.name,
        )
        metadata = processor.process()

        return FileMetadata(
            mime_type=metadata["mime_type"],
            hash_sha256=metadata["hash_sha256"],
            size=metadata["size"],
            original_filename=metadata["original_filename"],
            width=metadata.get("width"),
            height=metadata.get("height"),
        )

    def _build_defaults(
        self,
        metadata: FileMetadata,
        file: UploadedFile,
    ) -> dict:
        return {
            "file": file,
            "uploaded_by": self.uploaded_by,
            "purpose": self.purpose,
            "visibility": self.visibility,
            "mime_type": metadata.mime_type,
            "size": metadata.size,
            "original_filename": metadata.original_filename,
            "width": metadata.width,
            "height": metadata.height,
        }

    @staticmethod
    def _apply_metadata(upload: Upload, metadata: FileMetadata) -> None:
        upload.mime_type = metadata.mime_type
        upload.hash_sha256 = metadata.hash_sha256
        upload.size = metadata.size
        upload.original_filename = metadata.original_filename
        upload.width = metadata.width
        upload.height = metadata.height
