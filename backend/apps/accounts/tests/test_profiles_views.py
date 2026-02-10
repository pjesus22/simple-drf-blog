import pytest
from apps.accounts.permissions import IsOwner
from apps.accounts.serializers import PrivateProfileSerializer, PublicProfileSerializer
from apps.accounts.views import ProfileViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


class TestProfileViewSet:
    @pytest.fixture
    def viewset(self, mocker):
        def _create_viewset(action="list", method="GET"):
            mock_user = mocker.Mock()
            mock_request = mocker.Mock(user=mock_user, method=method)

            viewset = ProfileViewSet(action=action)
            viewset.request = mock_request
            viewset.format_kwarg = None
            return viewset, mock_request, mock_user

        return _create_viewset

    @pytest.mark.parametrize(
        "action, expected_permissions",
        [
            ("update", [IsOwner]),
            ("partial_update", [IsOwner]),
            ("me", [IsAuthenticated]),
            ("list", [AllowAny]),
            ("retrieve", [AllowAny]),
        ],
        ids=("update", "partial_update", "me", "list", "retrieve"),
    )
    def test_profile_viewset_returns_correct_permissions(
        self, action, expected_permissions
    ):
        viewset = ProfileViewSet(action=action)
        actual_permissions = viewset.get_permissions()

        assert len(actual_permissions) == len(expected_permissions), (
            f"Expected {len(expected_permissions)} permissions for {action}, "
            f"got {len(actual_permissions)}"
        )

        for actual, expected in zip(actual_permissions, expected_permissions):
            assert isinstance(actual, expected)

    @pytest.mark.parametrize(
        "action, expected_serializer",
        [
            ("update", PrivateProfileSerializer),
            ("partial_update", PrivateProfileSerializer),
            ("me", PrivateProfileSerializer),
            ("list", PublicProfileSerializer),
            ("retrieve", PublicProfileSerializer),
        ],
        ids=("update", "partial_update", "me", "list", "retrieve"),
    )
    def test_profile_viewset_returns_correct_serializer_class(
        self, action, expected_serializer
    ):
        viewset = ProfileViewSet(action=action)
        assert viewset.get_serializer_class() == expected_serializer

    @pytest.mark.parametrize(
        "action, manager_method",
        [
            ("update", "editable_by"),
            ("partial_update", "editable_by"),
            ("me", "me"),
            ("list", "visible_for"),
            ("retrieve", "visible_for"),
        ],
        ids=("update", "partial_update", "me", "list", "retrieve"),
    )
    def test_profile_viewset_get_queryset_calls_appropriate_profile_manager_method(
        self, viewset, mocker, action, manager_method
    ):
        vs_instance, _, mock_user = viewset(action=action)
        mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

        vs_instance.get_queryset()

        method_to_call = getattr(mock_manager, manager_method)
        method_to_call.assert_called_once_with(mock_user)

    def test_profile_viewset_me_action_get_returns_user_profile(self, viewset, mocker):
        vs_instance, mock_request, mock_user = viewset(action="me", method="GET")

        mock_profile = mocker.Mock()
        mock_queryset = mocker.Mock()
        mock_queryset.first.return_value = mock_profile

        mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")
        mock_manager.me.return_value = mock_queryset

        mock_get_object_or_404 = mocker.patch(
            "apps.accounts.views.profiles.get_object_or_404", return_value=mock_profile
        )

        mock_serializer_class = mocker.patch.object(vs_instance, "get_serializer_class")
        mock_serializer_instance = mocker.Mock()
        mock_serializer_class.return_value.return_value = mock_serializer_instance

        response = vs_instance.me(mock_request)

        mock_manager.me.assert_called_once_with(mock_user)
        mock_get_object_or_404.assert_called_once_with(mock_queryset)

        call_kwargs = mock_serializer_class.return_value.call_args[1]
        assert "data" not in call_kwargs
        assert "partial" not in call_kwargs
        assert response.data == mock_serializer_instance.data

    @pytest.mark.parametrize(
        "method, is_partial",
        [
            ("PUT", False),
            ("PATCH", True),
        ],
    )
    def test_profile_viewset_me_action_update_updates_user_profile(
        self, viewset, mocker, method, is_partial
    ):
        vs_instance, mock_request, _ = viewset(action="me", method=method)
        mock_request.data = {"biography": "New bio"}

        mock_profile = mocker.Mock()
        mock_queryset = mocker.Mock()

        mocker.patch(
            "apps.accounts.views.profiles.Profile.objects.me",
            return_value=mock_queryset,
        )
        mocker.patch(
            "apps.accounts.views.profiles.get_object_or_404", return_value=mock_profile
        )

        mock_serializer_class = mocker.patch.object(vs_instance, "get_serializer_class")
        mock_serializer_instance = mocker.Mock()
        mock_serializer_class.return_value.return_value = mock_serializer_instance

        response = vs_instance.me(mock_request)

        mock_serializer_class.return_value.assert_called_once()
        call_kwargs = mock_serializer_class.return_value.call_args[1]
        assert call_kwargs["data"] == mock_request.data
        assert call_kwargs["partial"] is is_partial

        mock_serializer_instance.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer_instance.save.assert_called_once()
        assert response.data == mock_serializer_instance.data

    def test_profile_viewset_http_methods_restricted(self):
        viewset = ProfileViewSet()
        allowed = {"get", "put", "patch", "head", "options"}
        assert set(viewset.http_method_names) == allowed
        assert "delete" not in viewset.http_method_names
        assert "post" not in viewset.http_method_names
