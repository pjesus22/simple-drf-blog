import pytest
from apps.accounts.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status

pytestmark = pytest.mark.django_db


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
    @pytest.mark.parametrize("role", User.Role.values)
    def test_create_user_success(self, admin_client, user_data, role):
        client, _ = admin_client
        payload = {**user_data, "role": role}

        response = client.post(
            path=reverse("v1:user-list"),
            data=payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_user = User.objects.get(username="testuser")
        data = response.json().get("data")

        assert data["type"] == "users"
        assert data["attributes"]["username"] == payload["username"]
        assert data["attributes"]["role"] == role
        assert "password" not in data["attributes"]
        assert "profile" not in data["attributes"]

        expected_fields = {
            "username": payload["username"],
            "first_name": payload["first_name"],
            "last_name": payload["last_name"],
            "email": payload["email"],
            "role": role,
        }

        for field, value in expected_fields.items():
            assert getattr(created_user, field) == value

    def test_create_user_bad_request_empty_data(self, admin_client):
        client, _ = admin_client

        response = client.post(path=reverse("v1:user-list"), data={}, format="json")
        errors = response.json().get("errors")
        required = {"username", "first_name", "last_name", "email", "password"}

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert {e["source"]["pointer"].split("/")[-1] for e in errors} == required

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
            path=reverse("v1:user-list"), data=payload, format="json"
        )
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert errors[0]["detail"] == "This field is required."
        assert errors[0]["source"]["pointer"] == f"/data/attributes/{field}"

    @pytest.mark.parametrize(
        "field, message",
        [
            ("username", "user with this username already exists."),
            ("email", "user with this email already exists."),
        ],
        ids=("username", "email"),
    )
    def test_create_user_bad_request_duplicate_attribute(
        self, admin_client, field, message, user_data, editor_factory
    ):
        client, _ = admin_client
        editor_factory(**user_data)

        payload = {**user_data, "username": "unique", "email": "unique@test.com"}
        payload[field] = user_data[field]

        response = client.post(
            path=reverse("v1:user-list"),
            data=payload,
            format="json",
        )
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert errors[0]["detail"] == message
        assert errors[0]["source"]["pointer"] == f"/data/attributes/{field}"

    def test_create_user_unauthorized(self, db, api_client, user_data):
        client = api_client

        response = client.post(
            path=reverse("v1:user-list"),
            data=user_data,
            format="json",
        )
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert errors[0]["detail"] == "Authentication credentials were not provided."
        assert errors[0]["source"]["pointer"] == "/data"

    def test_create_user_forbidden(self, editor_client, user_data):
        client, _ = editor_client

        response = client.post(
            path=reverse("v1:user-list"),
            data=user_data,
            format="json",
        )
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )
        assert errors[0]["source"]["pointer"] == "/data"


class TestReadUser:
    @pytest.mark.parametrize("client_fixture", ["admin_client", "editor_client"])
    def test_list_users_success(self, client_fixture, editor_factory, request):
        client, _ = request.getfixturevalue(client_fixture)
        users = editor_factory.create_batch(3)
        user_ids = {str(u.id) for u in users}

        response = client.get(path=reverse("v1:user-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert user_ids.issubset(received_ids)

    @pytest.mark.parametrize(
        "client_fixture, expected_fields",
        [
            (
                "admin_client",
                (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "date_joined",
                    "last_login",
                ),
            ),
            (
                "editor_client",
                (
                    "username",
                    "role",
                ),
            ),
        ],
        ids=["admin", "editor"],
    )
    def test_retrieve_user_success(
        self, client_fixture, editor_factory, request, expected_fields
    ):
        client, _ = request.getfixturevalue(client_fixture)
        user = editor_factory(last_login=timezone.now())

        response = client.get(path=reverse("v1:user-detail", args=[user.id]))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert data["type"] == "users"
        for field in expected_fields:
            if field in ["date_joined", "last_login"]:
                assert parse_datetime(data["attributes"][field]) == getattr(user, field)
            else:
                assert data["attributes"][field] == getattr(user, field)
        assert set(data["attributes"]).issubset(expected_fields)

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

        response = client.get(path=reverse("v1:user-detail", args=[999]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert errors[0]["detail"] == "No User matches the given query."

    def test_retrieve_user_unauthorized(self, db, api_client):
        client = api_client

        response = client.get(path=reverse("v1:user-detail", args=[1]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert errors[0]["detail"] == "Authentication credentials were not provided."
        assert errors[0]["source"]["pointer"] == "/data"

    @pytest.mark.parametrize(
        "client_name", ["admin_client", "editor_client"], ids=["admin", "editor"]
    )
    def test_retrieve_user_me_action_success(self, client_name, request):
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
            assert parse_datetime(data["attributes"][field]) == getattr(
                client_user, field
            )
        assert "profile" in data["relationships"]


class TestPartialUpdateUser:
    @pytest.mark.parametrize(
        "client_name, url_route, use_pk",
        [
            ("admin_client", "v1:user-detail", True),
            ("editor_client", "v1:user-me", False),
        ],
        ids=["admin", "editor"],
    )
    def test_partial_update_user_success(
        self, client_name, url_route, use_pk, editor_factory, request
    ):
        client, client_user = request.getfixturevalue(client_name)
        target_user = editor_factory() if use_pk else client_user
        url = (
            reverse(url_route, args=[target_user.id]) if use_pk else reverse(url_route)
        )

        response = client.patch(
            path=url,
            data={
                "username": "new_username",
                "first_name": "new_name",
                "last_name": "new_last_name",
                "email": "new_email@example.com",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["first_name"] == "new_name"
        assert data["attributes"]["username"] == "new_username"
        assert data["attributes"]["last_name"] == "new_last_name"
        assert data["attributes"]["email"] == "new_email@example.com"

        target_user.refresh_from_db()

        assert target_user.first_name == "new_name"
        assert target_user.username == "new_username"
        assert target_user.last_name == "new_last_name"
        assert target_user.email == "new_email@example.com"

    @pytest.mark.parametrize(
        "data, expected_error, pointer",
        [
            (
                {"username": "new_testuser"},
                "user with this username already exists.",
                "/data/attributes/username",
            ),
            (
                {"email": "new_testuser@example.com"},
                "user with this email already exists.",
                "/data/attributes/email",
            ),
        ],
        ids=["duplicate_username", "duplicate_email"],
    )
    def test_partial_update_user_bad_request(
        self, editor_client, data, expected_error, pointer, user_data, editor_factory
    ):
        client, client_user = editor_client
        editor_factory(username="new_testuser", email="new_testuser@example.com")

        response = client.patch(path=reverse("v1:user-me"), data=data, format="json")
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert errors[0]["detail"] == expected_error
        assert errors[0]["source"]["pointer"] == pointer

    def test_partial_update_user_unauthorized(self, db, api_client):
        client = api_client

        response = client.patch(path=reverse("v1:user-me"))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert errors[0]["detail"] == "Authentication credentials were not provided."
        assert errors[0]["source"]["pointer"] == "/data"

    def test_partial_update_user_forbidden(self, db, editor_client, editor_factory):
        client, _ = editor_client
        other_user = editor_factory()

        response = client.patch(path=reverse("v1:user-detail", args=[other_user.id]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )
        assert errors[0]["source"]["pointer"] == "/data"


class TestDeleteUser:
    def test_delete_user_success(self, admin_client, editor_factory):
        client, _ = admin_client
        user = editor_factory()
        initial_state = User.objects.count()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert User.objects.count() == initial_state - 1

    def test_delete_user_unauthorized(self, db, api_client, editor_factory):
        client = api_client
        user = editor_factory()
        initial_state = User.objects.count()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.count() == initial_state
        assert errors[0]["source"]["pointer"] == "/data"
        assert errors[0]["detail"] == "Authentication credentials were not provided."

    def test_delete_user_forbidden(self, db, editor_client, editor_factory):
        client, _ = editor_client
        user = editor_factory()
        initial_state = User.objects.count()

        response = client.delete(path=reverse("v1:user-detail", args=[user.id]))
        errors = response.json().get("errors")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.count() == initial_state
        assert errors[0]["source"]["pointer"] == "/data"
        assert (
            errors[0]["detail"] == "You do not have permission to perform this action."
        )
