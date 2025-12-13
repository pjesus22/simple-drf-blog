import pytest
from apps.content.serializers import CategorySerializer, PostSerializer, TagSerializer
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
