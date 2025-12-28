import pytest
from apps.users.serializers import EditorProfileSerializer, SocialLinkSerializer
from rest_framework.fields import DateTimeField

field = DateTimeField()


@pytest.fixture
def editor_profile_data():
    return {
        "biography": "Test Biography",
        "location": "Test Location",
        "occupation": "Test Occupation",
        "skills": "Test Skills",
        "experience_years": 5,
    }


def test_editor_profiles_serializes_object(db, profile_factory, editor_profile_data):
    profile = profile_factory(**editor_profile_data)
    serializer = EditorProfileSerializer(profile)
    expected = {
        "id": profile.id,
        "updated_at": field.to_representation(profile.updated_at),
        **editor_profile_data,
        "social_links": [],
    }

    assert serializer.data == expected


def test_social_link_serializes_object(db, social_link_factory):
    socials = social_link_factory()
    serializer = SocialLinkSerializer(socials)
    expected = {
        "id": socials.id,
        "created_at": field.to_representation(socials.created_at),
        "updated_at": field.to_representation(socials.updated_at),
        "name": socials.name,
        "url": socials.url,
    }

    assert serializer.data == expected


def test_editor_profile_serializer_creates_profile_without_social_links(
    db, editor_profile_data, editor_factory
):
    user = editor_factory()
    data = editor_profile_data.copy()
    data.update({"social_links": []})

    serializer = EditorProfileSerializer(data=data)

    assert serializer.is_valid()

    profile = serializer.save(user=user)

    assert profile.user == user
    assert profile.biography == data["biography"]
    assert profile.location == data["location"]
    assert profile.occupation == data["occupation"]
    assert profile.skills == data["skills"]
    assert profile.experience_years == data["experience_years"]
    assert profile.social_links.count() == 0


def test_editor_profile_serializer_creates_profile_with_social_links(
    db, editor_profile_data, editor_factory
):
    user = editor_factory()
    data = editor_profile_data.copy()
    data.update(
        {
            "social_links": [
                {"name": "github", "url": "https://github.com/username"},
                {"name": "facebook", "url": "https://facebook.com/username"},
            ]
        }
    )

    serializer = EditorProfileSerializer(data=data)

    assert serializer.is_valid()

    profile = serializer.save(user=user)

    assert profile.social_links.count() == 2
