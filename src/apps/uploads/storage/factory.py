from django.conf import settings

from apps.uploads.storage.gcs import GCSMediaStorage
from apps.uploads.storage.local import LocalMediaStorage
from apps.uploads.storage.s3 import S3MediaStorage

STORAGE_BACKENDS = {
    "local": LocalMediaStorage,
    "s3": S3MediaStorage,
    "gcs": GCSMediaStorage,
}

_storage_instance = None


def get_media_storage():
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    backend = getattr(settings, "MEDIA_STORAGE_BACKEND", "local").lower()

    if backend not in STORAGE_BACKENDS:
        raise ValueError(f"Unsupported storage backend: {backend}")

    _storage_instance = STORAGE_BACKENDS[backend]()

    return _storage_instance
