from rest_framework_json_api import serializers

from ..models import User


class PublicUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_id = serializers.PrimaryKeyRelatedField(
        source="editor_profile", read_only=True
    )

    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = User
        fields = ("id", "profile_id", "username", "full_name")
        resource_name = "users"
        read_only_fields = ("id", "profile_id", "username", "full_name")


class PrivateUserSerializer(serializers.ModelSerializer):
    profile_id = serializers.PrimaryKeyRelatedField(
        source="editor_profile", read_only=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "profile_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "date_joined",
            "last_login",
        )
        resource_name = "users"
        read_only_fields = ("id", "profile_id", "role", "date_joined", "last_login")
