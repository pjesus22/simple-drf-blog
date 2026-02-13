from apps.content.schemas.categories import category_viewset_schema
from apps.content.schemas.posts import (
    add_attachments_schema,
    change_status_schema,
    post_viewset_schema,
    remove_attachment_schema,
    restore_schema,
    soft_delete_schema,
    thumbnail_schema,
    trash_schema,
)
from apps.content.schemas.tags import tag_viewset_schema

__all__ = [
    "add_attachments_schema",
    "category_viewset_schema",
    "change_status_schema",
    "post_viewset_schema",
    "remove_attachment_schema",
    "restore_schema",
    "soft_delete_schema",
    "tag_viewset_schema",
    "thumbnail_schema",
    "trash_schema",
]
