from rest_framework_json_api import serializers

from apps.content.models import Tag


class TagSerializer(serializers.ModelSerializer):
    posts = serializers.ResourceRelatedField(many=True, read_only=True)
    included_serializers = {"posts": "apps.content.serializers.posts.PostSerializer"}

    class Meta:
        model = Tag
        fields = ("id", "name", "slug", "created_at", "updated_at", "posts")
        resource_name = "tags"
        read_only_fields = ("id", "created_at", "updated_at")
