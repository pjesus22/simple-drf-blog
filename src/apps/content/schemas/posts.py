from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.content.serializers import (
    PostAttachmentAddSerializer,
    PostAttachmentRemoveSerializer,
    PostCreateSerializer,
    PostRestoreSerializer,
    PostSerializer,
    PostSoftDeleteSerializer,
    PostStatusSerializer,
    PostThumbnailSerializer,
    PostUpdateSerializer,
)

POST_SLUG_PARAMETER = OpenApiParameter(
    name="slug",
    type=str,
    location=OpenApiParameter.PATH,
    description="Unique slug identifier of the post.",
)


post_viewset_schema = extend_schema_view(
    create=extend_schema(
        summary="posts_create",
        description="Create a new post.",
        request=PostCreateSerializer,
        responses={201: PostSerializer},
    ),
    update=extend_schema(
        summary="posts_update",
        description="Update a post.",
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    partial_update=extend_schema(
        summary="posts_partial_update",
        description="Update a post.",
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    retrieve=extend_schema(
        summary="posts_retrieve",
        description="Retrieve a published post.",
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    list=extend_schema(
        summary="posts_list",
        description="List all published posts.",
        responses={200: PostSerializer(many=True)},
        parameters=[
            OpenApiParameter(
                name="search",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Search in title and content.",
            ),
            OpenApiParameter(
                name="tags",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by selected tags.",
            ),
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by category.",
            ),
        ],
    ),
    destroy=extend_schema(exclude=True),
)

change_status_schema = extend_schema(
    summary="posts_change_status",
    description=(
        "Change the status of a post according to transition rules. "
        "Cannot modify deleted posts."
    ),
    request=PostStatusSerializer,
    responses={
        200: PostSerializer,
        400: OpenApiResponse(description="Invalid transition or validation error"),
    },
    parameters=[POST_SLUG_PARAMETER],
)

thumbnail_schema = extend_schema(
    summary="posts_thumbnail",
    description="POST: sets a thumbnail.\nDELETE: removes current thumbnail.",
    request=PostThumbnailSerializer,
    responses={
        200: PostSerializer,
        204: OpenApiResponse(description="Thumbnail removed"),
    },
    parameters=[POST_SLUG_PARAMETER],
)

add_attachments_schema = extend_schema(
    summary="posts_add_attachments",
    description="Attach one or multiple uploads to the post.",
    request=PostAttachmentAddSerializer,
    responses={200: PostSerializer},
    parameters=[POST_SLUG_PARAMETER],
)

remove_attachment_schema = extend_schema(
    summary="posts_remove_attachment",
    description="Remove a specific attachment from the post.",
    request=PostAttachmentRemoveSerializer,
    responses={204: OpenApiResponse(description="Attachment removed")},
    parameters=[
        POST_SLUG_PARAMETER,
        OpenApiParameter(
            name="attachment_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="UUID of the attachment to remove.",
        ),
    ],
)

soft_delete_schema = extend_schema(
    summary="posts_soft_delete",
    description="Mark a post as deleted. Requires confirmation",
    request=PostSoftDeleteSerializer,
    responses={204: OpenApiResponse(description="Post soft deleted")},
    parameters=[POST_SLUG_PARAMETER],
)

restore_schema = extend_schema(
    summary="posts_restore",
    description="Restore a deleted post (requires admin role).",
    request=PostRestoreSerializer,
    responses={200: PostSerializer},
    parameters=[POST_SLUG_PARAMETER],
)

trash_schema = extend_schema(
    summary="posts_trash",
    description="List posts currently in deleted state.",
    responses={200: PostSerializer(many=True)},
)
