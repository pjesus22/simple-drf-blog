from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pytest

from apps.accounts.models import Profile, SocialMediaProfile


@pytest.fixture
def profile(db, editor_factory):
    user = editor_factory(profile=True)
    return user.profile


def test_profile_str(profile):
    assert str(profile) == f"Profile(user={profile.user.id})"


def test_social_media_profile_str(profile):
    platform = SocialMediaProfile.Platform.GITHUB
    url = "https://github.com/fake"
    social_link = SocialMediaProfile(profile=profile, platform=platform, url=url)
    assert (
        str(social_link)
        == f"SocialMediaProfile(profile={profile.id}, platform={platform})"
    )


def test_profile_is_public_defaults_to_true(profile):
    assert profile.is_public is True


def test_user_cannot_have_multiple_profiles(db, editor_factory):
    user = editor_factory(profile=True)

    with pytest.raises(IntegrityError):
        Profile.objects.create(user=user)


def test_profile_cascade_delete(db, editor_factory):
    user = editor_factory(profile=True)
    profile_id = user.profile.id

    user.delete()

    assert not Profile.objects.filter(id=profile_id).exists()


def test_social_media_profile_cascade_delete(profile):
    link = SocialMediaProfile.objects.create(
        profile=profile,
        platform=SocialMediaProfile.Platform.GITHUB,
        url="https://github.com/testuser",
    )
    link_id = link.id

    profile.delete()

    assert not SocialMediaProfile.objects.filter(id=link_id).exists()


def test_profile_cannot_have_duplicate_social_media_urls(profile):
    url = "https://github.com/testuser"

    SocialMediaProfile.objects.create(
        profile=profile,
        platform=SocialMediaProfile.Platform.GITHUB,
        url=url,
    )

    with pytest.raises(IntegrityError):
        SocialMediaProfile.objects.create(
            profile=profile,
            platform=SocialMediaProfile.Platform.TWITTER,
            url=url,
        )


def test_different_profiles_can_have_same_url(db, profile_factory):
    profile1 = profile_factory()
    profile2 = profile_factory()
    url = "https://github.com/testuser"

    link1 = SocialMediaProfile.objects.create(
        profile=profile1,
        platform=SocialMediaProfile.Platform.GITHUB,
        url=url,
    )
    link2 = SocialMediaProfile.objects.create(
        profile=profile2,
        platform=SocialMediaProfile.Platform.GITHUB,
        url=url,
    )

    assert link1.url == link2.url
    assert link1.profile != link2.profile


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://github.com/user",
        "https://example.com/user",
        "https://github.com",
        "github.com/user",
        "https://subdomain.github.com/user",
    ],
    ids=("no_https", "invalid_domain", "no_path", "no_protocol", "invalid_subdomain"),
)
def test_social_media_profile_rejects_invalid_urls(profile, invalid_url):
    link = SocialMediaProfile(
        profile=profile,
        platform=SocialMediaProfile.Platform.GITHUB,
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
    ids=(
        "github",
        "github_www",
        "twitter",
        "twitter_www",
        "x",
        "x_www",
        "linkedin",
        "linkedin_www",
        "instagram",
        "facebook",
        "youtube",
        "tiktok",
    ),
)
def test_social_media_profile_accepts_valid_urls(profile, valid_url):
    link = SocialMediaProfile(
        profile=profile,
        platform=SocialMediaProfile.Platform.GITHUB,
        url=valid_url,
    )

    link.full_clean()  # Should not raise
    link.save()
    assert link.url == valid_url


def test_profile_default_values(db, editor_factory):
    user = editor_factory()
    profile = Profile.objects.create(user=user)

    assert profile.biography == ""
    assert profile.location == ""
    assert profile.occupation == ""
    assert profile.skills == ""
    assert profile.experience_years == 0
    assert profile.is_public is True


def test_profile_experience_years_validation(profile):
    profile.experience_years = -1
    with pytest.raises(ValidationError):
        profile.full_clean()
