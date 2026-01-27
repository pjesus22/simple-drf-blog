from apps.accounts.permissions import (
    CanCreateUpload,
    CanDeleteUpload,
    IsEditor,
    IsOwner,
)
from apps.uploads.models import Upload
from apps.uploads.serializers import UploadSerializer
from apps.uploads.services import UploadService
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated


class UploadViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

    def get_permissions(self):
        permission_map = {
            "retrieve": [IsAuthenticated],
            "create": [CanCreateUpload],
            "update": [IsEditor, IsOwner],
            "partial_update": [IsEditor, IsOwner],
            "destroy": [CanDeleteUpload, IsOwner],
        }
        permission_classes = permission_map.get(self.action, [])
        return [p() for p in permission_classes]

    def perform_create(self, serializer):
        service = UploadService(
            uploaded_by=self.request.user,
            purpose=self.request.data.get("purpose"),
            visibility=self.request.data.get("visibility"),
        )
        serializer.instance = service.create_or_get_upload(
            file=self.request.FILES.get("file")
        )
