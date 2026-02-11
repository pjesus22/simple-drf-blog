from django.urls import reverse
import pytest
from rest_framework import status

from apps.content.models import Category
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


@pytest.fixture
def category_data(category_factory):
    category = category_factory.build()
    return {
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
    }


class TestCreateCategory:
    def test_create_category_success(self, admin_client, category_data):
        client, _ = admin_client
        initial_count = Category.objects.count()

        response = client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == initial_count + 1

        data = response.json().get("data")
        assert Category.objects.filter(pk=data.get("id")).exists()
        assert data["type"] == "categories"
        assert data["attributes"]["name"] == category_data["name"]
        assert data["attributes"]["slug"] == category_data["slug"]
        assert data["attributes"]["description"] == category_data["description"]

    @pytest.mark.parametrize(
        "field, detail",
        [("name", "name already exists."), ("slug", "slug already exists.")],
        ids=("name", "slug"),
    )
    def test_create_category_bad_request_duplicate_attribute(
        self, admin_client, field, detail, category_data, category_factory
    ):
        client, _ = admin_client
        category_factory(**category_data)

        payload = {**category_data, "name": "Unique Name", "slug": "unique-slug"}
        payload[field] = category_data[field]

        response = client.post(
            path=reverse("v1:category-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="unique",
            pointer=f"/data/attributes/{field}",
            detail_contains=detail,
        )

    def test_create_category_bad_request_missing_name(
        self, admin_client, category_data
    ):
        client, _ = admin_client
        payload = category_data.copy()
        payload.pop("name")

        response = client.post(
            path=reverse("v1:category-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains="required.",
            pointer="/data/attributes/name",
            code="required",
        )

    def test_create_category_unauthorized(self, api_client, category_data):
        response = api_client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_create_category_forbidden(self, editor_client, category_data):
        client, _ = editor_client
        response = client.post(
            path=reverse("v1:category-list"),
            data=category_data,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="not have permission",
            pointer="/data",
            code="permission_denied",
        )


class TestReadCategory:
    def test_list_categories_success(self, api_client, category_factory):
        categories = category_factory.create_batch(size=3)
        expected_ids = {str(c.id) for c in categories}

        response = api_client.get(path=reverse("v1:category-list"))
        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        received_ids = {item["id"] for item in data}
        assert expected_ids.issubset(received_ids)

    def test_retrieve_category_success(self, api_client, category_factory):
        category = category_factory()

        response = api_client.get(
            path=reverse("v1:category-detail", args=[category.slug])
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["name"] == category.name
        assert data["attributes"]["slug"] == category.slug
        assert data["attributes"]["description"] == category.description

    @pytest.mark.parametrize(
        "client_fixture, expected_count",
        [("api_client", 2), ("editor_client", 4), ("admin_client", 6)],
        ids=("public", "editor", "admin"),
    )
    def test_retrieve_category_with_posts_success(
        self,
        request,
        category_factory,
        editor_factory,
        post_factory,
        client_fixture,
        expected_count,
    ):
        fixture_value = request.getfixturevalue(client_fixture)
        client, user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )

        draft_author = user or editor_factory()
        category = category_factory()

        post_factory.create_batch(size=2, category=category, status="published")
        post_factory.create_batch(
            size=2, category=category, status="draft", author=draft_author
        )
        post_factory.create_batch(size=2, category=category, status="archived")

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

        assert len(received_post_ids) == expected_count

    def test_retrieve_category_not_found(self, api_client):
        response = api_client.get(
            path=reverse("v1:category-detail", args=["fake-slug"])
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            detail_contains="No Category matches the given query.",
            code="not_found",
        )


class TestUpdateCategory:
    def test_partial_update_category_success(self, admin_client, category_factory):
        client, _ = admin_client
        category = category_factory()
        update_data = {"name": "Updated Name"}

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data=update_data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data")
        assert data["attributes"]["name"] == "Updated Name"
        assert data["attributes"]["slug"] == category.slug  # Unchanged

    @pytest.mark.parametrize(
        "payload, error, pointer, code",
        [
            pytest.param(
                {"name": "Existing Category"},
                "category with this name already exists.",
                "/data/attributes/name",
                "unique",
                id="duplicate_name",
            ),
            pytest.param(
                {"slug": "existing-slug"},
                "category with this slug already exists.",
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
    def test_partial_update_category_bad_request(
        self, admin_client, category_factory, payload, error, pointer, code
    ):
        client, _ = admin_client
        category = category_factory()
        category_factory(name="Existing Category", slug="existing-slug")

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains=error,
            pointer=pointer,
            code=code,
        )

    def test_update_category_unauthorized(self, api_client, category_factory):
        category = category_factory()
        response = api_client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={"name": "New Name"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_update_category_forbidden(self, editor_client, category_factory):
        client, _ = editor_client
        category = category_factory()

        response = client.patch(
            path=reverse("v1:category-detail", args=[category.slug]),
            data={"name": "New Name"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="do not have permission",
            pointer="/data",
            code="permission_denied",
        )


class TestDeleteCategory:
    def test_delete_category_success(self, admin_client, category_factory):
        client, _ = admin_client
        category = category_factory()
        initial_count = Category.objects.count()

        response = client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Category.objects.count() == initial_count - 1

    def test_delete_category_unauthorized(self, api_client, category_factory):
        category = category_factory()
        response = api_client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_delete_category_forbidden(self, editor_client, category_factory):
        client, _ = editor_client
        category = category_factory()

        response = client.delete(
            path=reverse("v1:category-detail", args=[category.slug])
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="do not have permission",
            pointer="/data",
            code="permission_denied",
        )
