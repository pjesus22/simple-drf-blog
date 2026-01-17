import pytest
from apps.content.models import Category
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def category_data():
    return {
        "name": "Test Category",
        "slug": "test-category",
        "description": "Test category description",
    }


class TestCreateCategory:
    def test_create_category_success(self, admin_client, category_data):
        client, _ = admin_client
        initial_state = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == initial_state + 1

        data = response.json().get("data")

        assert Category.objects.filter(pk=data.get("id")).exists()
        assert data["type"] == "categories"
        assert data["attributes"]["name"] == category_data["name"]
        assert data["attributes"]["slug"] == category_data["slug"]
        assert data["attributes"]["description"] == category_data["description"]

    @pytest.mark.parametrize(
        "conflict_field, expected_error",
        [
            ("name", "category with this name already exists."),
            ("slug", "category with this slug already exists."),
        ],
        ids=("name", "slug"),
    )
    def test_create_category_bad_request_duplicate_attribute(
        self,
        admin_client,
        conflict_field,
        expected_error,
        category_data,
        category_factory,
    ):
        client, _ = admin_client
        category_factory(**category_data)
        payload = {**category_data, "name": "Unique Name", "slug": "unique-slug"}
        payload[conflict_field] = category_data[conflict_field]
        initial_state = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["detail"] == expected_error
        assert errors[0]["source"]["pointer"] == f"/data/attributes/{conflict_field}"

    def test_create_category_bad_request_missing_name(
        self, admin_client, category_data
    ):
        client, _ = admin_client
        payload = category_data.copy()
        payload.pop("name")
        initial_state = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["detail"] == "This field is required."
        assert errors[0]["source"]["pointer"] == "/data/attributes/name"

    def test_create_category_unauthorized(self, api_client, category_data):
        client = api_client
        initial_state = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_create_category_forbidden(self, editor_client, category_data):
        client, _ = editor_client
        initial_state = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )


class TestReadCategory:
    def test_list_categories_success(self, api_client, category_factory):
        client = api_client
        categories = category_factory.create_batch(size=3)
        category_ids = {str(c.id) for c in categories}

        response = client.get(path=reverse("v1:category-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert category_ids.issubset(received_ids)

    def test_retrieve_category_success(self, api_client, category_factory):
        client = api_client
        category = category_factory()

        response = client.get(path=reverse("v1:category-detail", args=[category.slug]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["name"] == category.name
        assert data["attributes"]["slug"] == category.slug
        assert data["attributes"]["description"] == category.description

    @pytest.mark.parametrize(
        "client_name, expected_count",
        [("api_client", 2), ("editor_client", 4), ("admin_client", 6)],
        ids=("public", "editor", "admin"),
    )
    def test_retrieve_category_with_posts_success(
        self,
        request,
        category_factory,
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
        category = category_factory()
        posts = (
            post_factory.create_batch(size=2, category=category, status="published")
            + post_factory.create_batch(
                size=2, category=category, status="draft", author=draft_author
            )
            + post_factory.create_batch(size=2, category=category, status="archived")
        )
        posts_ids = {str(p.id) for p in posts}

        response = client.get(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={"include": "posts"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        received_post_ids = {
            item["id"] for item in data["relationships"]["posts"]["data"]
        }

        assert received_post_ids.issubset(posts_ids)
        assert len(received_post_ids) == expected_count

    def test_retrieve_category_not_found(self, api_client):
        client = api_client

        response = client.get(path=reverse("v1:category-detail", args=["fake-slug"]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert errors[0]["detail"] == "No Category matches the given query."


class TestPartialUpdateCategory:
    def test_partial_update_category_success(self, admin_client, category_factory):
        client, _ = admin_client
        category = category_factory()

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={
                "name": "Updated Category",
                "slug": "updated-category",
                "description": "Updated category description",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["name"] == "Updated Category"
        assert data["attributes"]["slug"] == "updated-category"
        assert data["attributes"]["description"] == "Updated category description"

    @pytest.mark.parametrize(
        "data, expected_error, pointer",
        [
            (
                {"name": "Updated Category"},
                "category with this name already exists.",
                "/data/attributes/name",
            ),
            (
                {"slug": "updated-category"},
                "category with this slug already exists.",
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
    def test_partial_update_category_bad_request(
        self, admin_client, category_factory, data, expected_error, pointer
    ):
        client, _ = admin_client
        category = category_factory()
        category_factory(name="Updated Category", slug="updated-category")
        initial_state = Category.objects.count()

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data=data,
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == pointer
        assert errors[0]["detail"] == expected_error

    def test_partial_update_category_unauthorized(self, api_client, category_factory):
        client = api_client
        category = category_factory()
        initial_state = Category.objects.count()

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={"name": "Updated Category"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_partial_update_category_forbidden(self, editor_client, category_factory):
        client, _ = editor_client
        category = category_factory()
        initial_state = Category.objects.count()

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={"name": "Updated Category"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )


class TestDeleteCategory:
    def test_delete_category_success(self, admin_client, category_factory):
        client, _ = admin_client
        category = category_factory()
        initial_state = Category.objects.count()

        response = client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Category.objects.count() == initial_state - 1

    def test_delete_category_unauthorized(self, api_client, category_factory):
        client = api_client
        category = category_factory()
        initial_state = Category.objects.count()

        response = client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_delete_category_forbidden(self, editor_client, category_factory):
        client, _ = editor_client
        category = category_factory()
        initial_state = Category.objects.count()

        response = client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Category.objects.count() == initial_state

        errors = response.json().get("errors")

        assert errors[0]["source"]["pointer"] == "/data"
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )
