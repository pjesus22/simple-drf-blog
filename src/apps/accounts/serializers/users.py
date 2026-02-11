from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from rest_framework_json_api import serializers

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    profile = serializers.ResourceRelatedField(read_only=True)
    included_serializers = {
        "profile": "apps.accounts.serializers.profiles.PrivateProfileSerializer"
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
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        min_length=8,
    )

    class Meta(BaseUserSerializer.Meta):
        fields = (*BaseUserSerializer.Meta.fields, "password")
        read_only_fields = ("id", "profile", "date_joined", "last_login")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserDetailSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields
        read_only_fields = ("id", "profile", "role", "date_joined", "last_login")


class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        min_length=8,
    )

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise ValidationError(
                {
                    "new_password": (
                        "The new password must be different from the old password."
                    )
                }
            )

        return attrs


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        min_length=8,
    )
