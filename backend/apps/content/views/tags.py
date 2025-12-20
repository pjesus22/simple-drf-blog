from apps.content.models import Tag
from apps.content.serializers import TagSerializer
from apps.users.permissions import IsEditor
from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [IsEditor]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
