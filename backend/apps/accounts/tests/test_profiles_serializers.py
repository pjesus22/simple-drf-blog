import pytest
from apps.accounts.models import SocialLink
from apps.accounts.serializers import EditorProfileSerializer, SocialLinkSerializer
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


def test_social_link_serializer_raises_error_for_invalid_url(db):
    data = {"name": "github", "url": "https://facebook.com/username"}

    serializer = SocialLinkSerializer(data=data)

    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors
    assert "URL must be a github link" in str(serializer.errors["non_field_errors"])


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


def test_editor_profile_serializer_updates_profile_without_social_links(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    data = editor_profile_data.copy()
    data.update({"social_links": []})

    serializer = EditorProfileSerializer(user.profile, data=data)
    assert serializer.is_valid()

    profile = serializer.save()

    assert profile.user == user
    assert profile.biography == data["biography"]
    assert profile.location == data["location"]
    assert profile.occupation == data["occupation"]
    assert profile.skills == data["skills"]
    assert profile.experience_years == data["experience_years"]


def test_editor_profile_serializer_update_profile_creates_new_social_links(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)

    assert user.profile.social_links.count() == 0

    data = editor_profile_data.copy()
    data.update(
        {
            "social_links": [
                {"name": "github", "url": "https://github.com/username"},
                {"name": "facebook", "url": "https://facebook.com/username"},
            ]
        }
    )

    serializer = EditorProfileSerializer(user.profile, data=data)
    assert serializer.is_valid()

    profile = serializer.save()

    assert profile.social_links.count() == 2


def test_editor_profile_serializer_update_profile_deletes_old_social_links(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    link_to_keep = SocialLink.objects.create(
        profile=user.profile,
        name="github",
        url="https://github.com/testuser",
    )
    link_to_delete = SocialLink.objects.create(
        profile=user.profile,
        name="facebook",
        url="https://facebook.com/testuser",
    )

    assert user.profile.social_links.count() == 2

    data = editor_profile_data.copy()
    data.update(
        {
            "social_links": [
                {
                    "id": link_to_keep.id,
                    "name": link_to_keep.name,
                    "url": link_to_keep.url,
                }
            ]
        }
    )

    serializer = EditorProfileSerializer(user.profile, data=data, partial=False)

    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.social_links.count() == 1
    assert profile.social_links.first().id == link_to_keep.id
    assert not SocialLink.objects.filter(id=link_to_delete.id).exists()
