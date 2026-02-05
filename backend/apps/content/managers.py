from django.db import models
from django.db.models import Q


class PostQueryset(models.QuerySet):
    def visible_for(self, user):
        qs = self.exclude(status="deleted")

        if user.is_authenticated and user.is_staff:
            return qs

        if user.is_authenticated:
            return qs.filter(Q(status="published") | Q(author=user))

        return qs.filter(status="published")

    def with_deleted(self):
        return self.all()

    def only_deleted(self):
        return self.filter(status="deleted")


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQueryset(self.model, using=self._db)

    def visible_for(self, user):
        return self.get_queryset().visible_for(user)

    def with_deleted(self):
        return self.get_queryset().with_deleted()

    def only_deleted(self):
        return self.get_queryset().only_deleted()
