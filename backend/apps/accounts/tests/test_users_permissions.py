import pytest
from apps.accounts.permissions import (
    CanChangeUserRole,
    CanCreateUpload,
    CanDeleteUpload,
    CanViewUser,
    HasMinRole,
    IsAdmin,
    IsEditor,
    IsOwner,
)


@pytest.mark.django_db
class TestHasMinRole:
    def test_unauthenticated_user_denied(self, rf, mocker):
        request = rf.get("/")
        request.user = mocker.Mock(is_authenticated=False)
        permission = HasMinRole()

        allowed = permission.has_permission(request, None)

        assert allowed is False

    def test_no_min_role_granted_to_authenticated(self, rf, default_user_factory):
        user = default_user_factory()
        request = rf.get("/")
        request.user = user
        permission = HasMinRole()

        allowed = permission.has_permission(request, None)

        assert allowed is True

    def test_editor_role_granted_access(self, rf, editor_factory):
        user = editor_factory()
        request = rf.get("/")
        request.user = user
        permission = IsEditor()

        allowed = permission.has_permission(request, None)

        assert allowed is True

    def test_admin_role_granted_access_to_editor_required(self, rf, admin_factory):
        user = admin_factory()
        request = rf.get("/")
        request.user = user
        permission = IsEditor()

        allowed = permission.has_permission(request, None)

        assert allowed is True

    def test_regular_user_denied_editor_required(self, rf, default_user_factory):
        user = default_user_factory(role="viewer")
        request = rf.get("/")
        request.user = user
        permission = IsEditor()

        allowed = permission.has_permission(request, None)

        assert allowed is False

    def test_admin_role_granted_access_to_admin_required(self, rf, admin_factory):
        user = admin_factory()
        request = rf.get("/")
        request.user = user
        permission = IsAdmin()

        allowed = permission.has_permission(request, None)

        assert allowed is True

    def test_editor_denied_admin_required(self, rf, editor_factory):
        user = editor_factory()
        request = rf.get("/")
        request.user = user
        permission = IsAdmin()

        allowed = permission.has_permission(request, None)

        assert allowed is False


@pytest.mark.django_db
class TestIsOwner:
    def test_admin_granted_permission(self, rf, admin_factory, default_user_factory):
        admin = admin_factory()
        user = default_user_factory(role="")
        request = rf.get("/")
        request.user = admin
        permission = IsOwner()

        allowed = permission.has_object_permission(request, None, user)

        assert allowed is True

    def test_user_self_granted_permission(self, rf, default_user_factory):
        user = default_user_factory()
        request = rf.get("/")
        request.user = user
        permission = IsOwner()

        allowed = permission.has_object_permission(request, None, user)

        assert allowed is True

    def test_other_user_denied_permission(self, rf, default_user_factory):
        user = default_user_factory(role="viewer")
        other_user = default_user_factory(role="viewer")
        request = rf.get("/")
        request.user = user
        permission = IsOwner()

        allowed = permission.has_object_permission(request, None, other_user)

        assert allowed is False

    @pytest.mark.parametrize("field", ["user", "owner", "author", "uploaded_by"])
    def test_ownership_fields_granted_permission(
        self, rf, default_user_factory, field, mocker
    ):
        user = default_user_factory()
        request = rf.get("/")
        request.user = user
        permission = IsOwner()
        obj = mocker.Mock()
        setattr(obj, field, user)

        allowed = permission.has_object_permission(request, None, obj)

        assert allowed is True

    def test_non_owner_denied_permission(self, rf, default_user_factory, mocker):
        user = default_user_factory(role="viewer")
        other_user = default_user_factory(role="viewer")
        request = rf.get("/")
        request.user = user
        permission = IsOwner()
        obj = mocker.Mock()
        obj.user = other_user

        allowed = permission.has_object_permission(request, None, obj)

        assert allowed is False

    def test_has_permission_authenticated(self, rf, default_user_factory):
        user = default_user_factory()
        request = rf.get("/")
        request.user = user
        permission = IsOwner()

        allowed = permission.has_permission(request, None)

        assert allowed is True

    def test_has_permission_unauthenticated(self, rf, mocker):
        request = rf.get("/")
        request.user = mocker.Mock(is_authenticated=False)
        permission = IsOwner()

        allowed = permission.has_permission(request, None)

        assert allowed is False


@pytest.mark.django_db
class TestUserPermissions:
    def test_can_change_user_role_only_admin_has_permission(
        self, rf, admin_factory, editor_factory
    ):
        admin = admin_factory()
        editor = editor_factory()
        permission = CanChangeUserRole()

        request_admin = rf.get("/")
        request_admin.user = admin

        request_editor = rf.get("/")
        request_editor.user = editor

        admin_allowed = permission.has_permission(request_admin, None)
        editor_allowed = permission.has_permission(request_editor, None)

        assert admin_allowed is True
        assert editor_allowed is False

    def test_can_change_user_role_only_admin_can_change_other(
        self, rf, admin_factory, editor_factory, default_user_factory
    ):
        admin = admin_factory()
        user = default_user_factory()
        permission = CanChangeUserRole()

        request_admin = rf.get("/")
        request_admin.user = admin

        allowed = permission.has_object_permission(request_admin, None, user)

        assert allowed is True

    def test_can_change_user_role_admin_cannot_change_self(self, rf, admin_factory):
        admin = admin_factory()
        permission = CanChangeUserRole()

        request_admin = rf.get("/")
        request_admin.user = admin

        allowed = permission.has_object_permission(request_admin, None, admin)

        assert allowed is False

    def test_can_change_user_role_non_user_object_denied(
        self, rf, admin_factory, mocker
    ):
        admin = admin_factory()
        permission = CanChangeUserRole()
        request = rf.get("/")
        request.user = admin
        obj = mocker.Mock()  # Not a User instance

        allowed = permission.has_object_permission(request, None, obj)

        assert allowed is False


@pytest.mark.django_db
class TestUploadPermissions:
    def test_can_create_upload_only_editor_or_above(
        self, rf, admin_factory, editor_factory, default_user_factory
    ):
        admin = admin_factory()
        editor = editor_factory()
        user = default_user_factory(role="viewer")
        permission = CanCreateUpload()

        request_admin = rf.get("/")
        request_admin.user = admin

        request_editor = rf.get("/")
        request_editor.user = editor

        request_user = rf.get("/")
        request_user.user = user

        admin_allowed = permission.has_permission(request_admin, None)
        editor_allowed = permission.has_permission(request_editor, None)
        user_allowed = permission.has_permission(request_user, None)

        assert admin_allowed is True
        assert editor_allowed is True
        assert user_allowed is False

    def test_can_delete_upload_owner_or_admin(
        self, rf, admin_factory, editor_factory, default_user_factory, mocker
    ):
        admin = admin_factory()
        owner = editor_factory()
        other_editor = editor_factory()
        permission = CanDeleteUpload()
        upload = mocker.Mock()
        upload.uploaded_by = owner

        request_admin = rf.get("/")
        request_admin.user = admin

        request_owner = rf.get("/")
        request_owner.user = owner

        request_other = rf.get("/")
        request_other.user = other_editor

        admin_allowed = permission.has_object_permission(request_admin, None, upload)
        owner_allowed = permission.has_object_permission(request_owner, None, upload)
        other_allowed = permission.has_object_permission(request_other, None, upload)

        assert admin_allowed is True
        assert owner_allowed is True
        assert other_allowed is False


@pytest.mark.django_db
class TestCanViewUser:
    def test_admin_can_view_any_user(self, rf, admin_factory, default_user_factory):
        admin = admin_factory()
        user = default_user_factory()
        permission = CanViewUser()
        request = rf.get("/")
        request.user = admin

        allowed = permission.has_object_permission(request, None, user)

        assert allowed is True

    def test_user_can_view_self(self, rf, default_user_factory):
        user = default_user_factory()
        permission = CanViewUser()
        request = rf.get("/")
        request.user = user

        allowed = permission.has_object_permission(request, None, user)

        assert allowed is True

    def test_user_cannot_view_other_user(self, rf, default_user_factory):
        user = default_user_factory(role="editor")
        other_user = default_user_factory()
        permission = CanViewUser()
        request = rf.get("/")
        request.user = user

        allowed = permission.has_object_permission(request, None, other_user)

        assert allowed is False
