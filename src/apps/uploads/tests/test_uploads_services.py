import hashlib

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
import pytest

from apps.uploads.exceptions import (
    InvalidFileError,
    InvalidPurposeError,
    InvalidVisibilityError,
)
from apps.uploads.models import Upload
from apps.uploads.services import UploadService

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "purpose, visibility, expected_purpose, expected_visibility",
    [
        (
            None,
            None,
            Upload.Purpose.ATTACHMENT,
            Upload.Visibility.PRIVATE,
        ),
        (
            Upload.Purpose.ATTACHMENT,
            Upload.Visibility.PUBLIC,
            Upload.Purpose.ATTACHMENT,
            Upload.Visibility.PUBLIC,
        ),
    ],
    ids=("defaults", "explicit"),
)
def test_upload_service_initialization(
    editor_factory, purpose, visibility, expected_purpose, expected_visibility
):
    user = editor_factory()
    kwargs = {"uploaded_by": user}
    if purpose:
        kwargs["purpose"] = purpose
    if visibility:
        kwargs["visibility"] = visibility

    service = UploadService(**kwargs)

    assert service.uploaded_by == user
    assert service.purpose == expected_purpose
    assert service.visibility == expected_visibility


def test_upload_service_creates_upload_object_successfully(
    editor_factory, file_factory
):
    user = editor_factory()
    file = file_factory.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload = service.create_upload(file=file)

    assert isinstance(upload, Upload)
    assert Upload.objects.filter(pk=upload.pk).exists()
    assert upload.uploaded_by == user
    assert upload.purpose == Upload.Purpose.ATTACHMENT
    assert upload.visibility == Upload.Visibility.PRIVATE
    assert upload.size == file.size
    assert upload.original_filename == file.name
    assert Upload.objects.count() == 1


def test_upload_service_updates_metadata_successfully(
    upload_factory, file_factory, clean_media
):
    file = file_factory.create_real_image_file()
    file_content = file.read()
    expected_hash = hashlib.sha256(file_content).hexdigest()

    upload = upload_factory(
        file=file,
        size=10240,
        hash_sha256=hashlib.sha256(b"wrong").hexdigest(),
        mime_type="text/plain",
        width=100,
        height=100,
    )

    service = UploadService(uploaded_by=upload.uploaded_by)
    updated_upload = service.update_metadata(upload)

    assert updated_upload.size == len(file_content)
    assert updated_upload.hash_sha256 == expected_hash
    assert updated_upload.mime_type == "image/png"
    assert (updated_upload.width, updated_upload.height) == (64, 64)

    upload.refresh_from_db()
    assert upload.hash_sha256 == expected_hash
    assert upload.size == len(file_content)


@pytest.mark.parametrize(
    "purpose, visibility, error, detail",
    [
        (
            "invalid",
            Upload.Visibility.PUBLIC,
            InvalidPurposeError,
            "is not a valid purpose",
        ),
        (
            Upload.Purpose.ATTACHMENT,
            "invalid",
            InvalidVisibilityError,
            "is not a valid visibility",
        ),
    ],
    ids=("invalid_purpose", "invalid_visibility"),
)
def test_upload_service_validate_choices(
    editor_factory, purpose, visibility, error, detail
):
    user = editor_factory()
    with pytest.raises(error, match=detail):
        UploadService(uploaded_by=user, purpose=purpose, visibility=visibility)


def test_upload_service_validate_file_raises_error_on_missing_file():
    with pytest.raises(InvalidFileError, match="Invalid file provided\\."):
        UploadService._validate_file(file=None)


def test_upload_soft_delete(editor_factory, file_factory, clean_media):
    user = editor_factory()
    file = file_factory.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload = service.create_upload(file=file)
    assert upload.deleted_at is None

    upload.deleted_at = timezone.now()
    upload.save()

    assert Upload.objects.filter(id=upload.id).count() == 0
    assert Upload.all_objects.filter(id=upload.id).count() == 1


def test_upload_service_allows_duplicate_hash(editor_factory, file_factory):
    user = editor_factory()
    file = file_factory.create_real_text_file()
    service = UploadService(uploaded_by=user)

    upload1 = service.create_upload(file=file)

    file.seek(0)
    upload2 = service.create_upload(file=file)

    assert upload1.hash_sha256 == upload2.hash_sha256
    assert upload1.pk != upload2.pk


class TestChangeVisibility:
    @staticmethod
    def _read(name: str) -> bytes:
        with default_storage.open(name, "rb") as fh:
            return fh.read()

    def test_private_to_public_moves_file_and_updates_name(
        self, upload_factory, clean_media
    ):
        upload = upload_factory(
            purpose=Upload.Purpose.AVATAR,
            visibility=Upload.Visibility.PRIVATE,
        )
        old_name = upload.file.name
        original_bytes = self._read(old_name)

        assert old_name.startswith("private/")
        assert f"{Upload.Purpose.AVATAR}/" in old_name

        result = UploadService.change_visibility(upload, Upload.Visibility.PUBLIC)

        expected_name = old_name.removeprefix("private/")
        assert result.visibility == Upload.Visibility.PUBLIC
        assert result.file.name == expected_name
        assert not result.file.name.startswith("private/")
        assert f"{Upload.Purpose.AVATAR}/" in result.file.name
        assert not default_storage.exists(old_name)
        assert default_storage.exists(result.file.name)
        assert self._read(result.file.name) == original_bytes

        upload.refresh_from_db()
        assert upload.visibility == Upload.Visibility.PUBLIC
        assert upload.file.name == expected_name

    def test_public_to_private_moves_file(self, upload_factory, clean_media):
        upload = upload_factory(
            purpose=Upload.Purpose.AVATAR,
            visibility=Upload.Visibility.PUBLIC,
        )
        old_name = upload.file.name
        original_bytes = self._read(old_name)

        assert not old_name.startswith("private/")

        result = UploadService.change_visibility(upload, Upload.Visibility.PRIVATE)

        expected_name = f"private/{old_name}"
        assert result.visibility == Upload.Visibility.PRIVATE
        assert result.file.name == expected_name
        assert result.file.name.startswith("private/")
        assert f"{Upload.Purpose.AVATAR}/" in result.file.name
        assert not default_storage.exists(old_name)
        assert default_storage.exists(result.file.name)
        assert self._read(result.file.name) == original_bytes

        upload.refresh_from_db()
        assert upload.visibility == Upload.Visibility.PRIVATE
        assert upload.file.name == expected_name

    def test_same_visibility_no_storage_io(self, upload_factory, mocker, clean_media):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
        old_name = upload.file.name
        old_visibility = upload.visibility

        storage = mocker.patch("apps.uploads.services.default_storage")
        os_replace = mocker.patch("apps.uploads.services.os.replace")

        result = UploadService.change_visibility(upload, old_visibility)

        storage.exists.assert_not_called()
        storage.save.assert_not_called()
        storage.delete.assert_not_called()
        storage.open.assert_not_called()
        os_replace.assert_not_called()

        assert result.file.name == old_name
        assert result.visibility == old_visibility

        upload.refresh_from_db()
        assert upload.file.name == old_name
        assert upload.visibility == old_visibility

    def test_change_visibility_missing_source_raises_error(
        self, upload_factory, clean_media
    ):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
        default_storage.delete(upload.file.name)

        with pytest.raises(FileNotFoundError):
            UploadService.change_visibility(upload, Upload.Visibility.PUBLIC)

    def test_change_visibility_existing_target_raises_error(
        self, upload_factory, clean_media
    ):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
        new_name = UploadService._target_path(
            upload.file.name, Upload.Visibility.PUBLIC
        )
        default_storage.save(new_name, ContentFile(b"occupant"))

        with pytest.raises(FileExistsError):
            UploadService.change_visibility(upload, Upload.Visibility.PUBLIC)

    def test_db_row_unchanged_on_failure(self, upload_factory, clean_media):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
        old_name = upload.file.name
        old_visibility = upload.visibility
        new_name = UploadService._target_path(old_name, Upload.Visibility.PUBLIC)
        default_storage.save(new_name, ContentFile(b"occupant"))

        with pytest.raises(FileExistsError):
            UploadService.change_visibility(upload, Upload.Visibility.PUBLIC)

        upload.refresh_from_db()
        assert upload.visibility == old_visibility
        assert upload.file.name == old_name
        assert default_storage.exists(old_name)

    def test_change_visibility_invalid_value_raises_error(
        self, upload_factory, clean_media
    ):
        upload = upload_factory(visibility=Upload.Visibility.PUBLIC)

        with pytest.raises(InvalidVisibilityError, match=r"not a valid visibility"):
            UploadService.change_visibility(upload, "bogus")

    def test_change_visibility_recovers_if_already_moved(
        self, upload_factory, clean_media
    ):
        upload = upload_factory(visibility=Upload.Visibility.PRIVATE)
        old_name = upload.file.name
        new_name = UploadService._target_path(old_name, Upload.Visibility.PUBLIC)

        with default_storage.open(old_name, "rb") as fh:
            default_storage.save(new_name, ContentFile(fh.read()))
        default_storage.delete(old_name)

        result = UploadService.change_visibility(upload, Upload.Visibility.PUBLIC)

        assert result.file.name == new_name
        assert result.visibility == Upload.Visibility.PUBLIC

        upload.refresh_from_db()
        assert upload.file.name == new_name
        assert upload.visibility == Upload.Visibility.PUBLIC
