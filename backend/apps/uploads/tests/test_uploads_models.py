import pytest
from apps.uploads.models import Upload
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile


def test_upload_str_returns_filename_and_mime_type():
    upload = Upload(original_filename="testfile.jpg", mime_type="image/jpeg")
    assert str(upload) == "testfile.jpg (image/jpeg)"


def test_save_upload(db, editor_factory):
    user = editor_factory()

    upload = Upload(
        file=SimpleUploadedFile(
            name="test.jpg",
            content=b"fake image content",
            content_type="image/jpeg",
        ),
        uploaded_by=user,
        original_filename="test.jpg",
        mime_type="image/jpeg",
        file_type=Upload.FileType.IMAGE,
    )
    upload.save()

    assert upload.id is not None
    assert upload.file.name.endswith("test.jpg")
    assert upload.uploaded_by == user
    assert upload.original_filename == "test.jpg"
    assert upload.mime_type == "image/jpeg"
    assert upload.file_type == Upload.FileType.IMAGE


def test_check_upload_default_attributes():
    upload = Upload(
        file=SimpleUploadedFile(
            name="test.txt",
            content=b"data",
            content_type="text/plain",
        ),
    )

    assert upload.file_type == Upload.FileType.OTHER
    assert upload.is_public is True
    assert upload.width is None
    assert upload.height is None


def test_upload_hash_md5_not_editable():
    field = Upload._meta.get_field("hash_md5")
    assert not field.editable


def test_upload_file_extension_validator_raises_validation_error():
    upload = Upload(
        file=SimpleUploadedFile(
            name="malicious.exe",
            content=b"data",
        ),
    )

    with pytest.raises(ValidationError):
        upload.full_clean()


def test_upload_uploaded_by_relationship(db, editor_factory, clean_media):
    user = editor_factory()

    upload = Upload.objects.create(
        file=SimpleUploadedFile(name="test.txt", content=b"data"),
        uploaded_by=user,
    )

    assert upload.uploaded_by == user
    assert upload in user.uploads.all()


def test_upload_uploaded_by_set_null_on_delete(db, editor_factory, clean_media):
    user = editor_factory()

    upload = Upload.objects.create(
        file=SimpleUploadedFile(name="test.txt", content=b"data"),
        uploaded_by=user,
    )

    user.delete()
    upload.refresh_from_db()

    assert upload.uploaded_by is None


def test_upload_default_ordering(db, editor_factory, clean_media):
    user = editor_factory()

    upload1 = Upload.objects.create(
        file=SimpleUploadedFile(name="first.txt", content=b"1"),
        uploaded_by=user,
    )
    upload2 = Upload.objects.create(
        file=SimpleUploadedFile(name="second.txt", content=b"2"),
        uploaded_by=user,
    )
    upload3 = Upload.objects.create(
        file=SimpleUploadedFile(name="third.txt", content=b"3"),
        uploaded_by=user,
    )

    uploads = list(Upload.objects.all())

    assert uploads[0] == upload3
    assert uploads[1] == upload2
    assert uploads[2] == upload1


def test_upload_has_indexes(db):
    meta = Upload._meta
    indexes = meta.indexes

    assert len(indexes) == 3

    index_fields = [tuple(idx.fields) for idx in indexes]

    assert ("file_type",) in index_fields
    assert ("uploaded_by", "created_at") in index_fields
    assert ("hash_md5",) in index_fields
