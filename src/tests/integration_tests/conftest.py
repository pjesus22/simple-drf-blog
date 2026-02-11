import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tests.factories import (
    AdminFactory,
    CategoryFactory,
    DefaultUserFactory,
    EditorFactory,
    PostFactory,
    ProfileFactory,
    SocialMediaProfileFactory,
    TagFactory,
    UploadFactory,
)

register(EditorFactory)
register(AdminFactory)
register(DefaultUserFactory)
register(CategoryFactory)
register(PostFactory)
register(TagFactory)
register(UploadFactory)
register(ProfileFactory)
register(SocialMediaProfileFactory)


@pytest.fixture
def test_user(editor_factory):
    return editor_factory(username="testuser", password="defaultpassword")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_client(api_client):
    """
    Returns a function that authenticates the API client
    for a given user using a JWT access token.
    """

    def _authenticate(user):
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return api_client

    return _authenticate


@pytest.fixture
def editor_client(editor_factory, auth_client):
    user = editor_factory()
    client = auth_client(user)
    return client, user


@pytest.fixture
def admin_client(admin_factory, auth_client):
    user = admin_factory()
    client = auth_client(user)
    return client, user


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    """
    Automatically override MEDIA_ROOT for every test to a unique
    temporary directory provided by pytest.
    """
    settings.MEDIA_ROOT = tmp_path
    yield
