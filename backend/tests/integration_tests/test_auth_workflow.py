import pytest
from django.urls import reverse
from rest_framework import status


class TestObtainJWTPair:
    @pytest.mark.parametrize("role", ("admin", "editor"))
    def test_valid_user_obtain_jwt_pair(
        self, db, default_user_factory, role, api_client
    ):
        client, _ = api_client
        default_user_factory(username="testuser", password="defaultpassword", role=role)

        response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    @pytest.mark.parametrize(
        "data, expected_status_code",
        (
            ({}, status.HTTP_400_BAD_REQUEST),
            ({"username": "testuser"}, status.HTTP_400_BAD_REQUEST),
            ({"password": "defaultpassword"}, status.HTTP_400_BAD_REQUEST),
            (
                {"username": "testuser", "password": "wrongpassword"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {"username": "nonexistentuser", "password": "defaultpassword"},
                status.HTTP_401_UNAUTHORIZED,
            ),
        ),
        ids=(
            "empty-data",
            "missing-username",
            "missing-password",
            "wrong-password",
            "nonexistent-user",
        ),
    )
    def test_invalid_credentials(
        self, db, data, expected_status_code, api_client, test_user
    ):
        client, _ = api_client
        response = client.post(
            path=reverse("token_obtain_pair"),
            data=data,
            format="json",
        )

        assert "errors" in response.json()
        assert response.status_code == expected_status_code

    def test_inactive_user_cannot_login(self, db, editor_factory, api_client):
        client, _ = api_client
        editor_factory(username="testuser", password="defaultpassword", is_active=False)

        response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshJWTPair:
    def test_jwt_refresh_success(self, db, api_client, test_user):
        client, _ = api_client
        login_response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        refresh_response = client.post(
            path=reverse("token_refresh"),
            data={"refresh": refresh_token},
            format="json",
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert login_response.data["access"] != refresh_response.data["access"]

    def test_jwt_refresh_invalid_token(self, db, api_client, test_user):
        client, _ = api_client
        refresh_token = "invalid_token"

        refresh_response = client.post(
            path=reverse("token_refresh"),
            data={"refresh": refresh_token},
            format="json",
        )

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVerifyJWTPair:
    def test_jwt_verify_success(self, db, test_user, api_client):
        client, _ = api_client
        login_response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )
        access_token = login_response.data["access"]

        verify_response = client.post(
            path=reverse("token_verify"),
            data={"token": access_token},
            format="json",
        )

        assert verify_response.status_code == status.HTTP_200_OK

    def test_jwt_verify_invalid_token(self, db, test_user, api_client):
        client, _ = api_client
        access_token = "invalid_token"

        verify_response = client.post(
            path=reverse("token_verify"),
            data={"token": access_token},
            format="json",
        )

        assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpointAccess:
    def test_access_with_valid_token(self, db, test_user, editor_client):
        client, _ = editor_client
        response = client.get(reverse("v1:user-me"))

        assert response.status_code == status.HTTP_200_OK
