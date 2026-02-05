import uuid

import pytest
from apps.content.serializers import (
    CategorySerializer,
    PostAttachmentAddSerializer,
    PostAttachmentRemoveSerializer,
    PostCreateSerializer,
    PostSerializer,
    PostStatusSerializer,
    PostThumbnailSerializer,
    PostUpdateSerializer,
    TagSerializer,
)
from rest_framework.fields import DateTimeField

pytestmark = pytest.mark.django_db
field = DateTimeField()


class TestCategorySerializer:
    def test_category_serializer_serializes_base_fields(self, category_factory):
        category = category_factory()
        serializer = CategorySerializer(category)
        expected = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "created_at": field.to_representation(category.created_at),
            "updated_at": field.to_representation(category.updated_at),
            "posts": [],
        }

        assert serializer.data == expected

    def test_category_serializer_serializes_relationships(
        self, category_factory, post_factory
    ):
        category = category_factory()
        posts = post_factory.create_batch(size=2, category=category)
        expected = [
            {"type": "posts", "id": str(posts[1].id)},
            {"type": "posts", "id": str(posts[0].id)},
        ]
        serializer = CategorySerializer(category)

        assert all(item in serializer.data["posts"] for item in expected)


class TestTagSerializer:
    def test_tag_serializer_serializes_base_fields(self, tag_factory):
        tag = tag_factory()
        serializer = TagSerializer(tag)
        expected = {
            "id": tag.id,
            "name": tag.name,
            "slug": tag.slug,
            "created_at": field.to_representation(tag.created_at),
            "updated_at": field.to_representation(tag.updated_at),
            "posts": [],
        }

        assert serializer.data == expected

    def test_tag_serializer_serializes_relationships(self, tag_factory, post_factory):
        tag = tag_factory()
        posts = post_factory.create_batch(size=2)
        tag.posts.set(posts)

        serializer = TagSerializer(tag)
        expected = [
            {"type": "posts", "id": str(posts[1].id)},
            {"type": "posts", "id": str(posts[0].id)},
        ]

        assert all(item in serializer.data["posts"] for item in expected)


class TestPostSerializer:
    def test_post_serializer_serializes_base_fields(self, post_factory):
        post = post_factory(status="published")
        serializer = PostSerializer(post)
        expected = {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "summary": post.summary,
            "status": post.status,
            "published_at": field.to_representation(post.published_at),
            "created_at": field.to_representation(post.created_at),
            "updated_at": field.to_representation(post.updated_at),
            "author": {"type": "users", "id": str(post.author.id)},
            "category": {"type": "categories", "id": str(post.category.id)},
            "tags": [],
            "thumbnail": None,
            "attachments": [],
        }

        assert serializer.data == expected

    def test_post_serializer_serializes_relationships(
        self, post_factory, tag_factory, category_factory, upload_factory, clean_media
    ):
        post = post_factory(status="published")
        tags = tag_factory.create_batch(size=2)
        thumbnail = upload_factory()
        attachments = upload_factory.create_batch(size=2)

        post.tags.set(tags)
        post.attachments.set(attachments)
        post.thumbnail = thumbnail

        serializer = PostSerializer(post)
        expected = {
            "tags": [
                {"type": "tags", "id": str(tags[1].id)},
                {"type": "tags", "id": str(tags[0].id)},
            ],
            "thumbnail": {"type": "uploads", "id": str(thumbnail.id)},
            "attachments": [
                {"type": "uploads", "id": str(attachments[1].id)},
                {"type": "uploads", "id": str(attachments[0].id)},
            ],
        }

        assert all(item in serializer.data["tags"] for item in expected["tags"])
        assert all(
            item in serializer.data["attachments"] for item in expected["attachments"]
        )
        assert expected["thumbnail"] == serializer.data["thumbnail"]


class TestPostStatusSerializer:
    def test_serializer_validates_valid_status(self, post_factory):
        post = post_factory(status="draft")
        data = {"status": "published"}

        serializer = PostStatusSerializer(post, data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["status"] == "published"

    def test_serializer_rejects_invalid_status(self, post_factory):
        post = post_factory(status="draft")
        data = {"status": "invalid_status"}

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
        self, category_factory, tag_factory
    ):
        category = category_factory()
        tags = tag_factory.create_batch(size=2)
        data = {
            "title": "New Post",
            "content": "Post content",
            "category": {"type": "categories", "id": str(category.id)},
            "tags": [{"type": "tags", "id": str(tag.id)} for tag in tags],
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
        assert "title" in serializer.errors
        assert "content" in serializer.errors
        assert "category" in serializer.errors


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
        import uuid

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
