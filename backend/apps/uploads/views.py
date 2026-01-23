from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.serializers import UploadSerializer
from apps.uploads.services import UploadService
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated


class NoListViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    pass


class UploadViewSet(NoListViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            permission_classes = [IsEditor, IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        service = UploadService(
            uploaded_by=self.request.user,
            purpose=self.request.data.get("purpose"),
        )
        serializer.instance = service.create_upload(file=self.request.FILES.get("file"))
