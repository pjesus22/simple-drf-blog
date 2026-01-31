import pytest
from apps.uploads.models import Upload
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


class TestCreateUpload:
    def test_create_upload_success(self, editor_client, clean_media):
        client, client_user = editor_client
        initial_state = Upload.objects.count()
        test_file = SimpleUploadedFile(
            name="test_text.txt", content=b"test", content_type="text/plain"
        )

        response = client.post(
            path=reverse("v1:upload-list"),
            data={"file": test_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Upload.objects.count() == initial_state + 1

        data = response.json().get("data")

        assert data.get("type") == "uploads"
        assert "/media/attachment/" in data["attributes"]["url"]
        assert data["attributes"]["original_filename"] == "test_text.txt"
        assert data["attributes"]["visibility"] == "inherit"
        assert data["attributes"]["mime_type"] == "text/plain"
        assert data["attributes"]["size"] == 4
        assert data["attributes"]["width"] is None
        assert data["attributes"]["height"] is None
        assert data["attributes"]["purpose"] == "attachment"

        relationships = data.get("relationships")

        assert "uploaded_by" in relationships
        assert relationships["uploaded_by"]["data"]["id"] == str(client_user.id)
        assert relationships["uploaded_by"]["data"]["type"] == "users"

    @pytest.mark.parametrize(
        "payload, detail_contains, pointer, code",
        [
            (
                {},
                "No file was submitted.",
                "/data/attributes/file",
                "required",
            ),
            (
                {
                    "file": SimpleUploadedFile(
                        name="test_text.txt",
                        content=b"test",
                        content_type="text/plain",
                    ),
                    "purpose": "invalid_purpose",
                },
                "is not a valid choice.",
                "/data/attributes/purpose",
                "invalid_choice",
            ),
            (
                {
                    "file": SimpleUploadedFile(
                        name="corrupt_file.jpg",
                        content=b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 500,
                        content_type="image/jpeg",
                    ),
                },
                "not a valid or supported image.",
                "/data",
                "invalid",
            ),
            (
                {
                    "file": SimpleUploadedFile(
                        name="invalid_file_type.jpg",
                        content=b"Hello World",
                        content_type="text/plain",
                    ),
                },
                "File extension '.jpg' is not allowed for MIME type 'text/plain'.",
                "/data",
                "invalid",
            ),
            (
                {
                    "file": SimpleUploadedFile(
                        name="large_file.txt",
                        content=b"\x00" * 1024 * 1024 * 11,  # 10MB
                        content_type="text/plain",
                    ),
                },
                "size exceeds the limit.",
                "/data",
                "invalid",
            ),
            (
                {
                    "file": SimpleUploadedFile(
                        name="invalid_file_type.exe",
                        content=b"MZ" + b"\x00" * 100,
                        content_type="application/x-msdownload",
                    ),
                },
                "Unsupported MIME type.",
                "/data",
                "invalid",
            ),
        ],
        ids=[
            "missing_file",
            "invalid_purpose",
            "corrupted_file",
            "wrong_extension_for_mime",
            "large_file",
            "invalid_file_type",
        ],
    )
    def test_create_upload_bad_request(
        self, editor_client, payload, detail_contains, pointer, code
    ):
        client, _ = editor_client

        response = client.post(
            path=reverse("v1:upload-list"),
            data=payload,
            format="multipart",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains=detail_contains,
            pointer=pointer,
            code=code,
        )

    def test_create_upload_unauthorized(self, api_client):
        client = api_client

        response = client.post(
            path=reverse("v1:upload-list"),
            data={"file": "test"},
            format="multipart",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )


class TestReadUpload:
    def test_list_uploads_success(self, admin_client, upload_factory, clean_media):
        client, _ = admin_client
        uploads = upload_factory.create_batch(3)
        upload_ids = {str(u.id) for u in uploads}

        response = client.get(path=reverse("v1:upload-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert upload_ids.issubset(received_ids)

    def test_list_uploads_as_editor_only_shows_own(
        self, editor_client, upload_factory, clean_media
    ):
        client, client_user = editor_client
        client_uploads = upload_factory.create_batch(2, uploaded_by=client_user)
        other_uploads = upload_factory.create_batch(2)
        client_upload_ids = {str(u.id) for u in client_uploads}

        response = client.get(path=reverse("v1:upload-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert client_upload_ids.issubset(received_ids)
        assert len(client_uploads + other_uploads) > len(received_ids)

    def test_retrieve_upload_success(self, editor_client, upload_factory, clean_media):
        client, client_user = editor_client
        upload = upload_factory.create(uploaded_by=client_user)

        response = client.get(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["type"] == "uploads"
        assert data["attributes"]["url"] == rf"http://testserver{upload.file.url}"
        assert data["attributes"]["original_filename"] == upload.original_filename
        assert data["attributes"]["mime_type"] == upload.mime_type
        assert data["attributes"]["size"] == upload.size
        assert data["attributes"]["width"] == upload.width
        assert data["attributes"]["height"] == upload.height
        assert data["attributes"]["purpose"] == upload.purpose
        assert data["attributes"]["visibility"] == upload.visibility

    def test_retrieve_upload_not_found(self, editor_client):
        client, _ = editor_client

        response = client.get(
            path=reverse("v1:upload-detail", kwargs={"pk": 0}),
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="Not found",
            code="not_found",
        )

    def test_retrieve_upload_other_user_not_found(self, editor_client, upload_factory):
        client, _ = editor_client
        upload = upload_factory.create()

        response = client.get(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Upload matches",
            code="not_found",
        )


class TestPartialUpdateUpload:
    def test_partial_update_upload_success(
        self, admin_client, upload_factory, clean_media
    ):
        client, _ = admin_client
        upload = upload_factory.create(
            purpose=Upload.Purpose.AVATAR,
            visibility=Upload.Visibility.PRIVATE,
        )

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={
                "purpose": "attachment",
                "visibility": "public",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["purpose"] == "attachment"
        assert data["attributes"]["visibility"] == "public"

    @pytest.mark.parametrize(
        "data, error, pointer, code",
        [
            (
                {"purpose": "invalid_purpose"},
                "is not a valid choice.",
                "/data/attributes/purpose",
                "invalid_choice",
            ),
            (
                {"visibility": "invalid_visibility"},
                "is not a valid choice.",
                "/data/attributes/visibility",
                "invalid_choice",
            ),
        ],
        ids=["invalid_purpose", "invalid_visibility"],
    )
    def test_partial_update_upload_bad_request(
        self, admin_client, upload_factory, clean_media, data, error, pointer, code
    ):
        client, _ = admin_client
        upload = upload_factory.create()

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data=data,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains=error,
            pointer=pointer,
            code=code,
        )

    def test_partial_update_upload_not_found(self, admin_client, upload_factory):
        client, _ = admin_client

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": 0}),
            data={"purpose": "attachment"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="Not found",
            code="not_found",
        )

    def test_partial_update_upload_other_user_not_found(
        self, editor_client, upload_factory
    ):
        client, _ = editor_client
        upload = upload_factory.create()

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={"purpose": "attachment"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Upload matches",
            code="not_found",
        )

    def test_partial_update_upload_unauthorized(self, api_client):
        client = api_client

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": 0}),
            data={"purpose": "attachment"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )


class TestDeleteUpload:
    def test_delete_upload_success(self, admin_client, upload_factory, clean_media):
        client, _ = admin_client
        upload = upload_factory.create()

        response = client.delete(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id})
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_upload_not_found(self, admin_client, upload_factory):
        client, _ = admin_client

        response = client.delete(path=reverse("v1:upload-detail", kwargs={"pk": 0}))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="Not found",
            code="not_found",
        )

    def test_delete_upload_unauthorized(self, api_client):
        client = api_client

        response = client.delete(path=reverse("v1:upload-detail", kwargs={"pk": 0}))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_delete_upload_other_user_not_found(self, editor_client, upload_factory):
        client, _ = editor_client
        upload = upload_factory.create()

        response = client.delete(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id})
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Upload matches",
            code="not_found",
        )
