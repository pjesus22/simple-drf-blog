import hashlib

import pytest
from apps.uploads.exceptions import (
    InvalidFileError,
    InvalidPurposeError,
    InvalidVisibilityError,
)
from apps.uploads.models import Upload
from apps.uploads.services import UploadService
from apps.uploads.tests.helpers import FileFactory as ff

pytestmark = pytest.mark.django_db


def test_upload_service_initialize_service_successfully(editor_factory):
    user = editor_factory()

    service = UploadService(
        uploaded_by=user,
        purpose=Upload.Purpose.ATTACHMENT,
        visibility=Upload.Visibility.PUBLIC,
    )

    assert service.uploaded_by == user
    assert service.purpose == Upload.Purpose.ATTACHMENT
    assert service.visibility == Upload.Visibility.PUBLIC


def test_upload_service_initialize_service_with_defaults(editor_factory):
    user = editor_factory()

    service = UploadService(uploaded_by=user)

    assert service.purpose == Upload.Purpose.ATTACHMENT
    assert service.visibility == Upload.Visibility.INHERIT


def test_upload_service_creates_upload_object_successfully(editor_factory):
    user = editor_factory()
    f = ff.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload = service.create_or_get_upload(file=f)

    assert isinstance(upload, Upload)
    assert Upload.objects.filter(pk=upload.pk).exists()
    assert upload.uploaded_by == user
    assert upload.purpose == Upload.Purpose.ATTACHMENT
    assert upload.visibility == Upload.Visibility.INHERIT
    assert upload.size == f.size
    assert upload.original_filename == f.name
    assert Upload.objects.count() == 1


def test_upload_service_updates_metadata_successfully(upload_factory, clean_media):
    f = ff.create_real_image_file()
    expected_hash = hashlib.sha256(f.read()).hexdigest()
    upload = upload_factory(
        file=f,
        size=10240,
        hash_sha256=hashlib.sha256(b"wrong").hexdigest(),
        mime_type="text/plain",
        width=100,
        height=100,
    )
    service = UploadService(uploaded_by=upload.uploaded_by)

    updated_upload = service.update_metadata(upload)

    assert updated_upload.size == f.size
    assert updated_upload.hash_sha256 == expected_hash
    assert updated_upload.mime_type == "image/png"
    assert upload.width, upload.height == (64, 64)


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
    ids=["invalid_purpose", "invalid_visibility"],
)
def test_upload_service_validate_choice(
    editor_factory, purpose, visibility, error, detail
):
    user = editor_factory()
    with pytest.raises(error, match=detail):
        UploadService(uploaded_by=user, purpose=purpose, visibility=visibility)


def test_upload_service_validate_file(editor_factory):
    with pytest.raises(InvalidFileError, match="Invalid file provided."):
        UploadService._validate_file(file=None)
