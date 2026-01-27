from apps.uploads.models import Upload
from apps.uploads.serializers import UploadSerializer
from rest_framework.fields import DateTimeField
from rest_framework.test import APIRequestFactory

field = DateTimeField()
factory = APIRequestFactory()


def test_uploads_serializer_serializes_object_successfully(
    db, upload_factory, clean_media
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
        "created_at": field.to_representation(upload.created_at),
        "updated_at": field.to_representation(upload.updated_at),
        "uploaded_by": {"type": "users", "id": str(upload.uploaded_by.id)},
    }

    assert serializer.data == expected


def test_get_url_returns_none_for_private_file(db, upload_factory, clean_media):
    upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
    serializer = UploadSerializer(upload)
    assert serializer.data["url"] is None


def test_get_url_returns_none_for_private_file_wrong_user(
    db, upload_factory, editor_factory, admin_factory, clean_media
):
    upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
    user = editor_factory()
    request = factory.get("/")
    request.user = user

    serializer = UploadSerializer(upload, context={"request": request})

    assert serializer.data["url"] is None


def test_get_url_returns_absolute_uri_for_private_file_correct_user(
    db, upload_factory, editor_factory, admin_factory, clean_media
):
    editor = editor_factory()
    admin = admin_factory()
    upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=editor)
    request = factory.get("/")

    request.user = editor
    serializer = UploadSerializer(upload, context={"request": request})

    assert serializer.data["url"] == request.build_absolute_uri(upload.file.url)

    request.user = admin
    serializer = UploadSerializer(upload, context={"request": request})

    assert serializer.data["url"] == request.build_absolute_uri(upload.file.url)
