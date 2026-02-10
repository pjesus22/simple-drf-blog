import pytest
from apps.accounts.permissions import (
    CanChangeUserRole,
    CanViewUser,
    HasMinRole,
    IsAdmin,
    IsEditor,
    IsOwner,
)


@pytest.fixture
def auth_request(rf, mocker):
    def _make_request(user=None, is_authenticated=True):
        request = rf.get("/")
        if user:
            request.user = user
        else:
            request.user = mocker.Mock(is_authenticated=is_authenticated)
        return request

    return _make_request


@pytest.mark.django_db
class TestHasMinRole:
    def test_unauthenticated_user_denied(self, auth_request):
        request = auth_request(is_authenticated=False)
        permission = HasMinRole()
        assert permission.has_permission(request, None) is False

    @pytest.mark.parametrize(
        "permission_class, role, expected",
        [
            (HasMinRole, "viewer", True),
            (HasMinRole, "editor", True),
            (HasMinRole, "admin", True),
            (IsEditor, "viewer", False),
            (IsEditor, "editor", True),
            (IsEditor, "admin", True),
            (IsAdmin, "viewer", False),
            (IsAdmin, "editor", False),
            (IsAdmin, "admin", True),
        ],
        ids=(
            "has_min_role_viewer",
            "has_min_role_editor",
            "has_min_role_admin",
            "is_editor_viewer",
            "is_editor_editor",
            "is_editor_admin",
            "is_admin_viewer",
            "is_admin_editor",
            "is_admin_admin",
        ),
    )
    def test_role_based_permissions(
        self, auth_request, default_user_factory, permission_class, role, expected
    ):
        user = default_user_factory(role=role)
        request = auth_request(user=user)
        permission = permission_class()

        assert permission.has_permission(request, None) is expected


@pytest.mark.django_db
class TestIsOwner:
    @pytest.mark.parametrize(
        "user_role, is_owner, expected",
        [
            ("admin", False, True),
            ("editor", True, True),
            ("editor", False, False),
            ("viewer", True, True),
            ("viewer", False, False),
        ],
        ids=(
            "is_owner_admin_not_owner",
            "is_owner_editor_owner",
            "is_owner_editor_not_owner",
            "is_owner_viewer_owner",
            "is_owner_viewer_not_owner",
        ),
    )
    def test_object_ownership_permissions(
        self, auth_request, default_user_factory, user_role, is_owner, expected
    ):
        user = default_user_factory(role=user_role)
        owner_user = user if is_owner else default_user_factory()

        request = auth_request(user=user)
        permission = IsOwner()

        assert permission.has_object_permission(request, None, owner_user) is expected

    @pytest.mark.parametrize(
        "field",
        ["user", "owner", "author", "uploaded_by"],
        ids=("user", "owner", "author", "uploaded_by"),
    )
    def test_ownership_fields_granted_permission(
        self, auth_request, default_user_factory, field, mocker
    ):
        user = default_user_factory()
        request = auth_request(user=user)
        permission = IsOwner()
        obj = mocker.Mock()
        setattr(obj, field, user)

        assert permission.has_object_permission(request, None, obj) is True

    def test_has_permission_authenticated_logic(self, auth_request):
        request = auth_request(is_authenticated=True)
        permission = IsOwner()
        assert permission.has_permission(request, None) is True

        request_unauth = auth_request(is_authenticated=False)
        assert permission.has_permission(request_unauth, None) is False


@pytest.mark.django_db
class TestCanChangeUserRole:
    @pytest.mark.parametrize(
        "requester_role, expected",
        [("admin", True), ("editor", False), ("viewer", False)],
        ids=("admin", "editor", "viewer"),
    )
    def test_permission_only_for_admin(
        self, auth_request, default_user_factory, requester_role, expected
    ):
        user = default_user_factory(role=requester_role)
        request = auth_request(user=user)
        permission = CanChangeUserRole()

        assert permission.has_permission(request, None) is expected

    def test_admin_cannot_change_self(self, auth_request, admin_factory):
        admin = admin_factory()
        request = auth_request(user=admin)
        permission = CanChangeUserRole()

        assert permission.has_object_permission(request, None, admin) is False

    def test_admin_can_change_others(
        self, auth_request, admin_factory, default_user_factory
    ):
        admin = admin_factory()
        other_user = default_user_factory()
        request = auth_request(user=admin)
        permission = CanChangeUserRole()

        assert permission.has_object_permission(request, None, other_user) is True

    def test_non_user_object_denied(self, auth_request, admin_factory, mocker):
        admin = admin_factory()
        request = auth_request(user=admin)
        permission = CanChangeUserRole()
        obj = mocker.Mock()

        assert permission.has_object_permission(request, None, obj) is False


@pytest.mark.django_db
class TestCanViewUser:
    @pytest.mark.parametrize(
        "requester_role, is_self, expected",
        [
            ("admin", False, True),
            ("admin", True, True),
            ("editor", True, True),
            ("editor", False, False),
            ("viewer", True, True),
            ("viewer", False, False),
        ],
        ids=(
            "can_view_user_admin_not_self",
            "can_view_user_admin_self",
            "can_view_user_editor_self",
            "can_view_user_editor_not_self",
            "can_view_user_viewer_self",
            "can_view_user_viewer_not_self",
        ),
    )
    def test_view_user_permissions(
        self, auth_request, default_user_factory, requester_role, is_self, expected
    ):
        user = default_user_factory(role=requester_role)
        target_user = user if is_self else default_user_factory()

        request = auth_request(user=user)
        permission = CanViewUser()

        assert permission.has_object_permission(request, None, target_user) is expected
