from rest_framework_json_api import serializers

from .models import Upload


class UploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    uploaded_by = serializers.ResourceRelatedField(read_only=True)
    file = serializers.FileField(write_only=True, required=True)

    included_serializers = {
        "uploaded_by": "apps.accounts.serializers.UserListSerializer"
    }

    class Meta:
        model = Upload
        fields = (
            "id",
            "url",
            "file",
            "original_filename",
            "mime_type",
            "size",
            "width",
            "height",
            "purpose",
            "visibility",
            "created_at",
            "updated_at",
            "uploaded_by",
        )
        read_only_fields = (
            "id",
            "url",
            "original_filename",
            "mime_type",
            "size",
            "width",
            "height",
            "created_at",
            "updated_at",
            "uploaded_by",
        )
        resource_name = "uploads"

    def get_url(self, obj):
        request = self.context.get("request")

        if obj.visibility == Upload.Visibility.PRIVATE:
            if not request or not request.user.is_authenticated:
                return
            if obj.uploaded_by != request.user and not request.user.is_staff:
                return

        if request:
            return request.build_absolute_uri(obj.file.url)

        return obj.file.url
