import pytest
from apps.content.models import Post
from django.urls import reverse
from rest_framework import status

from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


@pytest.fixture
def post_data():
    return {
        "title": "Test Post",
        "content": "Test post content",
        "summary": "Test post summary",
    }


class TestCreatePost:
    def test_create_base_post_success(self, editor_client, post_data, category_factory):
        client, client_user = editor_client
        initial_count = Post.objects.count()
        category = category_factory()

        data = post_data.copy()
        data["category"] = {"type": "categories", "id": str(category.id)}

        response = client.post(
            path=reverse("v1:post-list"),
            data=data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == initial_count + 1

        response_data = response.json().get("data")
        post_id = response_data.get("id")

        assert Post.objects.filter(pk=post_id).exists()
        assert response_data["type"] == "posts"
        assert response_data["attributes"]["title"] == post_data["title"]
        assert response_data["attributes"]["slug"] == "test-post"
        assert response_data["attributes"]["status"] == "draft"
        assert response_data["attributes"]["published_at"] is None

        relationships = response_data.get("relationships")
        assert relationships["category"]["data"]["id"] == str(category.id)
        assert relationships["author"]["data"]["id"] == str(client_user.id)

    @pytest.mark.parametrize(
        "field, detail, pointer, code",
        [
            ("title", "required.", "/data/attributes/title", "required"),
            ("content", "required.", "/data/attributes/content", "required"),
            ("category", "required.", "/data/relationships/category", "required"),
        ],
        ids=("missing-title", "missing-content", "missing-category"),
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
            ("thumbnail", "uploads", "00000000-0000-4000-a000-000000000000", False),
            ("attachments", "uploads", "00000000-0000-4000-a000-000000000000", True),
        ],
        ids=(
            "invalid-category",
            "invalid-tags",
            "invalid-thumbnail",
            "invalid-attachments",
        ),
    )
    def test_create_post_bad_request_relationship_not_found(
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

        rel_data = {"type": field_type, "id": field_id}
        payload[field] = [rel_data] if many else rel_data

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

    def test_create_post_unauthorized(self, api_client, post_data, category_factory):
        category = category_factory()
        payload = {
            **post_data,
            "category": {"type": "categories", "id": str(category.id)},
        }

        response = api_client.post(
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
        ids=("public", "editor", "admin"),
    )
    def test_list_post_success(
        self, fixture_client, expected_count, request, post_factory, editor_factory
    ):
        fixture_value = request.getfixturevalue(fixture_client)
        client, client_user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )

        author = client_user or editor_factory()
        post_factory.create_batch(size=2, status="draft", author=author)
        post_factory.create_batch(size=2, status="draft")
        post_factory.create_batch(size=2, status="published")
        post_factory.create_batch(size=2, status="deleted")

        response = client.get(path=reverse("v1:post-list"))
        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert len(data) == expected_count

        for item in data:
            assert item["attributes"]["status"] != "deleted"
            if item["attributes"]["status"] == "draft" and client_user:
                if not client_user.is_staff:
                    assert item["relationships"]["author"]["data"]["id"] == str(
                        client_user.id
                    )

    def test_retrieve_post_success_with_related(
        self, api_client, post_factory, tag_factory, upload_factory, clean_media
    ):
        tags = tag_factory.create_batch(size=2)
        thumbnail = upload_factory(purpose="thumbnail")
        attachments = upload_factory.create_batch(size=2, purpose="attachment")

        post = post_factory(status="published", thumbnail=thumbnail)
        post.tags.set(tags)
        post.attachments.set(attachments)

        response = api_client.get(path=reverse("v1:post-detail", args=[post.slug]))

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")

        assert data["id"] == str(post.id)
        assert len(data["relationships"]["tags"]["data"]) == 2
        assert data["relationships"]["thumbnail"]["data"]["id"] == str(thumbnail.id)
        assert len(data["relationships"]["attachments"]["data"]) == 2

    def test_retrieve_post_not_found(self, api_client):
        response = api_client.get(path=reverse("v1:post-detail", args=["non-existent"]))
        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Post matches",
            code="not_found",
        )


class TestUpdatePost:
    def test_partial_update_post_success(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        new_data = {"title": "Updated Title"}
        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data=new_data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["attributes"]["title"] == "Updated Title"

        post.refresh_from_db()
        assert post.title == "Updated Title"

    def test_update_post_forbidden_not_owner(
        self, editor_client, post_factory, editor_factory
    ):
        client, _ = editor_client
        other_post = post_factory(author=editor_factory(), status="published")

        response = client.patch(
            path=reverse("v1:post-detail", args=[other_post.slug]),
            data={"title": "Trying to update"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            code="permission_denied",
        )

    def test_update_post_bad_request_duplicate_slug(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        post_factory(slug="existing-slug")

        response = client.patch(
            path=reverse("v1:post-detail", args=[post.slug]),
            data={"slug": "existing-slug"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/slug",
            code="unique",
        )


class TestDeletePost:
    def test_hard_delete_not_allowed(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.delete(path=reverse("v1:post-detail", args=[post.slug]))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_soft_delete_success(self, editor_client, post_factory):
        client, client_user = editor_client
        post = post_factory(author=client_user)

        response = client.post(
            path=reverse("v1:post-soft-delete", args=[post.slug]),
            data={"confirm": True},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        post.refresh_from_db()
        assert post.status == "deleted"

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
        post.refresh_from_db()
        assert post.status == "draft"


class TestPostLifecycle:
    @pytest.mark.parametrize(
        "initial_status, target_status, expected_published",
        [
            ("draft", "published", True),
            ("published", "archived", True),
        ],
        ids=("draft-to-published", "published-to-archived"),
    )
    def test_change_status_transitions(
        self,
        editor_client,
        post_factory,
        initial_status,
        target_status,
        expected_published,
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user, status=initial_status)
        if initial_status != "draft":
            from django.utils import timezone

            post.published_at = timezone.now()
            post.save()

        response = client.post(
            path=reverse("v1:post-change-status", args=[post.slug]),
            data={"status": target_status},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.status == target_status
        if expected_published:
            assert post.published_at is not None

    def test_manage_thumbnail_flow(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user, thumbnail=None)
        thumbnail = upload_factory(purpose="thumbnail")

        # Add
        response = client.post(
            path=reverse("v1:post-thumbnail", args=[post.slug]),
            data={"id": str(thumbnail.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.thumbnail == thumbnail

        # Remove
        response = client.delete(path=reverse("v1:post-thumbnail", args=[post.slug]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        post.refresh_from_db()
        assert post.thumbnail is None

    def test_manage_attachments_flow(
        self, editor_client, post_factory, upload_factory, clean_media
    ):
        client, client_user = editor_client
        post = post_factory(author=client_user)
        attachments = upload_factory.create_batch(size=2, purpose="attachment")

        # Add
        response = client.post(
            path=reverse("v1:post-add-attachments", args=[post.slug]),
            data={"attachments": [str(a.id) for a in attachments]},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert post.attachments.count() == 2

        # Remove one
        response = client.delete(
            path=reverse(
                "v1:post-remove-attachment", args=[post.slug, str(attachments[0].id)]
            )
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert post.attachments.count() == 1
