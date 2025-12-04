import pytest
from pytest_factoryboy import register
from tests.factories.content_factories import (
    CategoryFactory,
    PostFactory,
    TagFactory,
)
from tests.factories.uploads_factories import UploadFactory
from tests.factories.users_factories import EditorFactory

register(CategoryFactory)
register(TagFactory)
register(PostFactory)
register(EditorFactory)
register(UploadFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield
