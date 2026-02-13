from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.content.serializers import TagSerializer

TAG_SLUG_PARAMETER = OpenApiParameter(
    name="slug",
    type=str,
    location=OpenApiParameter.PATH,
    description="Unique slug identifier of the tag.",
)

tag_viewset_schema = extend_schema_view(
    list=extend_schema(
        summary="tags_list",
        description="List all tags with their associated posts.",
        responses={200: TagSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="tags_retrieve",
        description="Retrieve a specific tag with its posts.",
        responses={200: TagSerializer},
        parameters=[TAG_SLUG_PARAMETER],
    ),
    create=extend_schema(
        summary="tags_create",
        description="Create a new tag (requires editor role or higher).",
        request=TagSerializer,
        responses={201: TagSerializer},
    ),
    partial_update=extend_schema(
        summary="tags_partial_update",
        description="Update a tag (requires editor role or higher).",
        request=TagSerializer,
        responses={200: TagSerializer},
        parameters=[TAG_SLUG_PARAMETER],
    ),
    destroy=extend_schema(
        summary="tags_delete",
        description="Delete a tag (requires editor role or higher).",
        responses={204: OpenApiResponse(description="Tag deleted successfully")},
        parameters=[TAG_SLUG_PARAMETER],
    ),
)
