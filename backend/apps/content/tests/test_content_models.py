import pytest
from apps.content.models import Category, Post, Tag
from apps.users.models import Editor


class TestCategoryModel:
    def test_category_str_returns_name(self):
        category = Category(name="Test Category")
        assert str(category) == "Test Category"

    def test_category_clean_generates_slug(self, db):
        category = Category(name="Test Category")
        category.clean()
        assert category.slug == "test-category"

    def test_category_clean_preserves_existing_slug(self, db):
        category = Category(name="Test Category", slug="test-category")
        category.clean()
        assert category.slug == "test-category"

    def test_save_category(self, db):
        category = Category(name="Test Category", description="A test category")
        category.save()
        assert category.id is not None


class TestTagModel:
    def test_tag_str_returns_name(self):
        tag = Tag(name="Test Tag")
        assert str(tag) == "Test Tag"

    def test_tag_clean_generates_slug(self, db):
        tag = Tag(name="Test Tag")
        tag.clean()
        assert tag.slug == "test-tag"

    def test_tag_clean_preserves_existing_slug(self, db):
        tag = Tag(name="Test Tag", slug="test-tag")
        tag.clean()
        assert tag.slug == "test-tag"

    def test_save_tag(self, db):
        tag = Tag(name="Test Tag")
        tag.save()
        assert tag.id is not None


class TestPostModel:
    def test_post_str_returns_title(self):
        post = Post(title="Test Post")
        assert str(post) == "Test Post"

    def test_post_clean_generates_slug(self, db):
        post = Post(title="Test Post")
        post.clean()
        assert post.slug == "test-post"

    def test_post_clean_preserves_existing_slug(self, db):
        post = Post(title="Test Post", slug="test-post")
        post.clean()
        assert post.slug == "test-post"

    def test_post_clean_sets_published_at(self, db):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        post.clean()
        assert post.published_at is not None

    def test_post_published_at_not_updated_on_republish(self, db, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()

        post.status = Post.Status.PUBLISHED
        post.save()
        assert post.published_at == original_published_at

    @pytest.mark.parametrize(
        "status",
        [
            Post.Status.DRAFT,
            Post.Status.ARCHIVED,
            Post.Status.DELETED,
        ],
    )
    def test_post_published_at_not_set_for_non_published_status(self, db, status):
        post = Post(title="Test Post", status=status)
        post.clean()
        assert post.published_at is None

    def test_save_post(self, db):
        category = Category.objects.create(name="Test Category")
        author = Editor.objects.create(
            username="testeditor",
            email="fake_email@example.com",
            first_name="Test",
            last_name="Editor",
        )
        post = Post(title="Test Post", category=category, author=author)
        post.save()
        assert post.id is not None

    def test_status_methods(self):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        assert post.is_published() is True
        assert post.is_draft() is False
        assert post.is_archived() is False
        assert post.is_deleted() is False

    @pytest.mark.parametrize(
        "initial_status, final_status",
        [
            (Post.Status.DRAFT, Post.Status.PUBLISHED),
            (Post.Status.PUBLISHED, Post.Status.ARCHIVED),
            (Post.Status.PUBLISHED, Post.Status.DELETED),
        ],
        ids=["first_publish", "archive", "delete"],
    )
    def test_post_status_transitions(
        self, db, initial_status, final_status, post_factory
    ):
        post = post_factory(status=initial_status)

        original_published_at = post.published_at

        post.status = final_status
        post.save()

        if (
            initial_status == Post.Status.DRAFT
            and final_status == Post.Status.PUBLISHED
        ):
            assert post.published_at is not None
            assert original_published_at is None
        elif final_status == Post.Status.PUBLISHED:
            assert post.published_at == original_published_at
        else:
            assert post.published_at == original_published_at

    def test_post_republish_preserves_published_at(self, db, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()

        post.status = Post.Status.PUBLISHED
        post.save()

        assert post.published_at == original_published_at

    def test_post_add_tags(self, db, post_factory, tag_factory):
        post = post_factory()
        tags = tag_factory.create_batch(size=2)

        post.tags.add(*tags)

        assert post.tags.count() == 2

    def test_post_add_attachments(self, db, post_factory, upload_factory, clean_media):
        post = post_factory()
        attachments = upload_factory.create_batch(size=2)

        post.attachments.add(*attachments)

        assert post.attachments.count() == 2

    def test_post_add_thumbnail(self, db, post_factory, upload_factory, clean_media):
        post = post_factory()
        thumbnail = upload_factory()

        post.thumbnail = thumbnail
        post.save()

        assert post.thumbnail == thumbnail
        assert post.thumbnail.purpose == "test"

    def test_post_add_thumbnail_deletion_sets_null(
        self, db, post_factory, upload_factory, clean_media
    ):
        post = post_factory()
        thumbnail = upload_factory()

        post.thumbnail = thumbnail
        post.save()

        thumbnail.delete()

        post.refresh_from_db()
        assert post.thumbnail is None
        assert Post.objects.filter(id=post.id).exists()
