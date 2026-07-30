from django.contrib.auth.models import AnonymousUser
import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.accounts.exceptions import CannotDemoteLastAdmin, InvalidPassword
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
from config.throttle import PasswordChangeThrottle, UserReadThrottle, WriteThrottle


@pytest.fixture
def viewset(mocker):
    viewset = UserViewSet()
    viewset.request = mocker.Mock()
    viewset.format_kwarg = None
    return viewset


pytestmark = pytest.mark.django_db


class TestUserViewSetSerializerClass:
    @pytest.mark.parametrize(
        "action, expected_serializer",
        [
            ("create", UserCreateSerializer),
            ("list", UserListSerializer),
            ("change_password", PasswordUpdateSerializer),
            ("force_password_change", PasswordResetSerializer),
            ("change_role", ChangeRoleSerializer),
            ("retrieve", UserDetailSerializer),
            ("update", UserDetailSerializer),
            ("partial_update", UserDetailSerializer),
        ],
    )
    def test_get_serializer_class_for_actions(
        self, viewset, action, expected_serializer
    ):
        viewset.action = action
        assert viewset.get_serializer_class() == expected_serializer


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
    def test_me_get_returns_user_data(self, viewset, mocker, default_user_factory):
        user = default_user_factory()
        viewset.action = "me"
        viewset.request.user = user
        viewset.request.method = "GET"

        expected_data = {"id": user.id, "username": user.username}
        mock_serializer = mocker.Mock(data=expected_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.me(viewset.request)

        assert response.status_code == 200
        assert response.data == expected_data
        viewset.get_serializer.assert_called_once_with(user)

    def test_me_patch_updates_user(self, viewset, mocker, default_user_factory):
        user = default_user_factory()
        viewset.action = "me"
        viewset.request.user = user
        viewset.request.method = "PATCH"
        viewset.request.data = {"username": "newname"}

        expected_data = {"id": user.id, "username": "newname"}
        mock_serializer = mocker.Mock(data=expected_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.me(viewset.request)

        assert response.status_code == 200
        assert response.data == expected_data
        viewset.get_serializer.assert_called_once_with(
            user, data=viewset.request.data, partial=True
        )
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    def test_change_role_success(self, viewset, mocker, editor_factory, admin_factory):
        actor = admin_factory()
        target_user = editor_factory()

        viewset.action = "change_role"
        viewset.request.user = actor
        viewset.request.data = {"role": "admin"}

        mocker.patch.object(viewset, "get_object", return_value=target_user)

        mock_change_role = mocker.patch("apps.accounts.views.users.change_user_role")

        mock_serializer = mocker.Mock()
        mock_serializer.validated_data = {"role": "admin"}
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        response = viewset.change_role(viewset.request, pk=target_user.pk)
        assert response.status_code == 200

        mock_change_role.assert_called_once_with(
            actor=actor, target_user=target_user, new_role="admin"
        )
        assert "id" in response.data
        assert response.data["id"] == target_user.id

    def test_change_role_last_admin_demotion_raises_error(
        self, viewset, mocker, admin_factory
    ):
        user = admin_factory()
        viewset.action = "change_role"
        viewset.request.user = user
        viewset.request.data = {"role": "editor"}

        mocker.patch.object(viewset, "get_object", return_value=user)

        mock_serializer = mocker.Mock()
        mock_serializer.validated_data = {"role": "editor"}
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        error_msg = "You cannot demote yourself if you are the last administrator."
        mocker.patch(
            "apps.accounts.views.users.change_user_role",
            side_effect=CannotDemoteLastAdmin(error_msg),
        )

        with pytest.raises(ValidationError) as excinfo:
            viewset.change_role(viewset.request, pk=user.pk)

        assert excinfo.value.detail["role"] == error_msg

    def test_change_password_success(self, viewset, mocker, default_user_factory):
        user = default_user_factory()
        viewset.action = "change_password"
        viewset.request.user = user

        validated_data = {"old_password": "old", "new_password": "new"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        mock_change_password = mocker.patch(
            "apps.accounts.views.users.change_own_password"
        )

        response = viewset.change_password(viewset.request)

        assert response.status_code == 204
        mock_change_password.assert_called_once_with(
            user=user,
            old_password="old",
            new_password="new",
        )

    def test_change_password_wrong_old_password_raises_error(
        self, viewset, mocker, default_user_factory
    ):
        user = default_user_factory()
        viewset.action = "change_password"
        viewset.request.user = user

        validated_data = {"old_password": "wrong", "new_password": "new"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        mocker.patch(
            "apps.accounts.views.users.change_own_password",
            side_effect=InvalidPassword(),
        )

        with pytest.raises(ValidationError) as excinfo:
            viewset.change_password(viewset.request)

        assert excinfo.value.detail["old_password"] == "Invalid password"

    def test_reset_password_success(
        self, viewset, mocker, default_user_factory, admin_factory
    ):
        actor = admin_factory()
        target_user = default_user_factory()
        viewset.action = "force_password_change"
        viewset.request.user = actor
        mocker.patch.object(viewset, "get_object", return_value=target_user)

        validated_data = {"new_password": "new_secure_pass"}
        mock_serializer = mocker.Mock(validated_data=validated_data)
        mocker.patch.object(viewset, "get_serializer", return_value=mock_serializer)

        mock_force_change = mocker.patch(
            "apps.accounts.views.users.force_user_password_change"
        )

        response = viewset.force_password_change(viewset.request, pk=target_user.pk)

        assert response.status_code == 204
        mock_force_change.assert_called_once_with(
            actor=actor,
            target_user=target_user,
            new_password="new_secure_pass",
        )


class TestUserViewSetThrottle:
    @pytest.mark.parametrize(
        "action, method, is_auth, expected_throttle_classes",
        [
            ("list", "GET", True, [UserReadThrottle]),
            ("retrieve", "GET", True, [UserReadThrottle]),
            ("me", "GET", True, [UserReadThrottle]),
            ("me", "PATCH", True, [WriteThrottle]),
            ("create", "POST", True, [WriteThrottle]),
            ("update", "PUT", True, [WriteThrottle]),
            ("partial_update", "PATCH", True, [WriteThrottle]),
            ("destroy", "DELETE", True, [WriteThrottle]),
            ("change_role", "POST", True, [WriteThrottle]),
            ("change_password", "POST", True, [PasswordChangeThrottle]),
            ("force_password_change", "POST", True, [WriteThrottle]),
            ("list", "OPTIONS", False, []),
            ("list", "OPTIONS", True, []),
        ],
    )
    def test_user_viewset_return_correct_throttle_for_action(
        self,
        rf,
        editor_factory,
        action,
        method,
        is_auth,
        expected_throttle_classes,
    ):
        request = getattr(rf, method.lower())("/")
        request.user = editor_factory() if is_auth else AnonymousUser()

        viewset = UserViewSet(action=action)
        viewset.request = request
        viewset.format_kwarg = None

        throttles = viewset.get_throttles()

        assert len(throttles) == len(expected_throttle_classes), (
            f"Expected {len(expected_throttle_classes)} throttles for"
            f"UserViewSet:{action}, got {len(throttles)}"
        )
        for throttle, expected_class in zip(throttles, expected_throttle_classes):
            assert isinstance(throttle, expected_class)
