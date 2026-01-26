import io
import os
import re
from unittest.mock import patch

import pytest
from apps.uploads.models import Upload
from apps.uploads.services import UploadService
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

pytestmark = pytest.mark.django_db


def test_create_upload_calls_processor_and_stores_metadata(
    editor_factory, clean_media, mock_file_processor
):
    user = editor_factory.create()

    mock = mock_file_processor()
    service = UploadService(uploaded_by=user)
    upload = service.create_upload(
        file=SimpleUploadedFile(
            name="test.txt",
            content=b"fake file content",
            content_type="text/plain",
        )
    )

    mock.assert_called_once()
    assert upload.uploaded_by == user
    assert upload.mime_type == "text/plain"
    assert upload.original_filename == "test.txt"
    assert upload.file_type == "document"
    assert upload.purpose == "attachments"


def test_create_upload_no_file(editor_factory):
    user = editor_factory.create()
    service = UploadService(uploaded_by=user)

    with pytest.raises(
        ValidationError, match="A file must be provided to create an upload"
    ):
        service.create_upload(file=None)


@pytest.mark.parametrize("purpose", Upload.Purpose.values)
def test_create_upload_generates_correct_path(editor_factory, clean_media, purpose):
    user = editor_factory()

    service = UploadService(uploaded_by=user, purpose=purpose)
    upload = service.create_upload(
        file=SimpleUploadedFile(name="avatar.jpg", content=b"data")
    )

    assert re.match(rf"{purpose}/\d{{8}}/avatar\.jpg", upload.file.name)


def test_create_upload_rejects_invalid_purpose(editor_factory, clean_media):
    user = editor_factory()

    with pytest.raises(
        ValidationError, match="Value 'invalid_purpose' is not a valid choice."
    ):
        UploadService(uploaded_by=user, purpose="invalid_purpose")


def test_create_upload_deduplicates_by_hash(editor_factory, clean_media):
    user = editor_factory()
    service = UploadService(uploaded_by=user)

    upload1 = service.create_upload(
        SimpleUploadedFile(name="file1.txt", content=b"data")
    )

    upload2 = service.create_upload(
        SimpleUploadedFile(name="file2.txt", content=b"data")
    )

    assert upload1.file.path == upload2.file.path
    assert upload1.hash_md5 == upload2.hash_md5


def test_create_upload_deduplication_when_file_missing_on_disk(
    editor_factory, clean_media
):
    user = editor_factory()
    service = UploadService(uploaded_by=user)

    upload1 = service.create_upload(
        SimpleUploadedFile(name="file1.txt", content=b"data")
    )
    file1_path = upload1.file.path
    os.remove(file1_path)

    upload2 = service.create_upload(
        SimpleUploadedFile(name="file2.txt", content=b"data")
    )

    assert upload1.hash_md5 == upload2.hash_md5
    assert os.path.exists(upload2.file.path)


def test_create_upload_rolls_back_on_error(editor_factory, clean_media):
    user = editor_factory()

    with patch(
        "apps.uploads.service.FileProcessor.process",
        side_effect=Exception("Something went wrong"),
    ):
        service = UploadService(uploaded_by=user)
        with pytest.raises(Exception, match="Something went wrong"):
            service.create_upload(
                file=SimpleUploadedFile(name="file.txt", content=b"data")
            )

    with patch(
        "apps.uploads.service.FileProcessor.process",
        side_effect=ValidationError("Something went wrong"),
    ):
        service = UploadService(uploaded_by=user)
        with pytest.raises(ValidationError, match="Something went wrong"):
            service.create_upload(
                file=SimpleUploadedFile(name="file.txt", content=b"data")
            )

    assert Upload.objects.count() == 0


def test_create_upload_integration(editor_factory, clean_media):
    user = editor_factory()

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    service = UploadService(uploaded_by=user, purpose="avatars")
    upload = service.create_upload(
        file=SimpleUploadedFile(
            name="test.png",
            content=img_bytes.read(),
            content_type="image/png",
        )
    )

    assert upload.id is not None
    assert upload.file_type == Upload.FileType.IMAGE
    assert upload.width == 100
    assert upload.height == 100
    assert upload.hash_md5 is not None
    assert os.path.exists(upload.file.path)


def test_create_upload_sanitizes_path_traversal_attempts(editor_factory, clean_media):
    user = editor_factory()
    service = UploadService(uploaded_by=user)

    upload = service.create_upload(
        SimpleUploadedFile(name="../../etc/passwd", content=b"malicious")
    )

    assert ".." not in upload.file.name
    assert upload.original_filename == "passwd"
    assert "attachments/" in upload.file.name


def test_create_upload_handles_null_bytes_in_filename(editor_factory, clean_media):
    user = editor_factory()
    service = UploadService(uploaded_by=user)

    upload = service.create_upload(
        SimpleUploadedFile(name="test\x00.txt", content=b"data")
    )

    assert "\x00" not in upload.file.name


def test_update_metadata_raises_without_file(upload_factory):
    upload = upload_factory.build(file=None)

    with pytest.raises(
        ValidationError, match="No file provided for metadata extraction"
    ):
        UploadService.update_metadata(upload)


def test_update_metadata_with_width_and_height(upload_factory, mock_file_processor):
    upload = upload_factory.create()

    mock_file_processor(
        meta={
            "mime_type": "image/png",
            "hash_md5": "abc123",
            "size": 1024,
            "original_filename": "test.png",
            "file_type": "image",
            "width": 800,
            "height": 600,
        }
    )
    UploadService.update_metadata(upload)

    assert upload.width == 800
    assert upload.height == 600
    assert upload.mime_type == "image/png"


def test_update_metadata_preserves_uploaded_by_and_purpose(
    upload_factory, mock_file_processor
):
    upload = upload_factory.create(purpose=Upload.Purpose.AVATARS)
    original_user = upload.uploaded_by
    original_purpose = upload.purpose

    mock_file_processor(
        meta={
            "mime_type": "image/png",
            "hash_md5": "abc123",
            "size": 1024,
            "original_filename": "test.png",
            "file_type": "image",
            "width": 800,
            "height": 600,
        }
    )
    UploadService.update_metadata(upload)

    assert upload.uploaded_by == original_user
    assert upload.purpose == original_purpose


def test_update_metadata_raises_validation_error(upload_factory):
    upload = upload_factory.create()

    with patch(
        "apps.uploads.utils.file_processor.FileProcessor.process",
        side_effect=ValidationError("Invalid file"),
    ):
        with pytest.raises(ValidationError, match="Invalid file"):
            UploadService.update_metadata(upload)


def test_update_metadata_raises_generic_exception(upload_factory):
    upload = upload_factory.create()

    with patch(
        "apps.uploads.utils.file_processor.FileProcessor.process",
        side_effect=Exception("Unexpected error"),
    ):
        with pytest.raises(Exception, match="Unexpected error"):
            UploadService.update_metadata(upload)
