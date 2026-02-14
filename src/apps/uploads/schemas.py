from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.uploads.serializers import UploadSerializer

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
            "Upload a new file."
            "Support images, documents, and other files."
            "File purpose determines usage (thumbnail, attachment, avatar, etc.)."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "The file to upload.",
                    },
                    "purpose": {
                        "type": "string",
                        "enum": ["thumbnail", "attachment", "avatar", "other"],
                        "description": "The purpose of the file.",
                    },
                    "visibility": {
                        "type": "string",
                        "enum": ["public", "private"],
                        "description": "The visibility of the upload.",
                    },
                },
                "required": ["file", "purpose", "visibility"],
            }
        },
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
        request=UploadSerializer,
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
