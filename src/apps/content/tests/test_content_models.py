from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
import pytest

from apps.content.models import Category, Post, Tag

pytestmark = pytest.mark.django_db


class TestCategoryModel:
    @pytest.mark.parametrize(
        "name, expected_str, expected_slug",
        [
            ("Test Category", "Test Category", "test-category"),
            ("New Name", "New Name", "new-name"),
        ],
        ids=("test_category", "new_name"),
    )
    def test_category_metadata(self, name, expected_str, expected_slug):
        category = Category(name=name)
        assert str(category) == expected_str

        category.clean()
        assert category.slug == expected_slug

    def test_category_clean_preserves_existing_slug(self):
        category = Category(name="Test Category", slug="custom-slug")
        category.clean()
        assert category.slug == "custom-slug"

    def test_save_category(self, category_factory):
        category = category_factory(name="Test Category")
        assert category.id is not None
        assert Category.objects.filter(id=category.id).exists()


class TestTagModel:
    @pytest.mark.parametrize(
        "name, expected_str, expected_slug",
        [
            ("Test Tag", "Test Tag", "test-tag"),
            ("Tech News", "Tech News", "tech-news"),
        ],
        ids=("test_tag", "tech_news"),
    )
    def test_tag_metadata(self, name, expected_str, expected_slug):
        tag = Tag(name=name)
        assert str(tag) == expected_str

        tag.clean()
        assert tag.slug == expected_slug

    def test_tag_clean_preserves_existing_slug(self):
        tag = Tag(name="Test Tag", slug="custom-tag-slug")
        tag.clean()
        assert tag.slug == "custom-tag-slug"

    def test_save_tag(self, tag_factory):
        tag = tag_factory(name="Test Tag")
        assert tag.id is not None
        assert Tag.objects.filter(id=tag.id).exists()


class TestPostModel:
    def test_post_str_returns_title(self):
        post = Post(title="Test Post")
        assert str(post) == "Test Post"

    @pytest.mark.parametrize(
        "title, expected_slug",
        [
            ("Test Post", "test-post"),
            ("Hello World!", "hello-world"),
        ],
        ids=("test_post", "hello_world"),
    )
    def test_post_clean_generates_slug(self, title, expected_slug):
        post = Post(title=title)
        post.clean()
        assert post.slug == expected_slug

    def test_post_clean_preserves_existing_slug(self):
        post = Post(title="Test Post", slug="manual-slug")
        post.clean()
        assert post.slug == "manual-slug"

    def test_post_clean_sets_published_at(self):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        post.clean()
        assert post.published_at is not None

    @pytest.mark.parametrize(
        "status",
        [Post.Status.DRAFT, Post.Status.ARCHIVED, Post.Status.DELETED],
        ids=("draft", "archived", "deleted"),
    )
    def test_post_published_at_not_set_for_non_published_status(self, status):
        post = Post(title="Test Post", status=status)
        post.clean()
        assert post.published_at is None

    def test_save_post(self, post_factory):
        post = post_factory()
        assert post.id is not None
        assert Post.objects.filter(id=post.id).exists()

    def test_status_methods(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        assert post.is_published is True
        assert post.is_draft is False
        assert post.is_archived is False
        assert post.is_deleted is False

    @pytest.mark.parametrize(
        "initial_status, final_status, expect_published_at_change",
        [
            (Post.Status.DRAFT, Post.Status.PUBLISHED, True),
            (Post.Status.PUBLISHED, Post.Status.ARCHIVED, False),
            (Post.Status.PUBLISHED, Post.Status.DELETED, False),
        ],
        ids=("draft_to_published", "published_to_archived", "published_to_deleted"),
    )
    def test_post_status_transitions(
        self, initial_status, final_status, expect_published_at_change, post_factory
    ):
        post = post_factory(status=initial_status)
        original_published_at = post.published_at

        post.status = final_status
        post.save()

        if expect_published_at_change:
            assert post.published_at is not None
            assert original_published_at is None
        else:
            assert post.published_at == original_published_at

    def test_post_republish_preserves_published_at(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()
        post.status = Post.Status.DRAFT
        post.save()
        post.status = Post.Status.PUBLISHED
        post.save()

        assert post.published_at == original_published_at

    def test_post_relationships(self, post_factory, tag_factory, upload_factory):
        post = post_factory()
        tags = tag_factory.create_batch(2)
        attachments = upload_factory.create_batch(2)
        thumbnail = upload_factory(purpose="thumbnail")

        post.tags.add(*tags)
        post.attachments.add(*attachments)
        post.thumbnail = thumbnail
        post.save()

        assert post.tags.count() == 2
        assert post.attachments.count() == 2
        assert post.thumbnail == thumbnail

    def test_thumbnail_deletion_sets_null(self, post_factory, upload_factory):
        post = post_factory()
        thumbnail = upload_factory()
        post.thumbnail = thumbnail
        post.save()

        thumbnail.delete()
        post.refresh_from_db()

        assert post.thumbnail is None
        assert Post.objects.filter(id=post.id).exists()


class TestPostModelMethods:
    def test_change_status_sucess(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        post.change_status(Post.Status.PUBLISHED)
        post.refresh_from_db()
        assert post.status == Post.Status.PUBLISHED
        assert post.published_at is not None

    def test_change_status_invalid_transition(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        with pytest.raises(
            ValidationError, match="Cannot transition from draft to archived"
        ):
            post.change_status(Post.Status.ARCHIVED)

    def test_change_status_deleted_post(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)
        with pytest.raises(
            ValidationError, match="Cannot change status of a deleted post"
        ):
            post.change_status(Post.Status.DRAFT)

    def test_publish_flow(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        post.publish()
        post.refresh_from_db()
        assert post.status == Post.Status.PUBLISHED

    def test_publish_deleted_fails(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)
        with pytest.raises(ValidationError, match="Cannot publish a deleted post"):
            post.publish()

    def test_archive_flow(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        post.archive()
        post.refresh_from_db()
        assert post.status == Post.Status.ARCHIVED

    def test_soft_delete_and_restore(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        # Delete
        post.soft_delete()
        post.refresh_from_db()
        assert post.status == Post.Status.DELETED

        # Restore
        post.restore()
        post.refresh_from_db()
        assert post.status == Post.Status.DRAFT

    def test_restore_fails_for_non_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        with pytest.raises(ValidationError, match="Only deleted posts can be restored"):
            post.restore()


class TestPostQuerySet:
    def test_queryset_filtering(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.PUBLISHED)
        post_factory(status=Post.Status.DELETED)

        assert Post.objects.with_deleted().count() == 3
        assert Post.objects.only_deleted().count() == 1

    @pytest.mark.parametrize(
        "role, expected_count, description",
        [
            ("anonymous", 1, "Only published posts"),
            ("editor", 2, "Published + own draft"),
            ("admin", 3, "Published + Draft + Archived (excluding deleted)"),
        ],
        ids=("anonymous", "editor", "admin"),
    )
    def test_visible_for_roles(
        self,
        role,
        expected_count,
        description,
        post_factory,
        editor_factory,
        admin_factory,
    ):
        editor = editor_factory()
        admin = admin_factory()

        post_factory(status=Post.Status.PUBLISHED)
        post_factory(status=Post.Status.DRAFT, author=editor)
        post_factory(status=Post.Status.ARCHIVED)
        post_factory(status=Post.Status.DELETED)

        if role == "anonymous":
            user = AnonymousUser()
        elif role == "editor":
            user = editor
        else:
            user = admin

        visible_posts = Post.objects.visible_for(user)
        assert visible_posts.count() == expected_count, description

    def test_editor_cannot_see_others_drafts(self, post_factory, editor_factory):
        editor1 = editor_factory()
        editor2 = editor_factory()

        post_factory(status=Post.Status.DRAFT, author=editor2)
        visible = Post.objects.visible_for(editor1)
        assert visible.count() == 0


class TestPostValidations:
    def test_prevent_publish_from_invalid_states(self, post_factory):
        archived_post = post_factory(status=Post.Status.ARCHIVED)
        archived_post.status = Post.Status.PUBLISHED
        with pytest.raises(
            ValidationError, match="Cannot publish a post from archived status"
        ):
            archived_post.clean()

        deleted_post = post_factory(status=Post.Status.DELETED)
        deleted_post.status = Post.Status.PUBLISHED
        with pytest.raises(
            ValidationError, match="Cannot publish a post from deleted status"
        ):
            deleted_post.clean()
