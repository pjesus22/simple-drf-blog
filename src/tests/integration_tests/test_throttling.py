from django.urls import reverse
from rest_framework import status

from config.throttle import LoginThrottle


def test_login_returns_429_when_rate_exceeded(db, api_client, monkeypatch):
    monkeypatch.setattr(LoginThrottle, "rate", "1/hour", raising=False)
    url = reverse("token_obtain_pair")
    payload = {"username": "nope", "password": "nope"}

    first = api_client.post(url, data=payload, format="json")
    assert first.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    second = api_client.post(url, data=payload, format="json")
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
