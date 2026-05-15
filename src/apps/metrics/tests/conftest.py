import pytest
from pytest_factoryboy import register
from tests.factories import EditorFactory, UploadFactory
from tests.factories.metrics import MetricRecordFactory

register(EditorFactory)
register(UploadFactory)
register(MetricRecordFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield
