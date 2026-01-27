import pytest
from pytest_factoryboy import register
from tests.factories import AdminFactory, EditorFactory, UploadFactory

register(EditorFactory)
register(AdminFactory)
register(UploadFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    """
    Automatically override MEDIA_ROOT for every test to a unique
    temporary directory provided by pytest.
    """
    settings.MEDIA_ROOT = tmp_path
    yield
