import hashlib

import pytest
from apps.uploads.exceptions import (
    InvalidFileError,
    InvalidPurposeError,
    InvalidVisibilityError,
)
from apps.uploads.models import Upload
from apps.uploads.services import UploadService

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "purpose, visibility, expected_purpose, expected_visibility",
    [
        (None, None, Upload.Purpose.ATTACHMENT, Upload.Visibility.INHERIT),
        (
            Upload.Purpose.ATTACHMENT,
            Upload.Visibility.PUBLIC,
            Upload.Purpose.ATTACHMENT,
            Upload.Visibility.PUBLIC,
        ),
    ],
    ids=("defaults", "explicit"),
)
def test_upload_service_initialization(
    editor_factory, purpose, visibility, expected_purpose, expected_visibility
):
    user = editor_factory()
    kwargs = {"uploaded_by": user}
    if purpose:
        kwargs["purpose"] = purpose
    if visibility:
        kwargs["visibility"] = visibility

    service = UploadService(**kwargs)

    assert service.uploaded_by == user
    assert service.purpose == expected_purpose
    assert service.visibility == expected_visibility


def test_upload_service_creates_upload_object_successfully(
    editor_factory, file_factory
):
    user = editor_factory()
    file = file_factory.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload = service.create_or_get_upload(file=file)

    assert isinstance(upload, Upload)
    assert Upload.objects.filter(pk=upload.pk).exists()
    assert upload.uploaded_by == user
    assert upload.purpose == Upload.Purpose.ATTACHMENT
    assert upload.visibility == Upload.Visibility.INHERIT
    assert upload.size == file.size
    assert upload.original_filename == file.name
    assert Upload.objects.count() == 1


def test_upload_service_reuses_existing_upload(editor_factory, file_factory):
    user = editor_factory()
    file = file_factory.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload1 = service.create_or_get_upload(file=file)

    file.seek(0)
    upload2 = service.create_or_get_upload(file=file)

    assert upload1.pk == upload2.pk
    assert Upload.objects.count() == 1


def test_upload_service_updates_metadata_successfully(
    upload_factory, file_factory, clean_media
):
    file = file_factory.create_real_image_file()
    file_content = file.read()
    expected_hash = hashlib.sha256(file_content).hexdigest()

    upload = upload_factory(
        file=file,
        size=10240,
        hash_sha256=hashlib.sha256(b"wrong").hexdigest(),
        mime_type="text/plain",
        width=100,
        height=100,
    )

    service = UploadService(uploaded_by=upload.uploaded_by)
    updated_upload = service.update_metadata(upload)

    assert updated_upload.size == len(file_content)
    assert updated_upload.hash_sha256 == expected_hash
    assert updated_upload.mime_type == "image/png"
    assert (updated_upload.width, updated_upload.height) == (64, 64)

    upload.refresh_from_db()
    assert upload.hash_sha256 == expected_hash
    assert upload.size == len(file_content)


@pytest.mark.parametrize(
    "purpose, visibility, error, detail",
    [
        (
            "invalid",
            Upload.Visibility.PUBLIC,
            InvalidPurposeError,
            "is not a valid purpose",
        ),
        (
            Upload.Purpose.ATTACHMENT,
            "invalid",
            InvalidVisibilityError,
            "is not a valid visibility",
        ),
    ],
    ids=("invalid_purpose", "invalid_visibility"),
)
def test_upload_service_validate_choices(
    editor_factory, purpose, visibility, error, detail
):
    user = editor_factory()
    with pytest.raises(error, match=detail):
        UploadService(uploaded_by=user, purpose=purpose, visibility=visibility)


def test_upload_service_validate_file_raises_error_on_missing_file():
    with pytest.raises(InvalidFileError, match="Invalid file provided."):
        UploadService._validate_file(file=None)
