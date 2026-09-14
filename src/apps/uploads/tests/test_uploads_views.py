from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.core.files.storage import default_storage
from django.http import Http404
from django.utils import timezone
import pytest
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer
from apps.uploads.views import UploadViewSet
from config.throttle import (
    AnonReadThrottle,
    UploadBurstThrottle,
    UploadHourThrottle,
    UserReadThrottle,
    WriteThrottle,
)


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("list", [IsEditor]),
        ("retrieve", [IsEditor, IsOwner]),
        ("create", [IsEditor]),
        ("update", [IsEditor, IsOwner]),
        ("partial_update", [IsEditor, IsOwner]),
        ("destroy", [IsEditor, IsOwner]),
        ("content", [IsEditor, IsOwner]),
    ],
    ids=(
        "list",
        "retrieve",
        "create",
        "update",
        "partial_update",
        "destroy",
        "content",
    ),
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

    viewset = UploadViewSet(action="list")

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


@pytest.mark.parametrize(
    "action, method, is_auth, expected_throttle_classes",
    [
        ("list", "GET", False, [AnonReadThrottle]),
        ("list", "GET", True, [UserReadThrottle]),
        ("retrieve", "GET", False, [AnonReadThrottle]),
        ("retrieve", "GET", True, [UserReadThrottle]),
        ("trash", "GET", False, [AnonReadThrottle]),
        ("trash", "GET", True, [UserReadThrottle]),
        ("create", "POST", True, [UploadHourThrottle, UploadBurstThrottle]),
        ("partial_update", "PATCH", True, [WriteThrottle]),
        ("destroy", "DELETE", True, [WriteThrottle]),
        ("restore", "POST", True, [WriteThrottle]),
        ("content", "GET", False, [AnonReadThrottle]),
        ("content", "GET", True, [UserReadThrottle]),
    ],
)
def test_upload_viewset_returns_correct_throttle_for_action(
    db, rf, editor_factory, action, method, is_auth, expected_throttle_classes
):
    request = getattr(rf, method.lower())("/")
    request.user = editor_factory() if is_auth else AnonymousUser()

    viewset = UploadViewSet(action=action, request=request, format_kwarg=None)
    throttles = viewset.get_throttles()

    assert len(throttles) == len(expected_throttle_classes), (
        f"Expected {len(expected_throttle_classes)} throttles for"
        f"UploadViewSet:{action}, got {len(throttles)}"
    )
    for throttle, expected_class in zip(throttles, expected_throttle_classes):
        assert isinstance(throttle, expected_class)


@pytest.mark.django_db
def test_upload_viewset_perform_create_implements_upload_service(mocker):
    mock_service_class = mocker.patch("apps.uploads.views.UploadService")
    mock_service_instance = mock_service_class.return_value
    mock_upload = Mock(spec=Upload, id=123)
    mock_service_instance.create_upload.return_value = mock_upload

    user = mocker.Mock()
    mock_file = Mock()

    request = Mock(
        user=user,
        data={"purpose": Upload.Purpose.AVATAR, "visibility": Upload.Visibility.PUBLIC},
        FILES={"file": mock_file},
    )
    viewset = UploadViewSet(request=request)
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

    mock_serializer = mocker.Mock()
    mock_serializer.data = {"id": 123, "status": "restored"}

    viewset = UploadViewSet(action="restore", request=rf.post("/restore/"))

    mock_get_object = mocker.patch.object(viewset, "get_object", return_value=upload)
    mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

    response = viewset.restore(viewset.request, pk=123)

    assert response.status_code == 200
    assert response.data == mock_serializer.data
    mock_get_object.assert_called_once_with()
    assert upload.deleted_at is None
    upload.save.assert_called_once()


def test_upload_restore_returns_400_if_not_deleted(mocker, rf):
    upload = mocker.Mock(spec=Upload)
    upload.deleted_at = None

    viewset = UploadViewSet()
    mocker.patch.object(viewset, "get_object", return_value=upload)
    viewset.action = "restore"
    viewset.request = rf.post("/restore/")

    response = viewset.restore(viewset.request, pk=123)

    assert response.status_code == 400
    assert response.data == {"detail": "Upload is not deleted."}


@pytest.mark.django_db
def test_upload_editor_cannot_restore_other_editors_upload(
    rf, editor_factory, upload_factory
):
    owner = editor_factory()
    other_editor = editor_factory()
    upload = upload_factory(uploaded_by=owner, deleted_at=timezone.now())

    request = rf.post("/restore/")
    request.user = other_editor

    viewset = UploadViewSet(
        action="restore", filter_backends=[], request=request, kwargs={"pk": upload.pk}
    )

    with pytest.raises(Http404):
        viewset.restore(request, pk=upload.pk)

    upload.refresh_from_db()
    assert upload.deleted_at is not None


def test_upload_trash_action(mocker, rf):
    mock_queryset = mocker.MagicMock()
    mock_deleted_qs = mocker.MagicMock()
    mock_queryset.deleted.return_value = mock_deleted_qs

    mock_serializer = mocker.Mock()
    mock_serializer.data = [{"id": 1}, {"id": 2}]

    request = Request(rf.get("/uploads/trash/"))

    viewset = UploadViewSet(action="trash", request=request, filter_backends=[])

    mocker.patch.object(viewset, "get_queryset", return_value=mock_queryset)
    mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)
    mocker.patch.object(viewset, "paginate_queryset", return_value=mock_deleted_qs)
    mocker.patch.object(
        viewset, "get_paginated_response", return_value=Response(mock_serializer.data)
    )

    response = viewset.trash(request)

    mock_queryset.deleted.assert_called_once()
    viewset.get_serializer.assert_called_once_with(mock_deleted_qs, many=True)
    assert response.status_code == 200
    assert response.data == mock_serializer.data


@pytest.mark.django_db
class TestContentAction:
    @staticmethod
    def _viewset(request, upload, mocker):
        viewset = UploadViewSet(action="content", request=request)
        mocker.patch.object(viewset, "get_object", return_value=upload)
        return viewset

    def test_owner_gets_file_response(self, rf, editor_factory, upload_factory, mocker):
        user = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)

        request = rf.get("/")
        request.user = user
        viewset = self._viewset(request, upload, mocker)

        response = viewset.content(request, pk=str(upload.pk))

        assert response.status_code == 200
        assert response["Content-Type"] == upload.mime_type
        assert response["Content-Disposition"] == (
            f'inline; filename="{upload.original_filename}"'
        )
        assert response["Content-Length"] == str(upload.size)
        assert response["Cache-Control"] == "private, no-store"
        assert "X-Accel-Redirect" not in response

        body = b"".join(response.streaming_content)
        with upload.file.open("rb") as fh:
            assert body == fh.read()

    def test_non_private_upload_raises_404(
        self, rf, editor_factory, upload_factory, mocker
    ):
        user = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PUBLIC, uploaded_by=user)

        request = rf.get("/")
        request.user = user
        viewset = self._viewset(request, upload, mocker)

        with pytest.raises(Http404):
            viewset.content(request, pk=str(upload.pk))

    def test_accel_redirect_header_when_enabled(
        self, rf, settings, editor_factory, upload_factory, mocker
    ):
        settings.USE_X_ACCEL_REDIRECT = True
        user = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)

        request = rf.get("/")
        request.user = user
        viewset = self._viewset(request, upload, mocker)

        response = viewset.content(request, pk=str(upload.pk))

        assert response.status_code == 200
        assert response["X-Accel-Redirect"] == (f"/internal_media/{upload.file.name}")
        assert response.content == b""

    def test_content_disposition_strips_quotes_from_filename(
        self, rf, editor_factory, upload_factory, mocker
    ):
        user = editor_factory()
        upload = upload_factory(
            visibility=Upload.Visibility.PRIVATE,
            uploaded_by=user,
            original_filename='we"ird.txt',
        )

        request = rf.get("/")
        request.user = user
        viewset = self._viewset(request, upload, mocker)

        response = viewset.content(request, pk=str(upload.pk))

        assert response["Content-Disposition"] == 'inline; filename="we\\"ird.txt"'

    def test_missing_file_on_disk_raises_404(
        self, rf, editor_factory, upload_factory, mocker
    ):
        user = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=user)
        default_storage.delete(upload.file.name)

        request = rf.get("/")
        request.user = user
        viewset = self._viewset(request, upload, mocker)

        with pytest.raises(Http404):
            viewset.content(request, pk=str(upload.pk))

    def test_other_editor_gets_404_from_queryset(
        self, rf, editor_factory, upload_factory
    ):
        owner = editor_factory()
        other_editor = editor_factory()
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE, uploaded_by=owner)

        request = rf.get("/")
        request.user = other_editor
        viewset = UploadViewSet(
            action="content",
            filter_backends=[],
            request=request,
            kwargs={"pk": upload.pk},
        )

        with pytest.raises(Http404):
            viewset.content(request, pk=upload.pk)
