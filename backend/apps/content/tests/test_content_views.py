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
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "viewset_class, action, expected_permissions",
    [
        (CategoryViewSet, "create", [IsAdmin]),
        (CategoryViewSet, "partial_update", [IsAdmin]),
        (CategoryViewSet, "destroy", [IsAdmin]),
        (CategoryViewSet, "list", [AllowAny]),
        (CategoryViewSet, "retrieve", [AllowAny]),
        (TagViewSet, "create", [IsEditor]),
        (TagViewSet, "partial_update", [IsEditor]),
        (TagViewSet, "destroy", [IsEditor]),
        (TagViewSet, "list", [AllowAny]),
        (TagViewSet, "retrieve", [AllowAny]),
        (PostViewSet, "create", [IsOwner, IsEditor]),
        (PostViewSet, "update", [IsOwner, IsEditor]),
        (PostViewSet, "partial_update", [IsOwner, IsEditor]),
        (PostViewSet, "change_status", [IsOwner, IsEditor]),
        (PostViewSet, "thumbnail", [IsOwner, IsEditor]),
        (PostViewSet, "add_attachments", [IsOwner, IsEditor]),
        (PostViewSet, "remove_attachment", [IsOwner, IsEditor]),
        (PostViewSet, "soft_delete", [IsOwner, IsEditor]),
        (PostViewSet, "list", [AllowAny]),
        (PostViewSet, "retrieve", [AllowAny]),
        (PostViewSet, "restore", [IsAdmin]),
        (PostViewSet, "trash", [IsAdmin]),
    ],
)
def test_content_viewsets_return_correct_permissions(
    viewset_class, action, expected_permissions
):
    viewset = viewset_class(action=action)
    permissions = viewset.get_permissions()
    assert len(permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions for {viewset_class.__name__}:{action}, got {len(permissions)}"
    )
    for permission, expected_permission in zip(permissions, expected_permissions):
        assert isinstance(permission, expected_permission)


class TestPostViewSet:
    def test_post_viewset_destroy_raises_method_not_allowed(self):
        factory = APIRequestFactory()
        request = factory.delete("/posts/test-slug/")
        viewset = PostViewSet(action="destroy")
        viewset.request = request

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
    def test_post_viewset_get_serializer_class_mapping(
        self, action, expected_serializer
    ):
        viewset = PostViewSet(action=action)
        serializer_class = viewset.get_serializer_class()
        assert serializer_class == expected_serializer

    def test_post_viewset_perform_create_sets_author(self, mocker, editor_factory):
        user = editor_factory()
        request = mocker.Mock(user=user)
        viewset = PostViewSet(request=request)
        mock_serializer = mocker.Mock()

        viewset.perform_create(mock_serializer)

        mock_serializer.save.assert_called_once_with(author=user)

    def test_get_queryset_default_action_uses_visible_for(
        self, rf, editor_factory, mocker
    ):
        request = rf.get("/posts/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="list")

        mock_post = mocker.patch("apps.content.views.posts.Post")
        viewset.get_queryset()
        mock_post.objects.visible_for.assert_called_once_with(request.user)

    def test_get_queryset_restore_action_staff_user(self, rf, admin_factory, mocker):
        request = rf.get("/posts/restore/")
        request.user = admin_factory()
        viewset = PostViewSet(request=request, action="restore")

        mock_post = mocker.patch("apps.content.views.posts.Post")
        viewset.get_queryset()
        mock_post.objects.with_deleted.assert_called_once()

    def test_get_queryset_restore_action_non_staff_user(
        self, rf, editor_factory, mocker
    ):
        request = rf.get("/posts/restore/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="restore")

        mock_post = mocker.patch("apps.content.views.posts.Post")
        mock_queryset = mocker.MagicMock()
        mock_post.objects.only_deleted.return_value = mock_queryset

        viewset.get_queryset()

        mock_post.objects.only_deleted.assert_called_once()
        mock_queryset.owned_by.assert_called_once_with(request.user)

    def test_get_queryset_trash_action(self, rf, admin_factory, mocker):
        request = rf.get("/posts/trash/")
        request.user = admin_factory()
        viewset = PostViewSet(request=request, action="trash")

        mock_post = mocker.patch("apps.content.views.posts.Post")
        mock_queryset = mocker.MagicMock()
        mock_post.objects.only_deleted.return_value = mock_queryset

        viewset.get_queryset()

        mock_post.objects.only_deleted.assert_called_once()
        mock_queryset.owned_by.assert_called_once_with(request.user)

    def test_get_queryset_soft_delete_action(self, rf, editor_factory, mocker):
        request = rf.get("/posts/soft_delete/")
        request.user = editor_factory()
        viewset = PostViewSet(request=request, action="soft_delete")

        mock_post = mocker.patch("apps.content.views.posts.Post")
        viewset.get_queryset()
        mock_post.objects.owned_by.assert_called_once_with(request.user)

    def test_change_status_action_success(
        self, rf, post_factory, editor_factory, mocker
    ):
        post = post_factory(status="draft")
        data = {"status": "published"}
        request = rf.post(f"/posts/{post.slug}/change_status/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="change_status", kwargs={"slug": post.slug}
        )
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        mock_change_status = mocker.Mock()
        post.change_status = mock_change_status
        response = viewset.change_status(request, slug=post.slug)

        assert response.status_code == 200
        mock_change_status.assert_called_once_with("published")

    def test_change_status_action_validation_error(
        self, rf, post_factory, editor_factory, mocker
    ):
        post = post_factory(status="deleted")
        data = {"status": "published"}
        request = rf.post(f"/posts/{post.slug}/change_status/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="change_status", kwargs={"slug": post.slug}
        )
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        with pytest.raises(ValidationError) as exc_info:
            viewset.change_status(request, slug=post.slug)

        assert "status" in exc_info.value.detail
        assert "Cannot change status of a deleted post" in str(
            exc_info.value.detail["status"][0]
        )

    def test_thumbnail_action_post_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory, mocker
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
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        response = viewset.thumbnail(request, slug=post.slug)

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.thumbnail == thumbnail

    def test_thumbnail_action_delete_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory, mocker
    ):
        thumbnail = upload_factory(purpose="thumbnail")
        post = post_factory(thumbnail=thumbnail)
        request = rf.delete(f"/posts/{post.slug}/thumbnail/")
        request.user = editor_factory()
        request.data = {}

        viewset = PostViewSet(
            request=request, action="thumbnail", kwargs={"slug": post.slug}
        )
        viewset.get_object = mocker.Mock(return_value=post)

        response = viewset.thumbnail(request, slug=post.slug)

        assert response.status_code == 204
        post.refresh_from_db()
        assert post.thumbnail is None

    def test_add_attachments_action_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory, mocker
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
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        response = viewset.add_attachments(request, slug=post.slug)

        assert response.status_code == 200
        assert post.attachments.count() == 2

    def test_remove_attachment_action_success(
        self, rf, post_factory, upload_factory, clean_media, editor_factory, mocker
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
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        response = viewset.remove_attachment(
            request, slug=post.slug, attachment_id=str(attachment.id)
        )

        assert response.status_code == 204
        assert post.attachments.count() == 0

    def test_soft_delete_action_success(self, rf, post_factory, editor_factory, mocker):
        post = post_factory(status="draft")
        data = {"confirm": True}
        request = rf.post(f"/posts/{post.slug}/soft_delete/", data)
        request.user = editor_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="soft_delete", kwargs={"slug": post.slug}
        )
        viewset.format_kwarg = None
        viewset.get_object = mocker.Mock(return_value=post)

        response = viewset.soft_delete(request, slug=post.slug)

        assert response.status_code == 204
        post.refresh_from_db()
        assert post.status == "deleted"

    def test_soft_delete_action_raises_validation_error_if_post_is_already_deleted(
        self, rf, post_factory, editor_factory, mocker
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
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        with pytest.raises(ValidationError) as exc_info:
            viewset.soft_delete(request, slug=post.slug)

        assert "This post is already deleted" in str(exc_info.value.detail)

    def test_restore_action_success(self, rf, post_factory, admin_factory, mocker):
        post = post_factory(status="deleted")
        data = {"confirm": True}
        request = rf.post(f"/posts/{post.slug}/restore/", data)
        request.user = admin_factory()
        request.data = data

        viewset = PostViewSet(
            request=request, action="restore", kwargs={"slug": post.slug}
        )
        viewset.format_kwarg = None
        viewset.get_object = mocker.Mock(return_value=post)
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        response = viewset.restore(request, slug=post.slug)

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.status == "draft"

    def test_post_viewset_trash_action_returns_deleted_posts(
        self, rf, post_factory, admin_factory, mocker
    ):
        admin = admin_factory()
        post_factory(status="draft", author=admin)
        deleted_post = post_factory(status="deleted", author=admin)
        wsgi_request = rf.get("/posts/trash/")
        wsgi_request.user = admin

        request = Request(wsgi_request)
        request.user = admin

        viewset = PostViewSet(request=request, action="trash")
        viewset.format_kwarg = None
        viewset.get_serializer_context = mocker.Mock(return_value={"request": request})

        response = viewset.trash(request)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == deleted_post.id
