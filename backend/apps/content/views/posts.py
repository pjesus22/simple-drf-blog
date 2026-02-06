from apps.accounts.permissions import IsAdmin, IsEditor, IsOwner
from apps.content.filters import PostFilter
from apps.content.models import Post
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
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_json_api.django_filters import DjangoFilterBackend


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter

    def get_queryset(self):
        user = self.request.user

        if self.action == "restore":
            return (
                Post.objects.with_deleted()
                if user.is_staff
                else Post.objects.only_deleted().owned_by(user)
            )

        elif self.action == "trash":
            return Post.objects.only_deleted().owned_by(user)

        elif self.action == "soft_delete":
            return Post.objects.owned_by(user)

        return Post.objects.visible_for(user)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            permission_classes = [AllowAny]
        elif self.action in ("restore", "trash"):
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsOwner, IsEditor]

        return [permission() for permission in permission_classes]

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            method="DELETE",
            detail="Use POST /posts/{slug}/soft-delete/ instead.",
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        serializer_map = {
            "create": PostCreateSerializer,
            "update": PostUpdateSerializer,
            "partial_update": PostUpdateSerializer,
            "soft_delete": PostSoftDeleteSerializer,
            "restore": PostRestoreSerializer,
            "change_status": PostStatusSerializer,
            "thumbnail": PostThumbnailSerializer,
            "add_attachments": PostAttachmentAddSerializer,
            "remove_attachment": PostAttachmentRemoveSerializer,
        }
        return serializer_map.get(self.action, PostSerializer)

    @action(detail=True, methods=["post"])
    def change_status(self, request, slug=None):
        post = self.get_object()
        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            PostSerializer(post, context=self.get_serializer_context()).data
        )

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
            data=PostSerializer(post, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="attachments")
    def add_attachments(self, request, slug=None):
        post = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post.attachments.add(*serializer.validated_data["attachments"])

        return Response(
            data=PostSerializer(post, context=self.get_serializer_context()).data,
            status=status.HTTP_200_OK,
        )

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

    @action(detail=True, methods=["post"])
    def soft_delete(self, request, slug=None):
        post = self.get_object()

        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request, slug=None):
        post = self.get_object()

        serializer = self.get_serializer(
            post, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(
            PostSerializer(post, context=self.get_serializer_context()).data,
        )

    @action(detail=False, methods=["get"])
    def trash(self, request):
        qs = self.filter_queryset(self.get_queryset())
        serializer = PostSerializer(
            qs, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)
