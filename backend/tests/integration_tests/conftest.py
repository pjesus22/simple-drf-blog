import pytest
from django.urls import reverse
from pytest_factoryboy import register
from rest_framework.test import APIClient
from tests.factories import (
    AdminFactory,
    CategoryFactory,
    DefaultUserFactory,
    EditorFactory,
    PostFactory,
    SocialLinkFactory,
    TagFactory,
    UploadFactory,
)

register(EditorFactory)
register(AdminFactory)
register(DefaultUserFactory)
register(CategoryFactory)
register(PostFactory)
register(TagFactory)
register(SocialLinkFactory)
register(UploadFactory)


@pytest.fixture
def test_user(editor_factory):
    return editor_factory(username="testuser", password="defaultpassword")


@pytest.fixture
def api_client():
    return (APIClient(), None)


@pytest.fixture
def editor_client(editor_factory):
    client = APIClient()
    user = editor_factory(username="testeditor", password="defaultpassword")
    response = client.post(
        path=reverse("token_obtain_pair"),
        data={"username": "testeditor", "password": "defaultpassword"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data.get('access')}")
    return (client, user)


@pytest.fixture
def admin_client(admin_factory):
    client = APIClient()
    user = admin_factory(username="testadmin", password="defaultpassword")
    response = client.post(
        path=reverse("token_obtain_pair"),
        data={"username": "testadmin", "password": "defaultpassword"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data.get('access')}")
    return (client, user)
