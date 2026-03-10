import pytest
from pytest_factoryboy import register
from tests.factories import EditorFactory, UploadFactory
from tests.factories.metrics import MetricEventFactory

register(EditorFactory)
register(UploadFactory)
register(MetricEventFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield
