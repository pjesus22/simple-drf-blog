import pytest
from apps.accounts.permissions import (
    CanChangeUserRole,
    CanViewUser,
    IsAdmin,
)
from apps.accounts.serializers import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from apps.accounts.views import UserViewSet
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated


@pytest.fixture
def viewset(mocker):
    viewset = UserViewSet()
    viewset.request = mocker.Mock()
    viewset.format_kwarg = None
    return viewset


pytestmark = pytest.mark.django_db


class TestUserViewSetSerializerClass:
    def test_get_serializer_class_create_returns_create_serializer(self, viewset):
        viewset.action = "create"
        assert viewset.get_serializer_class() == UserCreateSerializer

    def test_get_serializer_class_list_returns_list_serializer(self, viewset):
        viewset.action = "list"
        assert viewset.get_serializer_class() == UserListSerializer

    def test_get_serializer_class_change_password_returns_password_update_serializer(
        self, viewset
    ):
        viewset.action = "change_password"
        assert viewset.get_serializer_class() == PasswordUpdateSerializer

    def test_get_serializer_class_force_password_change_returns_password_reset_serializer(
        self, viewset
    ):
        viewset.action = "force_password_change"
        assert viewset.get_serializer_class() == PasswordResetSerializer

    def test_get_serializer_class_change_role_returns_role_serializer(self, viewset):
        viewset.action = "change_role"
        assert viewset.get_serializer_class() == ChangeRoleSerializer

    def test_get_serializer_class_default_returns_detail_serializer(self, viewset):
        viewset.action = "retrieve"
        assert viewset.get_serializer_class() == UserDetailSerializer


class TestUserViewSetPermissions:
    @pytest.mark.parametrize(
        "action, expected_permissions",
        [
            ("list", [IsAdmin]),
            ("retrieve", [CanViewUser]),
            ("create", [IsAdmin]),
            ("update", [IsAdmin]),
            ("partial_update", [IsAdmin]),
            ("destroy", [IsAdmin]),
            ("me", [IsAuthenticated]),
            ("change_password", [IsAuthenticated]),
            ("force_password_change", [IsAdmin]),
            ("change_role", [CanChangeUserRole]),
        ],
    )
    def test_get_permissions_returns_correct_classes(
        self, viewset, action, expected_permissions
    ):
        viewset.action = action
        permissions = viewset.get_permissions()

        assert len(permissions) == len(expected_permissions)
        for actual, expected in zip(permissions, expected_permissions):
            assert isinstance(actual, expected)


class TestUserViewSetActions:
    def test_me_get_returns_user_data(self, viewset, mocker):
        viewset.action = "me"
        user = mocker.Mock()
        viewset.request.user = user
        viewset.request.method = "GET"
        mock_serializer = mocker.Mock(data={"id": 1, "username": "testuser"})
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.me(viewset.request)

        assert response.status_code == 200
        assert response.data == {"id": 1, "username": "testuser"}
        viewset.get_serializer.assert_called_once_with(user)

    def test_me_patch_updates_user(self, viewset, mocker):
        viewset.action = "me"
        user = mocker.Mock()
        viewset.request.user = user
        viewset.request.method = "PATCH"
        viewset.request.data = {"username": "newname"}
        mock_serializer = mocker.Mock(data={"id": 1, "username": "newname"})
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.me(viewset.request)

        assert response.status_code == 200
        assert response.data == {"id": 1, "username": "newname"}
        viewset.get_serializer.assert_called_once_with(
            user, data=viewset.request.data, partial=True
        )
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    def test_change_role_success(self, viewset, mocker):
        viewset.action = "change_role"
        target_user = mocker.Mock(role="editor")
        target_user.id = 2

        now = timezone.now()
        target_user.date_joined = now
        target_user.last_login = now
        target_user.profile = None
        mocker.patch.object(viewset, "get_object", return_value=target_user)
        viewset.request.data = {"role": "admin"}
        viewset.request.user = mocker.Mock(role="admin")

        mock_serializer = mocker.Mock()
        mock_serializer.validated_data = {"role": "admin"}
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.change_role(viewset.request, pk=2)

        assert response.status_code == 200
        assert target_user.role == "admin"
        target_user.save.assert_called_once_with(update_fields=["role"])

    def test_change_role_last_admin_demotion_raises_error(self, viewset, mocker):
        viewset.action = "change_role"
        user = mocker.Mock(role="admin")
        mocker.patch.object(viewset, "get_object", return_value=user)
        viewset.request.user = user
        viewset.request.data = {"role": "editor"}

        mock_serializer = mocker.Mock()
        mock_serializer.validated_data = {"role": "editor"}
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        from apps.accounts.exceptions import CannotDemoteLastAdmin

        mocker.patch(
            "apps.accounts.views.users.change_user_role",
            side_effect=CannotDemoteLastAdmin(),
        )

        with pytest.raises(ValidationError) as excinfo:
            viewset.change_role(viewset.request, pk=1)

        assert (
            excinfo.value.detail["role"]
            == "You cannot demote yourself if you are the last administrator."
        )

    def test_change_password_success(self, viewset, mocker):
        viewset.action = "change_password"
        user = mocker.Mock()
        user.check_password.return_value = True
        viewset.request.user = user

        validated_data = {"old_password": "old", "new_password": "new"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.change_password(viewset.request)

        assert response.status_code == 204
        user.set_password.assert_called_once_with("new")
        user.save.assert_called_once()

    def test_change_password_wrong_old_password_raises_error(self, viewset, mocker):
        viewset.action = "change_password"
        user = mocker.Mock()
        viewset.request.user = user

        validated_data = {"old_password": "wrong", "new_password": "new"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        from apps.accounts.exceptions import InvalidPassword

        mocker.patch(
            "apps.accounts.views.users.change_own_password",
            side_effect=InvalidPassword(),
        )

        with pytest.raises(ValidationError) as excinfo:
            viewset.change_password(viewset.request)

        assert excinfo.value.detail["old_password"] == "Invalid password"

    def test_reset_password_success(self, viewset, mocker):
        viewset.action = "force_password_change"
        user = mocker.Mock()
        mocker.patch.object(viewset, "get_object", return_value=user)

        validated_data = {"new_password": "new_secure_pass"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.force_password_change(viewset.request, pk=1)

        assert response.status_code == 204
        user.set_password.assert_called_once_with("new_secure_pass")
        user.save.assert_called_once()
