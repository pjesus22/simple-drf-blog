from rest_framework_json_api import serializers

from ..models import Post


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ResourceRelatedField(read_only=True)
    category = serializers.ResourceRelatedField(read_only=True)
    tags = serializers.ResourceRelatedField(many=True, read_only=True)
    thumbnail = serializers.ResourceRelatedField(read_only=True)
    attachments = serializers.ResourceRelatedField(many=True, read_only=True)

    included_serializers = {
        "author": "apps.users.serializers.PublicUserSerializer",
        "category": "apps.content.serializers.CategorySerializer",
        "tags": "apps.content.serializers.TagSerializer",
        "thumbnail": "apps.uploads.serializers.UploadSerializer",
        "attachments": "apps.uploads.serializers.UploadSerializer",
    }

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "content",
            "summary",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "author",
            "category",
            "tags",
            "thumbnail",
            "attachments",
        )
        resource_name = "posts"
        read_only_fields = ("id", "created_at", "updated_at", "published_at")
