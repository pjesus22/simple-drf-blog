from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework_json_api import serializers

from .models import Upload

User = get_user_model()


class UploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    uploaded_by = serializers.ResourceRelatedField(read_only=True)
    file = serializers.FileField(write_only=True, required=False)

    included_serializers = {
        "uploaded_by": "apps.accounts.serializers.users.UserListSerializer",
    }

    class Meta:
        model = Upload
        fields = (
            "id",
            "uploaded_by",
            "file",
            "url",
            "original_filename",
            "mime_type",
            "size",
            "width",
            "height",
            "purpose",
            "visibility",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "uploaded_by",
            "url",
            "original_filename",
            "mime_type",
            "size",
            "width",
            "height",
            "created_at",
            "updated_at",
        )
        resource_name = "uploads"

    def get_url(self, obj) -> str | None:
        request = self.context.get("request")

        if obj.deleted_at is not None:
            return

        if obj.visibility != Upload.Visibility.PUBLIC:
            if not request or not request.user.is_authenticated:
                return
            if obj.uploaded_by != request.user and not request.user.is_admin:
                return
            url = reverse("v1:upload-content", kwargs={"pk": obj.pk})
            return request.build_absolute_uri(url)

        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class UploadCreateSerializer(UploadSerializer):
    file = serializers.FileField(write_only=True, required=True)


class UploadUpdateSerializer(UploadSerializer):
    class Meta:
        model = Upload
        fields = ("purpose", "visibility")
        resource_name = "uploads"
