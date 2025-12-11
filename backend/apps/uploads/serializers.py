from rest_framework_json_api import serializers

from .models import Upload


class UploadSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    included_serializers = {
        "uploaded_by": "users.serializers.users.PublicUserSerializer",
    }

    def get_url(self, obj):
        request = self.context.get("request")

        if not obj.is_public:
            if not request or not request.user.is_authenticated:
                return None
            if request.user != obj.uploaded_by:
                return None

        if request:
            return request.build_absolute_uri(obj.file.url)
        else:
            return obj.file.url if obj.file else None

    def validate(self, attrs):
        MEDIA_TYPES = ("image", "video")

        file_type = attrs.get("file_type")
        if file_type not in MEDIA_TYPES:
            attrs["width"] = None
            attrs["height"] = None
        return attrs

    class Meta:
        model = Upload
        fields = [
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
        ]
        read_only_fields = [
            "id",
            "url",
            "size",
            "mime_type",
            "width",
            "height",
            "is_public",
            "created_at",
            "updated_at",
        ]

    class JSONAPIMeta:
        included_resources = ["uploaded_by"]
