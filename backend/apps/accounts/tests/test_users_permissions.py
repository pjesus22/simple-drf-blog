from unittest.mock import Mock

from apps.accounts.permissions import IsAdmin, IsEditor, IsOwner


class TestIsEditor:
    def test_iseditor_has_permission_returns_true_for_editor(self):
        user = Mock(role="editor", is_authenticated=True)
        request = Mock(user=user)
        view = Mock()
        permission = IsEditor()
        assert permission.has_permission(request, view)

    def test_iseditor_has_permission_returns_true_for_admin(self):
        user = Mock(role="admin", is_authenticated=True)
        request = Mock(user=user)
        view = Mock()
        permission = IsEditor()
        assert permission.has_permission(request, view)

    def test_iseditor_has_permission_method_returns_false_when_user_is_none(self):
        request = Mock(user=None)
        view = Mock()
        permission = IsEditor()
        assert not permission.has_permission(request, view)

    def test_iseditor_has_permission_returns_false_when_not_authenticated(self):
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        view = Mock()
        permission = IsEditor()
        assert not permission.has_permission(request, view)

    def test_iseditor_has_permission_returns_false_when_wrong_role(self):
        user = Mock(is_authenticated=True, role="viewer")
        request = Mock(user=user)
        view = Mock()
        permission = IsEditor()
        assert not permission.has_permission(request, view)


class TestIsAdmin:
    def test_isadmin_has_permission_returns_true_for_admin(self):
        user = Mock(role="admin", is_authenticated=True)
        request = Mock(user=user)
        view = Mock()
        permission = IsAdmin()
        assert permission.has_permission(request, view)

    def test_isadmin_has_permission_returns_false_when_user_is_none(self):
        request = Mock(user=None)
        view = Mock()
        permission = IsAdmin()
        assert not permission.has_permission(request, view)

    def test_isadmin_has_permission_returns_false_when_not_authenticated(self):
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        view = Mock()
        permission = IsAdmin()
        assert not permission.has_permission(request, view)

    def test_isadmin_has_permission_returns_false_for_non_admin(self):
        user = Mock(is_authenticated=True, role="editor")
        request = Mock(user=user)
        view = Mock()
        permission = IsAdmin()
        assert not permission.has_permission(request, view)


class TestIsOwner:
    def test_isowner_has_permission_returns_true_when_authenticated(self):
        user = Mock(is_authenticated=True)
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert permission.has_permission(request, view)

    def test_isowner_has_permission_returns_false_when_user_is_none(self):
        request = Mock(user=None)
        view = Mock()
        permission = IsOwner()
        assert not permission.has_permission(request, view)

    def test_isowner_has_permission_returns_false_when_not_authenticated(self):
        user = Mock(is_authenticated=False)
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert not permission.has_permission(request, view)

    def test_isowner_has_object_permission_returns_true_when_user_is_owner(
        self, db, editor_factory
    ):
        user = editor_factory()
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert permission.has_object_permission(request, view, user)

    def test_isowner_has_object_permission_returns_true_when_user_is_admin(
        self, db, editor_factory, admin_factory
    ):
        admin = admin_factory()
        other_user = editor_factory()
        request = Mock(user=admin)
        view = Mock()
        permission = IsOwner()
        assert permission.has_object_permission(request, view, other_user)

    def test_isowner_has_object_permission_returns_false_when_user_is_different(
        self, db, editor_factory
    ):
        user1 = editor_factory()
        user2 = editor_factory()
        request = Mock(user=user1)
        view = Mock()
        permission = IsOwner()
        assert not permission.has_object_permission(request, view, user2)

    def test_isowner_has_object_permission_returns_true_for_owned_object_with_user_attr(
        self, db, editor_factory
    ):
        user = editor_factory()
        obj = Mock(user=user)
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert permission.has_object_permission(request, view, obj)

    def test_isowner_has_object_permission_returns_true_for_owned_object_with_uploaded_by_attr(
        self, db, editor_factory
    ):
        user = editor_factory()
        obj = Mock(spec=["uploaded_by"], user=None, uploaded_by=user)
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert permission.has_object_permission(request, view, obj)

    def test_isowner_has_object_permission_returns_false_when_user_is_none(self):
        obj = Mock(user=Mock())
        request = Mock(user=None)
        view = Mock()
        permission = IsOwner()
        assert not permission.has_object_permission(request, view, obj)

    def test_isowner_has_object_permission_returns_false_when_not_authenticated(self):
        user = Mock(is_authenticated=False)
        obj = Mock(user=Mock())
        request = Mock(user=user)
        view = Mock()
        permission = IsOwner()
        assert not permission.has_object_permission(request, view, obj)
