import pytest
from apps.accounts.permissions import IsOwner
from apps.accounts.views import ProfileViewSet
from rest_framework.permissions import IsAuthenticated


@pytest.mark.parametrize(
    "action, expected_permissions",
    [
        ("update", [IsOwner]),
        ("partial_update", [IsOwner]),
        ("list", [IsAuthenticated]),
        ("retrieve", [IsAuthenticated]),
    ],
    ids=("update", "partial_update", "list", "retrieve"),
)
def test_user_viewset_gets_appropriate_permissions(action, expected_permissions):
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
