import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from django.utils.http import content_disposition_header
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsEditor, IsOwner
from apps.uploads.exceptions import Conflict
from apps.uploads.models import Upload
from apps.uploads.schemas import (
    upload_content_action_schema,
    upload_restore_action_schema,
    upload_trash_action_schema,
    upload_viewset_schema,
)
from apps.uploads.serializers import (
    UploadCreateSerializer,
    UploadSerializer,
    UploadUpdateSerializer,
)
from apps.uploads.services import UploadService
from config.throttle import ReadWriteThrottleMixin

User = get_user_model()
logger = logging.getLogger(__name__)


@upload_viewset_schema
class UploadViewSet(ReadWriteThrottleMixin, ModelViewSet):
    queryset = Upload.objects.none()
    serializer_class = UploadSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    read_actions = ("list", "retrieve", "trash", "content")
    upload_actions = ("create",)

    def get_queryset(self):
        user = self.request.user
        if self.action == "restore":
            qs = Upload.all_objects.filter(deleted_at__isnull=False)
        elif self.action == "trash":
            qs = Upload.objects.only_deleted()
        else:
            qs = Upload.objects.all()

        if not user.is_admin:
            qs = qs.filter(uploaded_by=user)
        return qs

    def get_permissions(self):
        if self.action in ["list", "create"]:
            permission_classes = [IsEditor]
        else:
            permission_classes = [IsEditor, IsOwner]
        return [p() for p in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return UploadCreateSerializer
        elif self.action == "partial_update":
            return UploadUpdateSerializer
        return UploadSerializer

    def perform_create(self, serializer):
        service = UploadService(
            uploaded_by=self.request.user,
            purpose=self.request.data.get("purpose"),
            visibility=self.request.data.get("visibility"),
        )
        serializer.instance = service.create_upload(file=self.request.FILES.get("file"))

    def perform_update(self, serializer):
        upload = self.get_object()
        data = serializer.validated_data

        try:
            if "visibility" in data:
                upload = UploadService.change_visibility(upload, data["visibility"])

            if "purpose" in data:
                upload.purpose = data["purpose"]
                upload.save(update_fields=["purpose", "updated_at"])

            serializer.instance = upload
        except (FileNotFoundError, FileExistsError) as exc:
            logger.exception("Upload visibility move failed", exc_info=exc)
            raise Conflict() from exc

        if not data:
            return

        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at", "updated_at"])

    @upload_restore_action_schema
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        upload = self.get_object()

        if upload.deleted_at is None:
            return Response(
                {"detail": "Upload is not deleted."}, status=status.HTTP_400_BAD_REQUEST
            )

        upload.deleted_at = None
        upload.save()

        serializer = self.get_serializer(upload)
        return Response(serializer.data)

    @upload_trash_action_schema
    @action(detail=False, methods=["get"])
    def trash(self, request):
        qs = self.filter_queryset(self.get_queryset().deleted())
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @upload_content_action_schema
    @action(detail=True, methods=["get"], url_path="content")
    def content(self, request, pk=None):
        upload = self.get_object()

        if upload.visibility == Upload.Visibility.PUBLIC:
            raise Http404

        if settings.USE_X_ACCEL_REDIRECT:
            response = HttpResponse()
            response["X-Accel-Redirect"] = f"/internal_media/{upload.file.name}"
        else:
            try:
                fh = upload.file.open("rb")
            except FileNotFoundError as exc:
                raise Http404 from exc
            response = FileResponse(fh)

        response["Content-Type"] = upload.mime_type
        response["Content-Disposition"] = content_disposition_header(
            False, upload.original_filename
        )
        response["Content-Length"] = str(upload.size)
        response["Cache-Control"] = "private, no-store"

        return response
