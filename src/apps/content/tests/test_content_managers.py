from django.contrib.auth.models import AnonymousUser
import pytest

from apps.content.models import Post

pytestmark = pytest.mark.django_db


class TestPostQueryset:
    def test_alive_excludes_deleted(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.DELETED)

        assert Post.objects.with_deleted().alive().count() == 1

    def test_deleted_returns_only_deleted(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        deleted = post_factory(status=Post.Status.DELETED)

        qs = Post.objects.with_deleted().deleted()

        assert qs.count() == 1
        assert qs.first() == deleted

    @pytest.mark.parametrize(
        "role, expected_count",
        [("anonymous", 1), ("editor", 2), ("admin", 3)],
        ids=("anon", "editor", "admin"),
    )
    def test_visible_for_roles(
        self, role, expected_count, post_factory, editor_factory, admin_factory
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

        assert Post.objects.visible_for(user).count() == expected_count

    def test_editor_cannot_see_others_drafts(self, post_factory, editor_factory):
        editor1 = editor_factory()
        editor2 = editor_factory()
        post_factory(status=Post.Status.DRAFT, author=editor2)

        assert Post.objects.visible_for(editor1).count() == 0

    def test_owned_by_filters_to_author(self, post_factory, editor_factory):
        editor = editor_factory()
        post_factory(author=editor, status=Post.Status.DRAFT)
        post_factory(status=Post.Status.PUBLISHED)

        mine = Post.objects.owned_by(editor)

        assert mine.count() == 1
        assert mine.first().author == editor


class TestPostManager:
    def test_get_queryset_excludes_deleted(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.DELETED)

        assert Post.objects.count() == 1

    def test_with_deleted_returns_all(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        post_factory(status=Post.Status.DELETED)

        assert Post.objects.with_deleted().count() == 2

    def test_only_deleted_returns_deleted(self, post_factory):
        post_factory(status=Post.Status.DRAFT)
        deleted = post_factory(status=Post.Status.DELETED)

        qs = Post.objects.only_deleted()

        assert qs.count() == 1
        assert qs.first() == deleted

    @pytest.mark.parametrize("method_name", ["visible_for", "owned_by"])
    def test_manager_delegates_to_queryset_methods(
        self, method_name, post_factory, editor_factory
    ):
        editor = editor_factory()
        post_factory(author=editor, status=Post.Status.PUBLISHED)

        manager_method = getattr(Post.objects, method_name)
        qs_method = getattr(Post.objects.all(), method_name)

        assert manager_method(editor).count() == qs_method(editor).count()
