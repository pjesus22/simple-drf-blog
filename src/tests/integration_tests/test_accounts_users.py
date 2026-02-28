from django.urls import reverse
from django.utils import timezone
import pytest
from rest_framework import status

from apps.accounts.models import User
from tests.helpers import (
    assert_datetimes_close,
    assert_drf_error_response,
    assert_jsonapi_error_pointers,
    assert_jsonapi_error_response,
)

pytestmark = pytest.mark.django_db
ADMIN_ROLE = User.Role.ADMIN
EDITOR_ROLE = User.Role.EDITOR


@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "defaultpassword",
    }


class TestCreateUser:
    def test_create_user_success(self, admin_client, user_data):
        client, _ = admin_client

        response = client.post(
            path=reverse("v1:user-list"),
            data=user_data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_user = User.objects.get(username="testuser")
        data = response.json().get("data")

        assert User.objects.filter(id=created_user.id).exists()
        assert data["attributes"]["username"] == created_user.username
        assert data["attributes"]["first_name"] == created_user.first_name
        assert data["attributes"]["last_name"] == created_user.last_name
        assert data["attributes"]["email"] == created_user.email
        assert data["attributes"]["role"] == created_user.role

        assert_datetimes_close(
            data["attributes"]["date_joined"], created_user.date_joined
        )
        assert data["attributes"]["last_login"] is None

        relationships = data["relationships"]
        assert "profile" in relationships
        assert relationships["profile"]["data"] is None

    def test_create_user_bad_request_empty_data(self, admin_client):
        client, _ = admin_client

        response = client.post(path=reverse("v1:user-list"), data={}, format="json")

        assert_jsonapi_error_pointers(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            expected_pointers={
                "username",
                "first_name",
                "last_name",
                "email",
                "password",
            },
        )

    @pytest.mark.parametrize(
        "field", ["username", "first_name", "last_name", "email", "password"]
    )
    def test_create_user_bad_request_missing_attribute(
        self, admin_client, field, user_data
    ):
        client, _ = admin_client
        payload = user_data.copy()
        payload.pop(field)

        response = client.post(
            path=reverse("v1:user-list"),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer=f"/data/attributes/{field}",
            code="required",
            detail_contains="required",
        )

    @pytest.mark.parametrize("field", ["username", "email"])
    def test_create_user_bad_request_duplicate_attribute(
        self, admin_client, field, user_data, editor_factory
    ):
        client, _ = admin_client
        editor_factory(**user_data)
        payload = {**user_data, "username": "unique", "email": "unique@test.com"}
        payload[field] = user_data[field]

        response = client.post(
            path=reverse("v1:user-list"), data=payload, format="json"
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer=f"/data/attributes/{field}",
            code="unique",
            detail_contains="already exists.",
        )

    def test_create_user_unauthorized(self, api_client, user_data):
        client = api_client

        response = client.post(
            path=reverse("v1:user-list"), data=user_data, format="json"
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_create_user_forbidden(self, editor_client, user_data):
        client, _ = editor_client

        response = client.post(
            path=reverse("v1:user-list"),
            data=user_data,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            pointer="/data",
            code="permission_denied",
            status_code=status.HTTP_403_FORBIDDEN,
            detail_contains="do not have permission to perform this action.",
        )


class TestReadUser:
    def test_list_users_success(self, admin_client, editor_factory):
        client, _ = admin_client
        users = editor_factory.create_batch(3)
        user_ids = {str(u.id) for u in users}

        response = client.get(path=reverse("v1:user-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert user_ids.issubset(received_ids)

    def test_list_users_forbidden(self, editor_client):
        client, _ = editor_client

        response = client.get(path=reverse("v1:user-list"))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="do not have permission to perform this action.",
            code="permission_denied",
        )

    def test_retrieve_other_user_success(self, admin_client, editor_factory):
        client, _ = admin_client
        user = editor_factory(last_login=timezone.now())
        expected_fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "date_joined",
            "last_login",
        )

        response = client.get(path=reverse("v1:user-detail", args=[user.id]))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert data["type"] == "users"

        for field in expected_fields:
            if field in ["date_joined", "last_login"]:
                assert_datetimes_close(data["attributes"][field], getattr(user, field))
            else:
                assert data["attributes"][field] == getattr(user, field)

        assert set(data["attributes"].keys()).issubset(set(expected_fields))

    def test_retrieve_other_user_forbidden(self, editor_client, editor_factory):
        client, _ = editor_client
        other_user = editor_factory()

        response = client.get(path=reverse("v1:user-detail", args=[other_user.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="do not have permission to perform this action.",
            code="permission_denied",
        )

    def test_retrieve_self_user_by_id_success(self, editor_client):
        client, user = editor_client

        response = client.get(path=reverse("v1:user-detail", args=[user.id]))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert data["type"] == "users"
        assert data["attributes"]["username"] == user.username
        assert data["attributes"]["role"] == user.role
        assert "profile" in data["relationships"]

    def test_retrieve_user_not_found(self, editor_client):
        client, _ = editor_client

        response = client.get(path=reverse("v1:user-detail", args=[0]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No User matches the given query.",
        )

    def test_retrieve_user_unauthorized(self, api_client):
        client = api_client

        response = client.get(path=reverse("v1:user-detail", args=[0]))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPartialUpdateUser:
    def test_partial_update_other_user_as_admin_success(
        self, admin_client, editor_factory
    ):
        client, _ = admin_client
        user = editor_factory()
        payload = {
            "username": "new_username",
            "first_name": "new_name",
            "last_name": "new_last_name",
            "email": "new_email@example.com",
        }

        response = client.patch(
            path=reverse("v1:user-detail", args=[user.id]),
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["first_name"] == "new_name"
        assert data["attributes"]["username"] == "new_username"
        assert data["attributes"]["last_name"] == "new_last_name"
        assert data["attributes"]["email"] == "new_email@example.com"

        user.refresh_from_db()

        assert user.first_name == "new_name"
        assert user.last_name == "new_last_name"
        assert user.email == "new_email@example.com"
        assert user.username == "new_username"

    @pytest.mark.parametrize(
        "data, expected_error, pointer",
        [
            pytest.param(
                {"username": "new_testuser"},
                "user with this username already exists.",
                "/data/attributes/username",
                id="duplicate_username",
            ),
            pytest.param(
                {"email": "new_testuser@example.com"},
                "user with this email already exists.",
                "/data/attributes/email",
                id="duplicate_email",
            ),
        ],
    )
    def test_partial_update_self_bad_request(
        self, editor_client, data, expected_error, pointer, editor_factory
    ):
        client, _ = editor_client
        editor_factory(username="new_testuser", email="new_testuser@example.com")

        response = client.patch(path=reverse("v1:user-me"), data=data, format="json")

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail_contains=expected_error,
            pointer=pointer,
            code="unique",
        )

    def test_partial_update_self_unauthorized(self, api_client):
        client = api_client

        response = client.patch(path=reverse("v1:user-me"))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_partial_update_other_user_as_editor_forbidden(
        self, editor_client, editor_factory
    ):
        client, _ = editor_client
        other_user = editor_factory()

        response = client.patch(path=reverse("v1:user-detail", args=[other_user.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="not have permission to perform this action.",
            code="permission_denied",
        )


class TestDeleteUser:
    def test_delete_user_success(self, admin_client, editor_factory):
        client, _ = admin_client
        user = editor_factory()
        initial_state = User.objects.count()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert User.objects.count() == initial_state - 1

    def test_delete_user_unauthorized(self, api_client, editor_factory):
        client = api_client
        user = editor_factory()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_delete_user_forbidden(self, editor_client, editor_factory):
        client, _ = editor_client
        user = editor_factory()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="not have permission to perform this action.",
            code="permission_denied",
        )


class TestUserMe:
    @pytest.mark.parametrize(
        "client_name", ["admin_client", "editor_client"], ids=["admin", "editor"]
    )
    def test_get_me_success(self, client_name, request):
        client, client_user = request.getfixturevalue(client_name)
        client_user.last_login = timezone.now()
        client_user.save(update_fields=["last_login"])

        response = client.get(path=reverse("v1:user-me"))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert data["type"] == "users"
        for field in ("username", "first_name", "last_name", "email", "role"):
            assert data["attributes"][field] == getattr(client_user, field)
        for field in ("date_joined", "last_login"):
            assert_datetimes_close(
                data["attributes"][field], getattr(client_user, field)
            )
        assert "profile" in data["relationships"]

    def test_patch_me_success(self, editor_client):
        client, user = editor_client
        payload = {
            "username": "new_username",
            "first_name": "new_name",
            "last_name": "new_last_name",
            "email": "new_email@example.com",
        }
        response = client.patch(
            path=reverse("v1:user-me"),
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["first_name"] == "new_name"
        assert data["attributes"]["username"] == "new_username"
        assert data["attributes"]["last_name"] == "new_last_name"
        assert data["attributes"]["email"] == "new_email@example.com"

        user.refresh_from_db()

        assert user.first_name == "new_name"
        assert user.last_name == "new_last_name"
        assert user.email == "new_email@example.com"
        assert user.username == "new_username"

    def test_patch_me_unauthorized(self, api_client):
        client = api_client

        response = client.patch(path=reverse("v1:user-me"))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )


class TestChangeRole:
    def test_change_role_success(self, admin_client, editor_factory):
        client, _ = admin_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-change-role", args=[user.id]),
            data={"role": ADMIN_ROLE},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()

        assert user.role == "admin"

    def test_change_role_self_demotion_forbidden(self, admin_client, admin_factory):
        client, client_user = admin_client
        admin_factory()

        response = client.post(
            path=reverse("v1:user-change-role", args=[client_user.id]),
            data={"role": EDITOR_ROLE},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            code="permission_denied",
        )

    def test_change_role_unauthorized(self, api_client, editor_factory):
        client = api_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-change-role", args=[user.id]),
            data={"role": ADMIN_ROLE},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_change_role_forbidden(self, editor_client, editor_factory):
        client, _ = editor_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-change-role", args=[user.id]),
            data={"role": ADMIN_ROLE},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="not have permission to perform this action.",
            code="permission_denied",
        )

    def test_change_role_self_demotion_forbidden_last_admin(self, admin_client):
        client, client_user = admin_client

        response = client.post(
            path=reverse("v1:user-change-role", args=[client_user.id]),
            data={"role": EDITOR_ROLE},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            code="permission_denied",
        )

    @pytest.mark.parametrize(
        "payload", [{"role": "invalid_role"}, {}], ids=("invalid_role", "missing_role")
    )
    def test_change_role_bad_request(self, admin_client, editor_factory, payload):
        client, _ = admin_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-change-role", args=[user.id]),
            data=payload,
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/role",
        )


class TestChangePassword:
    def test_change_own_password_success(self, editor_client):
        client, client_user = editor_client

        response = client.post(
            path=reverse("v1:user-change-password"),
            data={"old_password": "defaultpassword", "new_password": "newpassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        client_user.refresh_from_db()

        assert client_user.check_password("newpassword")

    def test_set_other_user_password_as_admin_success(
        self, admin_client, editor_factory
    ):
        client, _ = admin_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-force-password-change", args=[user.id]),
            data={"new_password": "newpassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user.refresh_from_db()

        assert user.check_password("newpassword")

    def test_set_password_unauthorized(self, api_client, editor_factory):
        client = api_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-force-password-change", args=[user.id]),
            data={"new_password": "newpassword"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_set_other_user_password_as_editor_forbidden(
        self, editor_client, editor_factory
    ):
        client, _ = editor_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-force-password-change", args=[user.id]),
            data={"new_password": "newpassword"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_403_FORBIDDEN,
            pointer="/data",
            detail_contains="not have permission to perform this action.",
            code="permission_denied",
        )

    def test_set_password_bad_request_new_password_too_short(
        self, admin_client, editor_factory
    ):
        client, _ = admin_client
        user = editor_factory()

        response = client.post(
            path=reverse("v1:user-force-password-change", args=[user.id]),
            data={"new_password": "short"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/new_password",
        )
