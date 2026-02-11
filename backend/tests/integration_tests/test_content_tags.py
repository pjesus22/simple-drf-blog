import pytest
from apps.content.models import Tag
from django.urls import reverse
from rest_framework import status

from tests.helpers import assert_jsonapi_error_response


@pytest.mark.django_db
class TestCreateTag:
    def test_create_tag_success(self, editor_client):
        client, _ = editor_client
        initial_count = Tag.objects.count()

        response = client.post(
            path=reverse("v1:tag-list"),
            data={"name": "New Awesome Tag"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Tag.objects.count() == initial_count + 1

        data = response.json().get("data")
        assert data["type"] == "tags"
        assert data["attributes"]["name"] == "New Awesome Tag"
        assert data["attributes"]["slug"] == "new-awesome-tag"
        assert Tag.objects.filter(pk=data["id"]).exists()

    @pytest.mark.parametrize(
        "payload, error_detail, pointer, error_code",
        [
            pytest.param(
                {"name": "Existing Tag", "slug": "slug1"},
                "already exists",
                "/data/attributes/name",
                "unique",
                id="duplicate_name",
            ),
            pytest.param(
                {"name": "New Tag", "slug": "existing-slug"},
                "already exists",
                "/data/attributes/slug",
                "unique",
                id="duplicate_slug",
            ),
            pytest.param(
                {"name": ""},
                "This field may not be blank.",
                "/data/attributes/name",
                "blank",
                id="blank_name",
            ),
        ],
    )
    def test_create_tag_bad_request(
        self, tag_factory, editor_client, payload, error_detail, pointer, error_code
    ):
        client, _ = editor_client
        tag_factory(name="Existing Tag", slug="existing-slug")

        response = client.post(
            path=reverse("v1:tag-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            code=error_code,
            pointer=pointer,
            detail_contains=error_detail,
        )


@pytest.mark.django_db
class TestReadTag:
    def test_list_tags_success(self, api_client, tag_factory):
        tags = tag_factory.create_batch(3)
        tag_pks = {str(t.pk) for t in tags}

        response = api_client.get(reverse("v1:tag-list"))

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        received_pks = {item["id"] for item in data}
        assert tag_pks.issubset(received_pks)

    def test_retrieve_tag_success(self, api_client, tag_factory):
        tag = tag_factory(name="Refactoring")

        response = api_client.get(reverse("v1:tag-detail", args=[tag.slug]))

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        assert data["attributes"]["name"] == "Refactoring"
        assert data["attributes"]["slug"] == "refactoring"

    @pytest.mark.parametrize(
        "client_fixture, expected_posts",
        [
            ("api_client", 2),
            ("editor_client", 4),
            ("admin_client", 6),
        ],
        ids=("only_published", "published_and_drafts", "all_posts"),
    )
    def test_retrieve_tag_visibility_permissions(
        self,
        request,
        tag_factory,
        post_factory,
        editor_factory,
        client_fixture,
        expected_posts,
    ):
        fixture = request.getfixturevalue(client_fixture)
        client, user = fixture if isinstance(fixture, tuple) else (fixture, None)

        tag = tag_factory()
        draft_author = user or editor_factory()

        posts = (
            post_factory.create_batch(2, status="published")
            + post_factory.create_batch(2, status="draft", author=draft_author)
            + post_factory.create_batch(2, status="archived")
        )
        tag.posts.add(*posts)

        response = client.get(
            reverse("v1:tag-detail", args=[tag.slug]), data={"include": "posts"}
        )

        assert response.status_code == status.HTTP_200_OK
        relationships = response.json()["data"]["relationships"]["posts"]["data"]
        assert len(relationships) == expected_posts


@pytest.mark.django_db
class TestUpdateTag:
    def test_partial_update_success(self, editor_client, tag_factory):
        client, _ = editor_client
        tag = tag_factory(name="Old Name", slug="old-slug")

        response = client.patch(
            reverse("v1:tag-detail", args=[tag.slug]),
            data={"name": "New Name"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["attributes"]["name"] == "New Name"
        assert response.json()["data"]["attributes"]["slug"] == "old-slug"


@pytest.mark.django_db
class TestDeleteTag:
    def test_delete_tag_as_admin(self, admin_client, tag_factory):
        client, _ = admin_client
        tag = tag_factory()

        response = client.delete(reverse("v1:tag-detail", args=[tag.slug]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(pk=tag.pk).exists()

    def test_delete_tag_as_editor(self, editor_client, tag_factory):
        client, _ = editor_client
        tag = tag_factory()

        response = client.delete(reverse("v1:tag-detail", args=[tag.slug]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(pk=tag.pk).exists()
