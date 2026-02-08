from unittest.mock import Mock

import pytest
from apps.accounts.permissions import IsAdmin, IsEditor, IsOwner
from apps.content.serializers import (
    PostAttachmentAddSerializer,
    PostAttachmentRemoveSerializer,
    PostCreateSerializer,
    PostRestoreSerializer,
    PostSerializer,
    PostSoftDeleteSerializer,
    PostStatusSerializer,
    PostThumbnailSerializer,
    PostUpdateSerializer,
)
from apps.content.views import CategoryViewSet, PostViewSet, TagViewSet
from rest_framework.permissions import AllowAny

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "action, expected_permissions",
    [("create", [IsAdmin]), ("partial_update", [IsAdmin]), ("destroy", [IsAdmin])],
    ids=("create", "partial_update", "destroy"),
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
    [("create", [IsEditor]), ("partial_update", [IsEditor]), ("destroy", [IsEditor])],
    ids=("create", "partial_update", "destroy"),
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
        ("create", [IsOwner, IsEditor]),
        ("update", [IsOwner, IsEditor]),
        ("partial_update", [IsOwner, IsEditor]),
        ("change_status", [IsOwner, IsEditor]),
        ("thumbnail", [IsOwner, IsEditor]),
        ("add_attachments", [IsOwner, IsEditor]),
        ("remove_attachment", [IsOwner, IsEditor]),
        ("soft_delete", [IsOwner, IsEditor]),
    ],
    ids=(
        "create",
        "update",
        "partial_update",
        "change_status",
        "thumbnail",
        "add_attachments",
        "remove_attachment",
        "soft_delete",
    ),
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


def test_post_viewset_restore_requires_admin_permission():
    viewset = PostViewSet(action="restore")
    permissions = viewset.get_permissions()
    assert len(permissions) == 1
    assert isinstance(permissions[0], IsAdmin)


def test_post_viewset_trash_requires_admin_permission():
    viewset = PostViewSet(action="trash")
    permissions = viewset.get_permissions()
    assert len(permissions) == 1
    assert isinstance(permissions[0], IsAdmin)


def test_post_viewset_destroy_raises_method_not_allowed():
    from rest_framework.test import APIRequestFactory

    factory = APIRequestFactory()
    request = factory.delete("/posts/test-slug/")
    viewset = PostViewSet(action="destroy")
    viewset.request = request

    from rest_framework.exceptions import MethodNotAllowed

    with pytest.raises(MethodNotAllowed):
        viewset.destroy(request)


@pytest.mark.parametrize(
    "action, expected_serializer",
    [
        ("create", PostCreateSerializer),
        ("update", PostUpdateSerializer),
        ("partial_update", PostUpdateSerializer),
        ("change_status", PostStatusSerializer),
        ("thumbnail", PostThumbnailSerializer),
        ("add_attachments", PostAttachmentAddSerializer),
        ("remove_attachment", PostAttachmentRemoveSerializer),
        ("soft_delete", PostSoftDeleteSerializer),
        ("restore", PostRestoreSerializer),
        ("list", PostSerializer),
        ("retrieve", PostSerializer),
    ],
)
def test_post_viewset_get_serializer_class_mapping(action, expected_serializer):
    viewset = PostViewSet(action=action)
    serializer_class = viewset.get_serializer_class()
    assert serializer_class == expected_serializer


def test_post_viewset_perform_create_sets_author(editor_factory):
    user = editor_factory()
    request = Mock(user=user)
    viewset = PostViewSet(request=request)
    mock_serializer = Mock()

    viewset.perform_create(mock_serializer)

    mock_serializer.save.assert_called_once_with(author=user)


class TestPostViewSet:
    def test_get_queryset_default_action_uses_visible_for(self, rf, editor_factory):
        """Default queryset should use visible_for manager method"""
        request = rf.get("/posts/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="list")

        from unittest.mock import patch

        with patch("apps.content.views.posts.Post") as mock_post:
            viewset.get_queryset()
            mock_post.objects.visible_for.assert_called_once_with(request.user)

    def test_get_queryset_restore_action_staff_user(self, rf, admin_factory):
        """Restore action with staff user should use with_deleted"""
        request = rf.get("/posts/restore/")
        request.user = admin_factory()
        viewset = PostViewSet(request=request, action="restore")

        from unittest.mock import patch

        with patch("apps.content.views.posts.Post") as mock_post:
            viewset.get_queryset()
            mock_post.objects.with_deleted.assert_called_once()

    def test_get_queryset_restore_action_non_staff_user(self, rf, editor_factory):
        """Restore action with non-staff user should use only_deleted and owned_by"""
        request = rf.get("/posts/restore/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="restore")

        from unittest.mock import MagicMock, patch

        with patch("apps.content.views.posts.Post") as mock_post:
            mock_queryset = MagicMock()
            mock_post.objects.only_deleted.return_value = mock_queryset

            viewset.get_queryset()

            mock_post.objects.only_deleted.assert_called_once()
            mock_queryset.owned_by.assert_called_once_with(request.user)

    def test_get_queryset_trash_action(self, rf, admin_factory):
        """Trash action should use only_deleted and owned_by"""
        request = rf.get("/posts/trash/")
        request.user = admin_factory()
        viewset = PostViewSet(request=request, action="trash")

        from unittest.mock import MagicMock, patch

        with patch("apps.content.views.posts.Post") as mock_post:
            mock_queryset = MagicMock()
            mock_post.objects.only_deleted.return_value = mock_queryset

            viewset.get_queryset()

            mock_post.objects.only_deleted.assert_called_once()
            mock_queryset.owned_by.assert_called_once_with(request.user)

    def test_get_queryset_soft_delete_action(self, rf, editor_factory):
        """Soft delete action should use owned_by"""
        request = rf.get("/posts/soft_delete/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="soft_delete")

        from unittest.mock import patch

        with patch("apps.content.views.posts.Post") as mock_post:
            viewset.get_queryset()
            mock_post.objects.owned_by.assert_called_once_with(request.user)

    def test_change_status_action_success(self, rf, post_factory, editor_factory):
        post = post_factory(status="draft")
        data = {"status": "published"}
        request = rf.post(f"/posts/{post.slug}/change_status/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="change_status", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        mock_change_status = Mock()
        post.change_status = mock_change_status
        response = viewset.change_status(request, slug=post.slug)

        assert response.status_code == 200
        mock_change_status.assert_called_once_with("published")

    def test_change_status_action_validation_error(
        self, rf, post_factory, editor_factory
    ):
        post = post_factory(status="deleted")
        data = {"status": "published"}
        request = rf.post(f"/posts/{post.slug}/change_status/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="change_status", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        from rest_framework.exceptions import ValidationError as DRFValidationError

        with pytest.raises(DRFValidationError) as exc_info:
            viewset.change_status(request, slug=post.slug)

        assert "status" in exc_info.value.detail
        assert "Cannot change status of a deleted post" in str(
            exc_info.value.detail["status"][0]
        )

    def test_thumbnail_action_post_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory
    ):
        post = post_factory()
        thumbnail = upload_factory(purpose="thumbnail")
        data = {"id": str(thumbnail.id)}
        request = rf.post(f"/posts/{post.slug}/thumbnail/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="thumbnail", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        response = viewset.thumbnail(request, slug=post.slug)

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.thumbnail == thumbnail

    def test_thumbnail_action_delete_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory
    ):
        thumbnail = upload_factory(purpose="thumbnail")
        post = post_factory(thumbnail=thumbnail)
        request = rf.delete(f"/posts/{post.slug}/thumbnail/")
        request.user = editor_factory()
        request.data = {}

        viewset = PostViewSet(
            request=request, action="thumbnail", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)

        response = viewset.thumbnail(request, slug=post.slug)

        assert response.status_code == 204
        post.refresh_from_db()
        assert post.thumbnail is None

    def test_add_attachments_action_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory
    ):
        post = post_factory()
        attachments = upload_factory.create_batch(size=2, purpose="attachment")
        data = {"attachments": [str(a.id) for a in attachments]}
        request = rf.post(
            f"/posts/{post.slug}/attachments/",
            data,
        )
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="add_attachments", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        response = viewset.add_attachments(request, slug=post.slug)

        assert response.status_code == 200
        assert post.attachments.count() == 2

    def test_remove_attachment_action_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory
    ):
        post = post_factory()
        attachment = upload_factory(purpose="attachment")
        post.attachments.add(attachment)
        request = rf.delete(f"/posts/{post.slug}/attachments/{attachment.id}/")
        request.user = editor_factory()
        request.data = {}

        viewset = PostViewSet(
            request=request, action="remove_attachment", kwargs={"slug": post.slug}
        )
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        response = viewset.remove_attachment(
            request, slug=post.slug, attachment_id=str(attachment.id)
        )

        assert response.status_code == 204
        assert post.attachments.count() == 0

    def test_soft_delete_action_success(self, rf, post_factory, editor_factory):
        post = post_factory(status="draft")
        data = {"confirm": True}
        request = rf.post(f"/posts/{post.slug}/soft_delete/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="soft_delete", kwargs={"slug": post.slug}
        )
        viewset.format_kwarg = None
        viewset.get_object = Mock(return_value=post)

        response = viewset.soft_delete(request, slug=post.slug)

        assert response.status_code == 204
        post.refresh_from_db()
        assert post.status == "deleted"

    def test_soft_delete_action_raises_validation_error_if_post_is_already_deleted(
        self, rf, post_factory, editor_factory
    ):
        post = post_factory(status="deleted")
        data = {"confirm": True}
        request = rf.post(f"/posts/{post.slug}/soft_delete/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="soft_delete", kwargs={"slug": post.slug}
        )
        viewset.format_kwarg = None
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        from rest_framework.exceptions import ValidationError as DRFValidationError

        with pytest.raises(DRFValidationError) as exc_info:
            viewset.soft_delete(request, slug=post.slug)

        assert "This post is already deleted" in str(exc_info.value.detail)

    def test_restore_action_success(self, rf, post_factory, admin_factory):
        post = post_factory(status="deleted")
        data = {"confirm": True}
        request = rf.post(f"/posts/{post.slug}/restore/", data)
        request.user = admin_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="restore", kwargs={"slug": post.slug}
        )
        viewset.format_kwarg = None
        viewset.get_object = Mock(return_value=post)
        viewset.get_serializer_context = Mock(return_value={"request": request})

        response = viewset.restore(request, slug=post.slug)

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.status == "draft"

    def test_post_viewset_trash_action_returns_deleted_posts(
        self, rf, post_factory, admin_factory
    ):
        admin = admin_factory()
        post_factory(status="draft", author=admin)
        deleted_post = post_factory(status="deleted", author=admin)
        wsgi_request = rf.get("/posts/trash/")
        wsgi_request.user = admin

        # Wrap with DRF Request to provide query_params
        from rest_framework.request import Request

        request = Request(wsgi_request)
        request.user = admin  # Explicitly set user on DRF Request

        viewset = PostViewSet(request=request, action="trash")
        viewset.format_kwarg = None
        viewset.get_serializer_context = Mock(return_value={"request": request})

        response = viewset.trash(request)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == deleted_post.id
