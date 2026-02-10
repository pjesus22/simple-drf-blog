import pytest
from apps.uploads.tests.helpers import FileFactory
from pytest_factoryboy import register
from rest_framework.test import APIRequestFactory
from tests.factories import AdminFactory, EditorFactory, UploadFactory

register(EditorFactory)
register(AdminFactory)
register(UploadFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield


@pytest.fixture
def file_factory():
    return FileFactory


@pytest.fixture
def rf():
    return APIRequestFactory()
