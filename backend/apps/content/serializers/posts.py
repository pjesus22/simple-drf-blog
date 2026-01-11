from apps.content.models import Category, Tag
from apps.uploads.models import Upload
from rest_framework_json_api import serializers

from ..models import Post


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ResourceRelatedField(read_only=True)
    category = serializers.ResourceRelatedField(
        queryset=Category.objects.all(),
    )
    tags = serializers.ResourceRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    thumbnail = serializers.ResourceRelatedField(
        queryset=Upload.objects.filter(purpose=Upload.Purpose.THUMBNAILS).all(),
        allow_null=True,
    )
    attachments = serializers.ResourceRelatedField(
        many=True,
        queryset=Upload.objects.filter(purpose=Upload.Purpose.ATTACHMENTS).all(),
    )
    lookup_field = "slug"

    included_serializers = {
        "author": "apps.accounts.serializers.UserListSerializer",
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
