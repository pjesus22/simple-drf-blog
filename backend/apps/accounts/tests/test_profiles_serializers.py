import pytest
from apps.accounts.models import SocialMediaProfile
from apps.accounts.serializers import (
    PrivateProfileSerializer,
    PublicProfileSerializer,
    SocialMediaProfileSerializer,
)
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


def test_private_profile_serializer_serializes_object(
    db, profile_factory, editor_profile_data
):
    profile = profile_factory(**editor_profile_data)
    serializer = PrivateProfileSerializer(profile)
    expected = {
        "id": profile.id,
        "created_at": field.to_representation(profile.created_at),
        "updated_at": field.to_representation(profile.updated_at),
        **editor_profile_data,
        "is_public": profile.is_public,
        "social_media": [],
    }

    assert serializer.data == expected


def test_social_media_profile_serializer_serializes_object(
    db, social_media_profile_factory
):
    socials = social_media_profile_factory()
    serializer = SocialMediaProfileSerializer(socials)
    expected = {
        "id": socials.id,
        "created_at": field.to_representation(socials.created_at),
        "updated_at": field.to_representation(socials.updated_at),
        "platform": socials.platform,
        "url": socials.url,
    }

    assert serializer.data == expected


def test_social_media_profile_serializer_raises_error_for_invalid_url(db):
    data = {"platform": "github", "url": "https://facebook.com/username"}

    serializer = SocialMediaProfileSerializer(data=data)

    assert not serializer.is_valid()
    assert "url" in serializer.errors
    assert "The URL must be a valid github link." in str(serializer.errors["url"])


@pytest.mark.parametrize(
    "platform,valid_url",
    [
        ("facebook", "https://facebook.com/testuser"),
        ("github", "https://github.com/testuser"),
        ("instagram", "https://instagram.com/testuser"),
        ("linkedin", "https://linkedin.com/in/testuser"),
        ("tiktok", "https://tiktok.com/@testuser"),
        ("twitter", "https://twitter.com/testuser"),
        ("x", "https://x.com/testuser"),
        ("youtube", "https://youtube.com/c/testuser"),
    ],
    ids=[
        "facebook",
        "github",
        "instagram",
        "linkedin",
        "tiktok",
        "twitter",
        "x",
        "youtube",
    ],
)
def test_social_media_profile_serializer_accepts_valid_platform_urls(
    db, platform, valid_url
):
    data = {"platform": platform, "url": valid_url}
    serializer = SocialMediaProfileSerializer(data=data)

    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize(
    "platform,invalid_url,expected_error",
    [
        ("github", "https://twitter.com/user", "The URL must be a valid github link."),
        (
            "facebook",
            "https://github.com/user",
            "The URL must be a valid facebook link.",
        ),
        (
            "linkedin",
            "https://instagram.com/user",
            "The URL must be a valid linkedin link.",
        ),
        (
            "twitter",
            "https://facebook.com/user",
            "The URL must be a valid twitter link.",
        ),
        ("x", "https://twitter.com/user", "The URL must be a valid x link."),
    ],
    ids=[
        "github-twitter",
        "facebook-github",
        "linkedin-instagram",
        "twitter-facebook",
        "x-twitter",
    ],
)
def test_social_media_profile_serializer_rejects_mismatched_platform_urls(
    db, platform, invalid_url, expected_error
):
    data = {"platform": platform, "url": invalid_url}
    serializer = SocialMediaProfileSerializer(data=data)

    assert not serializer.is_valid()
    assert "url" in serializer.errors
    assert expected_error in str(serializer.errors["url"])


def test_private_profile_serializer_creates_profile_without_social_media(
    db, editor_profile_data, editor_factory
):
    user = editor_factory()
    data = editor_profile_data.copy()
    # Don't include social_media in data - omitting it means no social media links

    serializer = PrivateProfileSerializer(data=data)

    assert serializer.is_valid()

    profile = serializer.save(user=user)

    assert profile.user == user
    assert profile.biography == data["biography"]
    assert profile.location == data["location"]
    assert profile.occupation == data["occupation"]
    assert profile.skills == data["skills"]
    assert profile.experience_years == data["experience_years"]
    assert profile.social_media.count() == 0


def test_private_profile_serializer_creates_profile_with_social_media(
    db, editor_profile_data, editor_factory, social_media_profile_factory
):
    user = editor_factory()
    links = [
        {"platform": "github", "url": "https://github.com/username"},
        {"platform": "facebook", "url": "https://facebook.com/username"},
    ]
    payload = {**editor_profile_data, "social_media": links}

    serializer = PrivateProfileSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    profile = serializer.save(user=user)

    assert profile.user == user
    assert profile.social_media.count() == len(links)


def test_private_profile_serializer_updates_profile_without_social_media(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    data = editor_profile_data.copy()
    data.update({"social_media": []})

    serializer = PrivateProfileSerializer(user.profile, data=data)
    assert serializer.is_valid()

    profile = serializer.save()

    assert profile.user == user
    assert profile.biography == data["biography"]
    assert profile.location == data["location"]
    assert profile.occupation == data["occupation"]
    assert profile.skills == data["skills"]
    assert profile.experience_years == data["experience_years"]


def test_private_profile_serializer_update_profile_creates_new_social_media(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)

    assert user.profile.social_media.count() == 0

    data = editor_profile_data.copy()
    data.update(
        {
            "social_media": [
                {"platform": "github", "url": "https://github.com/username"},
                {"platform": "facebook", "url": "https://facebook.com/username"},
            ]
        }
    )

    serializer = PrivateProfileSerializer(user.profile, data=data)
    assert serializer.is_valid()

    profile = serializer.save()

    assert profile.social_media.count() == 2


def test_private_profile_serializer_update_profile_deletes_old_social_media(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    link_to_keep = SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="github",
        url="https://github.com/testuser",
    )
    link_to_delete = SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="facebook",
        url="https://facebook.com/testuser",
    )

    assert user.profile.social_media.count() == 2

    data = editor_profile_data.copy()
    data.update(
        {
            "social_media": [
                {
                    "id": link_to_keep.id,
                    "platform": link_to_keep.platform,
                    "url": link_to_keep.url,
                }
            ]
        }
    )

    serializer = PrivateProfileSerializer(user.profile, data=data, partial=False)

    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.social_media.count() == 1
    assert profile.social_media.first().id == link_to_keep.id
    assert not SocialMediaProfile.objects.filter(id=link_to_delete.id).exists()


def test_private_profile_serializer_update_modifies_existing_social_media(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    existing_link = SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="github",
        url="https://github.com/oldusername",
    )

    assert user.profile.social_media.count() == 1

    new_url = "https://github.com/newusername"
    data = editor_profile_data.copy()
    data.update(
        {
            "social_media": [
                {
                    "id": existing_link.id,
                    "platform": "github",
                    "url": new_url,
                }
            ]
        }
    )

    serializer = PrivateProfileSerializer(user.profile, data=data)
    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.social_media.count() == 1
    updated_link = profile.social_media.first()
    assert updated_link.id == existing_link.id
    assert updated_link.url == new_url


def test_private_profile_serializer_update_handles_mixed_operations(
    db, editor_factory, editor_profile_data
):
    """Test creating, updating, and deleting social media links in one operation"""
    user = editor_factory(profile=True)
    link_to_update = SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="github",
        url="https://github.com/oldusername",
    )
    link_to_delete = SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="facebook",
        url="https://facebook.com/testuser",
    )

    assert user.profile.social_media.count() == 2

    data = editor_profile_data.copy()
    data.update(
        {
            "social_media": [
                # Update existing
                {
                    "id": link_to_update.id,
                    "platform": "github",
                    "url": "https://github.com/newusername",
                },
                # Create new
                {"platform": "twitter", "url": "https://twitter.com/testuser"},
                # link_to_delete is omitted, so it should be deleted
            ]
        }
    )

    serializer = PrivateProfileSerializer(user.profile, data=data)
    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.social_media.count() == 2
    platforms = {link.platform for link in profile.social_media.all()}
    assert platforms == {"github", "twitter"}
    assert not SocialMediaProfile.objects.filter(id=link_to_delete.id).exists()


def test_private_profile_serializer_update_with_empty_social_media_deletes_all(
    db, editor_factory, editor_profile_data
):
    user = editor_factory(profile=True)
    SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="github",
        url="https://github.com/testuser",
    )
    SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="facebook",
        url="https://facebook.com/testuser",
    )

    assert user.profile.social_media.count() == 2

    data = editor_profile_data.copy()
    data.update({"social_media": []})

    serializer = PrivateProfileSerializer(user.profile, data=data)
    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.social_media.count() == 0


def test_private_profile_serializer_partial_update_without_social_media_preserves_links(
    db, editor_factory, editor_profile_data
):
    """Partial update without social_media field should preserve existing links"""
    user = editor_factory(profile=True)
    SocialMediaProfile.objects.create(
        profile=user.profile,
        platform="github",
        url="https://github.com/testuser",
    )

    assert user.profile.social_media.count() == 1

    data = {"biography": "Updated biography"}

    serializer = PrivateProfileSerializer(user.profile, data=data, partial=True)
    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.biography == "Updated biography"
    assert profile.social_media.count() == 1  # Should still exist


def test_public_profile_serializer_serializes_object(
    db, profile_factory, editor_profile_data
):
    profile = profile_factory(**editor_profile_data)
    serializer = PublicProfileSerializer(profile)
    expected = {
        "id": profile.id,
        **editor_profile_data,
        "social_media": [],
    }

    assert serializer.data == expected
    # Verify private fields are not included
    assert "is_public" not in serializer.data
    assert "created_at" not in serializer.data
    assert "updated_at" not in serializer.data


def test_public_profile_serializer_has_read_only_social_media(
    db, profile_factory, editor_profile_data
):
    profile = profile_factory(**editor_profile_data)
    data = editor_profile_data.copy()
    data.update(
        {"social_media": [{"platform": "github", "url": "https://github.com/username"}]}
    )

    serializer = PublicProfileSerializer(profile, data=data)

    # social_media should be read-only, so it should be valid even though we can't write to it
    assert serializer.is_valid()
    # Verify that social_media field is read-only
    assert serializer.fields["social_media"].read_only is True


def test_public_profile_serializer_includes_social_media_in_output(
    db, profile_factory, editor_profile_data
):
    """Test that PublicProfileSerializer includes social media links in serialized output"""
    profile = profile_factory(**editor_profile_data)
    SocialMediaProfile.objects.create(
        profile=profile,
        platform="github",
        url="https://github.com/testuser",
    )
    SocialMediaProfile.objects.create(
        profile=profile,
        platform="twitter",
        url="https://twitter.com/testuser",
    )

    serializer = PublicProfileSerializer(profile)

    assert "social_media" in serializer.data
    assert len(serializer.data["social_media"]) == 2
    platforms = {link["platform"] for link in serializer.data["social_media"]}
    assert platforms == {"github", "twitter"}
