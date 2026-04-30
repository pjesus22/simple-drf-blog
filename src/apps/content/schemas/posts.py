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

POST_SEARCH_PARAMETER = OpenApiParameter(
    name="search",
    type=str,
    location=OpenApiParameter.QUERY,
    description="Case-insensitive search across post title and content.",
    required=False,
)

POST_TAGS_PARAMETER = OpenApiParameter(
    name="tags",
    type=str,
    location=OpenApiParameter.QUERY,
    description=(
        "Comma-separated list of tag slugs to filter by (e.g. `python,django`)."
    ),
    required=False,
)

POST_CATEGORY_PARAMETER = OpenApiParameter(
    name="category",
    type=str,
    location=OpenApiParameter.QUERY,
    description="Filter by category slug (case-insensitive).",
    required=False,
)

POST_ATTACHMENT_ID_PARAMETER = OpenApiParameter(
    name="attachment_id",
    type=str,
    location=OpenApiParameter.PATH,
    description="UUID of the attachment to remove.",
)

post_viewset_schema = extend_schema_view(
    create=extend_schema(
        summary="posts_create",
        description=(
            "Create a new post. "
            "Required fields: title, content, category. "
            "Optional fields: slug, tags, thumbnail, attachments."
        ),
        request=PostCreateSerializer,
        responses={201: PostSerializer},
    ),
    update=extend_schema(
        summary="posts_update",
        description=(
            "Fully replace a post. "
            "Required fields: title, content, category. "
            "Optional fields: slug, summary, tags."
        ),
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    partial_update=extend_schema(
        summary="posts_partial_update",
        description=(
            "Partially update a post. "
            "Optional fields: title, content, category, slug, summary, tags."
        ),
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    retrieve=extend_schema(
        summary="posts_retrieve",
        description=(
            "Retrieve a post based on visibility rules.\n\n"
            "Visibility depends on the requesting user:\n"
            "- Anonymous users: only published posts.\n"
            "- Authenticated users: published posts and their own posts.\n"
            "- Staff users: all non-deleted posts.\n"
        ),
        responses={200: PostSerializer},
        parameters=[POST_SLUG_PARAMETER],
    ),
    list=extend_schema(
        summary="posts_list",
        description=(
            "List posts based on visibility rules.\n\n"
            "Visibility depends on the requesting user:\n"
            "- Anonymous users: only published posts.\n"
            "- Authenticated users: published posts and their own posts.\n"
            "- Staff users: all non-deleted posts.\n\n"
            "Supports filtering by search, tags, and category."
        ),
        responses={200: PostSerializer(many=True)},
        parameters=[
            POST_SEARCH_PARAMETER,
            POST_TAGS_PARAMETER,
            POST_CATEGORY_PARAMETER,
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

thumbnail_add_schema = extend_schema(
    summary="posts_thumbnail_add",
    description="POST: sets a thumbnail.",
    request=PostThumbnailSerializer,
    responses={200: PostSerializer},
    parameters=[POST_SLUG_PARAMETER],
    methods=["POST"],
)

thumbnail_remove_schema = extend_schema(
    summary="posts_thumbnail_remove",
    description="DELETE: removes current thumbnail.",
    responses={204: OpenApiResponse(description="Thumbnail removed")},
    parameters=[POST_SLUG_PARAMETER],
    methods=["DELETE"],
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
    parameters=[POST_SLUG_PARAMETER, POST_ATTACHMENT_ID_PARAMETER],
)

soft_delete_schema = extend_schema(
    summary="posts_soft_delete",
    description="Mark a post as deleted. Requires confirmation.",
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
