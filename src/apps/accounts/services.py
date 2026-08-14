from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.accounts.exceptions import CannotDemoteLastAdmin, InvalidPassword
from apps.accounts.models import User


def _blacklist_user_tokens(*, user: User) -> None:
    for outstanding in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding)


@transaction.atomic
def change_user_role(*, actor: User, target_user: User, new_role: User.Role) -> None:
    if actor == target_user and new_role != User.Role.ADMIN:
        admins = User.objects.select_for_update().filter(role=User.Role.ADMIN)

        if admins.count() <= 1:
            raise CannotDemoteLastAdmin()

    target_user.role = new_role
    target_user.save(update_fields=["role", "is_staff", "is_superuser"])


@transaction.atomic
def change_own_password(*, user: User, old_password: str, new_password: str) -> None:
    if not user.check_password(old_password):
        raise InvalidPassword()

    user.set_password(new_password)
    user.save(update_fields=["password"])
    _blacklist_user_tokens(user=user)


@transaction.atomic
def force_user_password_change(
    *, actor: User, target_user: User, new_password: str
) -> None:
    target_user.set_password(new_password)
    target_user.save(update_fields=["password"])
    _blacklist_user_tokens(user=target_user)
