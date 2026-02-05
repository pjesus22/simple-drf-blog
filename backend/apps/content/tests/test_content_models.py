import pytest
from apps.accounts.models import Editor
from apps.content.models import Category, Post, Tag

pytestmark = pytest.mark.django_db


class TestCategoryModel:
    def test_category_str_returns_name(self):
        category = Category(name="Test Category")
        assert str(category) == "Test Category"

    def test_category_clean_generates_slug(self):
        category = Category(name="Test Category")
        category.clean()
        assert category.slug == "test-category"

    def test_category_clean_preserves_existing_slug(self):
        category = Category(name="Test Category", slug="test-category")
        category.clean()
        assert category.slug == "test-category"

    def test_save_category(self):
        category = Category(name="Test Category", description="A test category")
        category.save()
        assert category.id is not None


class TestTagModel:
    def test_tag_str_returns_name(self):
        tag = Tag(name="Test Tag")
        assert str(tag) == "Test Tag"

    def test_tag_clean_generates_slug(self):
        tag = Tag(name="Test Tag")
        tag.clean()
        assert tag.slug == "test-tag"

    def test_tag_clean_preserves_existing_slug(self):
        tag = Tag(name="Test Tag", slug="test-tag")
        tag.clean()
        assert tag.slug == "test-tag"

    def test_save_tag(self):
        tag = Tag(name="Test Tag")
        tag.save()
        assert tag.id is not None


class TestPostModel:
    def test_post_str_returns_title(self):
        post = Post(title="Test Post")
        assert str(post) == "Test Post"

    def test_post_clean_generates_slug(self):
        post = Post(title="Test Post")
        post.clean()
        assert post.slug == "test-post"

    def test_post_clean_preserves_existing_slug(self):
        post = Post(title="Test Post", slug="test-post")
        post.clean()
        assert post.slug == "test-post"

    def test_post_clean_sets_published_at(self):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        post.clean()
        assert post.published_at is not None

    def test_post_published_at_not_updated_on_republish(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()

        # Must go back to draft first, then republish
        post.status = Post.Status.DRAFT
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
    def test_post_published_at_not_set_for_non_published_status(self, status):
        post = Post(title="Test Post", status=status)
        post.clean()
        assert post.published_at is None

    def test_save_post(self):
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
        assert post.is_published is True
        assert post.is_draft is False
        assert post.is_archived is False
        assert post.is_deleted is False

    @pytest.mark.parametrize(
        "initial_status, final_status",
        [
            (Post.Status.DRAFT, Post.Status.PUBLISHED),
            (Post.Status.PUBLISHED, Post.Status.ARCHIVED),
            (Post.Status.PUBLISHED, Post.Status.DELETED),
        ],
        ids=["first_publish", "archive", "delete"],
    )
    def test_post_status_transitions(self, initial_status, final_status, post_factory):
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
        else:
            assert post.published_at == original_published_at

    def test_post_republish_preserves_published_at(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()

        # Must go back to draft first, then republish
        post.status = Post.Status.DRAFT
        post.save()

        post.status = Post.Status.PUBLISHED
        post.save()

        assert post.published_at == original_published_at

    def test_post_add_tags(self, post_factory, tag_factory):
        post = post_factory()
        tags = tag_factory.create_batch(size=2)

        post.tags.add(*tags)

        assert post.tags.count() == 2

    def test_post_add_attachments(self, post_factory, upload_factory, clean_media):
        post = post_factory()
        attachments = upload_factory.create_batch(size=2)

        post.attachments.add(*attachments)

        assert post.attachments.count() == 2

    def test_post_add_thumbnail(self, post_factory, upload_factory, clean_media):
        post = post_factory()
        thumbnail = upload_factory(purpose="thumbnail")

        post.thumbnail = thumbnail
        post.save()

        assert post.thumbnail == thumbnail
        assert post.thumbnail.purpose == "thumbnail"

    def test_post_add_thumbnail_deletion_sets_null(
        self, post_factory, upload_factory, clean_media
    ):
        post = post_factory()
        thumbnail = upload_factory()

        post.thumbnail = thumbnail
        post.save()

        thumbnail.delete()

        post.refresh_from_db()
        assert post.thumbnail is None
        assert Post.objects.filter(id=post.id).exists()


class TestPostChangeStatus:
    def test_change_status_from_draft_to_published(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        assert post.published_at is None

        post.change_status(Post.Status.PUBLISHED)

        post.refresh_from_db()
        assert post.status == Post.Status.PUBLISHED
        assert post.published_at is not None

    def test_change_status_from_published_to_archived(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.change_status(Post.Status.ARCHIVED)

        post.refresh_from_db()
        assert post.status == Post.Status.ARCHIVED
        assert post.published_at == original_published_at

    def test_change_status_from_archived_to_draft(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.status = Post.Status.ARCHIVED
        post.save()

        post.change_status(Post.Status.DRAFT)

        post.refresh_from_db()
        assert post.status == Post.Status.DRAFT
        assert post.published_at == original_published_at

    def test_change_status_raises_error_when_post_is_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)

        from django.core.exceptions import ValidationError

        with pytest.raises(
            ValidationError, match="Cannot change status of a deleted post"
        ):
            post.change_status(Post.Status.DRAFT)

    def test_change_status_updates_fields(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        original_updated_at = post.updated_at

        post.change_status(Post.Status.PUBLISHED)

        post.refresh_from_db()
        assert post.updated_at > original_updated_at

    def test_change_status_invalid_transition_raises_error(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        from django.core.exceptions import ValidationError

        with pytest.raises(
            ValidationError, match="Cannot transition from draft to archived"
        ):
            post.change_status(Post.Status.ARCHIVED)

    def test_change_status_invalid_status_raises_error(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid status"):
            post.change_status("invalid_status")


class TestPostPublishArchive:
    def test_publish_from_draft(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        assert post.published_at is None

        post.publish()

        post.refresh_from_db()
        assert post.status == Post.Status.PUBLISHED
        assert post.published_at is not None

    def test_publish_deleted_post_raises_error(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Cannot publish a deleted post"):
            post.publish()

    def test_archive_from_published(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        original_published_at = post.published_at

        post.archive()

        post.refresh_from_db()
        assert post.status == Post.Status.ARCHIVED
        assert post.published_at == original_published_at

    def test_archive_deleted_post_raises_error(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Cannot archive a deleted post"):
            post.archive()


class TestPostSoftDelete:
    def test_soft_delete_changes_status_to_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        post.soft_delete()

        post.refresh_from_db()
        assert post.status == Post.Status.DELETED

    def test_soft_delete_from_published_post(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)
        published_at = post.published_at

        post.soft_delete()

        post.refresh_from_db()
        assert post.status == Post.Status.DELETED
        assert post.published_at == published_at

    def test_soft_delete_raises_error_when_already_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="This post is already deleted"):
            post.soft_delete()

    def test_soft_delete_updates_timestamp(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        original_updated_at = post.updated_at

        post.soft_delete()

        post.refresh_from_db()
        assert post.updated_at > original_updated_at


class TestPostRestore:
    def test_restore_to_draft_from_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)

        post.restore()

        post.refresh_from_db()
        assert post.status == Post.Status.DRAFT

    def test_restore_raises_error_when_not_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Only deleted posts can be restored"):
            post.restore()

    def test_restore_from_published_raises_error(self, post_factory):
        post = post_factory(status=Post.Status.PUBLISHED)

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Only deleted posts can be restored"):
            post.restore()

    def test_restore_updates_timestamp(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)
        original_updated_at = post.updated_at

        post.restore()

        post.refresh_from_db()
        assert post.updated_at > original_updated_at


class TestPostQueryset:
    def test_with_deleted_returns_all_posts(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.PUBLISHED)
        post_factory(status=Post.Status.DELETED)

        posts = Post.objects.with_deleted()

        assert posts.count() == 3

    def test_only_deleted_returns_deleted_posts(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.PUBLISHED)
        deleted_post = post_factory(status=Post.Status.DELETED)

        posts = Post.objects.only_deleted()

        assert posts.count() == 1
        assert posts.first() == deleted_post

    def test_visible_for_unauthenticated_excludes_deleted(
        self, post_factory, django_user_model
    ):
        from django.contrib.auth.models import AnonymousUser

        post_factory(status=Post.Status.PUBLISHED)
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.DELETED)

        user = AnonymousUser()
        posts = Post.objects.visible_for(user)

        assert posts.count() == 1
        assert posts.first().status == Post.Status.PUBLISHED

    def test_visible_for_editor_excludes_deleted(self, post_factory, editor_factory):
        editor = editor_factory()
        post_factory(status=Post.Status.PUBLISHED, author=editor)
        post_factory(status=Post.Status.DRAFT, author=editor)
        post_factory(status=Post.Status.DELETED, author=editor)

        posts = Post.objects.visible_for(editor)

        assert posts.count() == 2
        assert all(post.status != Post.Status.DELETED for post in posts)

    def test_visible_for_admin_excludes_deleted(self, post_factory, django_user_model):
        admin = django_user_model.objects.create_user(
            username="admin", email="admin@example.com", role="admin"
        )
        post_factory(status=Post.Status.PUBLISHED)
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.ARCHIVED)
        post_factory(status=Post.Status.DELETED)

        posts = Post.objects.visible_for(admin)

        assert posts.count() == 3
        assert all(post.status != Post.Status.DELETED for post in posts)

    def test_visible_for_editor_sees_own_drafts(self, post_factory, editor_factory):
        editor1 = editor_factory()
        editor2 = editor_factory()

        post_factory(status=Post.Status.PUBLISHED, author=editor1)
        own_draft = post_factory(status=Post.Status.DRAFT, author=editor1)
        post_factory(status=Post.Status.DRAFT, author=editor2)

        posts = Post.objects.visible_for(editor1)

        assert posts.count() == 2
        assert own_draft in posts
