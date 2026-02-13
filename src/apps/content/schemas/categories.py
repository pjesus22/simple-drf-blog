from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.content.serializers import CategorySerializer

CATEGORY_SLUG_PARAMETER = OpenApiParameter(
    name="slug",
    type=str,
    location=OpenApiParameter.PATH,
    description="Unique slug identifier of the category.",
)

category_viewset_schema = extend_schema_view(
    create=extend_schema(
        summary="categories_create",
        description="Create a new category (requires admin role).",
        request=CategorySerializer,
        responses={201: CategorySerializer},
    ),
    partial_update=extend_schema(
        summary="categories_partial_update",
        description="Update a category (requires admin role).",
        request=CategorySerializer,
        responses={200: CategorySerializer},
        parameters=[CATEGORY_SLUG_PARAMETER],
    ),
    retrieve=extend_schema(
        summary="categories_retrieve",
        description="Retrieve a category with its posts.",
        responses={200: CategorySerializer},
        parameters=[CATEGORY_SLUG_PARAMETER],
    ),
    list=extend_schema(
        summary="categories_list",
        description="List all categories with their associated posts.",
        responses={200: CategorySerializer(many=True)},
    ),
    destroy=extend_schema(
        summary="categories_delete",
        description="Delete a category (requires admin role).",
        parameters=[CATEGORY_SLUG_PARAMETER],
        responses={204: OpenApiResponse(description="Category deleted successfully.")},
    ),
)
