from unittest.mock import Mock

import pytest
from apps.users.permissions import IsAdmin, IsOwner
from apps.users.serializers import PrivateUserSerializer, PublicUserSerializer
from apps.users.views import UserViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


def test_user_viewset_get_serializer_class_returns_public_serializer():
    viewset = UserViewSet(action="list")
    assert viewset.get_serializer_class() == PublicUserSerializer


def test_user_viewset_get_serializer_class_returns_private_serializer():
    viewset = UserViewSet(action="me")
    assert viewset.get_serializer_class() == PrivateUserSerializer


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("list", [AllowAny]),
        ("retrieve", [AllowAny]),
        ("me", [IsAuthenticated]),
        ("update", [IsOwner]),
        ("partial_update", [IsOwner]),
        ("destroy", [IsOwner]),
        ("create", [IsAdmin]),
    ],
    ids=("list", "retrieve", "me", "update", "partial_update", "destroy", "create"),
)
def test_user_viewset_gets_appropriate_permissions(action, expected_permissions):
    viewset = UserViewSet(action=action)
    actual_permissions = viewset.get_permissions()

    assert len(actual_permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, "
        f"got {len(actual_permissions)}"
    )

    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(
            actual_permissions, expected_permissions
        )
    )


def test_user_viewset_me_action_calls_get_method(db, editor_factory):
    user = editor_factory()
    request = Mock(user=user, method="GET")
    viewset = UserViewSet()

    viewset.request = request
    response = viewset.me(request)

    assert response.status_code == 200
    assert response.data["id"] == user.id


def test_user_viewset_me_action_calls_patch_method(db, editor_factory):
    user = editor_factory()
    request = Mock(user=user, method="PATCH", data={"username": "new_username"})
    viewset = UserViewSet()

    viewset.request = request
    response = viewset.me(request)

    assert response.status_code == 200
    assert response.data["username"] == "new_username"
