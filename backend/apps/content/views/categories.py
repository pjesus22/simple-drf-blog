from apps.content.models import Category
from apps.content.serializers import CategorySerializer
from apps.users.permissions import IsAdmin
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [IsAdmin]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
