from django.contrib.auth import get_user_model
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer
from apps.uploads.services import UploadService

User = get_user_model()


class UploadViewSet(ModelViewSet):
    queryset = Upload.objects.none()
    serializer_class = UploadSerializer
    permission_classes = [IsOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        if user.role == User.Role.ADMIN:
            return Upload.objects.all()

        return Upload.objects.filter(uploaded_by=user)

    def get_permissions(self):
        if self.action == "create":
            return [IsEditor()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return UploadCreateSerializer
        return UploadSerializer

    def perform_create(self, serializer):
        service = UploadService(
            uploaded_by=self.request.user,
            purpose=self.request.data.get("purpose"),
            visibility=self.request.data.get("visibility"),
        )
        serializer.instance = service.create_or_get_upload(
            file=self.request.FILES.get("file")
        )
