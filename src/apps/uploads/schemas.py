from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.uploads.serializers import (
    UploadCreateSerializer,
    UploadSerializer,
    UploadUpdateSerializer,
)

UPLOAD_ID_PARAMETER = OpenApiParameter(
    name="id",
    type=str,
    location=OpenApiParameter.PATH,
    description="UUID of the upload.",
)

upload_viewset_schema = extend_schema_view(
    list=extend_schema(
        summary="uploads_list",
        description=(
            "List uploads. Users see their own uploads, admins see all uploads."
        ),
        responses={200: UploadSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="uploads_retrieve",
        description="Retrieve a specific upload.",
        responses={200: UploadSerializer},
        parameters=[UPLOAD_ID_PARAMETER],
    ),
    create=extend_schema(
        summary="uploads_create",
        description=(
            "Upload a new file. "
            "Support images, documents, and other files. "
            "File purpose determines usage (thumbnail, attachment, avatar, etc.)."
        ),
        request=UploadCreateSerializer,
        responses={
            201: UploadSerializer,
            400: OpenApiResponse(
                description="Invalid file or validation error",
            ),
        },
    ),
    partial_update=extend_schema(
        summary="uploads_partial_update",
        description=(
            "Update upload metadata (purpose, visibility). "
            "User can only update their own uploads."
        ),
        request=UploadUpdateSerializer,
        responses={200: UploadSerializer},
        parameters=[UPLOAD_ID_PARAMETER],
    ),
    destroy=extend_schema(
        summary="uploads_destroy",
        description="Delete an upload. Users can only delete their own uploads.",
        responses={
            204: OpenApiResponse(description="Upload deleted successfully"),
        },
        parameters=[UPLOAD_ID_PARAMETER],
    ),
)


upload_restore_action_schema = extend_schema(
    summary="uploads_restore",
    description="Restore a deleted upload.",
    responses={200: UploadSerializer},
    parameters=[UPLOAD_ID_PARAMETER],
    methods=["POST"],
)

upload_trash_action_schema = extend_schema(
    summary="uploads_trash",
    description="List deleted uploads.",
    responses={200: UploadSerializer(many=True)},
)
