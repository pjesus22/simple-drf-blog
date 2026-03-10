from django.contrib.auth.signals import user_logged_in, user_login_failed
import pytest

from apps.metrics.models import MetricEvent
from apps.metrics.signals import post_read

pytestmark = pytest.mark.django_db


def test_on_login_creates_metric_when_user_is_authenticated(editor_factory, rf):
    user = editor_factory()
    request = rf.get("/")
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    request.META["HTTP_USER_AGENT"] = "test-agent"

    user_logged_in.send(sender=type(user), request=request, user=user)

    event = MetricEvent.objects.get(event_type=MetricEvent.EventType.LOGIN)

    assert event.user == user
    assert event.metadata["ip"] == "127.0.0.1"
    assert event.metadata["user_agent"] == "test-agent"
    assert event.metadata["user_id"] == user.id


def test_on_login_failed_creates_metric_when_user_failed_to_login(rf):
    request = rf.get("/")
    request.META["REMOTE_ADDR"] = "10.0.0.1"
    request.META["HTTP_USER_AGENT"] = "bad-agent"
    credentials = {
        "username": "fake_username",
        "password": "wrong_password",
    }

    user_login_failed.send(sender=object, request=request, credentials=credentials)

    event = MetricEvent.objects.get(event_type=MetricEvent.EventType.LOGIN_FAILED)

    assert event.user is None
    assert event.metadata["ip"] == "10.0.0.1"
    assert event.metadata["user_agent"] == "bad-agent"
    assert event.metadata["username"] == "fake_username"


def test_on_created_upload_creates_metric_when_user_created_upload(
    upload_factory, clean_media
):
    upload = upload_factory()

    event = MetricEvent.objects.get(event_type=MetricEvent.EventType.UPLOAD_CREATED)

    assert event.user == upload.uploaded_by
    assert event.metadata["purpose"] == upload.purpose
    assert event.metadata["size"] == upload.size


def test_on_post_read_creates_metric_when_user_read_post(editor_factory, mocker):
    user = editor_factory()
    post = mocker.Mock(id=42, slug="my-post")

    post_read.send(sender=mocker.Mock, post=post, user=user)

    event = MetricEvent.objects.get(event_type=MetricEvent.EventType.POST_READ)

    assert event.user == user
    assert event.metadata["post_slug"] == "my-post"
