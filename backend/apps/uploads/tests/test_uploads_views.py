from unittest.mock import Mock, patch

import pytest
from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.views import UploadViewSet


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("retrieve", [IsOwner]),
        ("create", [IsEditor]),
        ("update", [IsOwner]),
        ("partial_update", [IsOwner]),
        ("destroy", [IsOwner]),
    ],
    ids=("retrieve", "create", "update", "partial_update", "destroy"),
)
def test_upload_viewset_gets_permissions(action, expected_permissions):
    viewset = UploadViewSet(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@patch("apps.uploads.views.UploadService")
def test_upload_viewset_perform_create_implements_upload_service(MockUploadService):
    viewset = UploadViewSet()

    mock_file = Mock(name="test.jpg")
    viewset.request = Mock(
        user=Mock(id=1, username="testuser"),
        data={"purpose": Upload.Purpose.AVATAR, "visibility": Upload.Visibility.PUBLIC},
        FILES={"file": mock_file},
    )

    mock_serializer = Mock()
    mock_upload = Mock(spec=Upload, id=123)
    MockUploadService.return_value.create_or_get_upload.return_value = mock_upload
    viewset.perform_create(mock_serializer)

    MockUploadService.assert_called_once_with(
        uploaded_by=viewset.request.user,
        purpose=Upload.Purpose.AVATAR,
        visibility=Upload.Visibility.PUBLIC,
    )
    MockUploadService.return_value.create_or_get_upload.assert_called_once_with(
        file=mock_file
    )
    assert mock_serializer.instance == mock_upload
