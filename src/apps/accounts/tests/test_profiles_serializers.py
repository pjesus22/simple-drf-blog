from django.contrib.auth.models import AnonymousUser
import pytest

from apps.accounts.serializers import (
    PrivateProfileSerializer,
    PublicProfileSerializer,
    SocialMediaProfileSerializer,
)


@pytest.fixture
def profile_data():
    return {
        "biography": "Test Biography",
        "location": "Test Location",
        "occupation": "Test Occupation",
        "skills": "Test Skills",
        "experience_years": 5,
    }


class TestSocialMediaProfileSerializer:
    def test_social_media_profile_serializes_object_successfully(
        self, db, social_media_profile_factory, drf_datetime
    ):
        socials = social_media_profile_factory()
        serializer = SocialMediaProfileSerializer(socials)

        expected = {
            "id": socials.id,
            "created_at": drf_datetime.to_representation(socials.created_at),
            "updated_at": drf_datetime.to_representation(socials.updated_at),
            "platform": socials.platform,
            "url": socials.url,
        }
        assert serializer.data == expected

    @pytest.mark.parametrize(
        "platform, url",
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
        ids=lambda p: f"valid-{p}",
    )
    def test_social_media_validates_url(self, db, platform, url):
        data = {"platform": platform, "url": url}
        serializer = SocialMediaProfileSerializer(data=data)
        assert serializer.is_valid(), f"Failed for {platform}: {serializer.errors}"

    @pytest.mark.parametrize(
        "platform, url, expected_error",
        [
            (
                "github",
                "https://twitter.com/user",
                "The URL must be a valid github link.",
            ),
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
        ids=(
            "wrong_platform_github",
            "wrong_platform_facebook",
            "wrong_platform_linkedin",
            "wrong_platform_twitter",
            "wrong_platform_x",
        ),
    )
    def test_social_media_rejects_url_from_wrong_platforms(
        self, db, platform, url, expected_error
    ):
        data = {"platform": platform, "url": url}
        serializer = SocialMediaProfileSerializer(data=data)

        assert not serializer.is_valid()
        assert "url" in serializer.errors
        assert expected_error in str(serializer.errors["url"])


class TestPrivateProfile:
    def test_private_profile_serializer_serializes_object_successfully(
        self, db, profile_factory, profile_data, drf_datetime
    ):
        profile = profile_factory(**profile_data)
        serializer = PrivateProfileSerializer(profile)

        expected = {
            "id": profile.id,
            "created_at": drf_datetime.to_representation(profile.created_at),
            "updated_at": drf_datetime.to_representation(profile.updated_at),
            **profile_data,
            "is_public": profile.is_public,
            "social_media": [],
        }
        assert serializer.data == expected

    def test_private_profile_creation_with_social_media(
        self, db, profile_data, editor_factory
    ):
        user = editor_factory()
        links = [
            {"platform": "github", "url": "https://github.com/username"},
            {"platform": "twitter", "url": "https://twitter.com/username"},
        ]
        payload = {**profile_data, "social_media": links, "is_public": True}

        serializer = PrivateProfileSerializer(data=payload)
        assert serializer.is_valid()

        profile = serializer.save(user=user)
        assert profile.social_media.count() == 2
        assert set(profile.social_media.values_list("platform", flat=True)) == {
            "github",
            "twitter",
        }

    def test_private_profile_update_social_media_sync(
        self, db, editor_factory, profile_data, social_media_profile_factory
    ):
        user = editor_factory(profile=True)
        link_to_update = social_media_profile_factory(
            profile=user.profile, platform="github", url="https://github.com/old"
        )
        link_to_delete = social_media_profile_factory(
            profile=user.profile, platform="facebook"
        )

        new_url = "https://github.com/new"
        data = {
            **profile_data,
            "is_public": False,
            "social_media": [
                {"id": link_to_update.id, "platform": "github", "url": new_url},
                {"platform": "twitter", "url": "https://twitter.com/test"},
            ],
        }

        serializer = PrivateProfileSerializer(user.profile, data=data)
        assert serializer.is_valid()
        profile = serializer.save()

        assert profile.social_media.count() == 2
        assert profile.social_media.filter(id=link_to_update.id, url=new_url).exists()
        assert profile.social_media.filter(platform="twitter").exists()
        assert not profile.social_media.filter(id=link_to_delete.id).exists()

    def test_partial_update_preserves_social_media(
        self, db, editor_factory, social_media_profile_factory
    ):
        user = editor_factory(profile=True)
        social_media_profile_factory(profile=user.profile)

        serializer = PrivateProfileSerializer(
            user.profile, data={"biography": "New Bio"}, partial=True
        )
        assert serializer.is_valid()
        profile = serializer.save()

        assert profile.biography == "New Bio"
        assert profile.social_media.count() == 1


class TestPublicProfileSerializer:
    def test_public_profile_serialization_filters_fields(
        self, db, profile_factory, profile_data
    ):
        profile = profile_factory(**profile_data, is_public=True)
        serializer = PublicProfileSerializer(profile)

        data = serializer.data
        assert "id" in data
        assert all(k in data for k in profile_data)
        assert "is_public" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_public_profile_social_media_read_only(
        self, db, profile_factory, profile_data
    ):
        profile = profile_factory(**profile_data, is_public=True)
        data = {
            **profile_data,
            "social_media": [{"platform": "github", "url": "https://github.com/user"}],
        }

        serializer = PublicProfileSerializer(profile, data=data)
        assert serializer.is_valid()
        assert serializer.fields["social_media"].read_only is True

    @pytest.mark.parametrize(
        "is_public, user_type, is_owner, expect_full",
        [
            (True, None, False, True),
            (True, "anonymous", False, True),
            (True, "editor", False, True),
            (False, None, False, False),
            (False, "anonymous", False, False),
            (False, "editor", False, False),
            (False, "editor", True, True),
            (False, "admin", False, True),
        ],
        ids=(
            "public-none",
            "public-anon",
            "public-editor",
            "private-none",
            "private-anon",
            "private-editor",
            "private-owner",
            "private-admin",
        ),
    )
    def test_public_profile_visibility_guard(
        self,
        db,
        editor_factory,
        admin_factory,
        profile_factory,
        profile_data,
        rf,
        is_public,
        user_type,
        is_owner,
        expect_full,
    ):
        owner = editor_factory()
        profile = profile_factory(user=owner, is_public=is_public, **profile_data)

        context = {}
        if user_type is not None:
            request = rf.get("/")
            if user_type == "anonymous":
                request.user = AnonymousUser()
            elif user_type == "editor":
                request.user = owner if is_owner else editor_factory()
            else:
                request.user = admin_factory()
            context["request"] = request

        data = PublicProfileSerializer(profile, context=context).data

        if expect_full:
            assert data["id"] == profile.id
            assert all(k in data for k in profile_data)
            assert data["biography"] == profile.biography
        else:
            assert data == {}
