from apps.users.serializers import PrivateUserSerializer, PublicUserSerializer
from rest_framework.fields import DateTimeField

field = DateTimeField()


def test_public_user_serializes_full_name(db, editor_factory):
    user = editor_factory()
    serializer = PublicUserSerializer(user)
    assert serializer.data["full_name"] == user.get_full_name()


def test_public_user_serializes_object(db, editor_factory):
    user = editor_factory(profile=True)
    serializer = PublicUserSerializer(user)
    expected = {
        "id": user.id,
        "profile_id": user.profile.id,
        "username": user.username,
        "full_name": user.get_full_name(),
    }

    assert serializer.data == expected


def test_private_user_serializes_object(db, editor_factory):
    user = editor_factory(profile=True)
    serializer = PrivateUserSerializer(user)
    expected = {
        "id": user.id,
        "profile_id": user.profile.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "date_joined": field.to_representation(user.date_joined),
        "last_login": user.last_login,
    }

    assert serializer.data == expected
