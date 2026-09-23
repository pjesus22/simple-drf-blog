import os

from django.utils import timezone

PRIVATE_STORAGE_PREFIX = "private"


def build_upload_relpath(instance, filename: str) -> str:
    """Build the path relative to the storage root"""
    _, ext = os.path.splitext(os.path.basename(filename))
    timestamp = timezone.now().strftime("%Y%m%d")

    return os.path.join(
        instance.purpose,
        timestamp,
        f"{instance.hash_sha256[:8]}{ext}",
    )


def is_private_storage_path(name: str) -> bool:
    """Returns True if the storage path lives under the private/ prefix"""
    return name.startswith(f"{PRIVATE_STORAGE_PREFIX}/")


def get_upload_path(instance, filename: str) -> str:
    """Returns the upload path.

    Path immutable after create; purpose segment reflects purpose at upload time.
    """
    relpath = build_upload_relpath(instance, filename)

    if instance.visibility != instance.Visibility.PUBLIC:
        return os.path.join(PRIVATE_STORAGE_PREFIX, relpath)

    return relpath
