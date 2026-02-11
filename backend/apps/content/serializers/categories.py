from rest_framework_json_api import serializers

from apps.content.models import Category


class CategorySerializer(serializers.ModelSerializer):
    posts = serializers.ResourceRelatedField(many=True, read_only=True)
    included_serializers = {"posts": "apps.content.serializers.posts.PostSerializer"}

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
            "posts",
        )
        resource_name = "categories"
        read_only_fields = ("id", "created_at", "updated_at")
