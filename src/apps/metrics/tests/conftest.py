from django.core.cache import cache
from django.test import RequestFactory
import pytest
from pytest_factoryboy import register
from tests.factories import EditorFactory, UploadFactory
from tests.factories.metrics import MetricRecordFactory

from apps.metrics.events.base import MetricEvent
from apps.metrics.events.registry import EventRegistry
from apps.metrics.events.types import PostViewEvent

register(EditorFactory)
register(UploadFactory)
register(MetricRecordFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield


@pytest.fixture(autouse=True)
def clear_cache():
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def clear_event_registry():
    EventRegistry._handlers.clear()
    yield
    EventRegistry._handlers.clear()


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def mock_post_view_event():
    return PostViewEvent(
        post_slug="test-post",
        client_ip="127.0.0.1",
        user_agent="Mozilla/5.0 (X11; Linux x86_64)",
        referer_domain=None,
        authenticated=True,
    )


@pytest.fixture
def mock_unknown_event():
    class UnknownEvent(MetricEvent):
        @property
        def event_type(self) -> str:
            return "unknown_event"

        def get_metadata(self) -> dict:
            return {
                "key1": "value1",
                "key2": "value2",
            }

    return UnknownEvent()
