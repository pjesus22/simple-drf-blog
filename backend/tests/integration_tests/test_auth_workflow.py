import pytest
from django.urls import reverse
from rest_framework import status
from tests.helpers import (
    assert_drf_error_response,
    assert_jsonapi_error_pointers,
    assert_jsonapi_error_response,
)


class TestObtainJWTPair:
    @pytest.mark.parametrize("role", ("admin", "editor"))
    def test_post_obtain_jwt_pair_success(
        self, db, default_user_factory, role, api_client
    ):
        client = api_client
        default_user_factory(username="testuser", password="defaultpassword", role=role)

        response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_post_obtain_jwt_pair_bad_request_empty_payload(self, db, api_client):
        client = api_client
        response = client.post(
            path=reverse("token_obtain_pair"),
            data={},
            format="json",
        )

        assert_jsonapi_error_pointers(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            expected_pointers={"username", "password"},
        )

    @pytest.mark.parametrize(
        "data, pointer, code, detail_contains",
        (
            (
                {"username": "testuser"},
                "/data/attributes/password",
                "required",
                "required",
            ),
            (
                {"password": "defaultpassword"},
                "/data/attributes/username",
                "required",
                "required",
            ),
        ),
        ids=("missing_username", "missing_password"),
    )
    def test_post_obtain_jwt_pair_bad_request_missing_fields(
        self,
        db,
        data,
        pointer,
        code,
        detail_contains,
        api_client,
    ):
        client = api_client
        response = client.post(
            path=reverse("token_obtain_pair"),
            data=data,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer=pointer,
            code=code,
            detail_contains=detail_contains,
        )

    @pytest.mark.parametrize(
        "data, detail_contains",
        (
            (
                {"username": "testuser", "password": "wrongpassword"},
                "No active account",
            ),
            (
                {"username": "nonexistentuser", "password": "defaultpassword"},
                "No active account",
            ),
        ),
        ids=("wrong_password", "nonexistent_user"),
    )
    def test_post_obtain_jwt_pair_unauthorized_invalid_credentials(
        self,
        db,
        data,
        detail_contains,
        api_client,
    ):
        client = api_client
        response = client.post(
            path=reverse("token_obtain_pair"),
            data=data,
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains=detail_contains,
        )

    def test_post_obtain_jwt_pair_unauthorized_inactive_user_cannot_login(
        self, db, editor_factory, api_client
    ):
        client = api_client
        editor_factory(username="testuser", password="defaultpassword", is_active=False)

        response = client.post(
            path=reverse("token_obtain_pair"),
            data={"username": "testuser", "password": "defaultpassword"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="No active account",
        )


class TestRefreshJWTPair:
    def test_jwt_refresh_success(self, db, api_client, test_user):
        client = api_client
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

    def test_jwt_refresh_unauthorized_invalid_token(self, db, api_client, test_user):
        client = api_client
        refresh_token = "invalid_token"

        response = client.post(
            path=reverse("token_refresh"),
            data={"refresh": refresh_token},
            format="json",
        )

        print(response.json())

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="token_not_valid",
            detail_contains="invalid",
        )


class TestVerifyJWTPair:
    def test_jwt_verify_success(self, db, test_user, api_client):
        client = api_client
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

    def test_jwt_verify_unauthorized_invalid_token(self, db, test_user, api_client):
        client = api_client
        access_token = "invalid_token"

        response = client.post(
            path=reverse("token_verify"),
            data={"token": access_token},
            format="json",
        )

        print(response.json())

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="token_not_valid",
            detail_contains="invalid",
        )


class TestProtectedEndpointAccess:
    def test_access_with_valid_token(self, db, editor_client):
        client, _ = editor_client
        response = client.get(reverse("v1:user-me"))

        assert response.status_code == status.HTTP_200_OK
