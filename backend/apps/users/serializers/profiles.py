from rest_framework_json_api import serializers

from ..models import EditorProfile, SocialLink


class EditorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorProfile
        fields = (
            "id",
            "biography",
            "location",
            "occupation",
            "skills",
            "experience_years",
            "updated_at",
        )
        resource_name = "profiles"
        read_only_fields = ("id", "updated_at")


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ("id", "name", "url", "created_at", "updated_at")
        resource_name = "social_links"
        read_only_fields = ("id", "created_at", "updated_at")
