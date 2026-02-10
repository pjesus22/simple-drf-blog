import hashlib

import pytest
from apps.uploads.models import Upload
from django.db import IntegrityError
from django.utils import timezone


def test_upload_str():
    upload = Upload(original_filename="testfile.jpg", purpose=Upload.Purpose.ATTACHMENT)
    assert str(upload) == f"{upload.original_filename} - {upload.purpose}"


def test_upload_saves_object(db, editor_factory, file_factory):
    user = editor_factory()
    f = file_factory.create_real_image_file(size=(100, 100))
    file_content = f.read()
    hash_sha256 = hashlib.sha256(file_content).hexdigest()
    f.seek(0)

    upload = Upload(
        file=f,
        uploaded_by=user,
        original_filename=f.name,
        mime_type=f.content_type,
        size=f.size,
        hash_sha256=hash_sha256,
        purpose=Upload.Purpose.ATTACHMENT,
        visibility=Upload.Visibility.PUBLIC,
        width=100,
        height=100,
    )
    upload.save()

    assert Upload.objects.filter(pk=upload.pk).exists()
    assert upload.file.name.startswith(
        f"{upload.purpose}/{timezone.now().strftime('%Y%m%d')}"
    )
    assert upload.uploaded_by == user
    assert upload.original_filename == f.name
    assert upload.mime_type == f.content_type
    assert upload.hash_sha256 == hash_sha256
    assert upload.size == f.size
    assert upload.width == 100
    assert upload.height == 100
    assert upload.purpose == Upload.Purpose.ATTACHMENT
    assert upload.visibility == Upload.Visibility.PUBLIC


@pytest.mark.parametrize("field_name", ["hash_sha256", "size"])
def test_upload_fields_are_not_editable(field_name):
    field = Upload._meta.get_field(field_name)
    assert not field.editable


def test_upload_hash_sha256_unique_constraint(db, editor_factory, file_factory):
    user = editor_factory()
    f = file_factory.create_mock_file()
    hash_val = "a" * 64

    Upload.objects.create(
        file=f,
        uploaded_by=user,
        original_filename="f1.txt",
        mime_type="text/plain",
        size=10,
        hash_sha256=hash_val,
    )

    with pytest.raises(IntegrityError):
        Upload.objects.create(
            file=f,
            uploaded_by=user,
            original_filename="f2.txt",
            mime_type="text/plain",
            size=10,
            hash_sha256=hash_val,
        )
