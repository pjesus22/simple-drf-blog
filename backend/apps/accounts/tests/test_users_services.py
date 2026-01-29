import pytest
from apps.accounts.exceptions import CannotDemoteLastAdmin, InvalidPassword
from apps.accounts.services import change_own_password, change_user_role
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserServices:
    def test_change_user_role_success(self, mocker):
        actor = mocker.Mock(spec=User)
        target_user = mocker.Mock(spec=User)

        change_user_role(actor=actor, target_user=target_user, new_role=User.Role.ADMIN)

        assert target_user.role == User.Role.ADMIN
        target_user.save.assert_called_once_with(update_fields=["role"])

    def test_change_user_role_last_admin_demotion_raises_error(self, mocker):
        actor = mocker.Mock(spec=User)
        actor.role = User.Role.ADMIN

        mock_queryset = mocker.Mock()
        mock_queryset.count.return_value = 1

        mocker.patch(
            "apps.accounts.services.User.objects.select_for_update",
            return_value=mocker.Mock(filter=mocker.Mock(return_value=mock_queryset)),
        )

        with pytest.raises(CannotDemoteLastAdmin):
            change_user_role(actor=actor, target_user=actor, new_role=User.Role.EDITOR)

    def test_change_own_password_success(self, mocker):
        user = mocker.Mock(spec=User)
        user.check_password.return_value = True

        change_own_password(user=user, old_password="old", new_password="new")

        user.set_password.assert_called_once_with("new")
        user.save.assert_called_once_with(update_fields=["password"])

    def test_change_own_password_wrong_old_password_raises_error(self, mocker):
        user = mocker.Mock(spec=User)
        user.check_password.return_value = False

        with pytest.raises(InvalidPassword):
            change_own_password(user=user, old_password="wrong", new_password="new")
