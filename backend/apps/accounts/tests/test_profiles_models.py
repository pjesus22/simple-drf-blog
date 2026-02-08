import pytest
from apps.accounts.models import Profile, SocialMediaProfile
from django.core.exceptions import ValidationError
from django.db import IntegrityError


def test_profile_str_returns_username(db, editor_factory):
    user = editor_factory(profile=True)
    profile = Profile.objects.get(user=user)
    assert str(profile) == f"Profile(user={user.id})"


def test_social_media_profile_str_returns_platform_and_url(db, profile_factory):
    profile = profile_factory()
    social_link = SocialMediaProfile(
        profile=profile, platform="github", url="https://github.com/fake"
    )
    assert (
        str(social_link) == f"SocialMediaProfile(profile={profile.id}, platform=github)"
    )


def test_profile_is_public_default_is_true(db, editor_factory):
    user = editor_factory(profile=True)
    profile = Profile.objects.get(user=user)
    assert profile.is_public is True


def test_profile_one_to_one_relationship_with_user(db, editor_factory):
    """Test that a user can only have one profile"""
    user = editor_factory(profile=True)

    # Attempting to create another profile for the same user should fail
    with pytest.raises(IntegrityError):
        Profile.objects.create(user=user)


def test_profile_cascade_deletes_with_user(db, editor_factory):
    """Test that deleting a user also deletes their profile"""
    user = editor_factory(profile=True)
    profile_id = user.profile.id

    user.delete()

    assert not Profile.objects.filter(id=profile_id).exists()


def test_social_media_profile_cascade_deletes_with_profile(db, profile_factory):
    """Test that deleting a profile also deletes associated social media links"""
    profile = profile_factory()
    link = SocialMediaProfile.objects.create(
        profile=profile,
        platform="github",
        url="https://github.com/testuser",
    )
    link_id = link.id

    profile.delete()

    assert not SocialMediaProfile.objects.filter(id=link_id).exists()


def test_social_media_profile_unique_together_constraint(db, profile_factory):
    """Test that a profile cannot have duplicate URLs"""
    profile = profile_factory()
    url = "https://github.com/testuser"

    SocialMediaProfile.objects.create(
        profile=profile,
        platform="github",
        url=url,
    )

    # Attempting to create another link with the same URL should fail
    with pytest.raises(IntegrityError):
        SocialMediaProfile.objects.create(
            profile=profile,
            platform="twitter",  # Different platform, same URL
            url=url,
        )


def test_social_media_profile_allows_same_url_for_different_profiles(
    db, profile_factory
):
    """Test that different profiles can have the same URL"""
    profile1 = profile_factory()
    profile2 = profile_factory()
    url = "https://github.com/testuser"

    link1 = SocialMediaProfile.objects.create(
        profile=profile1,
        platform="github",
        url=url,
    )
    link2 = SocialMediaProfile.objects.create(
        profile=profile2,
        platform="github",
        url=url,
    )

    assert link1.url == link2.url
    assert link1.profile != link2.profile


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://github.com/user",  # Not HTTPS
        "https://example.com/user",  # Invalid domain
        "https://github.com",  # Missing path
        "github.com/user",  # Missing protocol
        "https://subdomain.github.com/user",  # Invalid subdomain (not www)
    ],
    ids=["no-https", "invalid-domain", "no-path", "no-protocol", "invalid-subdomain"],
)
def test_social_media_profile_rejects_invalid_urls(db, profile_factory, invalid_url):
    """Test that invalid URLs are rejected by the URL validator"""
    profile = profile_factory()
    link = SocialMediaProfile(
        profile=profile,
        platform="github",
        url=invalid_url,
    )

    with pytest.raises(ValidationError):
        link.full_clean()


@pytest.mark.parametrize(
    "valid_url",
    [
        "https://github.com/user",
        "https://www.github.com/user",
        "https://twitter.com/user",
        "https://www.twitter.com/user",
        "https://x.com/user",
        "https://www.x.com/user",
        "https://linkedin.com/in/user",
        "https://www.linkedin.com/in/user",
        "https://instagram.com/user",
        "https://facebook.com/user",
        "https://youtube.com/c/user",
        "https://tiktok.com/@user",
    ],
    ids=[
        "github",
        "github-www",
        "twitter",
        "twitter-www",
        "x",
        "x-www",
        "linkedin",
        "linkedin-www",
        "instagram",
        "facebook",
        "youtube",
        "tiktok",
    ],
)
def test_social_media_profile_accepts_valid_urls(db, profile_factory, valid_url):
    """Test that valid URLs are accepted"""
    profile = profile_factory()
    link = SocialMediaProfile(
        profile=profile,
        platform="github",  # Platform doesn't matter for URL validation at model level
        url=valid_url,
    )

    link.full_clean()  # Should not raise
    link.save()
    assert link.url == valid_url


def test_profile_default_values(db, editor_factory):
    """Test that profile fields have correct default values"""
    user = editor_factory()
    # Create profile directly without using factory to test default values
    profile = Profile.objects.create(user=user)

    assert profile.biography == ""
    assert profile.location == ""
    assert profile.occupation == ""
    assert profile.skills == ""
    assert profile.experience_years == 0
    assert profile.is_public is True
