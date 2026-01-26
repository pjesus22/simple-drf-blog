import hashlib

from apps.uploads.models import Upload
from apps.uploads.tests.helpers import FileFactory as ff
from django.utils import timezone


def test_upload_str_returns_original_filename_and_purpose():
    upload = Upload(original_filename="testfile.jpg", purpose=Upload.Purpose.ATTACHMENT)
    assert str(upload) == f"{upload.original_filename} - {upload.purpose}"


def test_save_upload_object_successfully(db, editor_factory):
    user = editor_factory()
    f = ff.create_real_image_file(size=(100, 100))
    hash_sha256 = hashlib.sha256(f.read()).hexdigest()

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


def test_upload_hash_sha256_is_not_editable():
    f = ff.create_mock_file()
    hash_sha256 = hashlib.sha256(f.read()).hexdigest()
    upload = Upload(file=f, hash_sha256=hash_sha256)
    field = upload._meta.get_field("hash_sha256")
    assert not field.editable


def test_upload_size_is_not_editable():
    f = ff.create_mock_file()
    upload = Upload(file=f)
    field = upload._meta.get_field("size")
    assert not field.editable
