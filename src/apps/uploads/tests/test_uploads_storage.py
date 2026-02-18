import os

import pytest

from apps.uploads.storage.factory import STORAGE_BACKENDS, get_media_storage
from apps.uploads.storage.gcs import GCSMediaStorage
from apps.uploads.storage.local import LocalMediaStorage
from apps.uploads.storage.s3 import S3MediaStorage


class TestStorageFactory:
    @pytest.mark.parametrize(
        "backend, expected_class",
        [
            ("local", LocalMediaStorage),
            ("s3", S3MediaStorage),
            ("gcs", GCSMediaStorage),
        ],
        ids=("local", "s3", "gcs"),
    )
    def test_get_media_storage_returns_correct_backend(
        self, settings, backend, expected_class
    ):
        settings.MEDIA_STORAGE_BACKEND = backend
        storage = get_media_storage()
        assert isinstance(storage, expected_class)

    def test_get_media_storage_raises_on_unknown_backend(self, settings):
        settings.MEDIA_STORAGE_BACKEND = "unknown"
        with pytest.raises(ValueError, match="Unsupported storage backend: unknown"):
            get_media_storage()

    def test_get_media_storage_returns_new_instance_each_call(self, settings):
        """Singleton was removed — each call returns a fresh instance."""
        settings.MEDIA_STORAGE_BACKEND = "local"
        a = get_media_storage()
        b = get_media_storage()
        assert a is not b

    def test_storage_backends_registry_contains_all_expected_keys(self):
        assert set(STORAGE_BACKENDS.keys()) == {"local", "s3", "gcs"}


class TestLocalMediaStorage:
    def test_local_storage_health_check_returns_true_for_writable_dir(
        self, settings, tmp_path
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        storage = LocalMediaStorage()
        assert storage.health_check() is True

    def test_local_storage_health_check_returns_false_for_missing_dir(
        self, settings, tmp_path
    ):
        settings.MEDIA_ROOT = str(tmp_path / "nonexistent")
        storage = LocalMediaStorage()
        assert storage.health_check() is False

    def test_local_storage_health_check_returns_false_for_unwritable_dir(
        self, settings, tmp_path
    ):
        read_only = tmp_path / "readonly"
        read_only.mkdir()
        os.chmod(read_only, 0o444)
        settings.MEDIA_ROOT = str(read_only)
        storage = LocalMediaStorage()
        try:
            assert storage.health_check() is False
        finally:
            os.chmod(read_only, 0o755)  # restore so tmp_path cleanup works

    def test_local_storage_get_backend_name(self):
        storage = LocalMediaStorage()
        assert storage.get_backend_name() == "local"


class TestS3MediaStorage:
    def test_s3_storage_health_check_returns_true(self, mocker):
        storage = S3MediaStorage.__new__(S3MediaStorage)
        storage.bucket_name = "test-bucket"
        mock_client = mocker.MagicMock()
        mocker.patch.object(
            type(storage),
            "connection",
            new_callable=mocker.PropertyMock,
            return_value=mocker.MagicMock(meta=mocker.MagicMock(client=mock_client)),
        )
        mock_client.head_bucket.return_value = {}

        assert storage.health_check() is True
        mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")

    def test_s3_storage_health_check_returns_false_on_error(self, mocker):
        storage = S3MediaStorage.__new__(S3MediaStorage)
        storage.bucket_name = "test-bucket"
        mock_client = mocker.MagicMock()
        mocker.patch.object(
            type(storage),
            "connection",
            new_callable=mocker.PropertyMock,
            return_value=mocker.MagicMock(meta=mocker.MagicMock(client=mock_client)),
        )
        mock_client.head_bucket.side_effect = Exception("Access denied")

        assert storage.health_check() is False

    def test_s3_storage_get_backend_name(self):
        storage = S3MediaStorage.__new__(S3MediaStorage)
        assert storage.get_backend_name() == "s3"


class TestGCSMediaStorage:
    def test_gcs_storage_health_check_returns_true(self, mocker):
        storage = GCSMediaStorage.__new__(GCSMediaStorage)
        storage.bucket_name = "test-bucket"
        mock_bucket = mocker.MagicMock()
        mock_bucket.exists.return_value = True
        mock_client = mocker.MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mocker.patch.object(
            type(storage),
            "client",
            new_callable=mocker.PropertyMock,
            return_value=mock_client,
        )

        assert storage.health_check() is True
        mock_client.bucket.assert_called_once_with("test-bucket")
        mock_bucket.exists.assert_called_once()

    def test_gcs_storage_health_check_returns_false_on_error(self, mocker):
        storage = GCSMediaStorage.__new__(GCSMediaStorage)
        storage.bucket_name = "test-bucket"
        mock_client = mocker.MagicMock()
        mock_client.bucket.side_effect = Exception("Auth error")
        mocker.patch.object(
            type(storage),
            "client",
            new_callable=mocker.PropertyMock,
            return_value=mock_client,
        )

        assert storage.health_check() is False

    def test_gcs_storage_get_backend_name(self):
        storage = GCSMediaStorage.__new__(GCSMediaStorage)
        assert storage.get_backend_name() == "gcs"
