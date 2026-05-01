from django.contrib.auth import get_user_model
from rest_framework_json_api import serializers

from .models import Upload

User = get_user_model()


class UploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    uploaded_by = serializers.ResourceRelatedField(read_only=True)
    file = serializers.FileField(write_only=True, required=False)

    included_serializers = {
        "uploaded_by": "apps.accounts.serializers.users.BaseUserSerializer",
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

        if obj.visibility == Upload.Visibility.PRIVATE:
            if not request or not request.user.is_authenticated:
                return
            if obj.uploaded_by != request.user and request.user.role != User.Role.ADMIN:
                return

        if obj.deleted_at is not None:
            return

        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class UploadCreateSerializer(UploadSerializer):
    file = serializers.FileField(write_only=True, required=True)


class UploadUpdateSerializer(UploadSerializer):
    purpose = serializers.ChoiceField(
        choices=Upload.Purpose.choices,
        required=False,
    )
    visibility = serializers.ChoiceField(
        choices=Upload.Visibility.choices,
        required=False,
    )

    class Meta:
        model = Upload
        fields = ("purpose", "visibility")
        resource_name = "uploads"

    def validate_purpose(self, value):
        values = Upload.Purpose.values
        if value not in values:
            raise serializers.ValidationError(
                detail=(f"Invalid purpose. Must be one of: {', '.join(values)}."),
                code="invalid_purpose",
            )
        return value

    def validate_visibility(self, value):
        values = Upload.Visibility.values
        if value not in values:
            raise serializers.ValidationError(
                detail=(f"Invalid visibility. Must be one of: {', '.join(values)}."),
                code="invalid_visibility",
            )
        return value
