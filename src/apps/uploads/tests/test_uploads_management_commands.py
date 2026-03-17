from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
import pytest

from apps.uploads.models import Upload


@pytest.mark.django_db
def test_cleanup_command_deletes_old_uploads(editor_factory, upload_factory):
    user = editor_factory()

    old_upload = upload_factory.create(
        uploaded_by=user,
        deleted_at=timezone.now() - timedelta(days=31),
    )

    recent_upload = upload_factory.create(
        uploaded_by=user,
        deleted_at=timezone.now() - timedelta(days=15),
    )

    call_command("cleanup_deleted_uploads")

    assert not Upload.all_objects.filter(id=old_upload.id).exists()
    assert Upload.all_objects.filter(id=recent_upload.id).exists()


@pytest.mark.django_db
def test_cleanup_command_dry_run(editor_factory, upload_factory):
    user = editor_factory()

    upload_factory.create_batch(
        size=15,
        uploaded_by=user,
        deleted_at=timezone.now() - timedelta(days=31),
    )

    recent_upload = upload_factory.create(
        uploaded_by=user,
        deleted_at=timezone.now() - timedelta(days=15),
    )

    call_command("cleanup_deleted_uploads", dry_run=True)

    assert (
        Upload.all_objects.filter(deleted_at__day__lt=timezone.now().day).count() == 15
    )
    assert Upload.all_objects.filter(id=recent_upload.id).exists()


@pytest.mark.django_db
def test_cleanup_command_failed_to_delete_files(
    editor_factory, upload_factory, capsys, mocker
):
    user = editor_factory()

    upload = upload_factory.create(
        uploaded_by=user,
        deleted_at=timezone.now() - timedelta(days=31),
    )

    mocker.patch(
        "django.db.models.fields.files.FieldFile.delete",
        side_effect=OSError("disk I/O error"),
    )

    call_command("cleanup_deleted_uploads")

    assert Upload.all_objects.filter(id=upload.id).exists()

    captured = capsys.readouterr()
    assert "Failed to delete" in captured.out
    assert str(upload.id) in captured.out
