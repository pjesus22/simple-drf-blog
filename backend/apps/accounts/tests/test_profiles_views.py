import pytest
from apps.accounts.permissions import IsOwner
from apps.accounts.serializers import PrivateProfileSerializer, PublicProfileSerializer
from apps.accounts.views import ProfileViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated


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
def test_profile_viewset_gets_appropriate_permissions(action, expected_permissions):
    viewset = ProfileViewSet(action=action)
    actual_permissions = viewset.get_permissions()

    assert len(actual_permissions) == len(expected_permissions), (
        f"Expected {len(expected_permissions)} permissions, "
        f"got {len(actual_permissions)}"
    )

    assert all(
        isinstance(permission, expected_permission)
        for permission, expected_permission in zip(
            actual_permissions, expected_permissions
        )
    )


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
def test_profile_viewset_gets_appropriate_serializer_class(action, expected_serializer):
    viewset = ProfileViewSet(action=action)
    actual_serializer = viewset.get_serializer_class()

    assert actual_serializer == expected_serializer


def test_profile_viewset_get_queryset_for_update_uses_editable_by(mocker):
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user

    viewset = ProfileViewSet(action="update")
    viewset.request = mock_request

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

    viewset.get_queryset()

    mock_manager.editable_by.assert_called_once_with(mock_user)


def test_profile_viewset_get_queryset_for_partial_update_uses_editable_by(mocker):
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user

    viewset = ProfileViewSet(action="partial_update")
    viewset.request = mock_request

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

    viewset.get_queryset()

    mock_manager.editable_by.assert_called_once_with(mock_user)


def test_profile_viewset_get_queryset_for_me_uses_me(mocker):
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user

    viewset = ProfileViewSet(action="me")
    viewset.request = mock_request

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

    viewset.get_queryset()

    mock_manager.me.assert_called_once_with(mock_user)


def test_profile_viewset_get_queryset_for_list_uses_visible_for(mocker):
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user

    viewset = ProfileViewSet(action="list")
    viewset.request = mock_request

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

    viewset.get_queryset()

    mock_manager.visible_for.assert_called_once_with(mock_user)


def test_profile_viewset_get_queryset_for_retrieve_uses_visible_for(mocker):
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user

    viewset = ProfileViewSet(action="retrieve")
    viewset.request = mock_request

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")

    viewset.get_queryset()

    mock_manager.visible_for.assert_called_once_with(mock_user)


def test_profile_viewset_me_action_get_returns_user_profile(mocker):
    """Test that GET /profiles/me/ returns the authenticated user's profile"""
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user
    mock_request.method = "GET"

    mock_profile = mocker.Mock()
    mock_queryset = mocker.Mock()
    mock_queryset.first.return_value = mock_profile

    viewset = ProfileViewSet(action="me")
    viewset.request = mock_request
    viewset.format_kwarg = None

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")
    mock_manager.me.return_value = mock_queryset

    mock_get_object_or_404 = mocker.patch(
        "apps.accounts.views.profiles.get_object_or_404"
    )
    mock_get_object_or_404.return_value = mock_profile

    mock_serializer_class = mocker.patch.object(viewset, "get_serializer_class")
    mock_serializer_instance = mocker.Mock()
    mock_serializer_class.return_value.return_value = mock_serializer_instance

    response = viewset.me(mock_request)

    mock_manager.me.assert_called_once_with(mock_user)
    mock_get_object_or_404.assert_called_once_with(mock_queryset)
    # Verify serializer was called without data/partial for GET requests
    call_kwargs = mock_serializer_class.return_value.call_args[1]
    assert "data" not in call_kwargs
    assert "partial" not in call_kwargs
    assert "context" in call_kwargs
    assert response.data == mock_serializer_instance.data


def test_profile_viewset_me_action_put_updates_user_profile(mocker):
    """Test that PUT /profiles/me/ updates the authenticated user's profile"""
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user
    mock_request.method = "PUT"
    mock_request.data = {"biography": "Updated bio"}

    mock_profile = mocker.Mock()
    mock_queryset = mocker.Mock()

    viewset = ProfileViewSet(action="me")
    viewset.request = mock_request
    viewset.format_kwarg = None

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")
    mock_manager.me.return_value = mock_queryset

    mock_get_object_or_404 = mocker.patch(
        "apps.accounts.views.profiles.get_object_or_404"
    )
    mock_get_object_or_404.return_value = mock_profile

    mock_serializer_class = mocker.patch.object(viewset, "get_serializer_class")
    mock_serializer_instance = mocker.Mock()
    mock_serializer_instance.is_valid = mocker.Mock()
    mock_serializer_instance.save = mocker.Mock()
    mock_serializer_class.return_value.return_value = mock_serializer_instance

    response = viewset.me(mock_request)

    # Verify serializer was called (context is added automatically by get_serializer)
    call_kwargs = mock_serializer_class.return_value.call_args[1]
    assert call_kwargs["data"] == mock_request.data
    assert call_kwargs["partial"] is False
    assert "context" in call_kwargs
    mock_serializer_instance.is_valid.assert_called_once_with(raise_exception=True)
    mock_serializer_instance.save.assert_called_once()
    assert response.data == mock_serializer_instance.data


def test_profile_viewset_me_action_patch_partially_updates_user_profile(mocker):
    """Test that PATCH /profiles/me/ partially updates the authenticated user's profile"""
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user
    mock_request.method = "PATCH"
    mock_request.data = {"biography": "Partially updated bio"}

    mock_profile = mocker.Mock()
    mock_queryset = mocker.Mock()

    viewset = ProfileViewSet(action="me")
    viewset.request = mock_request
    viewset.format_kwarg = None

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")
    mock_manager.me.return_value = mock_queryset

    mock_get_object_or_404 = mocker.patch(
        "apps.accounts.views.profiles.get_object_or_404"
    )
    mock_get_object_or_404.return_value = mock_profile

    mock_serializer_class = mocker.patch.object(viewset, "get_serializer_class")
    mock_serializer_instance = mocker.Mock()
    mock_serializer_instance.is_valid = mocker.Mock()
    mock_serializer_instance.save = mocker.Mock()
    mock_serializer_class.return_value.return_value = mock_serializer_instance

    response = viewset.me(mock_request)

    # Verify serializer was called (context is added automatically by get_serializer)
    call_kwargs = mock_serializer_class.return_value.call_args[1]
    assert call_kwargs["data"] == mock_request.data
    assert call_kwargs["partial"] is True
    assert "context" in call_kwargs
    mock_serializer_instance.is_valid.assert_called_once_with(raise_exception=True)
    mock_serializer_instance.save.assert_called_once()
    assert response.data == mock_serializer_instance.data


def test_profile_viewset_me_action_uses_correct_queryset(mocker):
    """Test that the me action uses Profile.objects.me() for queryset"""
    mock_request = mocker.Mock()
    mock_user = mocker.Mock()
    mock_request.user = mock_user
    mock_request.method = "GET"

    mock_profile = mocker.Mock()
    mock_queryset = mocker.Mock()

    viewset = ProfileViewSet(action="me")
    viewset.request = mock_request
    viewset.format_kwarg = None

    mock_manager = mocker.patch("apps.accounts.views.profiles.Profile.objects")
    mock_manager.me.return_value = mock_queryset

    mock_get_object_or_404 = mocker.patch(
        "apps.accounts.views.profiles.get_object_or_404"
    )
    mock_get_object_or_404.return_value = mock_profile

    mock_serializer_class = mocker.patch.object(viewset, "get_serializer_class")
    mock_serializer_instance = mocker.Mock()
    mock_serializer_class.return_value.return_value = mock_serializer_instance

    viewset.me(mock_request)

    # Verify that Profile.objects.me() was called with the correct user
    mock_manager.me.assert_called_once_with(mock_user)
    # Verify that get_object_or_404 was called with the queryset
    mock_get_object_or_404.assert_called_once_with(mock_queryset)


def test_profile_viewset_http_method_names_restricted(mocker):
    """Test that ProfileViewSet only allows specific HTTP methods"""
    viewset = ProfileViewSet()

    allowed_methods = ["get", "put", "patch", "head", "options"]
    assert viewset.http_method_names == allowed_methods

    # Verify that DELETE and POST are not allowed
    assert "delete" not in viewset.http_method_names
    assert "post" not in viewset.http_method_names
