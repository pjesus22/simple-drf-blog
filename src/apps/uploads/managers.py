from django.db import models


class UploadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)


class UploadManager(models.Manager):
    def get_queryset(self):
        return UploadQuerySet(self.model, using=self._db).active()

    def only_deleted(self):
        return UploadQuerySet(self.model, using=self._db).deleted()
