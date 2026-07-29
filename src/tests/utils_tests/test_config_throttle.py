from django.contrib.auth.models import AnonymousUser
import pytest

from config.throttle import (
    AnonReadThrottle,
    LoginThrottle,
    PasswordChangeThrottle,
    TokenThrottle,
    UploadBurstThrottle,
    UploadHourThrottle,
    UserReadThrottle,
    WriteThrottle,
)


class _FakeUser:
    is_authenticated = True
    pk = 42


ANON_FOCUSED_THROTTLE = [AnonReadThrottle, LoginThrottle]
USER_FOCUSED_THROTTLE = [
    UserReadThrottle,
    WriteThrottle,
    UploadHourThrottle,
    UploadBurstThrottle,
    TokenThrottle,
    PasswordChangeThrottle,
]


@pytest.mark.parametrize("throttle_class", ANON_FOCUSED_THROTTLE)
def test_anon_throttle_returns_none_when_authenticated(rf, throttle_class):
    request = rf.get("/", REMOTE_ADDR="203.0.113.7")
    request.user = _FakeUser()

    throttle = throttle_class()
    cache_key = throttle.get_cache_key(request, view=None)

    assert cache_key is None


@pytest.mark.parametrize("throttle_class", ANON_FOCUSED_THROTTLE)
def test_anon_throttle_keyed_by_ip_when_anonymous(rf, throttle_class):
    request = rf.get("/", REMOTE_ADDR="203.0.113.7")
    request.user = AnonymousUser()

    throttle = throttle_class()
    cache_key = throttle.get_cache_key(request, view=None)

    assert cache_key == f"throttle_{throttle.scope}_203.0.113.7"


@pytest.mark.parametrize("throttle_class", USER_FOCUSED_THROTTLE)
def test_user_throttle_keyed_by_pk_when_authenticated(rf, throttle_class):
    request = rf.get("/", REMOTE_ADDR="203.0.113.7")
    request.user = _FakeUser()

    throttle = throttle_class()
    cache_key = throttle.get_cache_key(request, view=None)

    assert cache_key == f"throttle_{throttle.scope}_42"


@pytest.mark.parametrize("throttle_class", USER_FOCUSED_THROTTLE)
def test_user_throttle_keyed_by_ip_when_anonymous(rf, throttle_class):
    request = rf.get("/", REMOTE_ADDR="203.0.113.7")
    request.user = AnonymousUser()

    throttle = throttle_class()
    cache_key = throttle.get_cache_key(request, view=None)

    assert cache_key == f"throttle_{throttle.scope}_203.0.113.7"
