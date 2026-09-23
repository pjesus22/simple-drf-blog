from dataclasses import dataclass
import logging
import os
from typing import cast

from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.accounts.models import User
from apps.uploads.exceptions import (
    InvalidFileError,
    InvalidPurposeError,
    InvalidVisibilityError,
)
from apps.uploads.utils.path import is_private_storage_path

from .models import Upload
from .utils import FileProcessor

logger = logging.getLogger(__name__)


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
        purpose: str | None = None,
        visibility: str | None = None,
    ):
        self.uploaded_by = uploaded_by
        self.purpose = purpose or Upload.Purpose.ATTACHMENT
        self.visibility = visibility or Upload.Visibility.PRIVATE

        self._validate_choices()

    def create_upload(self, file: UploadedFile) -> Upload:
        """Create an Upload from an uploaded file."""
        self._validate_file(file)

        metadata = self._process_file(file)

        with transaction.atomic():
            upload = Upload.objects.create(
                hash_sha256=metadata.hash_sha256,
                **self._build_defaults(metadata, file),
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
        file = cast(File, upload.file)
        original_filename = cast(str, upload.original_filename)

        self._validate_file(file)

        metadata = self._process_file(file, file_name=original_filename)

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
    def _validate_file(file: File | None) -> None:
        if not file:
            raise InvalidFileError()

    @staticmethod
    def _process_file(file: File, file_name: str | None = None) -> FileMetadata:
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

    @staticmethod
    def _target_path(current_name: str, visibility: str) -> str:
        """Only visibility drives the move; the purpose segment is intentionally
        preserved."""
        relpath = (
            current_name.removeprefix("private/")
            if is_private_storage_path(current_name)
            else current_name
        )

        if visibility == Upload.Visibility.PRIVATE:
            return f"private/{relpath}"

        return relpath

    @staticmethod
    @transaction.atomic
    def change_visibility(upload: Upload, new_visibility: str) -> Upload:
        if new_visibility == upload.visibility:
            return upload

        if new_visibility not in upload.Visibility.values:
            raise InvalidVisibilityError(
                f"Value '{new_visibility}' is not a valid visibility"
            )

        upload = Upload.objects.select_for_update().get(pk=upload.pk)

        old_name = upload.file.name

        if not old_name:
            raise FileNotFoundError("Upload has no file.")

        new_name = UploadService._target_path(old_name, new_visibility)

        if old_name == new_name:
            upload.visibility = new_visibility
            upload.save(update_fields=["visibility", "updated_at"])
            return upload

        if not default_storage.exists(old_name):
            if default_storage.exists(new_name):
                logger.warning(
                    f"Upload {upload.pk} already at target {new_name}; syncing DB"
                )
                upload.file.name = new_name
                upload.visibility = new_visibility
                upload.save(update_fields=["file", "visibility", "updated_at"])
                return upload
            raise FileNotFoundError(old_name)

        if default_storage.exists(new_name):
            raise FileExistsError(new_name)

        if hasattr(default_storage, "path"):
            src = default_storage.path(old_name)
            dst = default_storage.path(new_name)

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(src, dst)
        else:
            with default_storage.open(old_name, "rb") as fh:
                default_storage.save(new_name, fh)

            default_storage.delete(old_name)

        upload.file.name = new_name
        upload.visibility = new_visibility
        upload.save(update_fields=["file", "visibility", "updated_at"])

        return upload
