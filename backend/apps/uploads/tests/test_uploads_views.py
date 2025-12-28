from unittest.mock import Mock

import pytest
from apps.uploads.views import UploadViewSet
from apps.users.permissions import IsEditor, IsOwner
from rest_framework.permissions import IsAuthenticated


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
def test_upload_viewset_gets_writing_permissions(action, expected_permissions):
    viewset = UploadViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


def test_upload_viewset_gets_reading_permissions():
    viewset = UploadViewSet(action="retrieve")
    permissions = viewset.get_permissions()
    assert len(permissions) == 1, "Expected 1 permission, got {}".format(
        len(permissions)
    )
    assert isinstance(permissions[0], IsAuthenticated)


def test_upload_viewset_perform_create_sets_uploaded_by(db, editor_factory):
    user = editor_factory()
    request = Mock(user=user)
    viewset = UploadViewSet(request=request)

    mock_serializer = Mock()

    viewset.perform_create(mock_serializer)

    mock_serializer.save.assert_called_once_with(uploaded_by=user)
