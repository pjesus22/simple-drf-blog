from unittest.mock import Mock

from django.utils import timezone
import pytest

from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer
from apps.uploads.views import UploadViewSet


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("list", [IsEditor]),
        ("retrieve", [IsEditor, IsOwner]),
        ("create", [IsEditor]),
        ("update", [IsEditor, IsOwner]),
        ("partial_update", [IsEditor, IsOwner]),
        ("destroy", [IsEditor, IsOwner]),
    ],
    ids=("list", "retrieve", "create", "update", "partial_update", "destroy"),
)
def test_upload_viewset_gets_permissions(action, expected_permissions):
    viewset = UploadViewSet(action=action)
    permissions = viewset.get_permissions()

    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions for "
        f"'{action}', got {len(permissions)}"
    )
    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(permissions, expected_permissions)
    )


@pytest.mark.parametrize(
    "action, expected_serializer",
    [
        ("create", UploadCreateSerializer),
        ("list", UploadSerializer),
        ("retrieve", UploadSerializer),
        ("update", UploadSerializer),
    ],
    ids=("create", "list", "retrieve", "update"),
)
def test_upload_viewset_get_serializer_class(action, expected_serializer):
    viewset = UploadViewSet(action=action)
    assert viewset.get_serializer_class() == expected_serializer


@pytest.mark.django_db
def test_upload_viewset_get_queryset_filtering(
    rf, admin_factory, editor_factory, upload_factory
):
    admin = admin_factory()
    editor = editor_factory()
    upload_by_editor = upload_factory(uploaded_by=editor)
    upload_by_admin = upload_factory(uploaded_by=admin)

    viewset = UploadViewSet()

    # 1. Test Regular User
    request = rf.get("/uploads/")
    request.user = editor
    viewset.request = request

    qs = viewset.get_queryset()
    assert qs.count() == 1
    assert upload_by_editor in qs
    assert upload_by_admin not in qs

    # 2. Test Admin
    request.user = admin
    viewset.request = request

    qs = viewset.get_queryset()
    assert qs.count() == Upload.objects.count()
    assert upload_by_editor in qs
    assert upload_by_admin in qs


@pytest.mark.django_db
def test_upload_viewset_perform_create_implements_upload_service(mocker):
    mock_service_class = mocker.patch("apps.uploads.views.UploadService")
    mock_service_instance = mock_service_class.return_value
    mock_upload = Mock(spec=Upload, id=123)
    mock_service_instance.create_upload.return_value = mock_upload

    user = mocker.Mock()
    mock_file = Mock()

    request = Mock()
    request.user = user
    request.data = {
        "purpose": Upload.Purpose.AVATAR,
        "visibility": Upload.Visibility.PUBLIC,
    }
    request.FILES = {"file": mock_file}

    viewset = UploadViewSet()
    viewset.request = request

    mock_serializer = Mock()

    viewset.perform_create(mock_serializer)

    mock_service_class.assert_called_once_with(
        uploaded_by=user,
        purpose=Upload.Purpose.AVATAR,
        visibility=Upload.Visibility.PUBLIC,
    )
    mock_service_instance.create_upload.assert_called_once_with(file=mock_file)
    assert mock_serializer.instance == mock_upload


def test_upload_viewset_perform_destroy_sets_deleted_at(mocker):
    upload = mocker.Mock(spec=Upload)
    viewset = UploadViewSet()
    viewset.perform_destroy(upload)

    assert upload.deleted_at is not None
    upload.save.assert_called_once()


def test_upload_restore_action(mocker, rf):
    upload = mocker.Mock(spec=Upload)
    upload.deleted_at = timezone.now()

    mock_get_object = mocker.patch(
        "apps.uploads.views.get_object_or_404", return_value=upload
    )

    mock_serializer = mocker.Mock()
    mock_serializer.data = {"id": 123, "status": "restored"}

    viewset = UploadViewSet()
    viewset.action = "restore"
    viewset.request = rf.post("/restore/")

    mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

    response = viewset.restore(viewset.request, pk=123)

    assert response.status_code == 200
    assert response.data == mock_serializer.data
    mock_get_object.assert_called_once_with(Upload.all_objects, pk=123)
    assert upload.deleted_at is None
    upload.save.assert_called_once()


def test_upload_restore_returns_400_if_not_deleted(mocker, rf):
    upload = mocker.Mock(spec=Upload)
    upload.deleted_at = None

    mocker.patch("apps.uploads.views.get_object_or_404", return_value=upload)

    viewset = UploadViewSet()
    viewset.action = "restore"
    viewset.request = rf.post("/restore/")

    response = viewset.restore(viewset.request, pk=123)

    assert response.status_code == 400
    assert response.data == {"detail": "Upload is not deleted."}


def test_upload_trash_action(mocker, rf):
    mock_queryset = mocker.MagicMock()
    mock_deleted_qs = mocker.MagicMock()
    mock_queryset.only_deleted.return_value = mock_deleted_qs

    mock_serializer = mocker.Mock()
    mock_serializer.data = [{"id": 1}, {"id": 2}]

    viewset = UploadViewSet()
    viewset.action = "trash"
    viewset.request = rf.get("/uploads/trash/")

    mocker.patch.object(viewset, "get_queryset", return_value=mock_queryset)
    mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

    response = viewset.trash(viewset.request)

    mock_queryset.only_deleted.assert_called_once()
    viewset.get_serializer.assert_called_once_with(mock_deleted_qs, many=True)
    assert response.status_code == 200
    assert response.data == mock_serializer.data
