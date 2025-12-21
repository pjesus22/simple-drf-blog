from apps.users.models import EditorProfile
from apps.users.permissions import IsOwner
from apps.users.serializers import EditorProfileSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = EditorProfile.objects.all()
    serializer_class = EditorProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            permission_classes = [IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
