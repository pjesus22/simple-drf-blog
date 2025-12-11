from rest_framework_json_api import serializers

from ..models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
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
        ]
        read_only_fields = ["id", "created_at", "updated_at", "published_at"]

    class JSONAPIMeta:
        included_resources = ["author", "category", "tags", "attachments", "thumbnail"]
