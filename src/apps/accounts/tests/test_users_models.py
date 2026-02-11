from django.core.exceptions import ValidationError
import pytest

from apps.accounts.models import Admin, Editor, User


@pytest.mark.django_db
def test_base_user_method_properties(editor_factory):
    user = editor_factory(first_name="John", last_name="Doe")
    assert str(user) == user.get_full_name()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_class, role, expected_role, is_staff, is_superuser",
    [
        (Editor, None, User.Role.EDITOR, False, False),
        (Admin, None, User.Role.ADMIN, True, True),
        (User, User.Role.ADMIN, User.Role.ADMIN, True, True),
        (User, User.Role.EDITOR, User.Role.EDITOR, False, False),
    ],
    ids=("editor_proxy", "admin_proxy", "user_admin_role", "user_editor_role"),
)
def test_user_save_sets_correct_role_and_permissions(
    user_class, role, expected_role, is_staff, is_superuser
):
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
    if role:
        user_data["role"] = role

    user = user_class(**user_data)
    user.save()

    assert user.role == expected_role
    assert user.is_staff == is_staff
    assert user.is_superuser == is_superuser


@pytest.mark.django_db
def test_user_default_role():
    user = User(
        username="defaultuser",
        email="default@example.com",
        first_name="Default",
        last_name="User",
    )
    user.save()
    assert user.role == User.Role.ADMIN


@pytest.mark.django_db
def test_username_min_length_validation():
    user = User(username="ab", email="ab@example.com")
    with pytest.raises(ValidationError) as excinfo:
        user.full_clean()
    assert "Username must be at least 3 characters" in str(excinfo.value)


@pytest.mark.django_db
def test_admin_manager_filters_user_by_role(admin_factory, editor_factory):
    admin_factory()
    editor_factory()
    assert Admin.objects.count() == 1
    assert Admin.objects.first().role == User.Role.ADMIN


@pytest.mark.django_db
def test_editor_manager_filters_user_by_role(editor_factory, admin_factory):
    editor_factory()
    admin_factory()
    assert Editor.objects.count() == 1
    assert Editor.objects.first().role == User.Role.EDITOR
