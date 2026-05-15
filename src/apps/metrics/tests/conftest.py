import pytest
from pytest_factoryboy import register
from tests.factories import EditorFactory, UploadFactory
from tests.factories.metrics import MetricRecordFactory

from apps.metrics.events.types import PostViewEvent

register(EditorFactory)
register(UploadFactory)
register(MetricRecordFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield


@pytest.fixture()
def mock_post_view_event():
    return PostViewEvent(
        post_slug="test-post",
        ip="127.0.0.1",
        user_agent="Mozilla/5.0 (X11; Linux x86_64)",
        referer=None,
        user_id=None,
    )
