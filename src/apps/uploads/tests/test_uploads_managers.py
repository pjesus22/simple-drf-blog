from django.utils import timezone
import pytest

from apps.uploads.models import Upload

pytestmark = pytest.mark.django_db


class TestUploadManager:
    def test_objects_excludes_deleted_uploads(self, upload_factory):
        active = upload_factory(deleted_at=None)
        upload_factory(deleted_at=timezone.now())

        qs = Upload.objects.all()

        assert qs.count() == 1
        assert active in qs

    def test_only_deleted_returns_only_deleted_uploads(self, upload_factory):
        deleted = upload_factory(deleted_at=timezone.now())
        upload_factory(deleted_at=None)

        qs = Upload.objects.only_deleted()

        assert qs.count() == 1
        assert deleted in qs

    def test_all_objects_returns_everything(self, upload_factory):
        upload_factory(deleted_at=None)
        upload_factory(deleted_at=timezone.now())

        assert Upload.all_objects.count() == 2
