from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.accounts.serializers import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)

USER_ID_PARAMETER = OpenApiParameter(
    name="id",
    type=int,
    location=OpenApiParameter.PATH,
    description="Unique identifier of the user.",
)

user_viewset_schema = extend_schema_view(
    list=extend_schema(
        summary="users_list",
        description="List all users (requires admin role).",
        responses={200: UserListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="users_retrieve",
        description=(
            "Retrieve a specific user (users can view their own profile, "
            "admins can view any user)."
        ),
        responses={200: UserDetailSerializer},
        parameters=[USER_ID_PARAMETER],
    ),
    create=extend_schema(
        summary="users_create",
        description="Create a new user (requires admin role).",
        request=UserCreateSerializer,
        responses={201: UserDetailSerializer},
    ),
    update=extend_schema(
        summary="users_update",
        description="Update a user (requires admin role).",
        request=UserDetailSerializer,
        responses={200: UserDetailSerializer},
        parameters=[USER_ID_PARAMETER],
    ),
    partial_update=extend_schema(
        summary="users_partial_update",
        description="Partially update a user (requires admin role).",
        request=UserDetailSerializer,
        responses={200: UserDetailSerializer},
        parameters=[USER_ID_PARAMETER],
    ),
    destroy=extend_schema(
        summary="users_delete",
        description="Delete a user (requires admin role).",
        responses={204: OpenApiResponse(description="User deleted successfully")},
        parameters=[USER_ID_PARAMETER],
    ),
)
user_me_schema = extend_schema(
    summary="users_me",
    description=(
        "GET: Get authenticated user profile.\n"
        "PATCH: Update authenticated user profile."
    ),
    request=UserDetailSerializer,
    responses={200: UserDetailSerializer},
    methods=["GET", "PATCH"],
)
change_role_schema = extend_schema(
    summary="users_change_role",
    description=(
        "Change a user's role (requires admin role). Cannot demote the last admin."
    ),
    request=ChangeRoleSerializer,
    responses={
        200: UserDetailSerializer,
        400: OpenApiResponse(description="Cannot demote last admin or invalid role"),
    },
    parameters=[USER_ID_PARAMETER],
)
change_password_schema = extend_schema(
    summary="users_change_password",
    description=(
        "Change the authenticated user's password (requires old password for "
        "verification)."
    ),
    request=PasswordUpdateSerializer,
    responses={
        204: OpenApiResponse(description="Password changed successfully"),
        400: OpenApiResponse(description="Invalid old password or validation error"),
    },
)
force_password_change_schema = extend_schema(
    summary="users_force_password_change",
    description="Force a password change for a user (requires admin role).",
    request=PasswordResetSerializer,
    responses={204: OpenApiResponse(description="Password changed successfully")},
    parameters=[USER_ID_PARAMETER],
)
