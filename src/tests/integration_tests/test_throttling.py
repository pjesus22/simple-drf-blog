from django.urls import reverse
from rest_framework import status


def test_login_returns_429_when_rate_exceeded(db, api_client, settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "login": "1/hour",
        },
    }
    url = reverse("token_obtain_pair")
    payload = {"username": "nope", "password": "nope"}

    first = api_client.post(url, data=payload, format="json")
    assert first.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    second = api_client.post(url, data=payload, format="json")
    assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
