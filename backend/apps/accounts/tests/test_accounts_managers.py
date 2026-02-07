import pytest
from apps.accounts.models import Profile
from django.contrib.auth.models import AnonymousUser

pytestmark = pytest.mark.django_db


class TestProfileQuerySet:
    def test_is_admin_returns_true_for_staff_user(self, admin_factory):
        """Test _is_admin returns True for staff users"""
        admin = admin_factory()
        qs = Profile.objects.all()
        assert qs._is_admin(admin) is True

    def test_is_admin_returns_false_for_regular_user(self, editor_factory):
        """Test _is_admin returns False for non-staff users"""
        editor = editor_factory()
        qs = Profile.objects.all()
        assert qs._is_admin(editor) is False

    def test_is_admin_returns_false_for_anonymous_user(self):
        """Test _is_admin returns False for anonymous users"""
        user = AnonymousUser()
        qs = Profile.objects.all()
        assert qs._is_admin(user) is False

    def test_visible_for_admin_returns_all_profiles(
        self, admin_factory, profile_factory
    ):
        """Test visible_for returns all profiles for admin users"""
        admin = admin_factory()
        profile_factory(is_public=True)
        profile_factory(is_public=False)

        profiles = Profile.objects.visible_for(admin)
        assert profiles.count() == 2

    def test_visible_for_authenticated_user_returns_public_and_own(
        self, editor_factory, profile_factory
    ):
        """Test visible_for returns public profiles and user's own profile"""
        editor = editor_factory()
        # Explicitly create profile for editor (signal doesn't run in tests)
        profile_factory(user=editor, is_public=True)
        profile_factory(is_public=True)  # Another public profile
        profile_factory(is_public=False)  # Private profile (not visible)

        profiles = Profile.objects.visible_for(editor)
        # Should see: editor's own profile (public) + the other public profile = 2
        assert profiles.count() == 2

    def test_visible_for_anonymous_returns_only_public(self, profile_factory):
        """Test visible_for returns only public profiles for anonymous users"""
        user = AnonymousUser()
        profile_factory(is_public=True)
        profile_factory(is_public=False)

        profiles = Profile.objects.visible_for(user)
        assert profiles.count() == 1

    def test_editable_by_admin_returns_all_profiles(
        self, admin_factory, profile_factory
    ):
        """Test editable_by returns all profiles for admin users"""
        admin = admin_factory()
        profile_factory()
        profile_factory()

        profiles = Profile.objects.editable_by(admin)
        assert profiles.count() == 2

    def test_editable_by_authenticated_user_returns_own_only(
        self, editor_factory, profile_factory
    ):
        """Test editable_by returns only user's own profile"""
        editor = editor_factory()
        # Explicitly create profile for editor (signal doesn't run in tests)
        profile_factory(user=editor)
        profile_factory()  # Another editor's profile (not editable by first editor)

        profiles = Profile.objects.editable_by(editor)
        assert profiles.count() == 1
        assert profiles.first().user == editor

    def test_editable_by_anonymous_returns_none(self, profile_factory):
        """Test editable_by returns empty queryset for anonymous users"""
        user = AnonymousUser()
        profile_factory()

        profiles = Profile.objects.editable_by(user)
        assert profiles.count() == 0

    def test_me_authenticated_returns_user_profile(
        self, editor_factory, profile_factory
    ):
        """Test me returns authenticated user's profile"""
        editor = editor_factory()
        # Explicitly create profile for editor (signal doesn't run in tests)
        profile_factory(user=editor)

        profiles = Profile.objects.me(editor)
        assert profiles.count() == 1
        assert profiles.first().user == editor

    def test_me_anonymous_returns_none(self):
        """Test me returns empty queryset for anonymous users"""
        user = AnonymousUser()

        profiles = Profile.objects.me(user)
        assert profiles.count() == 0


class TestProfileManager:
    def test_visible_for_delegates_to_queryset(self, editor_factory, profile_factory):
        """Test visible_for manager method delegates to queryset"""
        editor = editor_factory()
        profile_factory(is_public=True)

        profiles = Profile.objects.visible_for(editor)
        assert profiles.count() >= 1

    def test_editable_by_delegates_to_queryset(self, editor_factory, profile_factory):
        """Test editable_by manager method delegates to queryset"""
        editor = editor_factory()
        # Explicitly create profile for editor (signal doesn't run in tests)
        profile_factory(user=editor)

        profiles = Profile.objects.editable_by(editor)
        assert profiles.count() == 1

    def test_me_delegates_to_queryset(self, editor_factory, profile_factory):
        """Test me manager method delegates to queryset"""
        editor = editor_factory()
        # Explicitly create profile for editor (signal doesn't run in tests)
        profile_factory(user=editor)

        profiles = Profile.objects.me(editor)
        assert profiles.count() == 1
