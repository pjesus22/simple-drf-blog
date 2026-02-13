from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.permissions import IsAdmin
from apps.content.models import Category, Post
from apps.content.schemas import category_viewset_schema
from apps.content.serializers import CategorySerializer


@category_viewset_schema
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return Category.objects.prefetch_related(
            Prefetch(
                lookup="posts",
                queryset=Post.objects.visible_for(self.request.user),
            )
        )

    def get_permissions(self):
        if self.action in ("create", "partial_update", "destroy"):
            permission_classes = [IsAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
