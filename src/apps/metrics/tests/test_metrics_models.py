import pytest

from apps.metrics.models import MetricEvent

pytestmark = pytest.mark.django_db


def test_create_metric(editor_factory):
    user = editor_factory()
    metric = MetricEvent(
        event_type=MetricEvent.EventType.POST_READ,
        user=user,
        metadata={"post_id": 1},
    )

    metric.save()

    expected_str = (
        f"{metric.event_type} @{metric.created_at} by user_id={metric.user_id}"
    )

    assert str(metric) == expected_str
    assert metric.event_type == MetricEvent.EventType.POST_READ
    assert metric.user_id == user.id
    assert metric.metadata == {"post_id": 1}
    assert metric.id is not None
    assert metric.created_at is not None
    assert metric.updated_at is not None
