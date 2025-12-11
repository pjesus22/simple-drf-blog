from rest_framework_json_api import serializers

from ..models import Tag


class TagSerializer(serializers.ModelSerializer):
    posts = serializers.ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    class JSONAPIMeta:
        included_resources = ["posts"]
