import pytest
from apps.content.models import Post
from django.urls import reverse
from rest_framework import status
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


@pytest.fixture
def post_data(category_factory):
    return {
        "title": "Test Post",
        "content": "Test post content",
        "summary": "Test post summary",
    }


class TestCreatePost:
    def test_create_base_post_success(self, editor_client, post_data, category_factory):
        client, client_user = editor_client
        initial_state = Post.objects.count()
        category = category_factory()
        data = post_data.copy()
        data["category"] = {"type": "categories", "id": str(category.id)}

        response = client.post(
            path=reverse("v1:post-list"),
            data=data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == initial_state + 1

        data = response.json().get("data")

        assert Post.objects.filter(pk=data.get("id")).exists()
        assert data["type"] == "posts"
        assert data["attributes"]["title"] == post_data["title"]
        assert data["attributes"]["slug"] == "test-post"
        assert data["attributes"]["content"] == post_data["content"]
        assert data["attributes"]["summary"] == post_data["summary"]
        assert data["attributes"]["status"] == "draft"
        assert data["attributes"]["published_at"] is None

        relationships = data.get("relationships")

        assert relationships["category"]["data"]["id"] == str(category.id)
        assert relationships["category"]["data"]["type"] == "categories"
        assert relationships["author"]["data"]["id"] == str(client_user.id)
        assert relationships["author"]["data"]["type"] == "users"

    @pytest.mark.parametrize(
        "field, detail, pointer, code",
        [
            ("title", "required.", "/data/attributes/title", "required"),
            ("content", "required.", "/data/attributes/content", "required"),
            ("category", "required.", "/data/relationships/category", "required"),
        ],
        ids=["missing-title", "missing-content", "missing-category"],
    )
    def test_create_post_bad_request_missing_fields(
        self, editor_client, post_data, field, detail, pointer, code, category_factory
    ):
        client, _ = editor_client
        data = post_data.copy()
        category = category_factory()
        data["category"] = {"type": "categories", "id": str(category.id)}

        del data[field]

        response = client.post(
            path=reverse("v1:post-list"),
            data=data,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains=detail,
            pointer=pointer,
            code=code,
        )

    @pytest.mark.parametrize(
        "field, field_type, field_id, many",
        [
            ("category", "categories", 0, False),
            ("tags", "tags", 0, True),
            (
                "thumbnail",
                "uploads",
                "00000000-0000-4000-a000-000000000000",
                False,
            ),
            (
                "attachments",
                "uploads",
                "00000000-0000-4000-a000-000000000000",
                True,
            ),
        ],
        ids=[
            "invalid-category",
            "invalid-tags",
            "invalid-thumbnail",
            "invalid-attachments",
        ],
    )
    def test_create_post_bad_request_relationship_does_not_exists(
        self,
        editor_client,
        post_data,
        category_factory,
        field,
        field_type,
        field_id,
        many,
    ):
        client, _ = editor_client
        category = category_factory()

        payload = {
            **post_data,
            "category": {"type": "categories", "id": str(category.id)},
        }

        data = {"type": field_type, "id": field_id}
        payload[field] = [data] if many else data

        response = client.post(
            path=reverse("v1:post-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="does not exist",
            pointer=f"/data/relationships/{field}",
            code="does_not_exist",
        )

    def test_create_post_bad_request_invalid_status(
        self, editor_client, post_data, category_factory
    ):
        client, _ = editor_client
        category = category_factory()

        payload = {
            **post_data,
            "category": {"type": "categories", "id": str(category.id)},
        }
        payload["status"] = "invalid"

        response = client.post(
            path=reverse("v1:post-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="not a valid choice",
            pointer="/data/attributes/status",
            code="invalid_choice",
        )

    def test_create_post_unauthorized(self, api_client, post_data, category_factory):
        client = api_client
        category = category_factory()

        payload = {
            **post_data,
            "category": {"type": "categories", "id": str(category.id)},
        }

        response = client.post(
            path=reverse("v1:post-list"),
            data=payload,
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )


class TestReadPost:
    @pytest.mark.parametrize(
        "fixture_client, expected_count",
        [("api_client", 2), ("editor_client", 4), ("admin_client", 6)],
        ids=["public", "editor", "admin"],
    )
    def test_list_post_success(
        self, fixture_client, expected_count, request, post_factory, editor_factory
    ):
        fixture_value = request.getfixturevalue(fixture_client)
        client, client_user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )
        draft_author = client_user or editor_factory()
        private_posts = post_factory.create_batch(
            size=2,
            status="draft",
            author=draft_author,
        )
        other_private_posts = post_factory.create_batch(size=2, status="draft")
        published_posts = post_factory.create_batch(
            size=2,
            status="published",
        )
        # Deleted posts should be excluded from all listings
        deleted_posts = post_factory.create_batch(
            size=2,
            status="deleted",
        )
        post_ids = {
            str(p.id) for p in private_posts + published_posts + other_private_posts
        }
        deleted_ids = {str(p.id) for p in deleted_posts}

        response = client.get(path=reverse("v1:post-list"))
        data = response.json().get("data")
        received_ids = {item.get("id") for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert len(data) == expected_count
        assert received_ids.issubset(post_ids)
        # Verify deleted posts are not in the response
        assert not received_ids.intersection(deleted_ids)

    @pytest.mark.parametrize(
        "fixture_client, post_status, own_post",
        [
            ("api_client", "published", False),
            ("editor_client", "draft", True),
            ("admin_client", "archived", False),
        ],
        ids=["public-published", "editor-own-draft", "admin-other-archived"],
    )
    def test_retrieve_post_success(
        self,
        fixture_client,
        post_status,
        own_post,
        request,
        post_factory,
        clean_media,
    ):
        fixture_value = request.getfixturevalue(fixture_client)
        client, client_user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )

        if own_post:
            post = post_factory(status=post_status, author=client_user)
        else:
            post = post_factory(status=post_status)

        response = client.get(path=reverse("v1:post-detail", args=[post.slug]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["id"] == str(post.id)
        assert data["type"] == "posts"
        assert data["attributes"]["title"] == post.title
        assert data["attributes"]["slug"] == post.slug
        assert data["attributes"]["content"] == post.content
        assert data["attributes"]["summary"] == post.summary
        assert data["attributes"]["status"] == post.status

        relationships = data["relationships"]

        assert relationships["category"]["data"]["id"] == str(post.category.id)
        assert relationships["author"]["data"]["id"] == str(post.author.id)
        assert relationships["tags"]["data"] == []
        assert relationships["attachments"]["data"] == []
        assert relationships["thumbnail"]["data"] is None

    def test_retrieve_post_not_found(self, api_client):
        client = api_client

        response = client.get(path=reverse("v1:post-detail", args=["invalid-slug"]))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Post matches",
            code="not_found",
        )


class TestPartialUpdatePost:
    def test_partial_update_post_success(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        new_data = {
            "title": "Updated Title",
            "content": "Updated Content",
            "summary": "Updated Summary",
        }

        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data=new_data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        attrs = data["attributes"]

        assert attrs["title"] == new_data["title"]
        assert attrs["content"] == new_data["content"]
        assert attrs["summary"] == new_data["summary"]

        post.refresh_from_db()
        assert post.title == new_data["title"]
        assert post.content == new_data["content"]
        assert post.summary == new_data["summary"]

    def test_partial_update_post_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data={"title": "New Title"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )

    def test_partial_update_post_forbidden_not_owner(
        self, editor_client, post_factory, editor_factory
    ):
        client, _ = editor_client
        other_editor = editor_factory()
        post = post_factory(author=other_editor, status="published")

        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data={"title": "New Title"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="not have permission",
            pointer="/data",
            code="permission_denied",
        )

    def test_partial_update_post_bad_request_unique_slug(
        self, editor_client, post_factory
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        other_post = post_factory(slug="other-slug")

        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data={"slug": other_post.slug},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="slug already exists",
            pointer="/data/attributes/slug",
            code="unique",
        )


class TestDeletePost:
    def test_delete_post_method_not_allowed(self, editor_client, post_factory):
        """DELETE method should return 405 Method Not Allowed - use soft_delete instead"""
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.delete(path=reverse("v1:post-detail", args=[post.slug]))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_post_method_not_allowed_unauthenticated(
        self, api_client, post_factory
    ):
        """Unauthenticated DELETE returns 401 since auth check happens first"""
        client = api_client
        post = post_factory()

        response = client.delete(path=reverse("v1:post-detail", args=[post.slug]))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )


class TestChangePostStatus:
    def test_change_status_draft_to_published_success(
        self, editor_client, post_factory
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user, status="draft")

        response = client.post(
            path=reverse("v1:post-change-status", args=[post.slug]),
            data={"status": "published"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["status"] == "published"
        assert data["attributes"]["published_at"] is not None

        post.refresh_from_db()
        assert post.status == "published"
        assert post.published_at is not None

    def test_change_status_published_to_archived_success(
        self, editor_client, post_factory
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user, status="published")
        original_published_at = post.published_at

        response = client.post(
            path=reverse("v1:post-change-status", args=[post.slug]),
            data={"status": "archived"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["status"] == "archived"

        post.refresh_from_db()
        assert post.status == "archived"
        assert post.published_at == original_published_at

    def test_change_status_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.post(
            path=reverse("v1:post-change-status", args=[post.slug]),
            data={"status": "published"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )

    def test_change_status_invalid_status_bad_request(
        self, editor_client, post_factory
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.post(
            path=reverse("v1:post-change-status", args=[post.slug]),
            data={"status": "invalid_status"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="not a valid choice",
            pointer="/data/attributes/status",
            code="invalid_choice",
        )


class TestSoftDeletePost:
    def test_soft_delete_post_success(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user, status="draft")
        initial_count = Post.objects.with_deleted().count()

        response = client.post(
            path=reverse("v1:post-soft-delete", args=[post.slug]),
            data={"confirm": True},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Post still exists in database (use with_deleted to include deleted posts)
        assert Post.objects.with_deleted().count() == initial_count
        post.refresh_from_db()
        assert post.status == "deleted"

    def test_soft_delete_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.post(
            path=reverse("v1:post-soft-delete", args=[post.slug]),
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )

    def test_soft_delete_forbidden_not_owner(
        self, editor_client, post_factory, editor_factory
    ):
        """Test that soft deleting a post not owned by user returns 404

        Note: Returns 404 instead of 403 because the soft_delete action queryset
        uses owned_by(user), which filters out posts not owned by the user.
        """
        client, _ = editor_client
        other_editor = editor_factory()
        post = post_factory(author=other_editor, status="published")

        response = client.post(
            path=reverse("v1:post-soft-delete", args=[post.slug]),
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Post matches",
            code="not_found",
        )


class TestRestorePost:
    def test_restore_post_success(self, admin_client, post_factory):
        client, _ = admin_client
        post = post_factory(status="deleted")

        response = client.post(
            path=reverse("v1:post-restore", args=[post.slug]),
            data={"confirm": True},
            query_params={"include_deleted": "true"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["status"] == "draft"

        post.refresh_from_db()
        assert post.status == "draft"

    def test_restore_non_deleted_post_bad_request(self, admin_client, post_factory):
        client, _ = admin_client
        post = post_factory(status="draft")

        response = client.post(
            path=reverse("v1:post-restore", args=[post.slug]),
            data={"confirm": True},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="Only deleted posts can be restored",
            code="not_deleted",
        )

    def test_restore_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory(status="deleted")

        response = client.post(
            path=reverse("v1:post-restore", args=[post.slug]),
            data={"confirm": True},
            query_params={"include_deleted": "true"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )

    def test_restore_forbidden_non_admin(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user, status="deleted")

        response = client.post(
            path=reverse("v1:post-restore", args=[post.slug]),
            data={"confirm": True},
            query_params={"include_deleted": "true"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="not have permission",
            pointer="/data",
            code="permission_denied",
        )


class TestManagePostThumbnail:
    def test_add_thumbnail_success(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        thumbnail = upload_factory(purpose="thumbnail")

        response = client.post(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
            data={"id": str(thumbnail.id)},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["relationships"]["thumbnail"]["data"]["id"] == str(thumbnail.id)

        post.refresh_from_db()
        assert post.thumbnail == thumbnail

    def test_remove_thumbnail_success(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        thumbnail = upload_factory(purpose="thumbnail")
        post = post_factory(author=client_user, thumbnail=thumbnail)

        response = client.delete(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        post.refresh_from_db()
        assert post.thumbnail is None

    def test_add_thumbnail_invalid_id_bad_request(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.post(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
            data={"id": "00000000-0000-4000-a000-000000000000"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="Invalid thumbnail upload",
            pointer="/data/attributes/id",
            code="invalid",
        )

    def test_add_thumbnail_non_thumbnail_upload_bad_request(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        attachment = upload_factory(purpose="attachment")

        response = client.post(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
            data={"id": str(attachment.id)},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="Invalid thumbnail upload",
            pointer="/data/attributes/id",
            code="invalid",
        )

    def test_add_thumbnail_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.post(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
            data={"id": "00000000-0000-4000-a000-000000000000"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )


class TestManagePostAttachments:
    def test_add_attachments_success(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        attachments = upload_factory.create_batch(size=2, purpose="attachment")
        attachment_ids = [str(att.id) for att in attachments]

        response = client.post(
            path=reverse("v1:post-add-attachments", args=[post.slug]),
            data={"attachments": attachment_ids},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        received_attachment_ids = {
            item["id"] for item in data["relationships"]["attachments"]["data"]
        }
        assert set(attachment_ids).issubset(received_attachment_ids)

        post.refresh_from_db()
        assert post.attachments.count() == 2

    def test_add_attachments_invalid_ids_bad_request(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.post(
            path=reverse("v1:post-add-attachments", args=[post.slug]),
            data={
                "attachments": [
                    "00000000-0000-4000-a000-000000000000",
                    "00000000-0000-4000-a000-000000000001",
                ]
            },
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="One or more attachments are invalid",
            pointer="/data/attributes/attachments",
            code="invalid",
        )

    def test_add_attachments_empty_list_bad_request(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.post(
            path=reverse("v1:post-add-attachments", args=[post.slug]),
            data={"attachments": []},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/attachments",
        )

    def test_add_attachments_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.post(
            path=reverse("v1:post-add-attachments", args=[post.slug]),
            data={"attachments": ["00000000-0000-4000-a000-000000000000"]},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )

    def test_remove_attachment_success(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        attachment = upload_factory(purpose="attachment")
        post = post_factory(author=client_user)
        post.attachments.add(attachment)

        response = client.delete(
            path=reverse(
                "v1:post-remove-attachment", args=[post.slug, str(attachment.id)]
            ),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        post.refresh_from_db()
        assert post.attachments.count() == 0

    def test_remove_attachment_not_in_post_bad_request(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        attachment = upload_factory(purpose="attachment")

        response = client.delete(
            path=reverse(
                "v1:post-remove-attachment", args=[post.slug, str(attachment.id)]
            ),
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="Attachment not found in this post",
            pointer="/data/attributes/attachment_id",
            code="invalid",
        )

    def test_remove_attachment_unauthorized(self, api_client, post_factory):
        client = api_client
        post = post_factory()

        response = client.delete(
            path=reverse(
                "v1:post-remove-attachment",
                args=[post.slug, "00000000-0000-4000-a000-000000000000"],
            ),
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided",
        )
