from django.contrib.auth import get_user_model
from django.utils import timezone
import pytest

from apps.accounts.serializers.users import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)

User = get_user_model()


@pytest.mark.django_db
class TestUserListSerializer:
    def test_user_list_serializer_serializes_object_successfully(self, editor_factory):
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


@pytest.mark.django_db
class TestUserDetailSerializer:
    def test_user_detail_serializer_serializes_object_successfully(
        self, editor_factory, drf_datetime
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
            "date_joined": drf_datetime.to_representation(user.date_joined),
            "last_login": drf_datetime.to_representation(user.last_login),
            "profile": {
                "type": "profiles",
                "id": str(user.profile.id),
            },
        }

        assert serializer.data == expected


@pytest.mark.django_db
class TestUserCreateSerializer:
    def test_create_serializer_serializes_object_successfully(
        self, editor_factory, drf_datetime
    ):
        user = editor_factory(last_login=timezone.now(), profile=True)
        serializer = UserCreateSerializer(user)

        expected = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_joined": drf_datetime.to_representation(user.date_joined),
            "last_login": drf_datetime.to_representation(user.last_login),
            "role": user.role,
            "profile": {
                "type": "profiles",
                "id": str(user.profile.id),
            },
        }

        assert serializer.data == expected

    def test_create_serializer_creates_object(self):
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "securepassword123",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.username == data["username"]
        assert user.email == data["email"]
        assert user.check_password(data["password"])
        assert user.role == User.Role.EDITOR

    def test_create_serializer_always_creates_editor(self):
        """Passing role=admin in the payload must be ignored."""
        data = {
            "username": "sneakyuser",
            "first_name": "Sneaky",
            "last_name": "User",
            "email": "sneaky@example.com",
            "password": "securepassword123",
            "role": User.Role.ADMIN,  # attacker tries to escalate
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()

        assert user.role == User.Role.EDITOR


class TestChangeRoleSerializer:
    @pytest.mark.parametrize("role", [User.Role.ADMIN, User.Role.EDITOR])
    def test_change_role_serializer_validates_object_successfully(self, role):
        data = {"role": role}
        serializer = ChangeRoleSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["role"] == role

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
