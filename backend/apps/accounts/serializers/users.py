from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_json_api import serializers

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    profile = serializers.ResourceRelatedField(read_only=True)
    included_serializers = {
        "profile": "apps.accounts.serializers.profiles.EditorProfileSerializer"
    }

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "date_joined",
            "last_login",
            "profile",
        )
        abstract = True

    class JSONAPIMeta:
        resource_name = "users"


class UserListSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ("id", "username", "role", "profile")
        read_only_fields = ("id", "username", "role", "profile")


class UserCreateSerializer(BaseUserSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields
        read_only_fields = ("id", "profile", "date_joined", "last_login") + (
            "password",
        )


class UserDetailSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields
        read_only_fields = ("id", "profile", "role", "date_joined", "last_login")


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    class JSONAPIMeta:
        resource_name = "users"
