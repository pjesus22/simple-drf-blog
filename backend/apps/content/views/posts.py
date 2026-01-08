from apps.accounts.permissions import IsEditor, IsOwner
from apps.content.models import Post
from apps.content.serializers import PostSerializer
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.all()
        .select_related("author", "category", "thumbnail")
        .prefetch_related("tags", "attachments")
    )
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [IsEditor, IsOwner]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
