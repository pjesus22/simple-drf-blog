from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.permissions import IsEditor
from apps.content.models import Post, Tag
from apps.content.schemas import tag_viewset_schema
from apps.content.serializers import TagSerializer
from config.throttle import AnonReadThrottle, UserReadThrottle, WriteThrottle


@tag_viewset_schema
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

    def get_throttles(self):
        method = self.request.method
        if method in ("OPTIONS", "HEAD"):
            return []
        if self.action in ("list", "retrieve"):
            return (
                [UserReadThrottle()]
                if self.request.user.is_authenticated
                else [AnonReadThrottle()]
            )
        return [WriteThrottle()]
