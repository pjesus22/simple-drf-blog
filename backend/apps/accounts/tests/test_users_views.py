from unittest.mock import Mock

import pytest
from apps.accounts.permissions import IsAdmin, IsOwner
from apps.accounts.serializers import UserDetailSerializer, UserListSerializer
from apps.accounts.views import UserViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIRequestFactory, force_authenticate


@pytest.fixture
def api_factory():
    return APIRequestFactory()


def test_user_viewset_get_serializer_class_returns_public_serializer(api_factory):
    request = api_factory.get("/users/")
    request.user = Mock(is_authenticated=False)
    viewset = UserViewSet(action="list", request=request)
    assert viewset.get_serializer_class() == UserListSerializer


def test_user_viewset_get_serializer_class_returns_private_serializer(api_factory):
    request = api_factory.get("/users/me/")
    request.user = Mock(is_authenticated=True, role="editor")
    viewset = UserViewSet(action="me", request=request)
    assert viewset.get_serializer_class() == UserDetailSerializer


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("list", [IsAuthenticated]),
        ("retrieve", [IsAuthenticated]),
        ("me", [IsOwner]),
        ("partial_update", [IsOwner]),
        ("destroy", [IsAdmin]),
        ("create", [IsAdmin]),
    ],
    ids=("list", "retrieve", "me", "partial_update", "destroy", "create"),
)
def test_user_viewset_gets_appropriate_permissions(
    api_factory, action, expected_permissions
):
    if action in ("partial_update", "destroy"):
        request = api_factory.get("/users/me/")
    else:
        request = api_factory.get("/")
    request.user = Mock(is_authenticated=True, role="editor")
    viewset = UserViewSet(action=action, request=request)
    actual_permissions = viewset.get_permissions()

    assert len(actual_permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, "
        f"got {len(actual_permissions)}"
    )

    for actual, expected in zip(actual_permissions, expected_permissions):
        assert isinstance(actual, expected)


def test_user_viewset_me_action_calls_get_method(db, editor_factory, api_factory):
    user = editor_factory()
    request = api_factory.get("/me/")

    view = UserViewSet.as_view({"get": "me"})
    force_authenticate(request, user=user)
    response = view(request)

    assert response.status_code == 200
    assert response.data["id"] == user.id


def test_user_viewset_me_action_calls_patch_method(db, editor_factory, api_factory):
    user = editor_factory()
    payload = {
        "data": {
            "type": "users",
            "id": str(user.id),
            "attributes": {"username": "new_username"},
        }
    }
    request = api_factory.patch("/me/", payload)

    view = UserViewSet.as_view({"patch": "me"})
    force_authenticate(request, user=user)
    response = view(request, pk=str(user.id))

    assert response.status_code == 200
    assert response.data["username"] == "new_username"
