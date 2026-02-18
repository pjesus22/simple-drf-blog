from django.conf import settings

from apps.uploads.storage.gcs import GCSMediaStorage
from apps.uploads.storage.local import LocalMediaStorage
from apps.uploads.storage.s3 import S3MediaStorage

STORAGE_BACKENDS = {
    "local": LocalMediaStorage,
    "s3": S3MediaStorage,
    "gcs": GCSMediaStorage,
}


def get_media_storage():
    backend = getattr(settings, "MEDIA_STORAGE_BACKEND", "local").lower()

    if backend not in STORAGE_BACKENDS:
        raise ValueError(f"Unsupported storage backend: {backend}")

    return STORAGE_BACKENDS[backend]()
