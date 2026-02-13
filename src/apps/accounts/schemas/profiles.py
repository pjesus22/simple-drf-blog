from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from apps.accounts.serializers import (
    PrivateProfileSerializer,
    PublicProfileSerializer,
)

PROFILE_ID_PARAMETER = OpenApiParameter(
    name="id",
    type=int,
    location=OpenApiParameter.PATH,
    description="Unique identifier of the profile.",
)

profile_viewset_schema = extend_schema_view(
    list=extend_schema(
        summary="profiles_list",
        description=(
            "List all public profiles. Authenticated users can see more profiles."
        ),
        responses={200: PublicProfileSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="profiles_retrieve",
        description="Retrieve a specific profile.",
        responses={200: PublicProfileSerializer},
        parameters=[PROFILE_ID_PARAMETER],
    ),
    update=extend_schema(
        summary="profiles_update",
        description="Update a profile. Users can only update their own profile.",
        request=PrivateProfileSerializer,
        responses={200: PrivateProfileSerializer},
        parameters=[PROFILE_ID_PARAMETER],
    ),
    partial_update=extend_schema(
        summary="profiles_partial_update",
        description=(
            "Partially update a profile. Users can only update their own profile."
        ),
        request=PrivateProfileSerializer,
        responses={200: PrivateProfileSerializer},
        parameters=[PROFILE_ID_PARAMETER],
    ),
)


profile_me_schema = extend_schema(
    summary="profiles_me",
    description=(
        "GET: Get the authenticated user's profile.\n"
        "PUT: Update the authenticated user's profile.\n"
        "PATCH: Partially update the authenticated user's profile."
    ),
    request=PrivateProfileSerializer,
    responses={200: PrivateProfileSerializer},
    methods=["GET", "PUT", "PATCH"],
)
