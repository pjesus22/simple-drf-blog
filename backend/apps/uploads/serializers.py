from rest_framework_json_api import serializers

from .models import Upload


class UploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)
    uploaded_by = serializers.ResourceRelatedField(read_only=True)
    file = serializers.FileField(write_only=True, required=True)
    included_serializers = {
        "uploaded_by": "apps.accounts.serializers.UserListSerializer"
    }

    def get_url(self, obj):
        request = self.context.get("request")

        if not obj.is_public:
            if not request or not request.user.is_authenticated:
                return None
            if request.user != obj.uploaded_by and not request.user.is_staff:
                return None

        if request:
            return request.build_absolute_uri(obj.file.url)
        else:
            return obj.file.url if obj.file else None

    class Meta:
        model = Upload
        fields = (
            "id",
            "url",
            "file",
            "original_filename",
            "file_type",
            "mime_type",
            "size",
            "width",
            "height",
            "purpose",
            "is_public",
            "created_at",
            "updated_at",
            "uploaded_by",
        )
        read_only_fields = (
            "id",
            "url",
            "size",
            "mime_type",
            "width",
            "height",
            "file_type",
            "original_filename",
            "created_at",
            "updated_at",
            "hash_sha256",
        )
        resource_name = "uploads"
