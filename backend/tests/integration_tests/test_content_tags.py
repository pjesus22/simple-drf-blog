import pytest
from apps.content.models import Tag
from django.urls import reverse
from rest_framework import status


class TestCreateTag:
    def test_create_tag_success(self, db, editor_client):
        client, _ = editor_client
        initial_state = Tag.objects.count()

        response = client.post(
            path=reverse("v1:tag-list"),
            data={"name": "Test Tag"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Tag.objects.count() == initial_state + 1

        data = response.json().get("data")

        assert Tag.objects.filter(pk=data.get("id")).exists()
        assert data["type"] == "tags"
        assert data["attributes"]["name"] == "Test Tag"
        assert data["attributes"]["slug"] == "test-tag"

    @pytest.mark.parametrize(
        "data, expected_error, pointer",
        [
            (
                {"name": "Test Tag", "slug": "unique-slug"},
                "tag with this name already exists.",
                "/data/attributes/name",
            ),
            (
                {"name": "Unique Tag", "slug": "test-tag"},
                "tag with this slug already exists.",
                "/data/attributes/slug",
            ),
            (
                {"name": ""},
                "This field may not be blank.",
                "/data/attributes/name",
            ),
        ],
        ids=("duplicate_name", "duplicate_slug", "blank name"),
    )
    def test_create_tag_bad_request(
        self, db, tag_factory, editor_client, data, expected_error, pointer
    ):
        client, _ = editor_client
        tag_factory(name="Test Tag", slug="test-tag")
        initial_state = Tag.objects.count()

        response = client.post(
            path=reverse("v1:tag-list"),
            data=data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Tag.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == pointer
        assert errors[0]["detail"] == expected_error

    def test_create_tag_unauthorized(self, db, api_client):
        client = api_client
        initial_state = Tag.objects.count()

        response = client.post(
            path=reverse("v1:tag-list"),
            data={"name": "Test Tag"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Tag.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."


class TestReadTag:
    def test_list_tags_success(self, db, api_client, tag_factory):
        client = api_client
        tags = tag_factory.create_batch(size=3)
        tag_ids = {str(t.id) for t in tags}

        response = client.get(path=reverse("v1:tag-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert tag_ids.issubset(received_ids)

    def test_retrieve_tag_success(self, db, api_client, tag_factory):
        client = api_client
        tag = tag_factory()

        response = client.get(path=reverse("v1:tag-detail", args=[tag.slug]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["name"] == tag.name
        assert data["attributes"]["slug"] == tag.slug

    @pytest.mark.parametrize(
        "client_name, expected_count",
        [("api_client", 2), ("editor_client", 4), ("admin_client", 6)],
        ids=("public", "editor", "admin"),
    )
    def test_retrieve_tag_with_posts_success(
        self,
        db,
        request,
        tag_factory,
        editor_factory,
        post_factory,
        client_name,
        expected_count,
    ):
        fixture_value = request.getfixturevalue(client_name)
        client, user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )
        draft_author = user or editor_factory()
        tag = tag_factory()
        posts = (
            post_factory.create_batch(size=2, status="published")
            + post_factory.create_batch(size=2, status="draft", author=draft_author)
            + post_factory.create_batch(size=2, status="archived")
        )
        tag.posts.add(*posts)
        post_ids = {str(post.id) for post in posts}

        response = client.get(
            path=reverse("v1:tag-detail", args=[tag.slug]),
            data={"include": "posts"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        received_post_ids = {
            post["id"] for post in data["relationships"]["posts"]["data"]
        }

        assert received_post_ids.issubset(post_ids)
        assert len(received_post_ids) == expected_count

    def test_retrieve_tag_not_found(self, db, api_client):
        client = api_client

        response = client.get(path=reverse("v1:tag-detail", args=["nonexistent-slug"]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert errors[0]["detail"] == "No Tag matches the given query."


class TestPartialUpdateTag:
    def test_partial_update_tag_success(self, db, editor_client, tag_factory):
        client, _ = editor_client
        tag = tag_factory()

        response = client.patch(
            path=reverse("v1:tag-detail", args=[tag.slug]),
            data={"name": "Updated Tag", "slug": "updated-tag"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["name"] == "Updated Tag"
        assert data["attributes"]["slug"] == "updated-tag"

    @pytest.mark.parametrize(
        "data, expected_error, pointer",
        [
            (
                {"name": "Updated Tag"},
                "tag with this name already exists.",
                "/data/attributes/name",
            ),
            (
                {"slug": "updated-tag"},
                "tag with this slug already exists.",
                "/data/attributes/slug",
            ),
            (
                {"name": ""},
                "This field may not be blank.",
                "/data/attributes/name",
            ),
        ],
        ids=("duplicate_name", "duplicate_slug", "blank name"),
    )
    def test_partial_update_tag_bad_request(
        self, db, editor_client, tag_factory, data, expected_error, pointer
    ):
        client, _ = editor_client
        tag = tag_factory()
        tag_factory(name="Updated Tag", slug="updated-tag")
        initial_state = Tag.objects.count()

        response = client.patch(
            path=reverse("v1:tag-detail", args=[tag.slug]),
            data=data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Tag.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == pointer
        assert errors[0]["detail"] == expected_error

    def test_partial_update_tag_unauthorized(self, db, api_client, tag_factory):
        client = api_client
        tag = tag_factory()
        initial_state = Tag.objects.count()

        response = client.patch(
            path=reverse("v1:tag-detail", args=[tag.slug]),
            data={"name": "Updated Tag", "slug": "updated-tag"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Tag.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_partial_update_tag_not_found(self, db, editor_client):
        client, _ = editor_client

        response = client.patch(
            path=reverse("v1:tag-detail", args=["nonexistent-slug"]),
            data={"name": "Updated Tag"},
            format="json",
        )
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert errors[0]["detail"] == "No Tag matches the given query."


class TestDeleteTag:
    def test_delete_tag_success(self, db, admin_client, tag_factory):
        client, _ = admin_client
        tag = tag_factory()
        initial_state = Tag.objects.count()

        response = client.delete(path=reverse("v1:tag-detail", args=[tag.slug]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Tag.objects.count() == initial_state - 1
        assert not Tag.objects.filter(pk=tag.pk).exists()

    def test_delete_tag_unauthorized(self, db, api_client, tag_factory):
        client = api_client
        tag = tag_factory()
        initial_state = Tag.objects.count()

        response = client.delete(path=reverse("v1:tag-detail", args=[tag.slug]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Tag.objects.count() == initial_state
        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_delete_tag_not_found(self, db, editor_client):
        client, _ = editor_client

        response = client.delete(path=reverse("v1:tag-detail", args=["fake-slug"]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert errors[0]["detail"] == "No Tag matches the given query."
