from django.db import models
from django.db.models import Q


class ProfileQuerySet(models.QuerySet):
    def _is_admin(self, user):
        return user and user.is_authenticated and (user.is_staff or user.is_superuser)

    def visible_for(self, user):
        if user and user.is_authenticated:
            if self._is_admin(user):
                return self.all()
            return self.filter(Q(is_public=True) | Q(user=user))
        return self.filter(is_public=True)

    def editable_by(self, user):
        if user and user.is_authenticated:
            if self._is_admin(user):
                return self.all()
            return self.filter(user=user)
        return self.none()

    def me(self, user):
        if not user or not user.is_authenticated:
            return self.none()
        return self.filter(user=user)


class ProfileManager(models.Manager):
    def get_queryset(self):
        return ProfileQuerySet(self.model, using=self._db)

    def visible_for(self, user):
        return self.get_queryset().visible_for(user)

    def editable_by(self, user):
        return self.get_queryset().editable_by(user)

    def me(self, user):
        return self.get_queryset().me(user)
