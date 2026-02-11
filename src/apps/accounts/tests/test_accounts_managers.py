from django.contrib.auth.models import AnonymousUser
import pytest

from apps.accounts.models import Profile

pytestmark = pytest.mark.django_db


class TestProfileQuerySet:
    @pytest.mark.parametrize(
        "user_fixture, expected",
        [
            ("admin_factory", True),
            ("editor_factory", False),
            (lambda: AnonymousUser(), False),
        ],
        ids=("admin", "editor", "anonymous"),
    )
    def test_is_admin_detects_user_permissions(self, request, user_fixture, expected):
        user = (
            request.getfixturevalue(user_fixture)()
            if isinstance(user_fixture, str)
            else user_fixture()
        )
        qs = Profile.objects.all()
        assert qs._is_admin(user) is expected

    @pytest.mark.parametrize(
        "user_fixture, expected_count",
        [
            ("admin_factory", 2),
            ("editor_factory", 2),
            (lambda: AnonymousUser(), 1),
        ],
        ids=("admin", "editor", "anonymous"),
    )
    def test_visible_for_filters_by_user_visibility(
        self, request, user_fixture, expected_count, profile_factory
    ):
        user = (
            request.getfixturevalue(user_fixture)()
            if isinstance(user_fixture, str)
            else user_fixture()
        )

        profile_factory(is_public=True)
        profile_factory(is_public=False)

        if user.is_authenticated and not user.is_staff:
            Profile.objects.filter(is_public=False).update(user=user)

        profiles = Profile.objects.visible_for(user)
        assert profiles.count() == expected_count

    @pytest.mark.parametrize(
        "user_fixture, expected_count",
        [
            ("admin_factory", 2),
            ("editor_factory", 1),
            (lambda: AnonymousUser(), 0),
        ],
        ids=("admin", "editor", "anonymous"),
    )
    def test_editable_by_filters_by_edit_permissions(
        self, request, user_fixture, expected_count, profile_factory
    ):
        user = (
            request.getfixturevalue(user_fixture)()
            if isinstance(user_fixture, str)
            else user_fixture()
        )

        p1 = profile_factory()
        profile_factory()

        if user.is_authenticated and not user.is_staff:
            p1.user = user
            p1.save()

        profiles = Profile.objects.editable_by(user)
        assert profiles.count() == expected_count
        if expected_count == 1 and not user.is_staff:
            assert profiles.first().user == user

    @pytest.mark.parametrize(
        "user_fixture, expected_count",
        [
            ("editor_factory", 1),
            (lambda: AnonymousUser(), 0),
        ],
        ids=("editor", "anonymous"),
    )
    def test_me_returns_users_own_profile(
        self, request, user_fixture, expected_count, profile_factory
    ):
        user = (
            request.getfixturevalue(user_fixture)()
            if isinstance(user_fixture, str)
            else user_fixture()
        )

        if user.is_authenticated:
            profile_factory(user=user)

        profiles = Profile.objects.me(user)
        assert profiles.count() == expected_count
        if expected_count == 1:
            assert profiles.first().user == user


class TestProfileManager:
    @pytest.mark.parametrize(
        "method_name",
        ["visible_for", "editable_by", "me"],
        ids=("visible_for", "editable_by", "me"),
    )
    def test_manager_delegates_to_queryset_methods(
        self, method_name, editor_factory, profile_factory
    ):
        editor = editor_factory()
        profile_factory(user=editor, is_public=True)

        manager_method = getattr(Profile.objects, method_name)
        qs_method = getattr(Profile.objects.all(), method_name)

        assert manager_method(editor).count() == qs_method(editor).count()
