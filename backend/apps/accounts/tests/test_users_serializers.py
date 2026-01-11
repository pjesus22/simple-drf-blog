from apps.accounts.serializers import (
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from django.utils import timezone
from rest_framework.fields import DateTimeField

field = DateTimeField()


def test_user_list_serializer_serializes_object(db, editor_factory):
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


def test_user_detail_serializer_serializes_object(db, editor_factory):
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


def test_user_create_serializer_serializes_object(db, editor_factory):
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
