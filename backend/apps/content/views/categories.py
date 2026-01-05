from apps.content.mixins import PostFilterMixin
from apps.content.models import Category
from apps.content.serializers import CategorySerializer
from apps.users.permissions import IsAdmin
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class CategoryViewSet(PostFilterMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_permissions(self):
        if self.action in ("create", "partial_update", "destroy"):
            permission_classes = [IsAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        filtered_posts = self.get_filtered_posts_queryset()
        return (
            super()
            .get_queryset()
            .prefetch_related(Prefetch("posts", queryset=filtered_posts))
        )
