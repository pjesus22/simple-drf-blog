import pytest
from django.urls import reverse
from pytest_factoryboy import register
from rest_framework.test import APIClient
from tests.factories import (
    AdminFactory,
    DefaultUserFactory,
    EditorFactory,
)

register(EditorFactory)
register(AdminFactory)
register(DefaultUserFactory)


@pytest.fixture
def test_user(editor_factory):
    return editor_factory(username="testuser", password="defaultpassword")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(test_user):
    client = APIClient()
    response = client.post(
        path=reverse("token_obtain_pair"),
        data={"username": "testuser", "password": "defaultpassword"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data.get('access')}")
    return client
