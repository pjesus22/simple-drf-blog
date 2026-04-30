from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_json_api.django_filters import DjangoFilterBackend

from apps.accounts.permissions import IsAdmin, IsEditor, IsOwner
from apps.content.filters import PostFilter
from apps.content.models import Post
from apps.content.schemas import (
    add_attachments_schema,
    change_status_schema,
    post_viewset_schema,
    remove_attachment_schema,
    restore_schema,
    # soft_delete_schema,
    thumbnail_add_schema,
    thumbnail_remove_schema,
    trash_schema,
)
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


@post_viewset_schema
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter

    def get_queryset(self):
        if self.action == "restore":
            return self._get_restore_queryset()

        elif self.action == "trash":
            return self._get_trash_queryset()

        elif self.action == "destroy":
            return self._get_soft_delete_queryset()

        return Post.objects.visible_for(self.request.user)

    def _get_restore_queryset(self):
        user = self.request.user
        return (
            Post.objects.with_deleted()
            if user.is_staff
            else Post.objects.only_deleted().owned_by(user)
        )

    def _get_trash_queryset(self):
        return Post.objects.only_deleted().owned_by(self.request.user)

    def _get_soft_delete_queryset(self):
        return Post.objects.owned_by(self.request.user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action == "restore":
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsOwner, IsEditor]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        serializer_map = {
            "create": PostCreateSerializer,
            "update": PostUpdateSerializer,
            "partial_update": PostUpdateSerializer,
            "destroy": PostSoftDeleteSerializer,
            "restore": PostRestoreSerializer,
            "change_status": PostStatusSerializer,
            "thumbnail": PostThumbnailSerializer,
            "add_attachments": PostAttachmentAddSerializer,
            "remove_attachment": PostAttachmentRemoveSerializer,
        }
        return serializer_map.get(self.action, PostSerializer)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        request._metrics_post_instance = post
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @change_status_schema
    @action(detail=True, methods=["post"])
    def change_status(self, request, slug=None):
        post = self.get_object()
        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            data=PostSerializer(post, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @thumbnail_add_schema
    @thumbnail_remove_schema
    @action(detail=True, methods=["post", "delete"])
    def thumbnail(self, request, slug=None):
        post = self.get_object()

        if request.method == "DELETE":
            post.thumbnail = None
            post.save(update_fields=["thumbnail"])
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post.thumbnail = serializer.validated_data["id"]
        post.save(update_fields=["thumbnail", "updated_at"])

        return Response(
            data=self.get_serializer(post).data,
            status=status.HTTP_200_OK,
        )

    @add_attachments_schema
    @action(detail=True, methods=["post"], url_path="attachments")
    def add_attachments(self, request, slug=None):
        post = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post.attachments.add(*serializer.validated_data["attachments"])

        return Response(
            data=PostSerializer(
                post,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )

    @remove_attachment_schema
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"attachments/(?P<attachment_id>[^/.]+)",
    )
    def remove_attachment(self, request, slug=None, attachment_id=None):
        post = self.get_object()

        serializer = self.get_serializer(
            data={"attachment_id": attachment_id},
            context={"post": post},
        )
        serializer.is_valid(raise_exception=True)

        post.attachments.remove(serializer.validated_data["attachment_id"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @soft_delete_schema
    # @action(detail=True, methods=["post"])
    # def soft_delete(self, request, slug=None):
    #     post = self.get_object()

    #     serializer = self.get_serializer(
    #         post, data=request.data, context={"request": request}
    #     )
    #     serializer.is_valid(raise_exception=True)

    #     serializer.save()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    @restore_schema
    @action(detail=True, methods=["post"])
    def restore(self, request, slug=None):
        post = self.get_object()

        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(
            data=PostSerializer(post, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @trash_schema
    @action(detail=False, methods=["get"])
    def trash(self, request):
        qs = self.filter_queryset(self.get_queryset())
        serializer = PostSerializer(
            qs, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)
