from django.urls import reverse
import pytest
from rest_framework import status

from apps.accounts.models import Profile
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


class TestReadProfile:
    @pytest.mark.parametrize(
        "client_name, is_public, expected_count",
        [
            ("api_client", True, 3),
            ("api_client", False, 0),
            ("editor_client", True, 3),
            ("editor_client", False, 1),
            ("admin_client", True, 3),
            ("admin_client", False, 3),
        ],
        ids=(
            "public_profiles_unauthenticated",
            "private_profiles_unauthenticated",
            "public_profiles_editor",
            "private_profiles_editor_owns_one",
            "public_profiles_admin",
            "private_profiles_admin",
        ),
    )
    def test_list_profiles_visibility(
        self, request, profile_factory, client_name, is_public, expected_count
    ):
        client_fixture = request.getfixturevalue(client_name)
        client, user = (
            client_fixture
            if isinstance(client_fixture, tuple)
            else (client_fixture, None)
        )

        if user and client_name == "editor_client":
            profile_factory(user=user, is_public=is_public)
            profile_factory.create_batch(size=2, is_public=is_public)
        else:
            profile_factory.create_batch(size=3, is_public=is_public)

        response = client.get(path=reverse("v1:profile-list"))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert len(data) == expected_count

    def test_retrieve_public_profile_success(self, api_client, profile_factory):
        profile = profile_factory(is_public=True)

        response = api_client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        attrs = data["attributes"]

        assert attrs["biography"] == profile.biography
        assert attrs["location"] == profile.location
        assert attrs["occupation"] == profile.occupation
        assert attrs["skills"] == profile.skills
        assert attrs["experience_years"] == profile.experience_years
        assert "is_public" not in attrs

    def test_retrieve_private_profile_as_owner_success(
        self, editor_client, profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user, is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == profile.biography

    def test_retrieve_private_profile_as_admin_success(
        self, admin_client, profile_factory
    ):
        client, _ = admin_client
        profile = profile_factory(is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == profile.biography

    @pytest.mark.parametrize(
        "client_fixture_name, status_code, error_code, detail",
        [
            pytest.param(
                "editor_client",
                status.HTTP_404_NOT_FOUND,
                "not_found",
                "No Profile matches the given query.",
                id="other_user_private_profile",
            ),
            pytest.param(
                "api_client",
                status.HTTP_404_NOT_FOUND,
                "not_found",
                "No Profile matches the given query.",
                id="unauthenticated_private_profile",
            ),
        ],
    )
    def test_retrieve_profile_error_cases(
        self,
        request,
        profile_factory,
        client_fixture_name,
        status_code,
        error_code,
        detail,
    ):
        client_fixture = request.getfixturevalue(client_fixture_name)
        client = (
            client_fixture[0] if isinstance(client_fixture, tuple) else client_fixture
        )
        profile = profile_factory(is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status_code,
            code=error_code,
            detail_contains=detail,
        )

    def test_retrieve_profile_not_found(self, api_client):
        response = api_client.get(path=reverse("v1:profile-detail", args=[0]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )


class TestUpdateProfile:
    def test_partial_update_own_profile_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Updated biography",
                "location": "Updated City",
                "is_public": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == "Updated biography"
        assert data["attributes"]["location"] == "Updated City"
        assert data["attributes"]["is_public"] is False

        profile.refresh_from_db()
        assert profile.biography == "Updated biography"
        assert profile.is_public is False

    def test_partial_update_other_profile_as_admin_success(
        self, admin_client, profile_factory
    ):
        client, _ = admin_client
        profile = profile_factory()

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Admin updated biography",
                "occupation": "Admin updated occupation",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == "Admin updated biography"

        profile.refresh_from_db()
        assert profile.biography == "Admin updated biography"

    @pytest.mark.parametrize(
        "client_fixture_name, method, status_code, error_func",
        [
            pytest.param(
                "editor_client",
                "patch",
                status.HTTP_404_NOT_FOUND,
                assert_jsonapi_error_response,
                id="patch_other_profile_forbidden",
            ),
            pytest.param(
                "api_client",
                "patch",
                status.HTTP_401_UNAUTHORIZED,
                assert_drf_error_response,
                id="patch_profile_unauthorized",
            ),
            pytest.param(
                "editor_client",
                "put",
                status.HTTP_404_NOT_FOUND,
                assert_jsonapi_error_response,
                id="put_other_profile_forbidden",
            ),
            pytest.param(
                "api_client",
                "put",
                status.HTTP_401_UNAUTHORIZED,
                assert_drf_error_response,
                id="put_profile_unauthorized",
            ),
        ],
    )
    def test_update_profile_error_cases(
        self,
        request,
        profile_factory,
        client_fixture_name,
        method,
        status_code,
        error_func,
    ):
        client_fixture = request.getfixturevalue(client_fixture_name)
        client = (
            client_fixture[0] if isinstance(client_fixture, tuple) else client_fixture
        )
        profile = profile_factory()

        url = reverse("v1:profile-detail", args=[profile.id])
        data = {"biography": "Unauthorized update"}

        action = getattr(client, method)
        response = action(path=url, data=data, format="json")

        if status_code == status.HTTP_404_NOT_FOUND:
            error_func(
                response=response,
                status_code=status_code,
                code="not_found",
                detail_contains="No Profile matches the given query.",
            )
        else:
            error_func(
                response=response,
                status_code=status_code,
                detail_contains="credentials were not provided.",
            )

    def test_full_update_own_profile_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.put(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Completely new biography",
                "location": "New City",
                "occupation": "New Occupation",
                "skills": "New Skills",
                "experience_years": 10,
                "is_public": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == "Completely new biography"
        assert data["attributes"]["experience_years"] == 10

        profile.refresh_from_db()
        assert profile.biography == "Completely new biography"
        assert profile.experience_years == 10

    def test_full_update_other_profile_as_admin_success(
        self, admin_client, profile_factory
    ):
        client, _ = admin_client
        profile = profile_factory()

        response = client.put(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Admin full update",
                "location": "Admin City",
                "occupation": "Admin Occupation",
                "skills": "Admin Skills",
                "experience_years": 15,
                "is_public": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert data["attributes"]["biography"] == "Admin full update"

        profile.refresh_from_db()
        assert profile.biography == "Admin full update"


class TestProfileMe:
    def test_get_me_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.get(path=reverse("v1:profile-me"))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        attrs = data["attributes"]

        assert data["id"] == str(profile.id)
        assert attrs["biography"] == profile.biography
        assert attrs["is_public"] == profile.is_public

    @pytest.mark.parametrize(
        "method, data",
        [
            pytest.param(
                "patch",
                {
                    "biography": "Updated via me endpoint",
                    "location": "Me City",
                },
                id="patch_me_success",
            ),
            pytest.param(
                "put",
                {
                    "biography": "Full update via me endpoint",
                    "location": "Me City Full",
                    "occupation": "Me Occupation",
                    "skills": "Me Skills",
                    "experience_years": 20,
                    "is_public": False,
                },
                id="put_me_success",
            ),
        ],
    )
    def test_update_me_success(self, editor_client, profile_factory, method, data):
        client, user = editor_client
        profile = profile_factory(user=user)

        action = getattr(client, method)
        response = action(path=reverse("v1:profile-me"), data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json().get("data")
        assert response_data["attributes"]["biography"] == data["biography"]

        profile.refresh_from_db()
        assert profile.biography == data["biography"]

    @pytest.mark.parametrize("method", ["get", "patch", "put"])
    def test_profile_me_unauthorized(self, api_client, method):
        action = getattr(api_client, method)
        response = action(
            path=reverse("v1:profile-me"),
            data={"biography": "Unauthorized update"} if method != "get" else None,
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_get_me_not_found_no_profile(self, editor_client):
        client, user = editor_client
        Profile.objects.filter(user=user).delete()

        response = client.get(path=reverse("v1:profile-me"))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSocialMediaProfile:
    def test_create_social_media_profiles_on_profile_update(
        self, editor_client, profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Updated with socials",
                "social_media": [
                    {
                        "platform": "github",
                        "url": "https://github.com/testuser",
                    },
                    {
                        "platform": "twitter",
                        "url": "https://twitter.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        social_media = profile.social_media.all()

        assert social_media.count() == 2
        platforms = {sm.platform for sm in social_media}
        assert platforms == {"github", "twitter"}

    def test_create_social_media_profiles_on_profile_full_update(
        self, editor_client, profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.put(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Full update with socials",
                "location": "Test City",
                "occupation": "Developer",
                "skills": "Python",
                "experience_years": 5,
                "is_public": True,
                "social_media": [
                    {
                        "platform": "linkedin",
                        "url": "https://www.linkedin.com/in/testuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        social_media = profile.social_media.all()

        assert social_media.count() == 1
        assert social_media.first().platform == "linkedin"

    def test_update_existing_social_media_profile(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        social = social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/olduser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "id": social.id,
                        "platform": "github",
                        "url": "https://github.com/newuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        social.refresh_from_db()
        assert social.url == "https://github.com/newuser"

    def test_add_new_social_media_profile_to_existing_set(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        existing_social = social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/testuser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "id": existing_social.id,
                        "platform": "github",
                        "url": "https://github.com/testuser",
                    },
                    {
                        "platform": "twitter",
                        "url": "https://twitter.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        assert profile.social_media.count() == 2

    def test_delete_social_media_profile_by_omission(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        social1 = social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/testuser",
        )
        social2 = social_media_profile_factory(
            profile=profile,
            platform="twitter",
            url="https://twitter.com/testuser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "id": social1.id,
                        "platform": "github",
                        "url": "https://github.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        assert profile.social_media.count() == 1
        assert profile.social_media.first().id == social1.id

        from apps.accounts.models import SocialMediaProfile

        assert not SocialMediaProfile.objects.filter(id=social2.id).exists()

    def test_replace_all_social_media_profiles(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        old_social = social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/olduser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "platform": "linkedin",
                        "url": "https://www.linkedin.com/in/newuser",
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        assert profile.social_media.count() == 1
        assert profile.social_media.first().platform == "linkedin"

        from apps.accounts.models import SocialMediaProfile

        assert not SocialMediaProfile.objects.filter(id=old_social.id).exists()

    def test_platform_url_mismatch_validation(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "platform": "github",
                        "url": "https://twitter.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/social_media/0/url",
        )

    def test_invalid_url_format_validation(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "platform": "github",
                        "url": "https://invalid-domain.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_400_BAD_REQUEST,
            pointer="/data/attributes/social_media/0/url",
        )

    def test_unauthorized_cannot_add_social_media(self, api_client, profile_factory):
        profile = profile_factory()

        response = api_client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [
                    {
                        "platform": "github",
                        "url": "https://github.com/testuser",
                    },
                ],
            },
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_other_user_cannot_modify_social_media(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, _ = editor_client
        other_profile = profile_factory()
        social = social_media_profile_factory(
            profile=other_profile,
            platform="github",
            url="https://github.com/otheruser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[other_profile.id]),
            data={
                "social_media": [
                    {
                        "id": social.id,
                        "platform": "github",
                        "url": "https://github.com/hacker",
                    },
                ],
            },
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )

        social.refresh_from_db()
        assert social.url == "https://github.com/otheruser"

    def test_clear_all_social_media_profiles(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/testuser",
        )
        social_media_profile_factory(
            profile=profile,
            platform="twitter",
            url="https://twitter.com/testuser",
        )

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "social_media": [],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        assert profile.social_media.count() == 0

    def test_social_media_included_in_response(
        self, editor_client, profile_factory, social_media_profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user)
        social_media_profile_factory(
            profile=profile,
            platform="github",
            url="https://github.com/testuser",
        )

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")
        assert "social_media" in data["attributes"]
        social_media = data["attributes"]["social_media"]

        assert len(social_media) == 1
        assert social_media[0]["platform"] == "github"
        assert social_media[0]["url"] == "https://github.com/testuser"
