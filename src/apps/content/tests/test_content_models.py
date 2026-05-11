from itertools import product

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
import pytest

from apps.content.models import Category, Post, Tag

pytestmark = pytest.mark.django_db
POST_STATES = Post.Status.values
POST_TRANSITIONS = Post.ALLOWED_TRANSITIONS


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

        category.save()
        assert category.slug == expected_slug

    def test_category_save_preserves_existing_slug(self):
        category = Category(name="Test Category", slug="custom-slug")
        category.save()
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

        tag.save()
        assert tag.slug == expected_slug

    def test_tag_save_preserves_existing_slug(self):
        tag = Tag(name="Test Tag", slug="custom-tag-slug")
        tag.save()
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
        "status",
        [Post.Status.DRAFT, Post.Status.ARCHIVED, Post.Status.DELETED],
        ids=("draft", "archived", "deleted"),
    )
    def test_post_published_at_not_set_for_non_published_status(self, status):
        post = Post(title="Test Post", status=status)
        post.clean()
        assert post.published_at is None

    @pytest.mark.parametrize(
        "status, expected",
        [
            (
                Post.Status.DRAFT,
                {
                    "is_draft": True,
                    "is_published": False,
                    "is_archived": False,
                    "is_deleted": False,
                },
            ),
            (
                Post.Status.PUBLISHED,
                {
                    "is_draft": False,
                    "is_published": True,
                    "is_archived": False,
                    "is_deleted": False,
                },
            ),
            (
                Post.Status.ARCHIVED,
                {
                    "is_draft": False,
                    "is_published": False,
                    "is_archived": True,
                    "is_deleted": False,
                },
            ),
            (
                Post.Status.DELETED,
                {
                    "is_draft": False,
                    "is_published": False,
                    "is_archived": False,
                    "is_deleted": True,
                },
            ),
        ],
        ids=("draft", "published", "archived", "deleted"),
    )
    def test_status_properties(self, post_factory, status, expected):
        post = post_factory(status=status)

        assert post.is_draft is expected["is_draft"]
        assert post.is_published is expected["is_published"]
        assert post.is_archived is expected["is_archived"]
        assert post.is_deleted is expected["is_deleted"]

    def test_save_post(self, post_factory):
        post = post_factory()
        assert post.id is not None
        assert Post.objects.filter(id=post.id).exists()

    @pytest.mark.parametrize(
        "initial_state,final_state",
        [(src, tgt) for src, tgts in POST_TRANSITIONS.items() for tgt in tgts],
        ids=lambda case: f"{case[0]}_to_{case[1]}"
        if isinstance(case, tuple)
        else str(case),
    )
    def test_allowed_transitions(self, post_factory, initial_state, final_state):
        post = post_factory(status=initial_state)

        post.transition_to(final_state)
        post.refresh_from_db()

        assert post.status == final_state

    @pytest.mark.parametrize(
        "initial_state, final_state",
        [
            (src, tgt)
            for src, tgt in product(POST_STATES, POST_STATES)
            if src != tgt and tgt not in POST_TRANSITIONS[src]
        ],
        ids=lambda case: f"{case[0]}_to_{case[1]}"
        if isinstance(case, tuple)
        else str(case),
    )
    def test_invalid_transitions_raises_error(
        self, post_factory, initial_state, final_state
    ):
        post = post_factory(status=initial_state)

        with pytest.raises(
            ValidationError,
            match=f"Cannot transition from {initial_state} to {final_state}",
        ):
            post.transition_to(final_state)
        post.refresh_from_db()
        assert post.status == initial_state

    @pytest.mark.parametrize("status", Post.Status.values)
    def test_transition_to_same_status_is_noop(self, post_factory, status):
        post = post_factory(status=status)
        original = post.published_at

        post.transition_to(status)

        post.refresh_from_db()
        assert post.status == status
        assert post.published_at == original

    def test_transition_raises_error_if_object_not_saved(self, post_factory):
        post = post_factory.build()
        with pytest.raises(
            ValidationError, match="Cannot transition an unsaved object\\."
        ):
            post.transition_to(Post.Status.PUBLISHED)

    def test_transition_to_raises_error_if_invalid_status(self, post_factory):
        post = post_factory()
        with pytest.raises(ValidationError, match="Invalid status: invalid"):
            post.transition_to("invalid")

    def test_full_status_cycle_preserves_publish_timestamp(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)

        post.publish()
        first_publish = post.published_at

        post.archive()
        assert post.status == Post.Status.ARCHIVED

        post.restore()
        assert post.status == Post.Status.DRAFT

        post.publish()
        post.refresh_from_db()

        assert post.status == Post.Status.PUBLISHED
        assert post.published_at == first_publish

        post.soft_delete()
        assert post.status == Post.Status.DELETED
        assert post.published_at == first_publish

    def test_soft_delete_raises_if_already_deleted(self, post_factory):
        post = post_factory(status=Post.Status.DELETED)
        with pytest.raises(ValidationError, match="This post is already deleted"):
            post.soft_delete()

    def test_restore_raises_if_not_deleted_or_archived(self, post_factory):
        post = post_factory(status=Post.Status.DRAFT)
        with pytest.raises(
            ValidationError, match="This post is not deleted or archived"
        ):
            post.restore()

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
