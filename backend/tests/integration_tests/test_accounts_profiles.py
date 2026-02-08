import pytest
from apps.accounts.models import Profile
from django.urls import reverse
from rest_framework import status
from tests.helpers import assert_drf_error_response, assert_jsonapi_error_response

pytestmark = pytest.mark.django_db


@pytest.fixture
def profile_data():
    return {
        "biography": "Test biography",
        "location": "Test City",
        "occupation": "Test Occupation",
        "skills": "Python, Django, DRF",
        "experience_years": 5,
        "is_public": True,
    }


class TestReadProfile:
    def test_list_profiles_success(self, api_client, profile_factory):
        client = api_client
        profiles = profile_factory.create_batch(size=3, is_public=True)
        profile_ids = {str(p.id) for p in profiles}

        response = client.get(path=reverse("v1:profile-list"))
        data = response.json().get("data")
        received_ids = {item["id"] for item in data}

        assert response.status_code == status.HTTP_200_OK
        assert profile_ids.issubset(received_ids)

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
        ids=[
            "public_profiles_unauthenticated",
            "private_profiles_unauthenticated",
            "public_profiles_editor",
            "private_profiles_editor_owns_one",
            "public_profiles_admin",
            "private_profiles_admin",
        ],
    )
    def test_list_profiles_visibility(
        self, request, profile_factory, client_name, is_public, expected_count
    ):
        fixture_value = request.getfixturevalue(client_name)
        client, user = (
            fixture_value if isinstance(fixture_value, tuple) else (fixture_value, None)
        )

        # Create 3 profiles with the specified visibility
        if user and client_name == "editor_client":
            # Create one profile for the editor user
            profile_factory(user=user, is_public=is_public)
            # Create 2 more profiles for other users
            profile_factory.create_batch(size=2, is_public=is_public)
        else:
            profile_factory.create_batch(size=3, is_public=is_public)

        response = client.get(path=reverse("v1:profile-list"))
        data = response.json().get("data")

        assert response.status_code == status.HTTP_200_OK
        assert len(data) == expected_count

    def test_retrieve_public_profile_success(self, api_client, profile_factory):
        client = api_client
        profile = profile_factory(is_public=True)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["biography"] == profile.biography
        assert data["attributes"]["location"] == profile.location
        assert data["attributes"]["occupation"] == profile.occupation
        assert data["attributes"]["skills"] == profile.skills
        assert data["attributes"]["experience_years"] == profile.experience_years
        assert (
            "is_public" not in data["attributes"]
        )  # Public serializer doesn't expose this

    def test_retrieve_private_profile_as_owner_success(
        self, editor_client, profile_factory
    ):
        client, user = editor_client
        profile = profile_factory(user=user, is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["biography"] == profile.biography
        assert data["attributes"]["location"] == profile.location

    def test_retrieve_private_profile_as_admin_success(
        self, admin_client, profile_factory
    ):
        client, _ = admin_client
        profile = profile_factory(is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["biography"] == profile.biography

    def test_retrieve_private_profile_as_other_user_not_found(
        self, editor_client, profile_factory
    ):
        client, _ = editor_client
        profile = profile_factory(is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )

    def test_retrieve_private_profile_unauthenticated_not_found(
        self, api_client, profile_factory
    ):
        client = api_client
        profile = profile_factory(is_public=False)

        response = client.get(path=reverse("v1:profile-detail", args=[profile.id]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )

    def test_retrieve_profile_not_found(self, api_client):
        client = api_client

        response = client.get(path=reverse("v1:profile-detail", args=[0]))

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )


class TestPartialUpdateProfile:
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
        assert profile.location == "Updated City"
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
        assert data["attributes"]["occupation"] == "Admin updated occupation"

        profile.refresh_from_db()

        assert profile.biography == "Admin updated biography"
        assert profile.occupation == "Admin updated occupation"

    def test_partial_update_other_profile_forbidden(
        self, editor_client, profile_factory
    ):
        client, _ = editor_client
        profile = profile_factory()

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={"biography": "Unauthorized update"},
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )

    def test_partial_update_profile_unauthorized(self, api_client, profile_factory):
        client = api_client
        profile = profile_factory()

        response = client.patch(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={"biography": "Unauthorized update"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )


class TestFullUpdateProfile:
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
        assert data["attributes"]["location"] == "New City"
        assert data["attributes"]["occupation"] == "New Occupation"
        assert data["attributes"]["skills"] == "New Skills"
        assert data["attributes"]["experience_years"] == 10
        assert data["attributes"]["is_public"] is False

        profile.refresh_from_db()

        assert profile.biography == "Completely new biography"
        assert profile.location == "New City"
        assert profile.occupation == "New Occupation"
        assert profile.skills == "New Skills"
        assert profile.experience_years == 10
        assert profile.is_public is False

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
        assert data["attributes"]["location"] == "Admin City"

        profile.refresh_from_db()

        assert profile.biography == "Admin full update"
        assert profile.location == "Admin City"

    def test_full_update_other_profile_not_found(self, editor_client, profile_factory):
        client, _ = editor_client
        profile = profile_factory()

        response = client.put(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Unauthorized full update",
                "location": "Unauthorized City",
                "occupation": "Unauthorized Occupation",
                "skills": "Unauthorized Skills",
                "experience_years": 5,
                "is_public": True,
            },
            format="json",
        )

        assert_jsonapi_error_response(
            response=response,
            status_code=status.HTTP_404_NOT_FOUND,
            code="not_found",
            detail_contains="No Profile matches the given query.",
        )

    def test_full_update_profile_unauthorized(self, api_client, profile_factory):
        client = api_client
        profile = profile_factory()

        response = client.put(
            path=reverse("v1:profile-detail", args=[profile.id]),
            data={
                "biography": "Unauthorized full update",
                "location": "Unauthorized City",
                "occupation": "Unauthorized Occupation",
                "skills": "Unauthorized Skills",
                "experience_years": 5,
                "is_public": True,
            },
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )


class TestProfileMe:
    def test_get_me_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.get(path=reverse("v1:profile-me"))

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["id"] == str(profile.id)
        assert data["attributes"]["biography"] == profile.biography
        assert data["attributes"]["location"] == profile.location
        assert data["attributes"]["occupation"] == profile.occupation
        assert data["attributes"]["skills"] == profile.skills
        assert data["attributes"]["experience_years"] == profile.experience_years
        assert data["attributes"]["is_public"] == profile.is_public

    def test_patch_me_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.patch(
            path=reverse("v1:profile-me"),
            data={
                "biography": "Updated via me endpoint",
                "location": "Me City",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["biography"] == "Updated via me endpoint"
        assert data["attributes"]["location"] == "Me City"

        profile.refresh_from_db()

        assert profile.biography == "Updated via me endpoint"
        assert profile.location == "Me City"

    def test_put_me_success(self, editor_client, profile_factory):
        client, user = editor_client
        profile = profile_factory(user=user)

        response = client.put(
            path=reverse("v1:profile-me"),
            data={
                "biography": "Full update via me endpoint",
                "location": "Me City Full",
                "occupation": "Me Occupation",
                "skills": "Me Skills",
                "experience_years": 20,
                "is_public": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json().get("data")

        assert data["attributes"]["biography"] == "Full update via me endpoint"
        assert data["attributes"]["location"] == "Me City Full"
        assert data["attributes"]["occupation"] == "Me Occupation"
        assert data["attributes"]["skills"] == "Me Skills"
        assert data["attributes"]["experience_years"] == 20
        assert data["attributes"]["is_public"] is False

        profile.refresh_from_db()

        assert profile.biography == "Full update via me endpoint"
        assert profile.location == "Me City Full"
        assert profile.occupation == "Me Occupation"
        assert profile.skills == "Me Skills"
        assert profile.experience_years == 20
        assert profile.is_public is False

    def test_get_me_unauthorized(self, api_client):
        client = api_client

        response = client.get(path=reverse("v1:profile-me"))

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_patch_me_unauthorized(self, api_client):
        client = api_client

        response = client.patch(
            path=reverse("v1:profile-me"),
            data={"biography": "Unauthorized update"},
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_put_me_unauthorized(self, api_client):
        client = api_client

        response = client.put(
            path=reverse("v1:profile-me"),
            data={
                "biography": "Unauthorized full update",
                "location": "Unauthorized City",
                "occupation": "Unauthorized Occupation",
                "skills": "Unauthorized Skills",
                "experience_years": 5,
                "is_public": True,
            },
            format="json",
        )

        assert_drf_error_response(
            response=response,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail_contains="credentials were not provided.",
        )

    def test_get_me_not_found_no_profile(self, editor_client):
        client, user = editor_client
        # Ensure user has no profile
        Profile.objects.filter(user=user).delete()

        response = client.get(path=reverse("v1:profile-me"))

        assert response.status_code == status.HTTP_404_NOT_FOUND
