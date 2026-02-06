from django.db import models
from django.db.models import Q


class PostQueryset(models.QuerySet):
    def alive(self):
        return self.exclude(status=self.model.Status.DELETED)

    def deleted(self):
        return self.filter(status=self.model.Status.DELETED)

    def visible_for(self, user):
        qs = self.alive()

        if not user.is_authenticated:
            return qs.filter(status=self.model.Status.PUBLISHED)

        if user.is_staff:
            return qs

        return qs.filter(Q(status=self.model.Status.PUBLISHED) | Q(author=user))

    def owned_by(self, user):
        return self.filter(author=user)


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQueryset(self.model, using=self._db).alive()

    def with_deleted(self):
        return PostQueryset(self.model, using=self._db)

    def only_deleted(self):
        return self.with_deleted().deleted()

    def visible_for(self, user):
        return self.get_queryset().visible_for(user)

    def owned_by(self, user):
        return self.get_queryset().owned_by(user)
