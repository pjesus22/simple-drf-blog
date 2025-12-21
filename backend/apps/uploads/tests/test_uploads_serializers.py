from apps.uploads.serializers import UploadSerializer
from rest_framework.fields import DateTimeField
from rest_framework.test import APIRequestFactory

field = DateTimeField()
factory = APIRequestFactory()


def test_uploads_serializer_serializes_object(db, upload_factory):
    upload = upload_factory(
        original_filename="test.jpg",
        file_type="image",
        mime_type="image/jpeg",
        size=1024,
        width=100,
        height=100,
        purpose="test",
        is_public=True,
    )
    serializer = UploadSerializer(upload)
    expected = {
        "id": str(upload.id),
        "url": upload.file.url,
        "original_filename": upload.original_filename,
        "file_type": upload.file_type,
        "mime_type": upload.mime_type,
        "size": upload.size,
        "width": upload.width,
        "height": upload.height,
        "purpose": upload.purpose,
        "is_public": upload.is_public,
        "created_at": field.to_representation(upload.created_at),
        "updated_at": field.to_representation(upload.updated_at),
        "uploaded_by": {"type": "users", "id": str(upload.uploaded_by.id)},
    }

    assert serializer.data == expected


def test_get_url_returns_none_for_private_file_unauthenticated(db, upload_factory):
    upload = upload_factory(is_public=False)
    serializer = UploadSerializer(upload)
    assert serializer.data["url"] is None


def test_get_url_returns_none_for_private_file_wrong_user(
    db, upload_factory, editor_factory
):
    user1 = editor_factory()
    upload = upload_factory(is_public=False, uploaded_by=user1)
    user2 = editor_factory()

    request = factory.get("/")
    request.user = user2

    serializer = UploadSerializer(upload, context={"request": request})
    assert serializer.data["url"] is None


def test_get_url_returns_absolute_uri_for_private_file_correct_user(
    db, upload_factory, editor_factory
):
    user = editor_factory()
    upload = upload_factory(is_public=False, uploaded_by=user)

    request = factory.get("/")
    request.user = user

    serializer = UploadSerializer(upload, context={"request": request})
    assert serializer.data["url"] == request.build_absolute_uri(upload.file.url)
