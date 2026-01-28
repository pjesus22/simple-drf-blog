from apps.accounts.serializers.users import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.fields import DateTimeField

User = get_user_model()
field = DateTimeField()


class TestUserListSerializer:
    def test_user_list_serializer_serializes_object_successfully(
        self, db, editor_factory
    ):
        user = editor_factory(profile=True)
        serializer = UserListSerializer(user)
        expected = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "profile": {
                "type": "profiles",
                "id": str(user.profile.id),
            },
        }

        assert serializer.data == expected


class TestUserDetailSerializer:
    def test_user_detail_serializer_serializes_object_successfully(
        self, db, editor_factory
    ):
        user = editor_factory(last_login=timezone.now(), profile=True)
        serializer = UserDetailSerializer(user)

        expected = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "date_joined": field.to_representation(user.date_joined),
            "last_login": field.to_representation(user.last_login),
            "profile": {
                "type": "profiles",
                "id": str(user.profile.id),
            },
        }

        assert serializer.data == expected


class TestUserCreateSerializer:
    def test_create_serializer_serializes_object_successfully(self, db, editor_factory):
        user = editor_factory(last_login=timezone.now(), profile=True)
        serializer = UserCreateSerializer(user)

        expected = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "date_joined": field.to_representation(user.date_joined),
            "last_login": field.to_representation(user.last_login),
            "profile": {
                "type": "profiles",
                "id": str(user.profile.id),
            },
        }

        assert serializer.data == expected

    def test_create_serializers_creates_object(self, db):
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "role": User.Role.EDITOR,
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()

        assert user.username == data["username"]
        assert user.email == data["email"]
        assert user.check_password(data["password"])
        assert user.role == User.Role.EDITOR


class TestChangeRoleSerializer:
    def test_change_role_serializer_validates_object_successfully(self):
        data = {"role": User.Role.ADMIN}
        serializer = ChangeRoleSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["role"] == User.Role.ADMIN

    def test_change_role_serializer_raises_error_for_invalid_role(self):
        data = {"role": "invalid_role"}
        serializer = ChangeRoleSerializer(data=data)
        assert not serializer.is_valid()
        assert "role" in serializer.errors


class TestPasswordUpdateSerializer:
    def test_password_update_serializer_validates_object_successfully(self):
        data = {"old_password": "old_secure_pass", "new_password": "new_secure_pass123"}
        serializer = PasswordUpdateSerializer(data=data)
        assert serializer.is_valid()

    def test_password_update_serializer_raises_error_for_same_passwords(self):
        data = {"old_password": "samepassword123", "new_password": "samepassword123"}
        serializer = PasswordUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert "must be different" in str(serializer.errors["new_password"])


class TestPasswordResetSerializer:
    def test_password_reset_serializer_validates_object_successfully(self):
        data = {"new_password": "new_secure_pass123"}
        serializer = PasswordResetSerializer(data=data)
        assert serializer.is_valid()
