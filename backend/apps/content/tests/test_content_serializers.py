import uuid

import pytest
from rest_framework.fields import DateTimeField

from apps.content.serializers import (
    CategorySerializer,
    PostAttachmentAddSerializer,
    PostAttachmentRemoveSerializer,
    PostCreateSerializer,
    PostRestoreSerializer,
    PostSerializer,
    PostSoftDeleteSerializer,
    PostStatusSerializer,
    PostThumbnailSerializer,
    PostUpdateSerializer,
    TagSerializer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def drf_datetime():
    return DateTimeField()


@pytest.fixture
def to_relation():
    """Helper to format objects into JSON:API relationship format."""

    def _to_relation(resource_type, instance_id):
        return {"type": resource_type, "id": str(instance_id)}

    return _to_relation


class TestCategorySerializer:
    def test_category_serializer_serializes_object_successfully(
        self, category_factory, drf_datetime
    ):
        category = category_factory()
        serializer = CategorySerializer(category)
        expected = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": drf_datetime.to_representation(category.created_at),
            "updated_at": drf_datetime.to_representation(category.updated_at),
            "posts": [],
        }

        assert serializer.data == expected

    def test_category_serializer_serializes_relationships(
        self, category_factory, post_factory, to_relation
    ):
        category = category_factory()
        posts = post_factory.create_batch(size=2, category=category)
        expected = [
            to_relation("posts", posts[1].id),
            to_relation("posts", posts[0].id),
        ]
        serializer = CategorySerializer(category)

        assert all(item in serializer.data["posts"] for item in expected)


class TestTagSerializer:
    def test_tag_serializer_serializes_object_successfully(
        self, tag_factory, drf_datetime
    ):
        tag = tag_factory()
        serializer = TagSerializer(tag)
        expected = {
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "created_at": drf_datetime.to_representation(tag.created_at),
            "updated_at": drf_datetime.to_representation(tag.updated_at),
            "posts": [],
        }

        assert serializer.data == expected

    def test_tag_serializer_serializes_relationships(
        self, tag_factory, post_factory, to_relation
    ):
        tag = tag_factory()
        posts = post_factory.create_batch(size=2)
        tag.posts.set(posts)

        serializer = TagSerializer(tag)
        expected = [
            to_relation("posts", posts[1].id),
            to_relation("posts", posts[0].id),
        ]

        assert all(item in serializer.data["posts"] for item in expected)


class TestPostSerializer:
    def test_post_serializer_serializes_object_successfully(
        self, post_factory, drf_datetime, to_relation
    ):
        post = post_factory(status="published")
        serializer = PostSerializer(post)
        expected = {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "summary": post.summary,
            "status": post.status,
            "published_at": drf_datetime.to_representation(post.published_at),
            "created_at": drf_datetime.to_representation(post.created_at),
            "updated_at": drf_datetime.to_representation(post.updated_at),
            "author": to_relation("users", post.author.id),
            "category": to_relation("categories", post.category.id),
            "tags": [],
            "thumbnail": None,
            "attachments": [],
        }

        assert serializer.data == expected

    def test_post_serializer_serializes_relationships(
        self,
        post_factory,
        tag_factory,
        category_factory,
        upload_factory,
        clean_media,
        to_relation,
    ):
        post = post_factory(status="published")
        tags = tag_factory.create_batch(size=2)
        thumbnail = upload_factory()
        attachments = upload_factory.create_batch(size=2)

        post.tags.set(tags)
        post.attachments.set(attachments)
        post.thumbnail = thumbnail

        serializer = PostSerializer(post)
        expected_tags = [
            to_relation("tags", tags[1].id),
            to_relation("tags", tags[0].id),
        ]
        expected_attachments = [
            to_relation("uploads", attachments[1].id),
            to_relation("uploads", attachments[0].id),
        ]
        expected_thumbnail = to_relation("uploads", thumbnail.id)

        assert all(item in serializer.data["tags"] for item in expected_tags)
        assert all(
            item in serializer.data["attachments"] for item in expected_attachments
        )
        assert serializer.data["thumbnail"] == expected_thumbnail


class TestPostStatusSerializer:
    def test_serializer_validates_valid_status(self, post_factory):
        post = post_factory(status="draft")
        data = {"status": "published"}

        serializer = PostStatusSerializer(post, data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["status"] == "published"

    @pytest.mark.parametrize(
        "invalid_status",
        [
            "invalid_status",
            "",
            None,
        ],
        ids=("invalid_status", "empty_string", "none"),
    )
    def test_serializer_rejects_invalid_status(self, post_factory, invalid_status):
        post = post_factory(status="draft")
        data = {"status": invalid_status}

        serializer = PostStatusSerializer(post, data=data)

        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_serializer_requires_status_field(self, post_factory):
        post = post_factory(status="draft")
        data = {}

        serializer = PostStatusSerializer(post, data=data)

        assert not serializer.is_valid()
        assert "status" in serializer.errors


class TestPostCreateSerializer:
    def test_serializer_validates_valid_creation_data(
        self, category_factory, tag_factory, to_relation
    ):
        category = category_factory()
        tags = tag_factory.create_batch(size=2)
        data = {
            "title": "New Post",
            "content": "Post content",
            "category": to_relation("categories", category.id),
            "tags": [to_relation("tags", tag.id) for tag in tags],
        }

        serializer = PostCreateSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["title"] == "New Post"
        assert serializer.validated_data["category"] == category
        assert len(serializer.validated_data["tags"]) == 2

    def test_serializer_requires_mandatory_fields(self):
        data = {}
        serializer = PostCreateSerializer(data=data)

        assert not serializer.is_valid()
        assert all(
            field in serializer.errors for field in ["title", "content", "category"]
        )


class TestPostUpdateSerializer:
    def test_serializer_validates_partial_update(self, post_factory):
        post = post_factory()
        data = {"title": "Updated Title", "content": "Updated content"}

        serializer = PostUpdateSerializer(post, data=data, partial=True)

        assert serializer.is_valid()
        assert serializer.validated_data["title"] == "Updated Title"
        assert serializer.validated_data["content"] == "Updated content"

    def test_serializer_allows_optional_fields(self, post_factory):
        post = post_factory()
        data = {"title": "Only Title Update"}

        serializer = PostUpdateSerializer(post, data=data, partial=True)

        assert serializer.is_valid()
        assert "category" not in serializer.validated_data
        assert "tags" not in serializer.validated_data


class TestPostThumbnailSerializer:
    def test_serializer_validates_valid_thumbnail_id(self, upload_factory, clean_media):
        thumbnail = upload_factory(purpose="thumbnail")
        data = {"id": str(thumbnail.id)}

        serializer = PostThumbnailSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["id"] == thumbnail

    def test_serializer_rejects_invalid_thumbnail_id(self):
        data = {"id": str(uuid.uuid4())}

        serializer = PostThumbnailSerializer(data=data)

        assert not serializer.is_valid()
        assert "id" in serializer.errors
        assert "Invalid thumbnail upload" in str(serializer.errors["id"])

    def test_serializer_rejects_non_thumbnail_upload(self, upload_factory, clean_media):
        attachment = upload_factory(purpose="attachment")
        data = {"id": str(attachment.id)}

        serializer = PostThumbnailSerializer(data=data)

        assert not serializer.is_valid()
        assert "id" in serializer.errors


class TestPostAttachmentAddSerializer:
    def test_serializer_validates_valid_attachment_ids(
        self, upload_factory, clean_media
    ):
        attachments = upload_factory.create_batch(size=2, purpose="attachment")
        data = {"attachments": [str(att.id) for att in attachments]}

        serializer = PostAttachmentAddSerializer(data=data)

        assert serializer.is_valid()
        assert len(serializer.validated_data["attachments"]) == 2

    def test_serializer_rejects_invalid_attachment_ids(self):
        data = {"attachments": [str(uuid.uuid4()), str(uuid.uuid4())]}

        serializer = PostAttachmentAddSerializer(data=data)

        assert not serializer.is_valid()
        assert "attachments" in serializer.errors
        assert "One or more attachments are invalid" in str(
            serializer.errors["attachments"]
        )

    def test_serializer_rejects_empty_list(self):
        data = {"attachments": []}

        serializer = PostAttachmentAddSerializer(data=data)

        assert not serializer.is_valid()
        assert "attachments" in serializer.errors

    def test_serializer_rejects_non_attachment_uploads(
        self, upload_factory, clean_media
    ):
        thumbnail = upload_factory(purpose="thumbnail")
        data = {"attachments": [str(thumbnail.id)]}

        serializer = PostAttachmentAddSerializer(data=data)

        assert not serializer.is_valid()
        assert "attachments" in serializer.errors


class TestPostAttachmentRemoveSerializer:
    def test_serializer_validates_valid_attachment_in_post(
        self, post_factory, upload_factory, clean_media
    ):
        post = post_factory()
        attachment = upload_factory(purpose="attachment")
        post.attachments.add(attachment)

        data = {"attachment_id": str(attachment.id)}

        serializer = PostAttachmentRemoveSerializer(data=data, context={"post": post})

        assert serializer.is_valid()
        assert serializer.validated_data["attachment_id"] == attachment

    def test_serializer_rejects_attachment_not_in_post(
        self, post_factory, upload_factory, clean_media
    ):
        post = post_factory()
        attachment = upload_factory(purpose="attachment")

        data = {"attachment_id": str(attachment.id)}

        serializer = PostAttachmentRemoveSerializer(data=data, context={"post": post})

        assert not serializer.is_valid()
        assert "attachment_id" in serializer.errors
        assert "Attachment not found in this post" in str(
            serializer.errors["attachment_id"]
        )

    def test_serializer_rejects_invalid_uuid(self, post_factory):
        post = post_factory()
        data = {"attachment_id": "invalid-uuid"}

        serializer = PostAttachmentRemoveSerializer(data=data, context={"post": post})

        assert not serializer.is_valid()
        assert "attachment_id" in serializer.errors


class TestPostSoftDeleteSerializer:
    def test_serializer_validates_with_confirm_true(self, post_factory):
        post = post_factory(status="draft")
        data = {"confirm": True, "reason": "Test deletion"}

        serializer = PostSoftDeleteSerializer(post, data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["confirm"] is True

    @pytest.mark.parametrize(
        "data, expected_error",
        [
            ({"confirm": False}, "Must confirm deletion"),
            ({}, "confirm"),
        ],
        ids=("confirm_false", "no_confirm"),
    )
    def test_serializer_rejects_invalid_confirmation(
        self, post_factory, data, expected_error
    ):
        post = post_factory(status="draft")
        serializer = PostSoftDeleteSerializer(post, data=data)

        assert not serializer.is_valid()
        error_str = str(serializer.errors)
        assert expected_error in error_str
        post = post_factory(status="draft")
        serializer = PostSoftDeleteSerializer(post, data=data)

        assert not serializer.is_valid()
        error_str = str(serializer.errors)
        assert expected_error in error_str

    def test_serializer_rejects_already_deleted_post(self, post_factory):
        post = post_factory(status="deleted")
        data = {"confirm": True}

        serializer = PostSoftDeleteSerializer(post, data=data)

        assert not serializer.is_valid()
        assert "This post is already deleted" in str(serializer.errors)


class TestPostRestoreSerializer:
    def test_serializer_validates_with_confirm_true(self, post_factory):
        post = post_factory(status="deleted")
        data = {"confirm": True}

        serializer = PostRestoreSerializer(post, data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["confirm"] is True

    @pytest.mark.parametrize(
        "data, expected_error",
        [
            ({"confirm": False}, "Must confirm restoration"),
            ({}, "confirm"),
        ],
        ids=("confirm_false", "no_confirm"),
    )
    def test_serializer_rejects_invalid_confirmation(
        self, post_factory, data, expected_error
    ):
        post = post_factory(status="deleted")
        serializer = PostRestoreSerializer(post, data=data)

        assert not serializer.is_valid()
        error_str = str(serializer.errors)
        assert expected_error in error_str
        post = post_factory(status="deleted")
        serializer = PostRestoreSerializer(post, data=data)

        assert not serializer.is_valid()
        assert expected_error in str(serializer.errors)

    def test_serializer_rejects_non_deleted_post(self, post_factory):
        post = post_factory(status="draft")
        data = {"confirm": True}

        serializer = PostRestoreSerializer(post, data=data)

        assert not serializer.is_valid()
        assert "Only deleted posts can be restored" in str(serializer.errors)
