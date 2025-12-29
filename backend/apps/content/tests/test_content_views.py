from unittest.mock import Mock

import pytest
from apps.content.views import CategoryViewSet, PostViewSet, TagViewSet
from apps.users.permissions import IsAdmin, IsEditor, IsOwner
from rest_framework.permissions import AllowAny


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("create", [IsAdmin]),
        ("update", [IsAdmin]),
        ("partial_update", [IsAdmin]),
        ("destroy", [IsAdmin]),
    ],
    ids=("create", "update", "partial_update", "destroy"),
)
def test_category_viewset_gets_writing_permissions(action, expected_permissions):
    viewset = CategoryViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_permissions",
    [("list", [AllowAny]), ("retrieve", [AllowAny])],
    ids=("list", "retrieve"),
)
def test_category_viewset_gets_reading_permissions(action, expected_permissions):
    viewset = CategoryViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("create", [IsEditor]),
        ("update", [IsEditor]),
        ("partial_update", [IsEditor]),
        ("destroy", [IsEditor]),
    ],
    ids=("create", "update", "partial_update", "destroy"),
)
def test_tag_viewset_gets_writing_permissions(action, expected_permissions):
    viewset = TagViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_permissions",
    [("list", [AllowAny]), ("retrieve", [AllowAny])],
    ids=("list", "retrieve"),
)
def test_tag_viewset_gets_reading_permissions(action, expected_permissions):
    viewset = TagViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("create", [IsEditor, IsOwner]),
        ("update", [IsEditor, IsOwner]),
        ("partial_update", [IsEditor, IsOwner]),
        ("destroy", [IsEditor, IsOwner]),
    ],
    ids=("create", "update", "partial_update", "destroy"),
)
def test_post_viewset_gets_writing_permissions(action, expected_permissions):
    viewset = PostViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_permissions",
    [("list", [AllowAny]), ("retrieve", [AllowAny])],
    ids=("list", "retrieve"),
)
def test_post_viewset_gets_reading_permissions(action, expected_permissions):
    viewset = PostViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


def test_post_viewset_perform_create_sets_author(db, editor_factory):
    user = editor_factory()
    request = Mock(user=user)
    viewset = PostViewSet(request=request)

    mock_serializer = Mock()

    viewset.perform_create(mock_serializer)

    mock_serializer.save.assert_called_once_with(author=user)
