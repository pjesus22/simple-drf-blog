import pytest
from rest_framework.fields import DateTimeField

from apps.uploads.models import Upload
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer


@pytest.fixture
def drf_datetime():
    return DateTimeField()


def test_uploads_serializer_serializes_object_successfully(
    db, upload_factory, clean_media, drf_datetime
):
    upload = upload_factory()
    serializer = UploadSerializer(upload)

    expected = {
        "id": str(upload.id),
        "url": upload.file.url,
        "original_filename": upload.original_filename,
        "mime_type": upload.mime_type,
        "size": upload.size,
        "width": upload.width,
        "height": upload.height,
        "purpose": upload.purpose,
        "visibility": upload.visibility,
        "created_at": drf_datetime.to_representation(upload.created_at),
        "updated_at": drf_datetime.to_representation(upload.updated_at),
        "uploaded_by": {"type": "users", "id": str(upload.uploaded_by.id)},
    }

    assert serializer.data == expected


@pytest.mark.parametrize(
    "visibility, expected_url_is_none",
    [
        (Upload.Visibility.PUBLIC, False),
        (Upload.Visibility.INHERIT, False),
        (Upload.Visibility.PRIVATE, True),
    ],
    ids=("public", "inherit", "private"),
)
def test_get_url_visibility_no_context(
    db, upload_factory, clean_media, visibility, expected_url_is_none
):
    upload = upload_factory(visibility=visibility)
    serializer = UploadSerializer(upload)

    if expected_url_is_none:
        assert serializer.data["url"] is None
    else:
        assert serializer.data["url"] == upload.file.url


@pytest.mark.parametrize(
    "user_type, is_owner, expected_access",
    [
        ("anonymous", False, False),
        ("editor", False, False),
        ("editor", True, True),
        ("admin", False, True),
    ],
    ids=("anonymous", "editor_not_owner", "editor_owner", "admin"),
)
def test_get_url_private_file_access_control(
    db,
    upload_factory,
    editor_factory,
    admin_factory,
    user_type,
    is_owner,
    expected_access,
    rf,
):
    owner = editor_factory()
    other_user = editor_factory()
    admin = admin_factory()

    upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=owner)

    request = rf.get("/")
    if user_type == "anonymous":
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()
    elif user_type == "editor":
        request.user = owner if is_owner else other_user
    elif user_type == "admin":
        request.user = admin

    serializer = UploadSerializer(upload, context={"request": request})

    if expected_access:
        assert serializer.data["url"] == request.build_absolute_uri(upload.file.url)
    else:
        assert serializer.data["url"] is None


def test_upload_create_serializer_requires_file(db):
    serializer = UploadCreateSerializer(data={})
    assert not serializer.is_valid()
    assert "file" in serializer.errors


def test_upload_serializer_file_is_write_only_and_optional(db, upload_factory):
    upload = upload_factory()
    serializer = UploadSerializer(upload)

    assert "file" not in serializer.data

    serializer = UploadSerializer(data={})
    assert serializer.is_valid()
