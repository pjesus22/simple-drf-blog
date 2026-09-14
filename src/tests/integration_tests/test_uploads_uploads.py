from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
import pytest
from rest_framework import status

from apps.uploads.models import Upload
from apps.uploads.services import UploadService
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


class TestCreateUpload:
    def test_create_upload_success(self, editor_client):
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
        attributes = data["attributes"]

        assert data.get("type") == "uploads"
        assert settings.MEDIA_URL in attributes["url"]
        assert "attachment" in attributes["url"]

        assert attributes["original_filename"] == "test_text.txt"
        assert attributes["visibility"] == "inherit"
        assert attributes["mime_type"] == "text/plain"
        assert attributes["size"] == 4
        assert attributes["width"] is None
        assert attributes["height"] is None
        assert attributes["purpose"] == "attachment"

        relationships = data.get("relationships")
        assert "uploaded_by" in relationships
        assert relationships["uploaded_by"]["data"]["id"] == str(client_user.id)
        assert relationships["uploaded_by"]["data"]["type"] == "users"

    @pytest.mark.parametrize(
        "payload, error_detail, error_pointer, error_code",
        [
            pytest.param(
                {},
                "No file was submitted.",
                "/data/attributes/file",
                "required",
                id="missing_file",
            ),
            pytest.param(
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
                id="invalid_purpose",
            ),
            pytest.param(
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
                id="corrupted_file",
            ),
            pytest.param(
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
                id="wrong_extension_for_mime",
            ),
            pytest.param(
                {
                    "file": SimpleUploadedFile(
                        name="large_file.txt",
                        content=b"\x00" * 1024 * 1024 * 11,  # 11MB
                        content_type="text/plain",
                    ),
                },
                (
                    "File size (11,534,336 bytes) exceeds maximum allowed "
                    "(10,485,760 bytes)."
                ),
                "/data",
                "invalid",
                id="large_file",
            ),
            pytest.param(
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
                id="invalid_file_type",
            ),
        ],
    )
    def test_create_upload_bad_request(
        self, editor_client, payload, error_detail, error_pointer, error_code
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
            detail_contains=error_detail,
            pointer=error_pointer,
            code=error_code,
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
    def test_list_uploads_success(self, admin_client, upload_factory):
        client, _ = admin_client
        uploads = upload_factory.create_batch(3)
        upload_ids = {str(u.id) for u in uploads}

        response = client.get(path=reverse("v1:upload-list"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}
        assert upload_ids.issubset(received_ids)

    def test_list_uploads_as_editor_only_shows_own(self, editor_client, upload_factory):
        client, client_user = editor_client
        client_uploads = upload_factory.create_batch(2, uploaded_by=client_user)
        other_uploads = upload_factory.create_batch(2)

        client_upload_ids = {str(u.id) for u in client_uploads}
        other_upload_ids = {str(u.id) for u in other_uploads}

        response = client.get(path=reverse("v1:upload-list"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert client_upload_ids.issubset(received_ids)
        assert not (other_upload_ids & received_ids)

    def test_retrieve_upload_success(self, editor_client, upload_factory):
        client, client_user = editor_client
        upload = upload_factory.create(uploaded_by=client_user)

        response = client.get(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        attributes = data["attributes"]

        assert data["type"] == "uploads"
        assert upload.file.url in attributes["url"]

        assert attributes["original_filename"] == upload.original_filename
        assert attributes["mime_type"] == upload.mime_type
        assert attributes["size"] == upload.size
        assert attributes["width"] == upload.width
        assert attributes["height"] == upload.height
        assert attributes["purpose"] == upload.purpose
        assert attributes["visibility"] == upload.visibility

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
    def test_partial_update_upload_success(self, admin_client, upload_factory):
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
        "data, error_detail, error_pointer, error_code",
        [
            pytest.param(
                {"purpose": "invalid_purpose"},
                "is not a valid choice.",
                "/data/attributes/purpose",
                "invalid_choice",
                id="invalid_purpose",
            ),
            pytest.param(
                {"visibility": "invalid_visibility"},
                "is not a valid choice.",
                "/data/attributes/visibility",
                "invalid_choice",
                id="invalid_visibility",
            ),
        ],
    )
    def test_partial_update_upload_bad_request(
        self,
        admin_client,
        upload_factory,
        data,
        error_detail,
        error_pointer,
        error_code,
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
            detail_contains=error_detail,
            pointer=error_pointer,
            code=error_code,
        )

    def test_partial_update_upload_not_found(self, admin_client):
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

    def test_partial_update_purpose_only_does_not_move_file(
        self, admin_client, upload_factory
    ):
        client, _ = admin_client
        upload = upload_factory.create(
            purpose=Upload.Purpose.AVATAR,
            visibility=Upload.Visibility.INHERIT,
        )
        old_name = upload.file.name

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={"purpose": "attachment"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["attributes"]["purpose"] == "attachment"

        upload.refresh_from_db()
        assert upload.purpose == Upload.Purpose.ATTACHMENT
        assert upload.file.name == old_name
        assert default_storage.exists(old_name)

    def test_partial_update_visibility_and_purpose_keeps_original_purpose_segment(
        self, admin_client, upload_factory
    ):
        client, _ = admin_client
        upload = upload_factory(
            purpose=Upload.Purpose.AVATAR,
            visibility=Upload.Visibility.PRIVATE,
        )
        old_name = upload.file.name
        assert old_name.startswith("private/")
        assert f"{Upload.Purpose.AVATAR}/" in old_name

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={"visibility": "public", "purpose": "attachment"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        attrs = response.json()["data"]["attributes"]
        assert attrs["visibility"] == "public"
        assert attrs["purpose"] == "attachment"

        upload.refresh_from_db()
        assert upload.visibility == Upload.Visibility.PUBLIC
        assert upload.purpose == Upload.Purpose.ATTACHMENT
        assert not upload.file.name.startswith("private/")
        assert f"{Upload.Purpose.AVATAR}/" in upload.file.name
        assert f"{Upload.Purpose.ATTACHMENT}/" not in upload.file.name
        assert not default_storage.exists(old_name)
        assert default_storage.exists(upload.file.name)

    def test_partial_update_empty_body_is_noop(
        self, admin_client, upload_factory, mocker
    ):
        client, _ = admin_client
        upload = upload_factory.create(visibility=Upload.Visibility.PRIVATE)
        old_name = upload.file.name

        move = mocker.spy(UploadService, "change_visibility")
        save = mocker.spy(Upload, "save")

        response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        move.assert_not_called()
        save.assert_not_called()

        upload.refresh_from_db()
        assert upload.file.name == old_name
        assert default_storage.exists(old_name)


class TestUploadContent:
    @staticmethod
    def _url(upload):
        return reverse("v1:upload-content", kwargs={"pk": upload.id})

    def test_owner_can_download_private_upload(self, editor_client, upload_factory):
        client, user = editor_client
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == upload.mime_type
        assert response["Content-Disposition"] == (
            f'inline; filename="{upload.original_filename}"'
        )
        assert response["Content-Length"] == str(upload.size)
        assert response["Cache-Control"] == "private, no-store"

        body = b"".join(response.streaming_content)
        with upload.file.open("rb") as fh:
            assert body == fh.read()

    def test_admin_can_download_other_users_private_upload(
        self, admin_client, editor_factory, upload_factory
    ):
        client, _ = admin_client
        owner = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=owner)

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_200_OK

    def test_other_editor_gets_404(self, editor_client, upload_factory):
        client, _ = editor_client
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_gets_401(self, api_client, upload_factory):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)

        response = api_client.get(self._url(upload))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_public_upload_gets_404(self, editor_client, upload_factory):
        client, user = editor_client
        upload = upload_factory(visibility=Upload.Visibility.PUBLIC, uploaded_by=user)

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_trashed_upload_gets_404(self, editor_client, upload_factory):
        client, user = editor_client
        upload = upload_factory(
            visibility=Upload.Visibility.PRIVATE,
            uploaded_by=user,
            deleted_at=timezone.now(),
        )

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_accel_redirect_header_when_enabled(
        self, editor_client, upload_factory, settings
    ):
        settings.USE_X_ACCEL_REDIRECT = True
        client, user = editor_client
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)

        response = client.get(self._url(upload))

        assert response.status_code == status.HTTP_200_OK
        assert response["X-Accel-Redirect"] == (f"/internal_media/{upload.file.name}")
        assert response.content == b""

    def test_content_url_404_after_visibility_flip_to_public(
        self, editor_client, upload_factory
    ):
        client, user = editor_client
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)
        content_url = self._url(upload)

        patch_response = client.patch(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={"visibility": "public"},
            format="json",
        )
        assert patch_response.status_code == status.HTTP_200_OK

        response = client.get(content_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        detail = client.get(reverse("v1:upload-detail", kwargs={"pk": upload.id}))
        url_attr = detail.json()["data"]["attributes"]["url"]
        assert settings.MEDIA_URL in url_attr
        assert "content" not in url_attr


class TestDeleteUpload:
    def test_delete_upload_success(self, admin_client, upload_factory):
        client, _ = admin_client
        upload = upload_factory.create()

        response = client.delete(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id})
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Upload.objects.filter(pk=upload.id).exists()

    def test_delete_upload_not_found(self, admin_client):
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


class TestUploadIncludePrivacy:
    def test_include_uploaded_by_does_not_leak_pii(self, editor_client, upload_factory):
        client, client_user = editor_client
        upload = upload_factory(uploaded_by=client_user)

        response = client.get(
            path=reverse("v1:upload-detail", kwargs={"pk": upload.id}),
            data={"include": "uploaded_by"},
        )

        assert response.status_code == status.HTTP_200_OK

        included = response.json().get("included", [])
        users = [r for r in included if r["type"] == "users"]
        assert len(users) == 1

        attributes = users[0].get("attributes", {})
        assert set(attributes.keys()) == {"username", "role"}
        for pii in ("email", "first_name", "last_name", "date_joined", "last_login"):
            assert pii not in attributes

        assert client_user.email not in response.content.decode()


class TestUploadTrashPagination:
    def test_trash_is_paginated(self, admin_client, upload_factory):
        client, admin = admin_client
        upload_factory.create_batch(
            size=12, uploaded_by=admin, deleted_at=timezone.now()
        )

        response = client.get(reverse("v1:upload-trash"))
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["data"]) == 10
        assert body["meta"]["pagination"] == {"page": 1, "pages": 2, "count": 12}
        assert body["links"]["next"] is not None

    def test_trash_second_page(self, admin_client, upload_factory):
        client, admin = admin_client
        upload_factory.create_batch(
            size=12, uploaded_by=admin, deleted_at=timezone.now()
        )

        response = client.get(reverse("v1:upload-trash") + "?page[number]=2")
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(body["data"]) == 2
        assert body["links"]["next"] is None
