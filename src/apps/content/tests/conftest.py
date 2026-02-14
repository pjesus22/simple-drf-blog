import pytest
from pytest_factoryboy import register

from tests.factories import (
    AdminFactory,
    CategoryFactory,
    EditorFactory,
    PostFactory,
    TagFactory,
    UploadFactory,
)

register(CategoryFactory)
register(TagFactory)
register(PostFactory)
register(EditorFactory)
register(UploadFactory)
register(AdminFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield
