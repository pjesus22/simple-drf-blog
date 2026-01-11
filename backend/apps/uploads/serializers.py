from rest_framework_json_api import serializers

from .models import Upload


class UploadSerializer(serializers.ModelSerializer):
    queryset = Upload.objects.all().select_related("uploaded_by")
    url = serializers.SerializerMethodField()
    uploaded_by = serializers.ResourceRelatedField(read_only=True)
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
            "created_at",
            "updated_at",
        )
        resource_name = "uploads"
