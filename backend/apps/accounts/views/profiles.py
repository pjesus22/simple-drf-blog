from apps.accounts.models import EditorProfile
from apps.accounts.permissions import IsOwner
from apps.accounts.serializers import EditorProfileSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = EditorProfile.objects.select_related("user").prefetch_related(
        "social_links"
    )
    serializer_class = EditorProfileSerializer
    http_method_names = ["get", "put", "head", "options"]

    def get_permissions(self):
        if self.action == "update":
            return [IsOwner()]
        return [IsAuthenticated()]
