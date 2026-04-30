import pytest

from apps.metrics.models import MetricEvent

pytestmark = pytest.mark.django_db


def test_create_metric(editor_factory):
    user = editor_factory()
    metadata = {
        "post_id": "1",
        "ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "referer": "https://google.com",
        "user_id": str(user.id),
        "is_bot": False,
    }

    metric = MetricEvent(event_type="post_read", metadata=metadata)
    metric.save()
    expected_str = f"{metric.event_type} @{metric.created_at}"

    assert str(metric) == expected_str
    assert metric.event_type == "post_read"
    assert metric.metadata == metadata
    assert metric.id is not None
    assert metric.created_at is not None
    assert metric.updated_at is not None
