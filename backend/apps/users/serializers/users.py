from rest_framework_json_api import serializers

from ..models import User


class PublicUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = User
        fields = ["id", "username", "full_name"]


class PrivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "role", "date_joined", "last_login"]
