from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.models import Upload
from apps.uploads.schemas import upload_viewset_schema
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer
from apps.uploads.services import UploadService
from apps.uploads.storage import get_media_storage

User = get_user_model()


class StorageHealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        healthy = get_media_storage().health_check()
        if healthy:
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        return Response(
            {"status": "degraded"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@upload_viewset_schema
class UploadViewSet(ModelViewSet):
    queryset = Upload.objects.none()
    serializer_class = UploadSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        if user.role == User.Role.ADMIN:
            return Upload.objects.all()

        return Upload.objects.filter(uploaded_by=user)

    def get_permissions(self):
        if self.action in ["list", "create"]:
            permission_classes = [IsEditor]
        else:
            permission_classes = [IsEditor, IsOwner]
        return [p() for p in permission_classes]

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
        serializer.instance = service.create_upload(file=self.request.FILES.get("file"))

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        upload = get_object_or_404(Upload.all_objects, pk=pk)

        if upload.deleted_at is None:
            return Response(
                {"detail": "Upload is not deleted"}, status=status.HTTP_400_BAD_REQUEST
            )

        upload.deleted_at = None
        upload.save()

        serializer = self.get_serializer(upload)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trash(self, request):
        queryset = self.get_queryset().only_deleted()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
