from apps.accounts.permissions import IsEditor
from apps.content.models import Post, Tag
from apps.content.serializers import TagSerializer
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Tag.objects.prefetch_related(
            Prefetch(
                lookup="posts",
                queryset=Post.objects.visible_for(self.request.user),
            )
        )

    def get_permissions(self):
        if self.action in ("create", "partial_update", "destroy"):
            permission_classes = [IsEditor]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
