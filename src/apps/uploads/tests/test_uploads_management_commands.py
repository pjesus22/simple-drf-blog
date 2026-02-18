from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
import pytest

from apps.uploads.models import Upload


@pytest.mark.django_db
def test_cleanup_command_deletes_old_uploads(editor_factory, upload_factory):
    user = editor_factory()

    old_upload = upload_factory(uploaded_by=user)
    old_upload.deleted_at = timezone.now() - timedelta(days=31)
    old_upload.save()

    recent_upload = upload_factory(uploaded_by=user)
    recent_upload.deleted_at = timezone.now() - timedelta(days=15)
    recent_upload.save()

    call_command("cleanup_deleted_uploads")

    assert not Upload.all_objects.filter(id=old_upload.id).exists()
    assert Upload.all_objects.filter(id=recent_upload.id).exists()
