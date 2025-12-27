import pytest
from apps.users.models import Admin, Editor, User


def test_base_user_method_properties(editor_factory):
    user = Editor(first_name="John", last_name="Doe")

    assert str(user) == user.get_full_name()


@pytest.mark.parametrize(
    "user_class,expected_role",
    [(Editor, User.Role.EDITOR), (Admin, User.Role.ADMIN), (User, User.Role.ADMIN)],
    ids=lambda x: x,
)
def test_user_save_sets_role(db, user_class, expected_role):
    user = user_class(
        username="testuser",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
    )
    user.save()
    assert user.role == expected_role
    assert user.is_staff == (expected_role == User.Role.ADMIN)
    assert user.is_superuser == (expected_role == User.Role.ADMIN)


def test_admin_manager_filters_user_by_role(db, admin_factory):
    admin_factory()

    assert Admin.objects.count() == 1
    assert Admin.objects.first().role == User.Role.ADMIN


def test_editor_manager_filters_user_by_role(db, editor_factory):
    editor_factory()

    assert Editor.objects.count() == 1
    assert Editor.objects.first().role == User.Role.EDITOR
